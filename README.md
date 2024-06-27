# MassTransit Python

MassTransit for python.

POC status.

## Consumer

```shell
$ poetry run python -m masstransit consumer --help

 Usage: python -m masstransit consumer [OPTIONS] EXCHANGE QUEUE

 Start a message consumer

╭─ Arguments ───────────────────────────────────────────────────────────────────────────────────────────────╮
│ *    exchange      TEXT  [default: None] [required]                                                       │
│ *    queue         TEXT  [default: None] [required]                                                       │
╰───────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ─────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --url                  TEXT                           [default: amqp://guest:guest@localhost:5672/%2F]    │
│ --exchange-type        [direct|fanout|headers|topic]  [default: fanout]                                   │
│ --routing-key          TEXT                           [default: example.text]                             │
│ --help                                                Show this message and exit.                         │
╰───────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```