"""MassTransit decorators."""

import logging
from collections.abc import Callable
from functools import wraps
from typing import TYPE_CHECKING, ParamSpec, TypeVar

from pydantic import ValidationError

if TYPE_CHECKING:
    from masstransit.models import Contract, Message


logger = logging.getLogger(__name__)

P = ParamSpec("P")
R = TypeVar("R")
Callback = Callable[P, R]


def contract_callback(contract: type["Contract"], skip_invalid: bool = False) -> Callable[[Callback], Callback]:
    """Handles the instantiating the contract before executing the callback."""

    def _decorator(callback: Callback) -> Callback:
        @wraps(callback)
        def _callback(message: "Message", **kwargs):
            try:
                payload = contract.model_validate(message.message)
                callback(payload=payload, message=message, **kwargs)
            except ValidationError:
                if skip_invalid:
                    return
                raise

        return _callback

    return _decorator
