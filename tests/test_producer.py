"""Producer tests."""

import pytest
from pika import URLParameters
from pika.exchange_type import ExchangeType

from masstransit.models import Config, GettingStarted
from masstransit.producer import RabbitMQProducer


class TestRabbitMQProducer:
    """Test RabbitMQProducer class."""

    config = Config(dsn="amqp://examplehost:5672/")
    exchange = "my_exchange"
    exchange_type = ExchangeType.direct
    queue = "my_queue"
    contract_payload = {"Value": "Hello world!"}
    message = '{"Value": "Hello world!"}'
    routing_key = "my_routing_key"
    contract_class_path = "masstransit.models.GettingStarted"

    @pytest.fixture(name="message")
    def message_fixture(self, mocker):
        """Message mock fixture."""
        message = mocker.patch("masstransit.producer.Message")
        message.return_value = message
        message.model_validate.return_value = message
        return message

    @pytest.fixture(name="blocking_connection")
    def blocking_connection_fixture(self, mocker):
        """BlockingConnection mock fixture."""
        blocking_connection = mocker.patch("pika.BlockingConnection")
        blocking_connection.return_value = blocking_connection
        blocking_connection.channel.return_value = mocker.Mock()
        return blocking_connection

    def test_init(self, blocking_connection):
        """We expect a blocking connection to be established with a channel."""
        producer = RabbitMQProducer(self.config, self.exchange, self.exchange_type, self.queue)
        blocking_connection.assert_called_once_with(URLParameters(self.config.dsn))
        assert producer.channel == blocking_connection.channel.return_value
        assert producer.connection == blocking_connection

    def test_send_contract(self, blocking_connection, message):
        """We expect to be able to send Contract objects."""
        producer = RabbitMQProducer(self.config, self.exchange, self.exchange_type, self.queue)
        producer.send_contract(GettingStarted(**self.contract_payload), self.routing_key)
        producer.channel.basic_publish.assert_called_once_with(
            body=message.model_dump_json(), exchange=self.exchange, routing_key=self.routing_key
        )

    def test_send(self, blocking_connection, message):
        """We expect to be able to send json strings providing a contract_class_path."""
        producer = RabbitMQProducer(self.config, self.exchange, self.exchange_type, self.queue)
        producer.send(self.message, self.routing_key, self.contract_class_path)
        producer.channel.basic_publish.assert_called_once_with(
            body=message.model_dump_json(), exchange=self.exchange, routing_key=self.routing_key
        )
