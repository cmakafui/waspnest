# nexus/core/state.py
from typing import Generic, TypeVar
from dataclasses import dataclass, field
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


@dataclass(frozen=True)
class State(Generic[T]):
    """
    A wrapper around state data that includes metadata and context
    """

    data: T
    metadata: dict = field(default_factory=dict)
    context: dict = field(default_factory=dict)

    def with_context(self, **updates) -> "State[T]":
        """Creates new state with updated context"""
        return State(
            data=self.data, metadata=self.metadata, context={**self.context, **updates}
        )
