"""Configuration model."""

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class ConsumerConfig(BaseModel):
    """Consumer config."""

    exchange: str
    queue: str
    callback_path: str | None = None
    name: str | None = None
    number_of_consumers: int = 1
    routing_key: str | None = None
    exchange_type: str = "fanout"


class WorkerConfig(BaseModel):
    """Worker config."""

    name: str
    consumers: list[ConsumerConfig]


class Config(BaseSettings):
    """Config model."""

    dsn: str = "amqp://guest:guest@localhost:5672/%2F"
    log_level: str = "INFO"
    workers: list[WorkerConfig] | None = None

    model_config = SettingsConfigDict(
        env_prefix="MASSTRANSIT_",
    )
