"""Pathwise loss-constrained timing over a finite threshold-policy class."""
from fractions import Fraction as F
from itertools import product
import numpy as np
from scipy.optimize import linprog

FRACTIONS = (F(0), F(1,4), F(1,2), F(3,4), F(1))
POLICIES = ('threshold_0','threshold_25','threshold_50','threshold_75','threshold_100','last')


def thresholds(debt):
    if not isinstance(debt,int) or debt <= 0: raise ValueError('positive integer debt required')
    return tuple(max(1,(debt*x.numerator+x.denominator-1)//x.denominator) for x in FRACTIONS)


def take(policy, t, horizon, gain, debt):
    if not 0 <= policy < len(POLICIES): raise ValueError('unknown policy')
    return gain > 0 and (t == horizon-1 or (policy < 5 and gain >= thresholds(debt)[policy]))


def selected_gain(policy, gains, debt):
    return next((min(debt,g) for t,g in enumerate(gains) if take(policy,t,len(gains),g,debt)),0)


def critical_scenarios(debt, current, bounds):
    cutoffs = thresholds(debt)
    if current < 0 or any(lo < 0 or hi < lo for lo,hi in bounds): raise ValueError('invalid gain bounds')
    axes = []
    for lo,hi in bounds:
        lo,hi = min(debt,lo),min(debt,hi)
        values = {lo,hi}
        for cutoff in cutoffs:
            values.update(x for x in (cutoff-1,cutoff) if lo <= x <= hi)
        axes.append(sorted(values))
    if np.prod([len(a) for a in axes]) > 20000: raise ValueError('reference grid too large')
    return tuple((min(debt,current),)+rest for rest in product(*axes))


def rational_distribution(values):
    weights = tuple(F(float(max(x,0))).limit_denominator(1000000) if x > 1e-10 else F(0) for x in values)
    total = sum(weights)
    if not total: raise ValueError('empty probability witness')
    return tuple(w/total for w in weights)


def solve_game(regret_units, debt):
    matrix = np.asarray(regret_units,dtype=float)/debt
    m,n = matrix.shape
    result = linprog([0.]*m+[1.], A_ub=np.column_stack((matrix.T,-np.ones(n))),b_ub=np.zeros(n),
                     A_eq=[[1.]*m+[0.]],b_eq=[1.],bounds=[(0,None)]*m+[(None,None)],method='highs')
    if not result.success: raise RuntimeError(result.message)
    p = rational_distribution(result.x[:m])
    y = rational_distribution(-result.ineqlin.marginals)
    sparse_y = tuple((j,w) for j,w in enumerate(y) if w)
    upper = max(sum((p[i]*int(regret_units[i][j]) for i in range(m)),F(0))/debt for j in range(n))
    lower = min(sum((w*int(row[j]) for j,w in sparse_y),F(0))/debt for row in regret_units)
    if not 0 <= upper-lower <= F(1,10_000_000): raise AssertionError('uncertified LP solution')
    return p, {'upper':upper,'lower':lower,'gap':upper-lower,'dual':sparse_y}


def plan(debt, current, bounds, alpha=F(1,2)):
    alpha = F(alpha)
    if not 0 <= alpha <= 1: raise ValueError('loss cap must lie in [0,1]')
    scenarios = critical_scenarios(debt,current,bounds)
    loss = tuple(tuple(debt-selected_gain(i,s,debt) for s in scenarios) for i in range(6))
    best = tuple(debt-max(s) for s in scenarios)
    regrets = tuple(tuple(x-b for x,b in zip(row,best)) for row in loss)
    worst = tuple(max(row) for row in loss)
    admitted = tuple(i for i,w in enumerate(worst) if F(w,debt) <= alpha)
    if admitted:
        small,certificate = solve_game(tuple(regrets[i] for i in admitted),debt)
        weights = tuple(small[admitted.index(i)] if i in admitted else F(0) for i in range(6))
    else:
        i = min(range(6),key=lambda j:(worst[j],max(regrets[j]),j))
        weights = tuple(F(int(j==i)) for j in range(6))
        certificate = {'upper':F(max(regrets[i]),debt),'lower':None,'gap':None,'dual':()}
    return {'debt':debt,'current':current,'bounds':tuple(bounds),'alpha':alpha,
            'feasible':bool(admitted),'admitted':admitted,'weights':weights,
            'worst_loss':tuple(F(w,debt) for w in worst),'certificate':certificate,
            'critical_scenarios':len(scenarios)}


def verify_plan(planned):
    debt = planned['debt']; scenarios = critical_scenarios(debt,planned['current'],planned['bounds'])
    rows = tuple(tuple(F(max(s)-selected_gain(i,s,debt),debt) for s in scenarios) for i in range(6))
    p = planned['weights']; cert = planned['certificate']
    assert len(p) == 6 and sum(p) == 1 and all(w >= 0 for w in p)
    worst = tuple(max(F(debt-selected_gain(i,s,debt),debt) for s in scenarios) for i in range(6))
    assert worst == planned['worst_loss']
    admitted = tuple(i for i,w in enumerate(worst) if w <= planned['alpha'])
    assert admitted == planned['admitted'] and bool(admitted) == planned['feasible']
    assert max(sum((p[i]*rows[i][j] for i in range(6)),F(0)) for j in range(len(scenarios))) == cert['upper']
    if admitted:
        assert all(not w or i in admitted for i,w in enumerate(p))
        dual = cert['dual']; assert sum(w for _,w in dual) == 1 and all(w >= 0 for _,w in dual)
        lower = min(sum((w*rows[i][j] for j,w in dual),F(0)) for i in admitted)
        assert lower == cert['lower'] and cert['gap'] == cert['upper']-lower
        assert 0 <= cert['gap'] <= F(1,10_000_000)
    return True
