"""MassTransit main module"""

import logging
from importlib import import_module
import typer
from pika.exchange_type import ExchangeType

from masstransit.consumer import ReconnectingRabbitMQConsumer
from masstransit.producer import Producer

app = typer.Typer()


def logging_setup():
    LOG_FORMAT = (
        "%(levelname)s |  %(asctime)s | %(name)s.%(funcName)s:"
        "%(lineno)d | %(message)s"
    )
    logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)


@app.command()
def consume(
    exchange: str,
    queue: str,
    url="amqp://guest:guest@localhost:5672/%2F",
    exchange_type: ExchangeType = ExchangeType.fanout,
    routing_key: str | None = None,
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
    parts = contract_class_path.split(".")
    contract_mod = import_module(".".join(parts[:-1]))
    contract = getattr(contract_mod, parts[-1])
    obj = contract.model_validate_json(message)
    producer = Producer(url, exchange, exchange_type, queue)
    producer.send(obj, routing_key)


@app.callback()
def main():
    logging_setup()


if __name__ == "__main__":
    app()
