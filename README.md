# MassTransit Python

MassTransit for python.

# Goals

- [ ] Interoperability with masstransit
  - [x] basic consumer
    - messages model
    - custom message handler function
  - [x] basic producer
    - custom contract model
- [ ] django integration
- [ ] broker support
  - [x] rabbitmq
  - [ ] kafka

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
