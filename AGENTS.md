# MassTransit Python - Agent Guidelines

This document provides coding guidelines and commands for AI agents working on the MassTransit Python project. MassTransit Python is a messaging framework that bridges Python applications with the .NET MassTransit ecosystem using RabbitMQ.

## Build/Test/Lint Commands

### Development Setup
```bash
# Install UV package manager
make install-uv

# Install Python and dependencies
make install-python
uv sync
```

### Testing Commands
```bash
# Run all tests with coverage
make test
# or
pytest -vv --cov masstransit

# Run single test file
pytest tests/test_utils.py -vv

# Run single test function
pytest tests/test_utils.py::test_function_name -vv

# Run single test class
pytest tests/test_consumer.py::TestConsumerClass -vv

# Test all Python versions (CI style)
make test-all
```

### Linting and Formatting
```bash
# Format code (auto-fix)
make format
# or
ruff format masstransit/
ruff check masstransit/ --fix-only

# Check formatting (CI style)
make check-format
# or
ruff format --check masstransit/

# Lint code
make lint
# or
ruff check masstransit/
ty check masstransit
```

### CLI Usage
```bash
# Run consumer
uv run python -m masstransit consume

# Run producer  
uv run python -m masstransit produce

# Run worker
uv run python -m masstransit worker
```

## Code Style Guidelines

### Import Organization
Use the following import order (enforced by Ruff/isort):

```python
# 1. Standard library imports
import asyncio
import functools
import logging
from pathlib import Path

# 2. Third-party imports
import pika
from pydantic import BaseModel, Field
from typer import Typer

# 3. First-party/local imports
from masstransit.models import Config, Message
from masstransit.utils import import_string

# 4. TYPE_CHECKING imports (conditional)
if TYPE_CHECKING:
    from pika.spec import Basic, BasicProperties
```

### Type Annotations
- **Mandatory**: All function parameters, return types, and class attributes must be type-annotated
- **Modern syntax**: Use `str | None` instead of `Union[str, None]` (Python 3.10+)
- **Generics**: Properly annotate generic types: `list[ConsumerConfig]`, `dict[str, Any]`
- **Forward references**: Use quotes for not-yet-defined classes: `"WorkerConfig"`

```python
def send_contract(
    self, 
    obj: Contract,
    exchange: str | None = None,
    routing_key: str | None = None,
) -> None:
    """Send contract message."""
```

### Naming Conventions
- **Classes**: PascalCase (`RabbitMQProducer`, `ReconnectingConsumer`)
- **Functions/methods**: snake_case (`send_contract`, `on_connection_open`)  
- **Variables**: snake_case (`message_kwargs`, `reconnect_delay`)
- **Constants**: UPPER_SNAKE_CASE (`MASSTRANSIT_CONFIG`)
- **Private attributes**: Leading underscore (`self._connection`, `self._channel`)
- **Pydantic fields**: camelCase for MassTransit compatibility (`messageId`, `messageType`)

### Formatting Rules
- **Line length**: 119 characters (configured in pyproject.toml)
- **Indentation**: 4 spaces
- **String formatting**: Prefer f-strings: `f"Connection failed: {error}"`
- **Multi-line definitions**: Align parameters vertically

```python
def __init__(
    self,
    config: Config,
    queue: str,
    exchange: str | None = None,
    routing_key: str | None = None,
) -> None:
```

### Error Handling
- **Exception chaining**: Always use `raise ... from e` for proper tracebacks
- **Specific exceptions**: Use specific exception types (`ImportError`, `RuntimeError`, `ValueError`)
- **Property validation**: Validate state in property getters with descriptive error messages

```python
try:
    module_path, class_name = dotted_path.rsplit(".", 1)
except ValueError as e:
    raise ImportError(f'"{dotted_path}" doesn\'t look like a module path') from e

@property 
def channel(self) -> Channel:
    """Get the RabbitMQ channel."""
    if self._channel is None:
        raise RuntimeError("Channel not initialized")
    return self._channel
```

### Documentation Standards
- **Docstring style**: Google-style docstrings (configured in pyproject.toml)
- **Module docstrings**: Brief descriptions at file top
- **Class docstrings**: Comprehensive class descriptions
- **Method docstrings**: Include Args, Returns, Raises sections when applicable

```python
def get_worker_config(self, name: str) -> WorkerConfig | None:
    """Get worker config by name.
    
    Args:
        name: The name of the worker configuration.
        
    Returns:
        WorkerConfig object if found, None otherwise.
    """
```

### Configuration Patterns
- **Pydantic models**: Use Pydantic for all configuration with BaseSettings
- **Environment variables**: Support with `MASSTRANSIT_` prefix
- **YAML support**: Primary configuration via `masstransit.yaml`
- **Default values**: Always provide sensible defaults

```python
class Config(BaseSettings):
    """Configuration model."""
    
    dsn: str = "amqp://guest:guest@localhost:5672/%2F"
    log_level: str = "INFO"
    
    model_config = SettingsConfigDict(
        env_prefix="MASSTRANSIT_",
    )
```

## Project Structure

```
masstransit/
├── masstransit/           # Main package
│   ├── __main__.py        # CLI entry point
│   ├── consumer.py        # RabbitMQ consumer logic
│   ├── producer.py        # RabbitMQ producer logic  
│   ├── worker.py          # Worker management
│   ├── decorators.py      # Contract decorators
│   ├── utils.py           # Utility functions
│   ├── models/            # Data models
│   │   ├── config.py      # Configuration models
│   │   ├── contract.py    # Contract models
│   │   └── message.py     # Message models
│   └── django/            # Django integration
├── tests/                 # Test suite
├── examples/              # Example code
├── Makefile              # Build automation
└── pyproject.toml        # Project configuration
```

## Testing Guidelines

- **Framework**: Use pytest with pytest-mock, pytest-asyncio
- **Coverage**: Maintain test coverage with `pytest-cov`
- **Fixtures**: Use pytest fixtures for common setup (see `tests/test_utils.py`)
- **Naming**: Test files: `test_module.py`, Test classes: `TestClassName`, Test methods: `test_method_name`

## Key Dependencies

- **Core**: Python 3.10-3.14, Pika (RabbitMQ), Pydantic, Typer
- **Development**: UV (package manager), Ruff (linting/formatting), Pytest, TY (type checking)
- **Optional**: Django integration support

## Configuration Files

- **pyproject.toml**: Primary project configuration  
- **Makefile**: Build automation and common tasks
- **masstransit.yaml**: Runtime configuration for workers and RabbitMQ
- **.python-version**: Python version specification (3.14.3)

Remember: This is a messaging framework focused on RabbitMQ integration with MassTransit compatibility. Maintain clean separation between producer, consumer, and worker concerns.