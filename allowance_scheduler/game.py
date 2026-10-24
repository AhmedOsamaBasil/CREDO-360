"""Exact finite minimax game with independently checkable primal/dual witnesses."""
from fractions import Fraction as F
from itertools import combinations


def solve_linear(matrix, rhs):
    n = len(rhs)
    if len(matrix) != n or any(len(row) != n for row in matrix):
        raise ValueError('square system required')
    a = [[F(x) for x in row]+[F(b)] for row, b in zip(matrix, rhs)]
    for col in range(n):
        pivot = next((r for r in range(col, n) if a[r][col]), None)
        if pivot is None: return None
        a[col], a[pivot] = a[pivot], a[col]
        scale = a[col][col]
        a[col] = [x/scale for x in a[col]]
        for r in range(n):
            if r != col:
                scale = a[r][col]
                a[r] = [x-scale*y for x, y in zip(a[r], a[col])]
    return tuple(row[-1] for row in a)


def verify_certificate(matrix, weights, dual, value):
    assert len(weights) == len(matrix) and len(dual) == len(matrix[0])
    assert all(x >= 0 for x in weights+dual) and sum(weights) == sum(dual) == 1
    upper = tuple(sum((weights[i]*matrix[i][j] for i in range(len(matrix))), F(0)) for j in range(len(dual)))
    lower = tuple(sum((dual[j]*row[j] for j in range(len(dual))), F(0)) for row in matrix)
    assert max(upper) <= value <= min(lower)
    # Weak duality plus both feasible witnesses proves equality and optimality.
    assert max(upper) == value == min(lower)
    return {'scenario_upper': upper, 'policy_lower': lower, 'gap': F(0)}


def minimax(matrix):
    matrix = tuple(tuple(F(x) for x in row) for row in matrix)
    if not matrix or not matrix[0] or any(len(row) != len(matrix[0]) for row in matrix):
        raise ValueError('nonempty rectangular matrix required')
    m, n = len(matrix), len(matrix[0])
    if n > 4 or m > 2000:
        raise ValueError('exact reference solver is intentionally limited to small games')
    unique = [i for i in range(m) if matrix[i] not in matrix[:i]]
    retained = [i for i in unique if not any(all(a <= b for a, b in zip(matrix[j], matrix[i])) and
                                            matrix[j] != matrix[i] for j in unique)]
    if len(retained) > 24:
        raise ValueError('too many nondominated rows for exhaustive exact support search')
    best = None
    for k in range(1, min(len(retained), n)+1):
        for rows in combinations(retained, k):
            for cols in combinations(range(n), k):
                equations = [[F(1)]*k+[F(0)]]
                equations += [[matrix[i][j] for i in rows]+[F(-1)] for j in cols]
                solution = solve_linear(equations, [F(1)]+[F(0)]*k)
                if solution is None or any(p < 0 for p in solution[:-1]): continue
                value = solution[-1]
                weights = tuple(solution[rows.index(i)] if i in rows else F(0) for i in range(m))
                if any(sum((weights[i]*matrix[i][j] for i in range(m)), F(0)) > value for j in range(n)): continue
                candidate = (value, weights)
                if best is None or candidate < best: best = candidate
    if best is None: raise AssertionError('no finite game solution found')
    value, weights = best
    # Dual feasibility at the primal value, using a separate vertex search.
    for k in range(1, n+1):
        for cols in combinations(range(n), k):
            for rows in combinations(retained, k-1):
                equations = [[F(1)]*k]+[[matrix[i][j] for j in cols] for i in rows]
                y = solve_linear(equations, [F(1)]+[value]*(k-1))
                if y is None or any(p < 0 for p in y): continue
                dual = tuple(y[cols.index(j)] if j in cols else F(0) for j in range(n))
                if any(sum((dual[j]*row[j] for j in range(n)), F(0)) < value for row in matrix): continue
                certificate = verify_certificate(matrix, weights, dual, value)
                return {'value': value, 'weights': weights, 'dual': dual, 'certificate': certificate,
                        'retained_rows': tuple(retained)}
    raise AssertionError('primal solution has no exact dual certificate')
