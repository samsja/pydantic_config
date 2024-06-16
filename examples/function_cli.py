from typing import Literal
from pydantic import validate_call
from pydantic_config import parse_argv, BaseConfig


class TrainConfig(BaseConfig):
    mixed_precision: Literal["fp16", "bf16"] = "fp16"
    batch_size: int = 32


@validate_call
def main(train_config: TrainConfig, debug_mode: bool = False):
    print(train_config.model_dump())
    print(debug_mode)


if __name__ == "__main__":
    args = parse_argv()
    main(**args)
