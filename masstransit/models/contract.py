"""MassTransit contract model."""

from importlib import import_module

from pydantic import BaseModel


class Contract(BaseModel):
    """Contract model."""

    @classmethod
    def messageType(cls):
        """Retuns the module and class name as the message type."""
        return [f"{cls.__module__}.{cls.__name__}"]

    @classmethod
    def from_import_string(cls, contract_class_path: str) -> "Contract":
        """Return a contract instance given a dotted import path."""
        parts = contract_class_path.split(".")
        contract_mod = import_module(".".join(parts[:-1]))
        contract = getattr(contract_mod, parts[-1])
        assert issubclass(contract, cls), "Not a valid contract"
        return contract
