"""Test decorators module."""

import pytest
from pydantic import ValidationError

from masstransit.decorators import contract_callback
from masstransit.models.contract import Contract
from masstransit.models.message import Message


class Foo(Contract):
    """Foo contract."""

    foo: bool


class Bar(Contract):
    """Bar contract."""

    foo: Foo


@pytest.fixture(name="logger")
def logger_fixture(mocker):
    return mocker.patch("masstransit.decorators.logger")


@pytest.mark.asyncio
async def test_contract_callback_handles_no_contract():
    """We expect the decorator will raise a value error if no contract is provided."""
    with pytest.raises(ValueError, match="Must pass contract or contracts"):
        contract_callback()


@pytest.mark.asyncio
async def test_contract_callback_handles_invalid_contract():
    """We expect the decorator will raise a value error if no contract is provided."""
    with pytest.raises(AssertionError, match="contract values must inherit from Contract"):
        contract_callback(dict)


@pytest.mark.asyncio
async def test_contract_callback_with_single_contract():
    """We expect the callback will receive the message and payload."""

    @contract_callback(contract=Foo)
    async def callback(message, payload):
        """The payload is an instance of the contract model."""
        # assertions
        assert message.messageId
        assert payload.foo

    # system under test
    await callback(Message(message={"foo": True}))


@pytest.mark.asyncio
async def test_contract_callback_with_multiple_contracts():
    """We expect the callback will receive the message and payload."""

    @contract_callback(contracts={("foo",): Foo, ("bar",): Bar})
    async def callback(message, payload):
        """The payload is an instance of the contract model that matches the messageType."""
        # assertions
        assert message.messageId
        if message.messageType == ("bar",):
            assert isinstance(payload.foo, Foo)
        elif message.messageType == ("foo",):
            assert isinstance(payload.foo, bool)

    # system under test
    await callback(Message(messageType=("foo",), message={"foo": True}))
    await callback(Message(messageType=("bar",), message={"foo": {"foo": True}}))


@pytest.mark.asyncio
async def test_contract_callback_handles_unkown_message_type(logger):
    """We expect the callback will raise a key error if the message type is unknown."""

    @contract_callback(contracts={("foo",): Foo, ("bar",): Bar})
    async def callback(message, payload):
        assert False, "Will not be called"

    # system under test
    result = await callback(Message(messageType=("baz",), message={}))

    # assertions
    assert not result


@pytest.mark.asyncio
async def test_contract_callback_optionally_raise_error_on_unkown_type(logger):
    """We expect the callback will raise a key error if the message type is unknown."""

    @contract_callback(contracts={("foo",): Foo, ("bar",): Bar}, skip_unknown=False)
    async def callback(message, payload):
        assert False, "Will not be called"

    # system under test
    with pytest.raises(KeyError):
        await callback(Message(messageType=("baz",), message={}))

    # assertions
    logger.error.assert_called_once_with("Unknown message type: %s", ("baz",))


@pytest.mark.asyncio
async def test_contract_callback_optionally_skips_invalid_messages(logger):
    """We expect the callback will skip invalid messages when skip_invalid=True."""

    @contract_callback(contracts={("foo",): Foo, ("bar",): Bar}, skip_invalid=True)
    async def callback(message, payload):
        assert False, "Will not be called"

    # system under test
    result = await callback(Message(messageType=("bar",), message={}))

    # assertions
    assert not result
    logger.error.assert_called_once_with("Invalid message: %s for contract %s", {}, Bar)


@pytest.mark.asyncio
async def test_contract_callback_raises_validation_error_on_invalid_messages():
    """We expect the callback will skip invalid messages when skip_invalid=True."""

    @contract_callback(contracts={("foo",): Foo, ("bar",): Bar})
    async def callback(message, payload):
        assert False, "Will not be called"

    # system under test
    with pytest.raises(ValidationError):
        await callback(Message(messageType=("bar",), message={}))
