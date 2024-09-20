"""A simple example."""

import logging

from masstransit.decorators import contract_callback
from masstransit.models.contract import Contract

logger = logging.getLogger(__name__)


class SimpleContract(Contract):
    """A simple contract."""

    foo: str
    bar: str | None = None


@contract_callback(contract=SimpleContract)
async def simple_callback(payload, **kwargs):
    """A simple callback function."""
    logger.info("Got payload: %s %s", payload.foo, payload.bar)
