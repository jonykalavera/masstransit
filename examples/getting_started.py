"""Example Contracts."""

from masstransit.models.contract import Contract


class GettingStarted(Contract):
    """This is the contract used in MassTransit's RabbitMQ QuickStart Tutorial."""

    Value: str
