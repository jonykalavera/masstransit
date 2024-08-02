"""Worker for MassTransit commands."""

import logging
import subprocess as sp
import threading

from masstransit.models import Config

logger = logging.getLogger(__name__)


# Define a function to run a command and stream its output
def _run_command(name: str, command: list[str]) -> None:
    process = sp.Popen(" ".join(command), stdout=sp.PIPE, stderr=sp.STDOUT, text=True, shell=True)
    # Stream the output line by line
    logger.info("Running command: %s", command)
    for stdout in iter(process.stdout.readline, ""):
        if stdout:
            logger.info("%s | %s", name, stdout)
    if process.stdout:
        process.stdout.close()
    process.wait()


def _get_consumers(config: Config, worker: "WorkerConfig") -> dict[str, list[str]]:
    consumers = {}
    for consumer in worker.consumers:
        for n in range(1, consumer.number_of_consumers + 1):
            name = f"{consumer.name}-{n:02}"
            command = ["python3", "-m", "masstransit", "consume", consumer.queue]
            consumers[name] = command
            logger.info("Adding consumer %s", name)
    return consumers


def start(config: Config, name: str):
    """Start the worker process.

    This works as a multi-process worker. Starting a worker will start all consumers in the worker.
    Each worker will consume messages from their queues in the worker's config.
    """
    worker = config.get_worker_config(name)
    if not worker:
        raise ValueError(f"Worker '{name}' not found in config")
    logger.info("Starting worker %s", worker.name)
    consumers = _get_consumers(config=config, worker=worker)
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
