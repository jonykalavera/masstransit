"""Worker for MassTransit commands."""

import logging
import subprocess as sp
import threading

from masstransit.models import Config

logger = logging.getLogger(__name__)


# Define a function to run a command and stream its output
def _run_command(name, command):
    process = sp.Popen(command, stdout=sp.PIPE, stderr=sp.PIPE, text=True, shell=True)

    # Stream the output line by line
    for stdout, stderr in zip(iter(process.stdout.readline, b""), iter(process.stderr.readline, b""), strict=False):
        if stdout:
            logger.info("%s | %s", name, stdout)
        if stderr:
            logger.error("%s | %s", name, stderr)
    process.stdout.close()
    process.stderr.close()
    process.wait()


def start(config: Config, name: str):
    """Start the worker process.

    This works as a multi-process worker. Starting a worker will start all consumers in the worker.
    Each worker will consume messages from their queues in the worker's config.
    """
    worker = config.get_worker(name)
    if not worker:
        raise ValueError(f"Worker '{name}' not found in config")
    consumers = {}
    for consumer in worker.consumers:
        for n in range(1, consumer.number_of_consumers + 1):
            name = f"{consumer.name}-{n:02}"
            command = ["python3", "-m", "masstransit", "consume", "--dsn", config.dsn, consumer.queue]
            consumers[name] = command
            logger.info("Adding consumer %s", name)
    logger.info("Starting worker %s", worker.name)
    # Create a thread for each command
    threads = []
    for name, cmd in consumers.items():
        thread = threading.Thread(target=_run_command, args=(name, cmd))
        threads.append(thread)
    # Start all threads
    for thread in threads:
        thread.start()
    # Wait for all threads to finish
    for thread in threads:
        thread.join()
