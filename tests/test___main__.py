"""Test CLI __main__ module."""

import pytest

from masstransit.__main__ import consume, main, produce


@pytest.fixture(name="rabbitmq_producer")
def rabbitmq_producer_fixture(mocker):
    """RabbitMQProducer mock fixture."""
    producer = mocker.patch("masstransit.__main__.RabbitMQProducer")
    producer.return_value = producer
    return producer


@pytest.fixture(name="rabbitmq_consumer")
def rabbitmq_consumer_fixture(mocker):
    """RabbitMQConsumer mock fixture."""
    consumer = mocker.patch("masstransit.__main__.ReconnectingRabbitMQConsumer")
    consumer.return_value = consumer
    return consumer


@pytest.fixture(name="logging_setup", autouse=True)
def logging_setup_fixture(mocker):
    """logging_setup mock fixture."""
    return mocker.patch("masstransit.__main__.logging_setup")


@pytest.fixture(name="django_setup", autouse=True)
def django_settings_fixture(mocker):
    """django_setup fixture."""
    return mocker.patch("masstransit.__main__.django_setup")


@pytest.fixture(name="context")
def context_fixture(mocker):
    """Context mock fixture."""
    return mocker.patch("masstransit.__main__.typer.Context")


def test_consume(context, rabbitmq_consumer):
    """We expect consume to instantiate the consumer and run it."""
    # execute test
    consume(context, "getting-started", "getting-started")

    # assertions
    rabbitmq_consumer.run.assert_called_once_with()


def test_produce(context, rabbitmq_producer):
    """We expect produce to instantiate the producer and send the message."""
    # setup test
    message = '{"Value": "hello world!"}'
    routing_key = "my routing_key"
    contract_class_path = "examples.getting_started.GettingStarted"

    # execute test
    produce(
        context,
        "getting-started",
        "getting-started",
        message,
        routing_key=routing_key,
        contract_class_path=contract_class_path,
    )

    # assertions
    rabbitmq_producer.send.assert_called_once_with(message, routing_key, contract_class_path=contract_class_path)


def test_main_default(context, logging_setup, django_setup):
    """We expect main to configure the logging with default level."""
    # execute test
    main(context)

    # assertions
    django_setup.assert_not_called()
    logging_setup.assert_called_once_with("INFO")


def test_main_with_django_settings(context, logging_setup, django_setup):
    """We expect main to configure the django env."""
    # execute test
    main(context, django_settings="app.settings", log_level="ERROR")

    # assertions
    django_setup.assert_called_once_with("app.settings")
    logging_setup.assert_called_once_with("ERROR")


def test_main_no_configure_logging(context, logging_setup, django_setup):
    """We expect main to not configure the logging."""
    # execute test
    main(context, configure_logging=False)

    # assertions
    django_setup.assert_not_called()
    logging_setup.assert_not_called()
