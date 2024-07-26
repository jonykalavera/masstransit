"""MassTransit main module."""

import logging
import logging.config

import typer
from pika.exchange_type import ExchangeType

from masstransit.consumer import ReconnectingRabbitMQConsumer
from masstransit.models import Config
from masstransit.producer import RabbitMQProducer

app = typer.Typer()
logger = logging.getLogger(__name__)


def logging_setup(log_level):
    """Initializes logging configuration."""
    LOGGING = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "[%(asctime)s.%(msecs)03d] [%(levelname)s] [%(process)d] [%(name)s] %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
                "class": "logging.Formatter",
            }
        },
        "handlers": {
            "stdout": {
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
                "formatter": "default",
            }
        },
        "loggers": {
            "pika": {"handlers": ["stdout"], "level": logging.ERROR},
            "": {"handlers": ["stdout"], "level": log_level},
        },
    }

    logging.config.dictConfig(LOGGING)


@app.command()
def consume(
    ctx: typer.Context,
    queue: str,
    exchange: str | None = None,
    url="amqp://guest:guest@localhost:5672/%2F",
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
    url="amqp://guest:guest@localhost:5672/%2F",
    exchange_type: ExchangeType = ExchangeType.fanout,
    routing_key: str = "",
    contract_class_path: str = "masstransit.models.getting_started.GettingStarted",
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


@app.callback(no_args_is_help=True)
def main(ctx: typer.Context, dsn: str = "amqp://guest:guest@localhost:5672/%2F", log_level: str = "INFO"):
    """MassTransit for python."""
    config = Config(dsn=dsn)
    ctx.obj = {"config": config}
    logging_setup(log_level)
    logger.info("MassTransit for python.")


if __name__ == "__main__":
    app()
