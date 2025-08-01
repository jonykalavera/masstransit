"""MassTransit decorators."""

import logging
from collections import defaultdict
from collections.abc import Callable
from functools import wraps
from typing import TYPE_CHECKING, ParamSpec, TypeVar

from pydantic import ValidationError

from masstransit.models import Contract

if TYPE_CHECKING:
    from masstransit.models import Message


logger = logging.getLogger(__name__)

P = ParamSpec("P")
R = TypeVar("R")
Callback = Callable[P, R]


async def noop(*_args, **_kwargs):
    """Do Nothing."""


def contract_callback(
    contract: type["Contract"] | None = None,
    contracts: dict[tuple[str, ...] | None, type["Contract"]] | None = None,
    skip_invalid: bool = False,
    skip_unknown=True,
) -> Callable[[Callback], Callback]:
    """Handles  instantiating a contract before executing the callback."""
    if contracts:
        _contracts = contracts
    elif contract:
        _contracts = defaultdict(lambda: contract)
        _contracts[None] = contract
    else:
        raise ValueError("Must pass contract or contracts")
    assert all(issubclass(c, Contract) for c in _contracts.values()), "contract values must inherit from Contract"

    def _decorator(callback: Callback) -> Callback:
        @wraps(callback)
        def _callback(message: "Message", **kwargs):
            try:
                contract = _contracts[message.messageType]
            except KeyError:
                if skip_unknown:
                    return noop()
                logger.error("Unknown message type: %s", message.messageType)
                raise
            try:
                payload = contract.model_validate(message.message)
                return callback(payload=payload, message=message, **kwargs)
            except ValidationError:
                if skip_invalid:
                    logger.error("Invalid message: %s for contract %s", message.message, contract)
                    return noop()
                raise

        return _callback

    return _decorator
