"""Declared, hand-constructed opportunity sets; no empirical scenario fitting."""
from dataclasses import dataclass
from fractions import Fraction as F
from recovery_objective.core import Action, Step, Contract


@dataclass(frozen=True)
class Problem:
    name: str
    description: str
    contract: Contract
    scenarios: tuple
    scenario_names: tuple
    history: tuple


def offer(gain):
    baseline = Action('baseline', (3, 3))
    actions = (baseline,) if gain == 0 else (baseline, Action('boost', (3+F(gain), 2)))
    return Step((3, 3), actions)


def two_future(a=F(1), b=F(2), debt=F(2)):
    a, b, debt = F(a), F(b), F(debt)
    if not 0 < a < b <= debt: raise ValueError('require 0<a<b<=D')
    return Problem('ambiguous_allowance', 'One allowance: modest opportunity now; absent or better opportunity later.',
                   Contract((debt, 0), (0, 1), (0, 1)), ((offer(a), offer(0)), (offer(a), offer(b))),
                   ('opportunity_disappears', 'better_later'), ((F(3), F(3)),)*23)


def problems():
    main = two_future()
    cases = [main]
    for j, name in enumerate(('known_disappearance', 'known_better_later')):
        cases.append(Problem(name, 'Singleton declared future: perfect-model illustration, not prediction evidence.',
                             main.contract, (main.scenarios[j],), (main.scenario_names[j],), main.history))
    cases.append(Problem('three_period_delayed_revelation', 'Wait through a dominated early offer; future remains hidden at the second decision.',
                         main.contract, ((offer(F(1,2)), offer(1), offer(0)), (offer(F(1,2)), offer(1), offer(2))),
                         ('last_disappears', 'last_improves'), main.history))
    base = Action('baseline', (3, 3, 3))
    first, second = Action('help_first', (4, 3, 2)), Action('help_second', (3, 4, 2))
    current = Step((3, 3, 3), (base, first, second))
    cases.append(Problem('two_recipient_opportunities', 'Either recipient may have the final compensation opportunity.',
                         Contract((2, 1, 0), (0, 0, 1), (0, 0, 2)),
                         ((current, Step((3, 3, 3), (base, first))), (current, Step((3, 3, 3), (base, second)))),
                         ('first_only_later', 'second_only_later'), ((F(3),)*3,)*23))
    cases.append(Problem('no_donor_allowance', 'Zero regret need not mean any recovery is possible.',
                         Contract((2, 0), (0, 0), (0, 0)), main.scenarios, main.scenario_names, main.history))
    cases.append(Problem('no_headroom', 'No recipient surplus exists in any period.',
                         main.contract, ((offer(0), offer(0)),), ('blocked',), main.history))
    cases.append(Problem('three_possible_future_gains', 'One common current observation and three possible later gains.',
                         main.contract, tuple((offer(1), offer(g)) for g in (0, F(3,2), 2)),
                         ('none_later', 'moderate_later', 'large_later'), main.history))
    return tuple(cases)
