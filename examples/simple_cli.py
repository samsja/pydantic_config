from pydantic_config import cli, BaseConfig


class Config(BaseConfig):
    hello: str
    foo: int


def main(config: Config):
    print(f"hello: {config.hello}, foo: {config.foo}")


if __name__ == "__main__":
    config = cli(Config)
    main(config)
