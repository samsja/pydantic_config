from pydantic_config.parse import parse_argv_as_list

ARTIFACT_PATH = "tests/artifacts"


def test_config_file():
    argv = ["main.py", "--hey", f"@{ARTIFACT_PATH}/dummy_config.json", "--hello", "world"]
    assert parse_argv_as_list(argv) == {"hey": {"foo": "bar"}, "hello": "world"}
