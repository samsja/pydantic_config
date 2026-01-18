from pathlib import Path
from pydantic_config import cli, BaseConfig


class TrainingConfig(BaseConfig):
    lr: float = 3e-4
    batch_size: int = 32


class DataConfig(BaseConfig):
    path: Path = Path("./data")


class Config(BaseConfig):
    train: TrainingConfig = TrainingConfig()
    data: DataConfig = DataConfig()


def prepare_data(conf: DataConfig):
    print(f"Data config: {conf}")


def train_model(conf: TrainingConfig):
    print(f"Training config: {conf}")


def main(config: Config):
    prepare_data(config.data)
    train_model(config.train)


if __name__ == "__main__":
    config = cli(Config)
    main(config)
