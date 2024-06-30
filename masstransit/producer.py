import logging
from typing import Any

import pika
from pika.exchange_type import ExchangeType

from masstransit.models.contract import Contract
from masstransit.models.message import Message

logger = logging.getLogger(__name__)


class RabbitMQProducer:
    """RabbitMQ producer for basic publish."""

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
        self.connection = pika.BlockingConnection(
            pika.URLParameters(self._amqp_url),
        )
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue=self._queue)

    def _get_message(self, message: Contract, message_kwargs: dict[str, Any] | None = None) -> Message:
        attributes = {
            "message": message.dict(),
            "messageType": message.messageType(),
            **(message_kwargs or {}),
        }
        mt_message = Message.model_validate(attributes)
        return mt_message

    def send_contract(
        self,
        obj: Contract,
        routing_key: str = "",
        message_kwargs: dict[str, Any] | None = None,
    ):
        """Publish message with contract object."""
        message = self._get_message(obj, message_kwargs)
        self.channel.basic_publish(
            exchange=self._exchange,
            routing_key=routing_key,
            body=message.json(),
        )
        logger.info("Sent message | %s | %s", routing_key, message.json())

    def send(
        self,
        message: str,
        routing_key: str = "",
        contract_class_path: str = "masstransit.models.GettingStarted",
        message_kwargs: dict[str, Any] | None = None,
    ):
        """Publish message with json message and contract-class-path."""
        contract = Contract.from_import_string(contract_class_path)
        obj = contract.model_validate_json(message)
        self.send_contract(obj, routing_key, message_kwargs)
