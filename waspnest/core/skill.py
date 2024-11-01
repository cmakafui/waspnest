# nexus/core/skill.py
from typing import Generic, TypeVar, Type
from pydantic import BaseModel
from .state import State

InputT = TypeVar("InputT", bound=BaseModel)
OutputT = TypeVar("OutputT", bound=BaseModel)


class Skill(Generic[InputT, OutputT]):
    """Base class for skills that transform states"""

    def __init__(self, name: str = None):
        self.name = name or self.__class__.__name__
        self.agent = None
        # Store the type hints for runtime checking
        self.input_type = self.__class__.__orig_bases__[0].__args__[0]
        self.output_type = self.__class__.__orig_bases__[0].__args__[1]

    def can_handle(self, state: State) -> bool:
        """Check if this skill can handle the given state"""
        return isinstance(state.data, self.input_type)

    def execute(self, state: State) -> State:
        """Execute this skill on a state"""
        raise NotImplementedError

    def ask(
        self,
        prompt: str,
        response_model: Type[BaseModel],
        system_prompt: str | None = None,
        **kwargs,
    ) -> BaseModel:
        """Helper for LLM interactions"""
        if not self.agent:
            raise RuntimeError("Skill must be attached to an agent")

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        return self.agent.client.chat.completions.create(
            model=self.agent.model,
            messages=messages,
            response_model=response_model,
            **kwargs,
        )
