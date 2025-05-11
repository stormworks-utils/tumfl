from __future__ import annotations

from typing import Generic, TypeVar

from _weakrefset import WeakSet

V = TypeVar("V")


class SharedList(Generic[V]):
    # pylint: disable=protected-access
    def __init__(self, member: V):
        self._members: WeakSet[V] = WeakSet((member,))

    def absorb(self, other: SharedList) -> list[V]:
        self._members.update(other._members)
        for obj in list(other._members):
            obj._members = self._members
        return list(other._members)
