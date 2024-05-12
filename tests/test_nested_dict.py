from pydantic_cli.error import DuplicateKeyError
from pydantic_cli.nested_dict import merge_nested_dict


import pytest


@pytest.mark.parametrize(
    "nested_dict1, nested_dict2, expected",
    [
        (
            {"main": {"foo": {"a": 1}}},
            {"main": {"foo": {"b": 2}}},
            {"main": {"foo": {"a": 1, "b": 2}}},
        ),
        (
            {"level1": {"key1": {"a": {"x": 5}}}},
            {"level1": {"key1": {"b": 20}}},
            {"level1": {"key1": {"a": {"x": 5}, "b": 20}}},
        ),
    ],
)
def test_merge_nested_dict(nested_dict1, nested_dict2, expected):
    merged_dict = merge_nested_dict(nested_dict1, nested_dict2)
    assert merged_dict == expected


@pytest.mark.parametrize(
    "nested_dict1, nested_dict2",
    [
        ({"main": {"foo": {"a": 1}}}, {"main": {"foo": 0}}),
    ],
)
def test_merge_nested_dict_duplicate_key_error(nested_dict1, nested_dict2):
    with pytest.raises(DuplicateKeyError):
        merge_nested_dict(nested_dict1, nested_dict2)
