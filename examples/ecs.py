import time
from dataclasses import dataclass
from typing import Tuple

from bruv.ecs import Query, Simulation


@dataclass
class Position:
    x: float = 0.0
    y: float = 0.0


@dataclass
class Velocity:
    x: float = 0.0
    y: float = 0.0


@dataclass
class Health:
    value: float = 0.0


@dataclass
class Lifetime:
    value: float = 0.0


@dataclass
class Debugging:
    pass


def update_positions(sim: Simulation):
    # We can execute basic queries to fetch components
    entities = sim.execute(Query[Tuple[Position, Velocity]])

    # Entity here is a reference inside an iterator, meaning it shouldn't be shared
    #  and will only be valid for the current iteration.
    for entity, (position, velocity) in entities:
        print(entity.id, position, velocity)

        # We can also query things dynamically via the entity reference
        if entity.has(Health):
            print(f"Entity health is {entity.get(Health).value}")


def remove_dead(sim: Simulation):
    to_kill = []
    for entity, (lifetime,) in sim.execute(Query[Tuple[Lifetime]]):
        if lifetime.value <= sim.time:
            to_kill.append(entity.id)

    for entity_id in to_kill:
        sim.remove_entity(entity_id)


def undebug(sim: Simulation):
    for entity, _ in sim.execute(Query[Tuple[Debugging]]):
        print(f"Remove debugging from {entity.id}")
        sim.remove_component(entity.id, Debugging)


sim = Simulation()
sim.add_system(update_positions)
sim.add_system(remove_dead)
sim.add_system(undebug)

bob = sim.create_entity(Position(), Velocity(x=1.0, y=1.0), Health(25))
test = sim.create_entity(Position(), Velocity(), Lifetime(3))

sim.add_component(test, Debugging())

while True:
    sim.tick()
    time.sleep(1)
