"""Worker for MassTransit commands."""

import logging
import subprocess as sp
import threading
from functools import lru_cache
from random import choice
from typing import TYPE_CHECKING

from masstransit.colors import Background, Foreground, Style
from masstransit.models import Config

if TYPE_CHECKING:
    from masstransit.models.config import WorkerConfig

logger = logging.getLogger(__name__)


@lru_cache
def _random_color(*args, **kwargs) -> tuple[str, str]:
    bg = choice(list(Background))
    fg = Foreground.CBLACK if bg != Background.CBLACKBG else Foreground.CWHITE
    return fg, bg


# Define a function to run a command and stream its output
def _run_command(name: str, command: list[str], color) -> None:
    process = sp.Popen(" ".join(command), stdout=sp.PIPE, stderr=sp.STDOUT, text=True, shell=True)
    # Stream the output line by line
    assert process.stdout, "should get stdout reference"
    fg, bg = color
    for stdout in iter(process.stdout.readline, ""):
        if stdout:
            print(f"{fg}{bg} {name} {Style.CEND} {stdout}", end="")  # noqa: T201
    if process.stdout:
        process.stdout.close()
    process.wait()


def _get_consumers(config: Config, worker: "WorkerConfig") -> tuple[dict[str, list[str]], dict[str, tuple[str, str]]]:
    consumers = {}
    colors = {}
    for consumer in worker.consumers:
        for n in range(1, consumer.number_of_consumers + 1):
            name = f"{worker.display()}:{consumer.display()}-{n:02}"
            command = ["python3", "-m", "masstransit", "consume", consumer.queue]
            consumers[name] = command
            colors[name] = _random_color(_name=name)
            logger.info("Adding consumer %s", name)
    return consumers, colors


def start(config: Config, name: str):
    """Start the worker process.

    This works as a multi-process worker. Starting a worker will start all consumers in the worker.
    Each worker will consume messages from their queues in the worker's config.
    """
    worker = config.get_worker_config(name)
    if not worker:
        raise ValueError(f"Worker '{name}' not found in config")
    logger.info("Starting worker %s", worker.name)
    consumers, colors = _get_consumers(config=config, worker=worker)
    # Create a thread for each command
    threads = []
    for _name, cmd in consumers.items():
        color = colors[_name]
        thread = threading.Thread(target=_run_command, args=(_name, cmd, color))
        threads.append(thread)
    # Start all threads
    for thread in threads:
        thread.start()
    # Wait for all threads to finish
    for thread in threads:
        thread.join()
