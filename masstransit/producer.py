"""MassTransit Producers."""

import logging
from typing import Any

import pika
from pika.exchange_type import ExchangeType

from masstransit.models import Config, Contract, Message

logger = logging.getLogger(__name__)


class RabbitMQProducer:
    """RabbitMQ producer for basic publish."""

    def __init__(
        self,
        config: Config,
        exchange: str,
        exchange_type: ExchangeType,
        queue: str,
        durable: bool = True,
    ):
        """Initializes RabbitMQProducer instance."""
        self._config = config
        self._exchange = exchange
        self._exchange_type = exchange_type
        self._queue = queue
        parameters = pika.URLParameters(self._config.dsn)
        self.connection = pika.BlockingConnection(parameters)
        logger.info("Connected to RabbitMQ: %s", parameters)
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue=self._queue, durable=durable)

    def _get_message(self, message: Contract, message_kwargs: dict[str, Any] | None = None) -> Message:
        attributes = {
            "message": message.model_dump(),
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
            body=message.model_dump_json(),
        )
        logger.info("Sent message to %s | %s | %s", self._queue, routing_key, message.json())

    def send(
        self,
        message: str,
        routing_key: str = "",
        contract_class_path: str = "masstransit.models.Contract",
        message_kwargs: dict[str, Any] | None = None,
    ):
        """Publish message with json message and contract-class-path."""
        contract = Contract.from_import_string(contract_class_path)
        obj = contract.model_validate_json(message)
        self.send_contract(obj, routing_key, message_kwargs)
