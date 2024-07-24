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


def contract_callback(
    contract: type["Contract"] | None = None,
    contracts: dict[str, type["Contract"]] | None = None,
    skip_invalid: bool = False,
    skip_unknown=True,
) -> Callable[[Callback], Callback]:
    """Handles  instantiating a contract before executing the callback."""
    assert contract or contracts, "Must pass either contract or contracts"
    _contracts = defaultdict(lambda: contract) if contract else contracts
    assert _contracts, "Must pass at least one contract"
    assert all(isinstance(c, Contract) for c in _contracts.values()), "contract values must inherit from Contract"

    def _decorator(callback: Callback) -> Callback:
        @wraps(callback)
        def _callback(message: "Message", **kwargs):
            contract = _contracts.get(message.messageType[0])
            if not contract:
                if skip_unknown:
                    return
                logger.error("Unknown message type: %s", message.messageType)
                return
            try:
                payload = contract.model_validate(message.message)
                callback(payload=payload, message=message, **kwargs)
            except ValidationError:
                if skip_invalid:
                    return
                raise

        return _callback

    return _decorator
