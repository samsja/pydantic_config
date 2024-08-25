"""
this test is not a pytest test but a visual one.

Just call `python tests/ui_testing.py --foo bar` to see the ui and error rendering.
"""

from pydantic_config import parse_argv

if __name__ == "__main__":
    print(parse_argv())
