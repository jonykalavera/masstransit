# MassTransit Python

A Framework to integrate python applications with MassTransit.

## Goals

- Integration with [MassTransit](https://masstransit.io/):
  - [x] Consumer: Implement a basic consumer that handles messages.
    - [x] Custom `Message` Handler Function to handle incoming messages.
  - [x] Basic producer: Implement a basic producer
    - [x] custom `Contract` model
- [ ] Django Integration: Seamlessly integrate MassTransit with Django applications.
- Broker Support: Support popular message brokers, including:
  - [x] RabbitMQ
  - [ ] Kafka

## Command Line Interface

```shell
$ poetry run python -m masstransit --help

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
│ consume   Start a message consumer                                           │
│ produce   Produce a message                                                  │
╰──────────────────────────────────────────────────────────────────────────────╯
```
