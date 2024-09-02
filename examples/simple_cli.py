from pydantic_config import parse_argv
from pydantic import validate_call


@validate_call
def main(hello: str, foo: int):
    print(f"hello: {hello}, foo: {foo}")


if __name__ == "__main__":
    main(**parse_argv())
