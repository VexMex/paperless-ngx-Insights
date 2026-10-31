"""Enable the integration in an isolated Home Assistant test instance."""

import pytest


@pytest.fixture(autouse=True)
def custom_integrations(enable_custom_integrations):
    """Use the repository's custom_components during HA contract tests."""
    yield
