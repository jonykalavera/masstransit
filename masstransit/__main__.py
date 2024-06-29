"""MassTransit main module"""

import logging
import logging.config

import typer
from pika.exchange_type import ExchangeType

from masstransit.consumer import ReconnectingRabbitMQConsumer
from masstransit.models import Contract
from masstransit.producer import RabbitMQProducer

app = typer.Typer()


def logging_setup(log_level):
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
    exchange: str,
    queue: str,
    url="amqp://guest:guest@localhost:5672/%2F",
    exchange_type: ExchangeType = ExchangeType.fanout,
    routing_key: str | None = None,
    callback_path: str = "masstransit.consumer.default_callback",
):
    """Start a message consumer"""
    ReconnectingRabbitMQConsumer(
        url,
        exchange,
        exchange_type,
        queue,
        routing_key,
        callback_path,
    ).run()


@app.command()
def produce(
    exchange: str,
    queue: str,
    message: str,
    url="amqp://guest:guest@localhost:5672/%2F",
    exchange_type: ExchangeType = ExchangeType.fanout,
    routing_key: str = "",
    contract_class_path: str = "masstransit.models.getting_started.GettingStarted",
):
    """Produce a message"""
    contract = Contract.from_import_string(contract_class_path)
    obj = contract.model_validate_json(message)
    producer = RabbitMQProducer(url, exchange, exchange_type, queue)
    producer.send(obj, routing_key)


@app.callback()
def main(log_level: str = "INFO"):
    """MassTransit for python."""
    logging_setup(log_level)


if __name__ == "__main__":
    app()
