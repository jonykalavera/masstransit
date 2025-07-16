"""Test worker module."""

import pytest

from masstransit import worker
from masstransit.models.config import Config


@pytest.fixture(name="logger")
def logger_fixture(mocker):
    """Logger mock fixture."""
    return mocker.patch("masstransit.worker.logger")


@pytest.fixture(name="threading")
def threading_fixture(mocker):
    """Threading mock fixture."""
    return mocker.patch("masstransit.worker.threading")


def test_start_worker_not_found():
    """We expect a ValueError to be raised if the worker is not found."""
    config = Config()

    with pytest.raises(ValueError, match="Worker 'foo' not found in config"):
        worker.start(config, "foo")


def test_start_worker_starts_consumer_thread(mocker, logger, threading):
    """We expect the worker to start a thread for each consumer in the worker."""
    config = Config.model_validate(
        {
            "workers": [
                {
                    "name": "foo",
                    "consumers": [
                        {
                            "name": "bar",
                            "queue": "queue",
                            "exchange": "exchange",
                        }
                    ],
                },
            ]
        }
    )

    # system under test
    worker.start(config, "foo", log_level="INFO", django_settings="app.settings", configure_logging=False)

    # assertions
    logger.info.mock_calls = [
        mocker.call("Starting worker %s", "foo"),
        mocker.call("Adding consumer foo: bar"),
    ]
    threading.Thread.assert_called_once_with(
        target=worker._run_command,
        args=(
            "FOO:BAR-01",
            [
                "python",
                "-u",
                "-m",
                "masstransit",
                "--log-level",
                "INFO",
                "--django-settings",
                "app.settings",
                "--no-configure-logging",
                "consume",
                "queue",
                "--exchange",
                "exchange",
                "--exchange-type",
                "fanout",
            ],
        ),
    )
    threading.Thread.return_value.start.assert_called_once()
    threading.Thread.return_value.join.assert_called_once()
