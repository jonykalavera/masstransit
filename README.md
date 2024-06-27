# MassTransit Python

MassTransit for python.

POC status.

## Quick start

For this quick start, we recommend running the preconfigured Docker image maintained by the MassTransit team. The container image includes the delayed exchange plug-in and the management interface is enabled.

```
$ docker run -p 15672:15672 -p 5672:5672 masstransit/rabbitmq
```
Once its up and running you can sign in to the management UI with the username guest and password guest. You can see message rates, exchange bindings, and active consumers using the management interface.

Start the consumer

```
poetry run python -m masstransit
```