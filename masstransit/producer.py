import logging
from typing import Any

import pika
from pika.exchange_type import ExchangeType

from masstransit.models.contract import Contract
from masstransit.models.message import Message

logger = logging = logging.getLogger(__name__)


class RabbitMQProducer:
    def __init__(
        self,
        amqp_url: str,
        exchange: str,
        exchange_type: ExchangeType,
        queue: str,
    ):
        self._amqp_url = amqp_url
        self._exchange = exchange
        self._exchange_type = exchange_type
        self._queue = queue

    def send(
        self,
        message: Contract,
        routing_key="",
        message_kwargs: dict[str, Any] | None = None,
    ):
        attributes = {
            "message": message.dict(),
            "messageType": message.messageType(),
            **(message_kwargs or {}),
        }
        mt_message = Message.model_validate(attributes)
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(self._ampq_url),
        )
        channel = connection.channel()
        channel.queue_declare(queue=self._queue)
        channel.basic_publish(
            exchange=self._exchange,
            routing_key=routing_key,
            body=mt_message.json(),
        )
        logger.info("Sent message | %s | %s", routing_key, mt_message.json())
