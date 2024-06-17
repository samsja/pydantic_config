from pydantic_config import validate_call, parse_argv


@validate_call
def main(hello: str, foo: int):
    print(f"hello: {hello}, foo: {foo}")


if __name__ == "__main__":
    main(**parse_argv())
