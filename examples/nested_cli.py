from pathlib import Path
from pydantic_config import parse_argv, BaseConfig
from pydantic import validate_call


class TrainingConfig(BaseConfig):
    lr: float = 3e-4
    batch_size: int


class DataConfig(BaseConfig):
    path: Path


def prepare_data(conf: DataConfig): ...  # prepare data


def train_model(conf: TrainingConfig): ...  # train model


@validate_call
def main(train: TrainingConfig, data: DataConfig):
    prepare_data(data)
    train_model(train)


if __name__ == "__main__":
    main(**parse_argv())
