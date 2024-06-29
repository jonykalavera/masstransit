"""MassTransit main module"""

import logging
import typer
from pika.exchange_type import ExchangeType

from masstransit.consumer import ReconnectingRabbitMQConsumer
from masstransit.producer import Producer
from masstransit.models import Contract

app = typer.Typer()


def logging_setup(log_level):
    LOG_FORMAT = (
        "%(levelname)s |  %(asctime)s | %(name)s.%(funcName)s:"
        "%(lineno)d | %(message)s"
    )
    logging.basicConfig(level=log_level, format=LOG_FORMAT)


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
    producer = Producer(url, exchange, exchange_type, queue)
    producer.send(obj, routing_key)


@app.callback()
def main(log_level: str = "INFO"):
    """MassTransit for python."""
    logging_setup(log_level)


if __name__ == "__main__":
    app()
