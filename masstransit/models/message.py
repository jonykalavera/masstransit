"""MassTransit message model."""

from datetime import datetime, timedelta
from typing import Any

from dateutil.parser import parse
from pydantic import BaseModel


class Host(BaseModel):
    """MassTransit message host model"""

    machineName: str
    processName: str
    processId: int
    assembly: str
    assemblyVersion: str
    frameworkVersion: str
    massTransitVersion: str
    operatingSystemVersion: str


class Message(BaseModel):
    """MassTransit message model"""

    messageId: str
    requestId: str | None
    correlationId: str | None
    conversationId: str
    initiatorId: str | None
    sourceAddress: str | None
    destinationAddress: str
    responseAddress: str | None
    faultAddress: str | None
    messageType: list[str]
    message: dict[str, Any]
    expirationTime: str | None
    sentTime: str
    headers: dict[str, Any]
    host: Host

    @property
    def lag(self) -> timedelta:
        """Event lag

        Args:

        Returns:
          timedelta: between produce time and now

        Raises:
          KeyError: if the `produced_at` key is not present in metadata

        """
        return parse(self.sentTime) - datetime.now()
