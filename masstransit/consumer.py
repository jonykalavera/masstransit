"""MassTransit Consumers."""

import functools
import logging
import time
from asyncio import get_running_loop
from enum import Enum
from functools import partial
from typing import TYPE_CHECKING

import pika
from pika.adapters.asyncio_connection import AsyncioConnection
from pika.exchange_type import ExchangeType
from pydantic import ValidationError

from masstransit.models import Config, Message
from masstransit.utils import import_string

if TYPE_CHECKING:
    from pika.spec import Basic, BasicProperties

logger = logging.getLogger(__name__)


class MessageAction(Enum):
    """Actions that can be taken on messages."""

    ACK = 100
    NACK = 200
    NACK_AND_REQUEUE = 201
    REJECT = 400
    REJECT_AND_REQUEUE = 401


async def default_callback(
    message: Message, basic_deliver: "Basic.Deliver", properties: "BasicProperties", **kwargs
) -> None:
    """Logs the messages."""
    logger.info(
        "Received message # %s from %s | %s | %s",
        basic_deliver.delivery_tag,
        properties.app_id,
        message.messageId,
        message.message,
    )


class RabbitMQConsumer:
    """RabbitMQ consumer for MassTransit.

    This is a consumer that will handle unexpected interactions
    with RabbitMQ such as channel and connection closures.

    If RabbitMQ closes the connection, this class will stop and indicate
    that reconnection is necessary. You should look at the output, as
    there are limited reasons why the connection may be closed, which
    usually are tied to permission related issues or socket timeouts.

    If the channel is closed, it will indicate a problem with one of the
    commands that were issued and that should surface in the output as well.

    """

    def __init__(
        self,
        config: Config,
        queue: str,
        exchange: str | None = None,
        exchange_type: ExchangeType = ExchangeType.fanout,
        routing_key: str | None = None,
        callback_path: str = "masstransit.consumer.default_callback",
    ):
        """Create a new instance of the consumer class."""
        self.should_reconnect = False
        self.was_consuming = False

        self._connection = None
        self._channel = None
        self._closing = False
        self._consumer_tag = None
        self._config = config
        self._queue = queue
        self._exchange = exchange
        self._exchange_type = exchange_type
        self._routing_key = routing_key
        self._consuming = False
        # In production, experiment with higher prefetch values
        # for higher consumer throughput
        self._prefetch_count = 1
        self._on_message_handler = import_string(callback_path)

    def connect(self):
        """Connects to RabbitMQ, returning the connection handle.

        When the connection is established, the on_connection_open method
        will be invoked by pika.
        """
        logger.debug("Connecting to %s", self._config.dsn)
        return AsyncioConnection(
            parameters=pika.URLParameters(self._config.dsn),
            on_open_callback=self.on_connection_open,
            on_open_error_callback=self.on_connection_open_error,
            on_close_callback=self.on_connection_closed,
        )

    def close_connection(self):
        """Closes current connection instance."""
        self._consuming = False
        if self._connection.is_closing or self._connection.is_closed:
            logger.info("Connection is closing or already closed")
        else:
            logger.info("Closing connection")
            self._connection.close()

    def on_connection_open(self, _unused_connection):
        """Called once the connection to RabbitMQ been established.

        It passes the handle to the connection object in
        case we need it, but in this case, we'll just mark it unused.

        Args:
          pika: adapters.asyncio_connection.AsyncioConnection _unused_connection:
        The connection
          _unused_connection:
        """
        parameters = pika.URLParameters(self._config.dsn)
        logger.info("Connection opened: %s", parameters)
        self.open_channel()

    def on_connection_open_error(self, _unused_connection, err):
        """This method is called by pika if the connection to RabbitMQ can't be established.

        Args:
          pika: adapters.asyncio_connection.AsyncioConnection _unused_connection:
        The connection
          Exception: err: The error
          _unused_connection: param err:
          err:
        """
        logger.error("Connection open failed: %s", err)
        self.reconnect()

    def on_connection_closed(self, _unused_connection, reason):
        """Invoked when the connection to RabbitMQ is closed unexpectedly.

        Since it is unexpected, we will reconnect to RabbitMQ if it disconnects.

        Args:
          pika: connection.Connection connection: The closed connection obj
          Exception: reason: exception representing reason for loss of
        connection.
          _unused_connection: param reason:
          reason:
        """
        self._channel = None
        if self._closing:
            self._connection.ioloop.stop()
        else:
            logger.warning("Connection closed, reconnect necessary: %s", reason)
            self.reconnect()

    def reconnect(self):
        """Invoked if the connection can't be opened or is closed.

        Indicates that a reconnect is necessary then stops the io-loop.
        """
        self.should_reconnect = True
        self.stop()

    def open_channel(self):
        """Open a new channel with RabbitMQ by issuing the Channel.Open RPC command.

        When RabbitMQ responds that the channel is open, the on_channel_open callback will be invoked by pika.
        """
        logger.debug("Creating a new channel")
        self._connection.channel(on_open_callback=self.on_channel_open)

    def on_channel_open(self, channel):
        """This method is invoked by pika when the channel has been opened.

        The channel object is passed in so we can make use of it.
        Since the channel is now open, we'll declare the exchange to use.

        Args:
          pika: channel.Channel channel: The channel object
          channel:
        """
        logger.debug("Channel opened")
        self._channel = channel
        self.add_on_channel_close_callback()
        if self._exchange:
            self.setup_exchange(self._exchange)
        else:
            self.setup_queue(self._queue)

    def add_on_channel_close_callback(self):
        """This method tells pika to call the on_channel_closed method if RabbitMQ unexpectedly closes the channel."""
        logger.debug("Adding channel close callback")
        self._channel.add_on_close_callback(self.on_channel_closed)

    def on_channel_closed(self, channel, reason):
        """Invoked when RabbitMQ unexpectedly closes the channel.

        Channels are usually closed if you attempt to do something that
        violates the protocol, such as re-declare an exchange or queue with
        different parameters. In this case, we'll close the connection
        to shutdown the object.

        Args:
          pika: channel.Channel: The closed channel
          Exception: reason: why the channel was closed
          channel: param reason:
          reason:
        """
        logger.info("Channel %i was closed: %s", channel, reason)
        self.close_connection()

    def setup_exchange(self, exchange_name):
        """Setup the exchange on RabbitMQ by invoking the Exchange.Declare RPC command.

        When it is complete, the on_exchange_declareok method will be invoked by pika.

        Args:
          str: unicode exchange_name: The name of the exchange to declare
          exchange_name:
        """
        logger.debug("Declaring exchange: %s", exchange_name)
        # Note: using functools.partial is not required, it is demonstrating
        # how arbitrary data can be passed to the callback when it is called
        cb = functools.partial(self.on_exchange_declareok, userdata=exchange_name)
        self._channel.exchange_declare(
            exchange=exchange_name,
            exchange_type=self._exchange_type,
            durable=True,
            callback=cb,
        )

    def on_exchange_declareok(self, _unused_frame, userdata):
        """Invoked by pika when RabbitMQ has finished the Exchange.Declare RPC command.

        Args:
          pika: Frame.Method unused_frame: Exchange.DeclareOk response frame
          str: unicode userdata: Extra user data (exchange name)
          _unused_frame: param userdata:
          userdata:
        """
        logger.debug("Exchange declared: %s", userdata)
        self.setup_queue(self._queue)

    def setup_queue(self, queue_name):
        """Setup the queue on RabbitMQ by invoking the Queue.Declare RPC command.

        When it is complete, the on_queue_declareok method will be invoked by pika.

        Args:
          str: unicode queue_name: The name of the queue to declare.
          queue_name:
        """
        logger.debug("Declaring queue %s", queue_name)
        cb = functools.partial(self.on_queue_declareok, userdata=queue_name)
        self._channel.queue_declare(queue=queue_name, callback=cb, durable=True)

    def on_queue_declareok(self, _unused_frame, userdata):
        """Method invoked by pika when the Queue.Declare RPC call made in setup_queue has completed.

        In this method we will bind the queue and exchange together with the routing key by issuing the
        Queue.Bind RPC command. When this command is complete, the on_bindok method will be invoked by pika.

        Args:
          pika: frame.Method _unused_frame: The Queue.DeclareOk frame
          str: unicode userdata: Extra user data (queue name)
          _unused_frame: param userdata:
          userdata:
        """
        queue_name = userdata
        logger.debug("Binding %s to %s with %s", self._exchange, queue_name, self._routing_key)
        cb = functools.partial(self.on_bindok, userdata=queue_name)
        if self._exchange:
            self._channel.queue_bind(queue_name, self._exchange, routing_key=self._routing_key, callback=cb)
        else:
            self.set_qos()

    def on_bindok(self, _unused_frame, userdata):
        """Invoked by pika when the Queue.Bind method has completed.

        At this point we will set the prefetch count for the channel.

        Args:
          pika: frame.Method _unused_frame: The Queue.BindOk response frame
          str: unicode userdata: Extra user data (queue name)
          _unused_frame: param userdata:
          userdata:
        """
        logger.debug("Queue bound: %s", userdata)
        self.set_qos()

    def set_qos(self):
        """This method sets up the consumer prefetch to only be delivered one message at a time.

        The consumer must acknowledge this message before RabbitMQ will deliver another one. You should experiment
        with different prefetch values to achieve desired performance.
        """
        self._channel.basic_qos(prefetch_count=self._prefetch_count, callback=self.on_basic_qos_ok)

    def on_basic_qos_ok(self, _unused_frame):
        """Invoked by pika when the Basic.QoS method has completed.

        At this point we will start consuming messages by calling start_consuming
        which will invoke the needed RPC commands to start the process.

        Args:
          pika: frame.Method _unused_frame: The Basic.QosOk response frame
          _unused_frame:
        """
        logger.debug("QOS set to: %d", self._prefetch_count)
        self.start_consuming()

    def start_consuming(self):
        """This method sets up the consumer so that the object is notified if RabbitMQ cancels the consumer.

        It then issues the Basic.Consume RPC command
        which returns the consumer tag that is used to uniquely identify the
        consumer with RabbitMQ. We keep the value to use it when we want to
        cancel consuming. The on_message method is passed in as a callback pika
        will invoke when a message is fully received.
        """
        logger.debug("Issuing consumer related RPC commands")
        self.add_on_cancel_callback()
        self._consumer_tag = self._channel.basic_consume(self._queue, self.on_message)
        self.was_consuming = True
        self._consuming = True
        logger.info("Consuming queue: %s.", self._queue)

    def add_on_cancel_callback(self):
        """Add a callback that will be invoked if RabbitMQ cancels the consumer for some reason.

        If RabbitMQ does cancel the consumer, on_consumer_cancelled will be invoked by pika.
        """
        logger.debug("Adding consumer cancellation callback")
        self._channel.add_on_cancel_callback(self.on_consumer_cancelled)

    def on_consumer_cancelled(self, method_frame):
        """Invoked by pika when RabbitMQ sends a Basic.Cancel for a consumer receiving messages.

        Args:
          pika: frame.Method method_frame: The Basic.Cancel frame
          method_frame:
        """
        logger.info("Consumer was canceled remotely, shutting down: %r", method_frame)
        if self._channel:
            self._channel.close()

    def on_message(self, channel, basic_deliver, properties, body):
        """Invoked by pika when a message is delivered from RabbitMQ.

        The channel is passed for your convenience. The basic_deliver object that
        is passed in carries the exchange, routing key, delivery tag and
        a redelivered flag for the message. The properties passed in is an
        instance of BasicProperties with the message properties and the body
        is the message that was sent.
        """
        message = Message.model_validate_json(body)
        handler = self._on_message_handler or default_callback
        try:
            task = get_running_loop().create_task(
                handler(
                    message=message,
                    basic_deliver=basic_deliver,
                    properties=properties,
                    channel=channel,
                )
            )
            task.add_done_callback(partial(self._task_done_callback, basic_deliver=basic_deliver))
        except ValidationError as err:
            logger.error("ABORTING! %s Body: %s", err, body)
            self.stop()

    def _task_done_callback(self, task, basic_deliver):
        result = task.result()
        try:
            action = MessageAction(result)
        except (TypeError, ValueError):
            action = MessageAction.ACK

        match action:
            case MessageAction.ACK:
                self.acknowledge_message(basic_deliver.delivery_tag)
                return
            case MessageAction.NACK:
                self.nack_message(basic_deliver.delivery_tag)
                return
            case MessageAction.NACK_AND_REQUEUE:
                self.nack_message(basic_deliver.delivery_tag, requeue=True)
                return
            case MessageAction.REJECT:
                self.reject_message(basic_deliver.delivery_tag)
                return
            case MessageAction.REJECT_AND_REQUEUE:
                self.reject_message(basic_deliver.delivery_tag, requeue=True)
                return
        raise RuntimeError("Unknown message action")

    def acknowledge_message(self, delivery_tag):
        """Acknowledge the message delivery from RabbitMQ by sending a Basic.Ack RPC method for the delivery tag.

        Args:
          int: delivery_tag: The delivery tag from the Basic.Deliver frame
          delivery_tag:
        """
        logger.debug("Acknowledging message %s", delivery_tag)
        self._channel.basic_ack(delivery_tag)

    def nack_message(self, delivery_tag, requeue=False):
        """Reject the message, such as putting it back on the queue."""
        logger.debug("Rejecting message %s", delivery_tag)
        self._channel.basic_nack(delivery_tag, requeue=requeue)

    def reject_message(self, delivery_tag, requeue=False):
        """Reject the message, such as putting it back on the queue."""
        logger.debug("Rejecting message %s", delivery_tag)
        self._channel.basic_reject(delivery_tag, requeue=requeue)

    def stop_consuming(self):
        """Tell RabbitMQ that you would like to stop consuming by sending the Basic.Cancel RPC command."""
        if self._channel:
            logger.debug("Sending a Basic.Cancel RPC command to RabbitMQ")
            cb = functools.partial(self.on_cancelok, userdata=self._consumer_tag)
            self._channel.basic_cancel(self._consumer_tag, cb)

    def on_cancelok(self, _unused_frame, userdata):
        """This method is invoked by pika when RabbitMQ acknowledges the cancellation of a consumer.

        At this point we will close the channel. This will invoke the on_channel_closed method once the channel
        has been closed, which will in-turn close the connection.

        Args:
          pika: frame.Method _unused_frame: The Basic.CancelOk frame
          str: unicode userdata: Extra user data (consumer tag)
          _unused_frame: param userdata:
          userdata:
        """
        self._consuming = False
        logger.debug("RabbitMQ acknowledged the cancellation of the consumer: %s", userdata)
        self.close_channel()

    def close_channel(self):
        """Call to close the channel with RabbitMQ cleanly by issuing the Channel.Close RPC command."""
        logger.info("Closing the channel")
        self._channel.close()

    def run(self):
        """Run the consumer by connecting to RabbitMQ.

        Starting the IOLoop to block and allow the AsyncioConnection to operate.
        """
        self._connection = self.connect()
        self._connection.ioloop.run_forever()

    def stop(self):
        """Cleanly shutdown the connection to RabbitMQ by stopping the consumer with RabbitMQ.

        When RabbitMQ confirms the cancellation, on_cancelok will be invoked by pika, which will thenclosing
        closing the channel and connection. The IOLoop is started again because this method is invoked
        when CTRL-C is pressed raising a KeyboardInterrupt exception. This Raises:

          communicate: with RabbitMQ
          the: IOLoop will be buffered but not processed.
        """
        if not self._closing:
            self._closing = True
            logger.info("Stopping")
            if self._consuming:
                self.stop_consuming()
                self._connection.ioloop.run_forever()
            else:
                self._connection.ioloop.stop()
            logger.info("Stopped")


