from feedback_opportunity.diagnose import same_action


def test_serialized_action_comparison():
    assert same_action((2,3),[2,3])
    assert not same_action((2,3),[3,2])
