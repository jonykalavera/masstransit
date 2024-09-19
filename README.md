# MassTransit Python

A Framework to integrate python applications with MassTransit.

![Hero Banner](./docs/hero-banner.png)

## Goals

- Integration with [MassTransit](https://masstransit.io/):
  - [x] Consumer: Implement a basic consumer that handles messages.
    - [x] Custom `Message` Handler Function to handle incoming messages.
  - [x] Basic producer: Implement a basic producer
    - [x] custom `Contract` model
- [x] Django compatibility
- Broker Support: Support popular message brokers, including:
  - [x] RabbitMQ

## Command Line Interface

```shell
$ python -m masstransit --help

 Usage: python -m masstransit [OPTIONS] COMMAND [ARGS]...

 MassTransit for python.

╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --log-level                 TEXT  [default: INFO]                            │
│ --install-completion              Install completion for the current shell.  │
│ --show-completion                 Show completion for the current shell, to  │
│                                   copy it or customize the installation.     │
│ --help                            Show this message and exit.                │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ───────────────────────────────────────────────────────────────────╮
│ consume   Start a message consumer.                                          │
│ produce   Produce a message.                                                 │
│ worker    Run worker from config.                                            │
╰──────────────────────────────────────────────────────────────────────────────╯

```

## Contracts

Declare your message contract specification using pydantic models.

```python
"""Example Contracts."""

from masstransit.models.contract import Contract


class GettingStarted(Contract):
    """This is the contract used in MassTransit's RabbitMQ QuickStart Tutorial."""

    Value: str
```

## Callbacks

Use async callbacks.

```python
async def custom_callback(
    message: Message, **kwargs
) -> None:
    """Logs the messages."""
    logger.info(
        "Received message %s | %s",
        message.messageId,
        message.message,
    )
```

With a contract you can use the `contract_callback` decorator:

```python
from masstransit.decorators import contract_callback

@contract_callback(contract=GettingStarted)
async def custom_callback(payload: GettingStarted, **kwargs):
    """GettingStarted contract callback."""
    logger.info("Received message: %s", payload.Value)
```

## Workers

MassTransit uses pydantic-settings. See `masstransit.models.config.Config` for details.
Environment variables are supported with the `MASSTRANSIT_` prefix.
A `masstransit.yaml` file in the current directory can be used for configuration.

```yaml
dsn: amqp://guest:guest@localhost:5672
workers:
  - name: auctions
    consumers:
      - name: auction_events
        queue: Auction
        callback_path: masstransit.consumer.default_callback
      - name: auction_item_events
        queue: AuctionItem
        callback_path: myapp.custom_callback
  - name: auction_stock
    consumers:
      - name: auction_stock_changed
        queue: AuctionStock
        callback_path: myapp.custom_stock_callback
        number_of_consumers: 5
```

This would allow using the following command to start the auction worker:

```bash
$ python -m masstransit worker auctions
...
```

### Django example

Put all your callbacks in a single package. Adding the following to your `__init__.py`:

```python
"""MassTransit entry-point."""

import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myapp.settings")

from django import setup as django_setup

django_setup()

```

Make sure to use async callbacks. Newer versions of Django support async models.
For older versions, you can use the `database_async_to_sync` function from `channels`
or just use `async_to_sync` and make sure to close any open db connections.
