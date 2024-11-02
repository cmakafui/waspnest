# waspnest/core/state.py
from typing import Generic, TypeVar, Optional
from dataclasses import dataclass
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


@dataclass(frozen=True)
class State(Generic[T]):
    """A wrapper around state data that includes metadata and context."""

    data: T
    metadata: Optional[dict] = None
    context: Optional[dict] = None

    def __post_init__(self):
        """Initialize with empty dicts if None"""
        # Using object.__setattr__ because the class is frozen
        object.__setattr__(self, "metadata", self.metadata or {})
        object.__setattr__(self, "context", self.context or {})

    def with_context(self, **updates) -> "State[T]":
        """Creates new state with updated context"""
        new_context = {**self.context, **updates}
        return State(data=self.data, metadata=self.metadata.copy(), context=new_context)
