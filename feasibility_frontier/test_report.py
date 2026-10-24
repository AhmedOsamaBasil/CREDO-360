from fractions import Fraction as F
from feasibility_frontier.run import quantile,opportunity_counts,validate_monotonicity
from feasibility_frontier.core import frontier,required
from feasibility_frontier.test_core import option


def test_quantiles_use_declared_nearest_rank_without_interpolation():
    assert quantile([F(1),F(2),F(3),F(4)],F(1,2))==2
    assert quantile([F(1),F(2),F(3),F(4)],F(9,10))==4
    assert quantile([],F(1,2)) is None


def test_positive_opportunities_are_not_joint_feasibility():
    p=((option(0,0,r=0),option(300,250)),)*2
    counts=opportunity_counts(p,500,250,250,F(1))
    assert counts=={'positive_periods':2,'substantial_periods':2}
    assert required(frontier(p,1000)['frontiers'],2,250,250) is None


def test_monotonicity_across_all_declared_allowances():
    p=((option(0,0,r=0),option(500,125,F(3,2),1),option(750,250,F(1),2)),)*4
    validate_monotonicity(frontier(p,2500)['frontiers'])


def test_quarter_target_opportunity_does_not_use_a_zero_threshold():
    p=((option(0,0,r=0),),)*4
    assert opportunity_counts(p,1,0,0,F(1))=={'positive_periods':0,'substantial_periods':0}
