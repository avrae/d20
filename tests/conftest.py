import d20

import pytest


@pytest.fixture(autouse=True, scope="function")
def global_fixture():
    """Seed each individual test with the same seed, so that different runs of the same test are deterministic"""
    # noinspection PyProtectedMember
    d20._roller.rng.seed(42)
    yield
