import pytest

from masstransit.__main__ import consume, main, produce


@pytest.fixture(name="rabbitmq_producer")
def rabbitmq_producer_fixture(mocker):
    producer = mocker.patch("masstransit.__main__.RabbitMQProducer")
    producer.return_value = producer
    return producer


@pytest.fixture(name="rabbitmq_consumer")
def rabbitmq_consumer_fixture(mocker):
    consumer = mocker.patch("masstransit.__main__.ReconnectingRabbitMQConsumer")
    consumer.return_value = consumer
    return consumer


@pytest.fixture(name="logging", autouse=True)
def logging_fixture(mocker):
    return mocker.patch("masstransit.__main__.logging")


def test_consume(rabbitmq_consumer):
    # Test the consume function
    consume("getting-started", "getting-started")
    rabbitmq_consumer.run.assert_called_once_with()


def test_produce(rabbitmq_producer):
    """We expect produce to instantiate the producer and send the message."""
    message = '{"Value": "hello world!"}'
    routing_key = "my routing_key"
    contract_class_path = "masstransit.models.getting_started.GettingStarted"
    produce("getting-started", "getting-started", message, routing_key=routing_key)
    rabbitmq_producer.send.assert_called_once_with(message, routing_key, contract_class_path=contract_class_path)


@pytest.mark.parametrize("log_level", ["INFO", "WARNING", "ERROR"])
def test_main(log_level, logging):
    # Test the main function with different log levels
    main(log_level=log_level)
    logging.config.dictConfig.assert_called_once()
