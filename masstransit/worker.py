"""Worker for MassTransit commands."""

import logging
import subprocess as sp
import sys
import threading
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from masstransit.models.config import Config, WorkerConfig

logger = logging.getLogger(__name__)


def _run_command(name: str, command: list[str]) -> None:
    sp.Popen(command, stdout=sys.stdout, stderr=sys.stderr).communicate()


def _get_consumer_commands(
    worker: "WorkerConfig",
    log_level: str,
    django_settings: str | None,
    configure_logging: bool = True,
) -> dict[str, list[str]]:
    consumers = {}
    for consumer in worker.consumers:
        for n in range(1, consumer.number_of_consumers + 1):
            name = f"{worker.display()}:{consumer.display()}-{n:02}"
            command = ["python", "-u", "-m", "masstransit"]
            # OPTIONS
            if log_level:
                command += ["--log-level", log_level]
            if django_settings:
                command += ["--django-settings", django_settings]
            if not configure_logging:
                command += ["--no-configure-logging"]
            # COMMAND
            command += ["consume", consumer.queue]
            # ARGUMENTS
            if consumer.exchange:
                command += ["--exchange", consumer.exchange]
            if consumer.exchange_type:
                command += ["--exchange-type", consumer.exchange_type]
            if consumer.routing_key:
                command += ["--routing-key", consumer.routing_key]
            if consumer.callback_path:
                command += ["--callback-path", consumer.callback_path]
            consumers[name] = command
            logger.info("Adding consumer %s: %s", name, " ".join(command))
    return consumers


def start(
    config: "Config",
    name: str,
    log_level: str = "INFO",
    django_settings: str | None = None,
    configure_logging: bool = True,
) -> None:
    """Start the worker process.

    This works as a multi-process worker. Starting a worker will start all consumers in the worker.
    Each worker will consume messages from their queues in the worker's config.
    """
    worker = config.get_worker_config(name)
    if not worker:
        raise ValueError(f"Worker '{name}' not found in config")
    logger.info("Starting worker %s", worker.name)
    consumers = _get_consumer_commands(
        worker=worker,
        log_level=log_level,
        django_settings=django_settings,
        configure_logging=configure_logging,
    )
    # Create a thread for each command
    threads = []
    for _name, cmd in consumers.items():
        thread = threading.Thread(target=_run_command, args=(_name, cmd))
        threads.append(thread)
    # Start all threads
    for thread in threads:
        thread.start()
    # Wait for all threads to finish
    for thread in threads:
        thread.join()
