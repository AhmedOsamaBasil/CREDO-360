"""Hand-constructed analytical witnesses, not sampled or held-out evidence."""
from dataclasses import dataclass
from fractions import Fraction as F
from recovery_objective.core import Action, Contract, Step, event_loss


@dataclass(frozen=True)
class Case:
    name: str
    purpose: str
    contract: Contract
    schedule: tuple
    history: tuple
    event_reference: tuple
    event_quality: tuple
    affected: tuple


def build(name, purpose, event_q, affected, steps, allowances, budgets, neutral_history=23):
    ref = (F(3),)*len(event_q)
    past = tuple(F(x) for x in event_q)
    debt = event_loss((ref,), (past,), affected)
    return Case(name, purpose, Contract(debt, allowances, budgets), tuple(steps),
                (past,)+(ref,)*neutral_history, (ref,), (past,), tuple(affected))


def all_cases():
    baseline = Action('baseline', (3, 3))
    compensate = Action('compensate', (4, 2))
    shared = Step((3, 3), (baseline, compensate))
    cases = [
        build('forgotten_event', 'Finite-window averaging forgets an unresolved old event.',
              (1, 3), (True, False), (shared, shared), (0, 1), (0, 2)),
        build('recent_event', 'Rolling equalization can repay part of a recent loss but optimize a different endpoint.',
              (1, 3), (True, False), (shared, shared), (0, 1), (0, 2), neutral_history=0),
        build('zero_harm_allowance', 'No compensation without slack or permitted donor loss on this frontier.',
              (1, 3), (True, False), (shared, shared), (0, 0), (0, 0)),
        build('no_recipient_headroom', 'Inability to deliver excess does not erase outstanding event loss.',
              (1, 3), (True, False), (Step((3, 3), (baseline, Action('help_other', (3, 4)))),)*2,
              (0, 1), (0, 2)),
    ]
    slack = Step((3, 3), (baseline, Action('help_first', (4, 3)), Action('help_second', (3, 4))))
    cases.append(build('shared_success_with_slack', 'Both direct rolling rules and recovery can fully compensate; no exclusive advantage.',
                       (2, 2), (True, True), (slack, slack), (0, 0), (0, 0)))
    three_b = Action('baseline', (3, 3, 3))
    first, second = Action('help_first', (4, 3, 2)), Action('help_second', (3, 4, 2))
    first_step = Step((3, 3, 3), (three_b, first, second))
    second_step = Step((3, 3, 3), (three_b, second))
    cases.append(build('future_opportunity_trap', 'Myopic normalized recovery loses to a known-future oracle and debt-weighted control.',
                       (1, 2, 3), (True, True, False), (first_step, second_step), (0, 0, 1), (0, 0, 2)))
    better_later = Step((3, 3), (baseline, Action('later_compensation', (5, 2))))
    cases.append(build('donor_budget_trap', 'Spending a scarce donor budget early makes greedy recovery worse than rolling Nash.',
                       (1, 3), (True, False), (shared, better_later), (0, 1), (0, 1)))
    cases.append(build('opportunity_disappears', 'Same first step and budget, but waiting now loses the only compensation opportunity.',
                       (1, 3), (True, False), (shared, Step((3, 3), (baseline,))), (0, 1), (0, 1)))
    cases.append(build('quality_ceiling', 'A reference already at maximum quality cannot be compensated by more quality.',
                       (1, 3), (True, False), (Step((5, 3), (Action('baseline', (5, 3)), Action('wasteful_transfer', (5, 2)))),)*2,
                       (0, 1), (0, 2)))
    return tuple(cases)
