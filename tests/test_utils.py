"""Test utils module."""

import pytest

from masstransit.utils import django_setup


@pytest.fixture(name="import_module")
def import_module_fixture(mocker):
    """import_module mock fixture."""
    return mocker.patch("masstransit.utils.import_module")


@pytest.fixture(name="setdefault")
def setdefault_fixture(mocker):
    """os.environ.setdefault mock fixture."""
    return mocker.patch("masstransit.utils.os.environ.setdefault")


@pytest.fixture(name="logger")
def logger_fixture(mocker):
    """Logger mock fixture."""
    return mocker.patch("masstransit.utils.logger")


def test_django_setup_configures_django(import_module, setdefault, logger):
    """We expect django_setup to initialize django."""
    # system under test
    django_setup("app.settings")

    # assertions
    import_module.assert_called_once_with("django")
    setdefault.assert_called_once_with("DJANGO_SETTINGS_MODULE", "app.settings")
    import_module.return_value.setup.assert_called_once_with()
    logger.debug.assert_called_once_with("Django initialized")


def test_django_setup_handles_import_error(import_module, setdefault, logger):
    """We expect django_setup to initialize django."""
    import_module.side_effect = ImportError
    # system under test
    django_setup("app.settings")

    # assertions
    import_module.assert_called_once_with("django")
    setdefault.assert_not_called()
    import_module.return_value.setup.assert_not_called()
    logger.error.assert_called_once_with("Could not import django")
