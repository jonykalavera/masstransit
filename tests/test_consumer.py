"""Test masstransit.consumer."""

import pytest
from pika.exchange_type import ExchangeType

from masstransit.consumer import RabbitMQConsumer, ReconnectingRabbitMQConsumer
from masstransit.models import Config


def on_message_callback(message, basic_deliver, properties, **kwargs):
    """Callback for on_message."""
    assert message.message == "test message"


class TestRabbitMQConsumer:
    """Test case for RabbitMQConsumer."""

    config = Config(url="amqp://guest:guest@localhost:5672/%2F")
    exchange = "test_exchange"
    exchange_type = ExchangeType.direct
    queue = "test_queue"
    routing_key = "test_routing_key"

    @pytest.fixture(name="callback", autouse=True)
    def callback_fixture(self, mocker):
        """Callback test target fixture."""
        callback = mocker.patch("masstransit.consumer.default_callback", wraps=on_message_callback)
        return callback

    @pytest.fixture(name="rabbitmq_consumer")
    def rabbitmq_consumer_fixture(self):
        """RabbitMQConsumer test target fixture."""
        return RabbitMQConsumer(self.config, self.exchange, self.exchange_type, self.queue, self.routing_key)

    @pytest.fixture(name="mock_asyncio_connection", autouse=True)
    def mock_asyncio_connection_fixture(self, mocker):
        """AsyncioConnection mock fixture."""
        mock_asyncio_connection = mocker.patch("masstransit.consumer.AsyncioConnection")
        mock_asyncio_connection.return_value = mock_asyncio_connection
        return mock_asyncio_connection

    def test_connect(self, mocker, rabbitmq_consumer, mock_asyncio_connection):
        """We expect connect to create the connection."""
        mock_url_parameters = mocker.patch("masstransit.consumer.pika.URLParameters")

        rabbitmq_consumer.connect()

        mock_url_parameters.assert_called_once_with(self.config.url)
        mock_asyncio_connection.assert_called_once()

    def test_on_connection_open(self, mocker, rabbitmq_consumer):
        """We expect to create a channel after connection open."""
        mock_open_channel = mocker.patch.object(RabbitMQConsumer, "open_channel")

        mock_connection = mocker.MagicMock()
        rabbitmq_consumer.on_connection_open(mock_connection)

        mock_open_channel.assert_called_once()

    def test_on_connection_open_error(self, mocker, rabbitmq_consumer):
        """We expect to reconnect when connection error."""
        mock_reconnect = mocker.patch.object(RabbitMQConsumer, "reconnect")

        mock_connection = mocker.MagicMock()
        rabbitmq_consumer.on_connection_open_error(mock_connection, Exception("Connection error"))

        mock_reconnect.assert_called_once()

    def test_on_connection_closed(self, mocker, rabbitmq_consumer):
        """We expect to try to reconnect when connection is closed."""
        mock_reconnect = mocker.patch.object(RabbitMQConsumer, "reconnect")

        rabbitmq_consumer._closing = False
        mock_connection = mocker.MagicMock()
        rabbitmq_consumer.on_connection_closed(mock_connection, Exception("Connection closed"))

        mock_reconnect.assert_called_once()

    def test_on_channel_open(self, mocker, rabbitmq_consumer):
        """We expect callbacks to be set and to setup exchange when channel open."""
        mock_add_on_channel_close_callback = mocker.patch.object(RabbitMQConsumer, "add_on_channel_close_callback")
        mock_setup_exchange = mocker.patch.object(RabbitMQConsumer, "setup_exchange")

        mock_channel = mocker.MagicMock()
        rabbitmq_consumer.on_channel_open(mock_channel)

        mock_add_on_channel_close_callback.assert_called_once()
        mock_setup_exchange.assert_called_once_with(self.exchange)

    def test_on_channel_closed(self, mocker, rabbitmq_consumer):
        """We expect to close the connection when channel closed."""
        mock_close_connection = mocker.patch.object(RabbitMQConsumer, "close_connection")

        mock_channel = mocker.MagicMock()
        rabbitmq_consumer.on_channel_closed(mock_channel, Exception("Channel closed"))

        mock_close_connection.assert_called_once()

    def test_on_exchange_declareok(self, mocker, rabbitmq_consumer):
        """We expect to setup queue when exchange declareok."""
        mock_setup_queue = mocker.patch.object(RabbitMQConsumer, "setup_queue")

        rabbitmq_consumer.on_exchange_declareok(mocker.MagicMock(), self.exchange)

        mock_setup_queue.assert_called_once_with(self.queue)

    def test_on_queue_declareok(self, mocker, rabbitmq_consumer):
        """We expect channel to bind the queue when queue declareok."""
        mocker.patch.object(RabbitMQConsumer, "on_bindok")
        rabbitmq_consumer._channel = mocker.MagicMock()

        rabbitmq_consumer.on_queue_declareok(mocker.MagicMock(), self.queue)

        rabbitmq_consumer._channel.queue_bind.assert_called_once()

    def test_on_basic_qos_ok(self, mocker, rabbitmq_consumer):
        """We expect to start consuming when qos ok."""
        mock_start_consuming = mocker.patch.object(RabbitMQConsumer, "start_consuming")

        rabbitmq_consumer.on_basic_qos_ok(mocker.MagicMock())

        mock_start_consuming.assert_called_once()

    def test_on_message(self, mocker, rabbitmq_consumer, callback):
        """We expect to execute callback when new message arrives."""
        mock_model_validate_json = mocker.patch("masstransit.consumer.Message.model_validate_json")
        mock_acknowledge_message = mocker.patch.object(RabbitMQConsumer, "acknowledge_message")
        mock_model_validate_json.return_value = mocker.MagicMock(message="test message")
        channel = mocker.MagicMock()
        basic_deliver = mocker.MagicMock()
        properties = mocker.MagicMock()
        body = b'{"message": "test message"}'

        rabbitmq_consumer.on_message(
            channel,
            basic_deliver,
            properties,
            body,
        )

        mock_model_validate_json.assert_called_once()
        mock_acknowledge_message.assert_called_once()
        callback.assert_called_once_with(
            message=mock_model_validate_json.return_value,
            basic_deliver=basic_deliver,
            properties=properties,
            channel=channel,
        )

    def test_on_connection_closed_reconnect(self, mocker, rabbitmq_consumer):
        """We expect to reconnect when connection closed unexpectedly."""
        rabbitmq_consumer._closing = False
        rabbitmq_consumer._connection = mocker.MagicMock()
        rabbitmq_consumer.on_connection_closed(mocker.MagicMock(), Exception("Connection closed"))

        assert rabbitmq_consumer.should_reconnect

    def test_on_channel_closed_reconnect(self, mocker, rabbitmq_consumer):
        """We expect to reconnect when channel closed."""
        rabbitmq_consumer._connection = mocker.MagicMock(is_closing=False, is_closed=False)

        rabbitmq_consumer.on_channel_closed(mocker.MagicMock(), Exception("Channel closed"))

        rabbitmq_consumer._connection.close.assert_called_once()


