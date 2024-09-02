import os
import pytest
from pydantic_config.errors import CliError
from pydantic_config.parse import parse_args


def string_to_file(tmp_path, content):
    with open(tmp_path, "w") as f:
        f.write(content)


@pytest.fixture()
def tmp_file(tmp_path):
    return os.path.join(tmp_path, "dummy_config.json")


@pytest.fixture()
def tmp_yaml_file(tmp_path):
    return os.path.join(tmp_path, "dummy_config.yaml")


@pytest.fixture()
def tmp_toml_file(tmp_path):
    return os.path.join(tmp_path, "dummy_config.toml")


def test_config_file(tmp_file):
    config_dot_json = """
    {
        "foo": "bar"
    }
    """
    string_to_file(tmp_file, config_dot_json)

    argv = ["--hey", f"@{tmp_file}", "--hello", "world"]
    assert parse_args(argv) == {"hey": {"foo": "bar"}, "hello": "world"}


def test_override_config_file_pre(tmp_file):
    config_dot_json = """
    {
        "foo": "bar",
        "abc": "xyz"
    }
    """
    string_to_file(tmp_file, config_dot_json)

    argv = ["--hey", f"@{tmp_file}", "--hey.foo", "world"]
    assert parse_args(argv) == {"hey": {"foo": "world", "abc": "xyz"}}


def test_load_nested_config(tmp_file):
    config_dot_json = """
    {
        "foo": "bar",
        "abc": "xyz"
    }
    """
    string_to_file(tmp_file, config_dot_json)

    argv = ["--hey.config", f"@{tmp_file}"]
    assert parse_args(argv) == {"hey": {"config": {"foo": "bar", "abc": "xyz"}}}


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

    argv = ["--hey.foo", "world", "--hey", f"@{tmp_file}"]
    assert parse_args(argv) == {"hey": {"foo": "world", "abc": "xyz"}}


def test_sub_config_file(tmp_file):
    config_dot_json = """
    {
        "foo": "bar"
    }
    """
    string_to_file(tmp_file, config_dot_json)

    argv = ["--abc.xyz", "world", "--abc.ijk", f"@{tmp_file}"]

    assert parse_args(argv) == {"abc": {"xyz": "world", "ijk": {"foo": "bar"}}}


def test_sub_config_file_override(tmp_file):
    config_dot_json = """
    {
        "foo": "bar"
    }
    """
    string_to_file(tmp_file, config_dot_json)

    argv = ["--abc.ijk", f"@{tmp_file}", "--abc.ijk.foo", "world"]
    assert parse_args(argv) == {"abc": {"ijk": {"foo": "world"}}}


def test_wrong_config_file(tmp_file):
    config_dot_json = """
    {
        foo": "bar"
    }
    """
    string_to_file(tmp_file, config_dot_json)
    argv = ["--hey", f"@{tmp_file}", "--hello", "world"]

    with pytest.raises(CliError):
        parse_args(argv)


def test_yaml_config_file(tmp_yaml_file):
    config_dot_yaml = """
    foo: bar
    """
    string_to_file(tmp_yaml_file, config_dot_yaml)

    argv = ["--hey", f"@{tmp_yaml_file}", "--hello", "world"]
    assert parse_args(argv) == {"hey": {"foo": "bar"}, "hello": "world"}


def test_toml_config_file(tmp_toml_file):
    config_dot_toml = """
    foo = "bar"
    """
    string_to_file(tmp_toml_file, config_dot_toml)

    argv = ["--hey", f"@{tmp_toml_file}", "--hello", "world"]
    assert parse_args(argv) == {"hey": {"foo": "bar"}, "hello": "world"}
