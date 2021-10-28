import time
from dataclasses import dataclass
from typing import Tuple

from bruv.ecs import MutationType, Query, Simulation, TimingSystem


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


sim = Simulation()

# Systems are simply callables, but we can encapsulate their behavior and local
#  (private) state within a class.
sim.add_system(TimingSystem())


@sim.add_system
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


@sim.add_system
def undebug(sim: Simulation):
    for entity, _ in sim.execute(Query[Tuple[Debugging]]):
        print(f"Remove debugging from {entity.id}")
        sim.remove_component(entity.id, Debugging)


# Sometimes we want to share global state between systems, in this example
#  we extract the current frame number from the result of the timing system. This
#  data is automatically injected into our system execution call.
@sim.add_system
def remove_dead(sim: Simulation, timing: TimingSystem.Data):
    for entity, (lifetime,) in sim.execute(Query[Tuple[Lifetime]]):
        if lifetime.value <= timing.frame:
            sim.remove_entity(entity.id)


@sim.add_system
def print_frame(sim: Simulation, timing: TimingSystem.Data):
    print(f"Frame is {timing.frame}")


# Adding/removing entities and components are tracked within a frame, and can be
#  queried as "mutations" within the next frame.
@sim.add_system
def track_debug_objects(sim: Simulation):
    for mutation in sim.get_component_mutations(Debugging):
        if mutation.type in (MutationType.REMOVE_COMPONENT, MutationType.DELETE):
            print(f"Debugging was disabled on entity {mutation.entity_id}")


bob = sim.create_entity(Position(), Velocity(x=1.0, y=1.0), Health(25))
test = sim.create_entity(Position(), Velocity(), Lifetime(3))

sim.add_component(test, Debugging())

while True:
    sim.tick()
    time.sleep(1)
