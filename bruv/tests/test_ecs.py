from dataclasses import dataclass
from typing import Tuple

from bruv.ecs import Query, Simulation


def test_basic_simulation(sim: Simulation):
    x = 0

    def increment(sim):
        nonlocal x
        x += 1

    sim.add_system(increment)
    sim.tick()

    assert x == 1


@dataclass
class BasicComponent:
    x: float = 0
    y: str = "test"
    z: bool = False


def test_basic_component(sim: Simulation, entity: int):
    sim.add_component(entity, BasicComponent())

    result = sim.execute(Query[Tuple[BasicComponent]])
    assert len(list(result)) == 1


@dataclass
class XComponent:
    pass


@dataclass
class YComponent:
    pass


@dataclass
class ZComponent:
    pass


def test_multiple_component(sim: Simulation, entity: int):
    sim.add_component(entity, XComponent())
    sim.add_component(entity, YComponent())
    sim.add_component(entity, ZComponent())

    result = sim.execute(Query[Tuple[XComponent]])
    assert len(list(result)) == 1

    result = sim.execute(Query[Tuple[XComponent, YComponent]])
    assert len(list(result)) == 1

    result = list(sim.execute(Query[Tuple[XComponent, YComponent, ZComponent]]))
    assert len(result) == 1
    assert result[0][0].id == entity
    assert len(result[0][1]) == 3


def test_multiple_component_multiple_entity(sim: Simulation):
    entity_ids = [sim.create_entity() for _ in range(1000)]
    for entity_id in entity_ids:
        sim.add_component(entity_id, XComponent())
        sim.add_component(entity_id, YComponent())

    sim.add_component(entity_ids[0], ZComponent())

    result = list(sim.execute(Query[Tuple[XComponent]]))
    assert len(result) == 1000

    result = sim.execute(Query[Tuple[XComponent, YComponent]])
    assert len(list(result)) == 1000

    result = sim.execute(Query[Tuple[ZComponent]])
    assert len(list(result)) == 1

    result = sim.execute(Query[Tuple[XComponent, YComponent, ZComponent]])
    assert len(list(result)) == 1
