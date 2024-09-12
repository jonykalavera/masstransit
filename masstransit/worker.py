"""Worker for MassTransit commands."""

import logging
import subprocess as sp
import threading
from functools import lru_cache
from random import choice
from typing import TYPE_CHECKING

from masstransit.colors import Background, Foreground, Style

if TYPE_CHECKING:
    from masstransit.models.config import Config, WorkerConfig

logger = logging.getLogger(__name__)


OUTPUT_TEMPLATE = "{fg}{bg}⑆ {name}:{end} {stdout}"


@lru_cache
def _random_color(*args, **kwargs) -> tuple[str, str]:
    bg = choice(list(Background))
    fg = Foreground.CBLACK if bg != Background.CBLACKBG else Foreground.CWHITE
    return fg, bg


# Define a function to run a command and stream its output
def _run_command(name: str, command: list[str]) -> None:
    process = sp.Popen(" ".join(command), stdout=sp.PIPE, stderr=sp.STDOUT, text=True, shell=True)
    # Stream the output line by line
    assert process.stdout, "should get stdout reference"
    fg, bg = _random_color(name)
    for stdout in iter(process.stdout.readline, ""):
        if stdout:
            output = OUTPUT_TEMPLATE.format(fg=fg, bg=bg, name=name, end=Style.CEND, stdout=stdout)
            print(output, end="")  # noqa: T201
    if process.stdout:
        process.stdout.close()
    process.wait()


def _get_consumer_commands(config: "Config", worker: "WorkerConfig") -> dict[str, list[str]]:
    consumers = {}
    for consumer in worker.consumers:
        for n in range(1, consumer.number_of_consumers + 1):
            name = f"{worker.display()}:{consumer.display()}-{n:02}"
            command = ["python3", "-m", "masstransit", "consume", consumer.queue]
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


def start(config: "Config", name: str):
    """Start the worker process.

    This works as a multi-process worker. Starting a worker will start all consumers in the worker.
    Each worker will consume messages from their queues in the worker's config.
    """
    worker = config.get_worker_config(name)
    if not worker:
        raise ValueError(f"Worker '{name}' not found in config")
    logger.info("Starting worker %s", worker.name)
    consumers = _get_consumer_commands(config=config, worker=worker)
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
