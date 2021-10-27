import itertools
import typing
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    Iterator,
    List,
    Optional,
    Set,
    Tuple,
    Type,
    TypeVar,
)

T = TypeVar("T")


class StorageIterator(Generic[T]):
    def __init__(self, storage, components=None):
        self._storage = storage
        self._field_indexes_cache = [
            storage._component_classes.index(i) for i in (components or [])
        ]
        self._index = 0
        self._ref = EntityRef()
        self._ref.storage = self._storage

    def __iter__(self):
        return self

    def __next__(self) -> T:
        while True:
            if self._index >= len(self._storage._ids):
                raise StopIteration()

            if self._storage._ids[self._index] is None:
                self._index += 1
                continue

            break

        self._ref.storage_index = self._index
        self._ref.id = self._storage._ids[self._index]

        data = [self._storage._datas[self._index][i] for i in self._field_indexes_cache]
        self._index += 1
        return (self._ref, tuple(data))


class ShapedStorage:
    def __init__(self, component_classes: List[Any]):
        self._component_classes = component_classes
        self._ids = []
        self._datas = []

    def __len__(self):
        return len(self._ids)

    def has(self, entity_id: int):
        return entity_id in self._ids

    def prune(self):
        if None in self._ids:
            self._ids = [i for i in self._ids if i is not None]
            self._datas = [i for i in self._datas if i is not None]

    def insert(self, entity_id, data):
        sorted_data = [None] * len(self._component_classes)
        for value in data:
            sorted_data[self._component_classes.index(value.__class__)] = value

        self._ids.append(entity_id)
        self._datas.append(sorted_data)

    def pop(self, entity_id) -> Optional[List[Any]]:
        try:
            idx = self._ids.index(entity_id)
        except ValueError:
            return None
        self._ids[idx] = None
        res = self._datas[idx]
        self._datas[idx] = None
        return res


class EntityRef:
    id: int
    storage: ShapedStorage
    storage_index: int

    def __init__(self):
        self.id = 0
        self.storage = None
        self.storage_index = 0

    def has(self, cls):
        return cls in self.storage._component_classes

    def get(self, cls):
        return self.storage._datas[self.storage_index][
            self.storage._component_classes.index(cls)
        ]


class System:
    def __init__(self, fn):
        self._fn = fn

    def __call__(self, *args, **kwargs):
        return self._fn(*args, **kwargs)


QueryDataT = TypeVar("QueryDataT")


class Query(Generic[QueryDataT]):
    pass


class Simulation:
    _entities: Set[int]
    _storage: Dict[Tuple, ShapedStorage]
    _systems: List[System]
    _entity_id_inc: int

    def __init__(self):
        self._entities = set()
        self._storage = {}
        self._systems = []
        self._entity_id_inc = 0
        self.time = 0

    def _next_entity_id(self) -> int:
        our_id = self._entity_id_inc
        self._entity_id_inc += 1
        return our_id

    def _get_storages(self, classes) -> List[ShapedStorage]:
        return [
            storage
            for storage in self._storage.values()
            if all(i in storage._component_classes for i in classes)
        ]

    def _get_or_create_storage(self, classes) -> ShapedStorage:
        storage_hash = tuple(sorted(hash(i) for i in classes))
        if storage_hash not in self._storage:
            self._storage[storage_hash] = ShapedStorage(classes)
        return self._storage[storage_hash]

    def add_system(self, fn: Callable[..., None]) -> System:
        new_system = System(fn)
        self._systems.append(new_system)
        return new_system

    def add_component(self, entity_id, component):
        components = None
        for storage in self._storage.values():
            existing = storage.pop(entity_id)
            if existing:
                components = existing
                break

        if not components:
            components = []

        components.append(component)
        storage = self._get_or_create_storage(tuple(i.__class__ for i in components))
        storage.insert(entity_id, components)

    def remove_component(self, entity_id, cls):
        components = None
        for storage in self._storage.values():
            existing = storage.pop(entity_id)
            if existing:
                components = existing
                break
        else:
            raise Exception(f"No such entity {entity_id}")

        components = [i for i in components if i.__class__ != cls]
        storage = self._get_or_create_storage(tuple(i.__class__ for i in components))
        storage.insert(entity_id, components)

    def create_entity(self, *components) -> int:
        entity_id = self._next_entity_id()
        self._entities.add(entity_id)

        storage = self._get_or_create_storage(tuple(i.__class__ for i in components))
        storage.insert(entity_id, components)

        return entity_id

    def remove_entity(self, entity_id: int):
        for storage in self._storage.values():
            if storage.has(entity_id):
                storage.pop(entity_id)
                return
        else:
            raise Exception(f"No such entity {entity_id}")

    def tick(self):
        for system in self._systems:
            system(self)

        for id, storage in list(self._storage.items()):
            storage.prune()

            if len(storage) == 0:
                del self._storage[id]

        self.time += 1

    def execute(self, query: Type[Query[T]]) -> Iterator[Tuple[EntityRef, T]]:
        assert isinstance(query, typing._GenericAlias)

        (query_data,) = typing.get_args(query)
        components = typing.get_args(query_data)
        storages = self._get_storages(components)
        if not storages:
            return []

        return itertools.chain.from_iterable(
            [StorageIterator(storage, components=components) for storage in storages]
        )