class TestReconnectingRabbitMQConsumer:
    """ReconnectingRabbitMQConsumer test case."""

    amqp_url = "amqp://guest:guest@localhost:5672/%2F"
    exchange = "test_exchange"
    exchange_type = ExchangeType.fanout
    queue = "test_queue"
    routing_key = ""
    callback_path = "masstransit.consumer.default_callback"

    @pytest.fixture(name="callback", autouse=True)
    def callback_fixture(self, mocker):
        """Callback mock fixture."""
        mock = mocker.MagicMock()
        return mock

    @pytest.fixture(name="mock_rabbitmq_consumer", autouse=True)
    def mock_rabbitmq_consumer_fixture(self, mocker):
        """RabbitMQConsumer mock fixture."""
        mock = mocker.patch("masstransit.consumer.RabbitMQConsumer")
        mock.return_value = mock
        mock.should_reconnect = False
        return mock

    @pytest.fixture(name="mock_sleep", autouse=True)
    def mock_sleep_fixture(self, mocker):
        """Mock sleep fixture."""
        mock = mocker.patch("time.sleep")
        return mock

    @pytest.fixture(name="reconnecting_consumer")
    def reconnecting_consumer_fixture(self, mock_rabbitmq_consumer):
        """ReconnectingRabbitMQConsumer fixture. Test case target."""
        reconnecting_consumer = ReconnectingRabbitMQConsumer(
            self.config.url,
            self.exchange,
            self.exchange_type,
            self.queue,
            self.routing_key,
            self.callback_path,
            consumer_class=mock_rabbitmq_consumer,
        )
        return reconnecting_consumer

    def test_stops_on_keyboard_interrupt(self, reconnecting_consumer, mock_rabbitmq_consumer):
        """We expect to stop consumer when KeyboardInterrupt."""
        mock_rabbitmq_consumer.run.side_effect = KeyboardInterrupt()

        reconnecting_consumer.run()

        mock_rabbitmq_consumer.run.assert_called_once()
        mock_rabbitmq_consumer.stop.assert_called_once()

    def test_maybe_reconnects_when_consumer_drops(self, reconnecting_consumer, mock_rabbitmq_consumer, mock_sleep):
        """We expect the consumer will try to reconnect with an increasing delay."""
        mock_rabbitmq_consumer.should_reconnect = True
        mock_rabbitmq_consumer.run.side_effect = [None, KeyboardInterrupt()]

        reconnecting_consumer.run()

        assert mock_rabbitmq_consumer.call_count == 2
        assert mock_rabbitmq_consumer.run.call_count == 2
        assert mock_rabbitmq_consumer.stop.call_count == 2
        mock_sleep.assert_called_once()
