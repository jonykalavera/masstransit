"""Configuration model."""

from pydantic import BaseModel, Field
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    YamlConfigSettingsSource,
)


class ConsumerConfig(BaseModel):
    """Consumer config."""

    queue: str
    exchange: str | None = None
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
    workers: list[WorkerConfig] = Field(default_factory=list)

    model_config = SettingsConfigDict(
        env_prefix="MASSTRANSIT_",
        yaml_file="masstransit.yaml",
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """Override default settings sources."""
        return (
            env_settings,
            init_settings,
            dotenv_settings,
            file_secret_settings,
            YamlConfigSettingsSource(settings_cls),
        )

    def get_worker(self, name: str) -> WorkerConfig | None:
        """Get worker config by name."""
        for worker in self.workers or []:
            if worker.name == name:
                return worker
        return None
