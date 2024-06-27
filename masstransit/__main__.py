"""MassTransit main module"""

import logging

from masstransit.consumer import ReconnectingRabbitMQConsumer

LOG_FORMAT = (
    "%(levelname) -10s %(asctime)s %(name) -30s %(funcName) "
    "-35s %(lineno) -5d: %(message)s"
)
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
AMQP_URL = "amqp://guest:guest@localhost:5672/%2F"
consumer = ReconnectingRabbitMQConsumer(AMQP_URL)
consumer.run()
