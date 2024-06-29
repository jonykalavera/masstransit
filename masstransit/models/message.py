"""MassTransit message model."""

import os
import sys
from datetime import datetime, timedelta
from typing import Any
from uuid import uuid4
import platform
from dateutil.parser import parse
from pydantic import BaseModel, Field


class Host(BaseModel):
    """MassTransit message host model"""

    machineName: str = Field(default_factory=platform.node)
    processName: str = Field(default_factory=lambda: sys.argv[0])
    processId: int = Field(default_factory=os.getpid)
    assembly: str = "masstransit-python"
    assemblyVersion: str = "0.0.1"
    frameworkVersion: str = "net6.0"
    massTransitVersion: str = "8.2.3"
    operatingSystemVersion: str = os.name


class Message(BaseModel):
    """MassTransit message model"""

    messageId: str = Field(default_factory=lambda: uuid4().hex)
    requestId: str | None = None
    correlationId: str | None = None
    conversationId: str = None
    initiatorId: str | None = "masstransit-python"
    sourceAddress: str | None = None
    destinationAddress: str = None
    responseAddress: str | None = None
    faultAddress: str | None = None
    messageType: list[str] = []
    message: dict | str | int | float | list = Field(default_factory=dict)
    expirationTime: str | None = None
    sentTime: str = Field(default_factory=lambda: datetime.now().isoformat())
    headers: dict[str, Any] = Field(default_factory=dict)
    host: Host = Host()

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