class ReconnectingRabbitMQConsumer:
    """RabbitMQConsumer that will reconnect if the nested RabbitMQConsumer indicates that a reconnect is necessary."""

    def __init__(
        self,
        config: Config,
        queue: str,
        exchange: str | None = None,
        exchange_type: ExchangeType = ExchangeType.fanout,
        routing_key: str | None = None,
        callback_path: str = "masstransit.consumer.default_callback",
        consumer_class=RabbitMQConsumer,
    ):
        """Initializes the ReconnectingRabbitMQConsumer instance."""
        self._reconnect_delay = 0
        self._config = config
        self._exchange = exchange
        self._exchange_type = exchange_type
        self._queue = queue
        self._routing_key = routing_key
        self._callback_path = callback_path
        self._consumer_class = consumer_class
        self._connect_consumer()

    def run(self):
        """Run the consumer loop."""
        while True:
            try:
                self._consumer.run()
            except KeyboardInterrupt:
                self._consumer.stop()
                break
            self._maybe_reconnect()

    def _maybe_reconnect(self):
        if self._consumer.should_reconnect:
            self._consumer.stop()
            reconnect_delay = self._get_reconnect_delay()
            logger.info("Reconnecting after %d seconds", reconnect_delay)
            time.sleep(reconnect_delay)
            self._connect_consumer()

    def _connect_consumer(self):
        self._consumer = self._consumer_class(
            config=self._config,
            queue=self._queue,
            exchange=self._exchange,
            exchange_type=self._exchange_type,
            routing_key=self._routing_key,
            callback_path=self._callback_path,
        )

    def _get_reconnect_delay(self):
        if self._consumer.was_consuming:
            self._reconnect_delay = 0
        else:
            self._reconnect_delay += 1
        self._reconnect_delay = min(self._reconnect_delay, 30)
        return self._reconnect_delay
