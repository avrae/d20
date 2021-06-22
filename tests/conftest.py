import random

import pytest


@pytest.fixture(autouse=True, scope="function")
async def global_fixture():
    """Seed each individual test with the same seed, so that different runs of the same test are deterministic"""
    random.seed(42)
    yield
