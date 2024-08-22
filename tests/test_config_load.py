import os
import pytest
from pydantic_config.parse import parse_argv_as_list


def string_to_file(tmp_path, content):
    with open(tmp_path, "w") as f:
        f.write(content)


@pytest.fixture()
def tmp_file(tmp_path):
    return os.path.join(tmp_path, "dummy_config.json")


def test_config_file(tmp_file):
    config_dot_json = """
    {
        "foo": "bar"
    }
    """
    string_to_file(tmp_file, config_dot_json)

    argv = ["main.py", "--hey", f"@{tmp_file}", "--hello", "world"]
    assert parse_argv_as_list(argv) == {"hey": {"foo": "bar"}, "hello": "world"}


def test_override_config_file_pre(tmp_file):
    config_dot_json = """
    {
        "foo": "bar",
        "abc": "xyz"
    }
    """
    string_to_file(tmp_file, config_dot_json)

    argv = ["main.py", "--hey", f"@{tmp_file}", "--hey.foo", "world"]
    assert parse_argv_as_list(argv) == {"hey": {"foo": "world", "abc": "xyz"}}


def test_override_config_file_post(tmp_file):
    """
    testing the same as the pre test, but with the config file specified last
    """
    config_dot_json = """
    {
        "foo": "bar",
        "abc": "xyz"
    }
    """
    string_to_file(tmp_file, config_dot_json)

    argv = ["main.py", "--hey.foo", "world", "--hey", f"@{tmp_file}"]
    assert parse_argv_as_list(argv) == {"hey": {"foo": "world", "abc": "xyz"}}


def test_sub_config_file(tmp_file):
    config_dot_json = """
    {
        "foo": "bar"
    }
    """
    string_to_file(tmp_file, config_dot_json)

    argv = ["main.py", "--abc.xyz", "world", "--abc.ijk", f"@{tmp_file}"]

    assert parse_argv_as_list(argv) == {"abc": {"xyz": "world", "ijk": {"foo": "bar"}}}


def test_sub_config_file_override(tmp_file):
    config_dot_json = """
    {
        "foo": "bar"
    }
    """
    string_to_file(tmp_file, config_dot_json)

    argv = ["main.py", "--abc.ijk", f"@{tmp_file}", "--abc.ijk.foo", "world"]
    assert parse_argv_as_list(argv) == {"abc": {"ijk": {"foo": "world"}}}
