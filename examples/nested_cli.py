from pathlib import Path
from pydantic_config import parse_argv, BaseConfig


class TrainingConfig(BaseConfig):
    lr: float = 3e-4
    batch_size: int


class DataConfig(BaseConfig):
    path: Path


class Config(BaseConfig):
    train: TrainingConfig
    data: DataConfig


def prepare_data(conf: DataConfig): ...  # prepare data


def train(conf: TrainingConfig): ...  # train model


def main(conf: Config):
    prepare_data(conf.data)
    train(conf.train)


if __name__ == "__main__":
    config = Config(**parse_argv())
    main(config)
