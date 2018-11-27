import pytest
from transform.utilities.general import merge_dicts


@pytest.mark.parametrize('inputs, expected_output', [
    (({1: 1}, {'test': 3}, {'another test': 'Some value'}), {1: 1, 'test': 3, 'another test': 'Some value'}),
    (({1: 1}, {1: 2}), {1: 2}),
    (({}, {}), {}),
    (({}, {1: 1}), {1: 1})
])
def test_merge_dicts(inputs, expected_output):
    assert merge_dicts(*inputs) == expected_output
