__version__ = "0.0.1"

from pydantic_config.parse import parse_argv
from pydantic import BaseModel as PydanticBaseModel
from pydantic import ConfigDict


class BaseConfig(PydanticBaseModel):
    model_config = ConfigDict(extra="forbid")


__all__ = ["parse_argv", "BaseConfig"]
