import pytest

from bruv.ecs import Simulation


@pytest.fixture
def sim() -> Simulation:
    return Simulation()


@pytest.fixture
def entity(sim) -> int:
    return sim.create_entity()
