from pydantic_cli import parse_argv, BaseModel


class Config(BaseModel):
    hello: str
    foo: int


def main(conf: Config):
    print(conf.model_dump())


if __name__ == "__main__":
    config = Config(**parse_argv())
    main(config)
