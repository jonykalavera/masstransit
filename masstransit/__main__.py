"""MassTransit main module"""

import logging

import typer
from pika.exchange_type import ExchangeType

from masstransit.consumer import ReconnectingRabbitMQConsumer


app = typer.Typer()


def logging_setup():
    LOG_FORMAT = (
        "%(levelname) -10s %(asctime)s %(name) -30s %(funcName) "
        "-35s %(lineno) -5d: %(message)s"
    )
    logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)


@app.command()
def consumer(
    exchange: str,
    queue: str,
    url="amqp://guest:guest@localhost:5672/%2F",
    exchange_type: ExchangeType = ExchangeType.fanout,
    routing_key: str = "example.text",
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
def produce(value: str):
    """Produce a message"""
    print(f"Producing {value} not.")


@app.callback()
def main():
    logging_setup()


if __name__ == "__main__":
    app()
