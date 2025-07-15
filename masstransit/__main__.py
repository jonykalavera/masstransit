"""MassTransit main module."""

import logging

import typer
from pika.exchange_type import ExchangeType

from masstransit import worker as _worker
from masstransit.consumer import ReconnectingRabbitMQConsumer
from masstransit.models import Config
from masstransit.producer import RabbitMQProducer
from masstransit.utils import django_setup, logging_setup

app = typer.Typer()
logger = logging.getLogger(__name__)


@app.command()
def consume(
    ctx: typer.Context,
    queue: str,
    exchange: str | None = None,
    exchange_type: ExchangeType = ExchangeType.fanout,
    routing_key: str | None = None,
    callback_path: str = "masstransit.consumer.default_callback",
):
    """Start a message consumer."""
    ReconnectingRabbitMQConsumer(
        ctx.obj["config"],
        queue,
        exchange,
        exchange_type,
        routing_key,
        callback_path,
    ).run()


@app.command()
def produce(
    ctx: typer.Context,
    exchange: str,
    queue: str,
    message: str,
    exchange_type: ExchangeType = ExchangeType.fanout,
    routing_key: str = "",
    contract_class_path: str = "masstransit.models.Contract",
):
    """Produce a message."""
    RabbitMQProducer(
        ctx.obj["config"],
        exchange,
        exchange_type,
        queue,
    ).send(
        message,
        routing_key,
        contract_class_path=contract_class_path,
    )


@app.command()
def worker(ctx: typer.Context, name: str):
    """Run worker from config."""
    config = ctx.obj["config"]
    log_level = ctx.obj["log_level"]
    django_settings = ctx.obj["django_settings"]
    _worker.start(config, name, log_level, django_settings)


@app.callback(no_args_is_help=True)
def main(
    ctx: typer.Context, log_level: str = "INFO", django_settings: str | None = None, configure_logging: bool = True
):
    """MassTransit for python."""
    config = Config()
    ctx.obj = {"config": config, "log_level": log_level, "django_settings": django_settings}
    django_setup(django_settings)
    if configure_logging:
        logging_setup(log_level)


if __name__ == "__main__":
    app()
