import pytest


@pytest.fixture
def email():
    # Compatibilidade para testes legados que declaram fixture `email`.
    return None


@pytest.fixture
def password():
    # Compatibilidade para testes legados que declaram fixture `password`.
    return None
