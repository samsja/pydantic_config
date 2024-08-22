import pytest

from pydantic_config.parse import DuplicateKeyError, CliArgError, merge_nested_dict, parse_nested_arg


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


def test_parse_nested_arg():
    input_dict = {"main.hello": "world", "main.foo": "bar"}
    expected_output = {"main": {"hello": "world", "foo": "bar"}}
    assert parse_nested_arg(input_dict) == expected_output


def test_parse_nested_arg_failure_due_to_main():
    input_dict = {"main.": "world", "main.foo": "bar"}
    with pytest.raises(CliArgError):
        parse_nested_arg(input_dict)


@pytest.mark.parametrize(
    "input_dict, expected_output",
    [
        (
            {"main.hello": "world", "main.foo.bar": "baz"},
            {"main": {"hello": "world", "foo": {"bar": "baz"}}},
        ),
        (
            {
                "main.hello": "world",
                "main.foo.bar.qux.corge": "grault",
                "main.foo.bar.a": "b",
            },
            {
                "main": {
                    "hello": "world",
                    "foo": {"bar": {"qux": {"corge": "grault"}, "a": "b"}},
                }
            },
        ),
    ],
)
def test_parse_nested_multi_level_arg(input_dict, expected_output):
    assert parse_nested_arg(input_dict) == expected_output


def test_parse_nested_multi_level_arg_failure_due_to_duplicate_key():
    input_dict = {"main.hello": "world", "main.hello.foo": "bar"}
    with pytest.raises(DuplicateKeyError):
        parse_nested_arg(input_dict)
