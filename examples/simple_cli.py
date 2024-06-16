from pydantic_config import parse_argv, BaseConfig


class Config(BaseConfig):
    hello: str
    foo: int


def main(conf: Config):
    print(conf.model_dump())


if __name__ == "__main__":
    config = Config(**parse_argv())
    main(config)
