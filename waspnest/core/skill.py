# waspnest/core/skill.py
from typing import Type, get_args, get_type_hints, Union
from functools import wraps
from pydantic import BaseModel
from .state import State


def skill(func: callable = None):
    """Decorator that ensures state types are Pydantic models and handles type checking.

    Examples:
    ```python
    @skill
    def process_query(self, state: State[Query]) -> State[Response]:
        result = self.ask(state.data.text, Response)
        return State(result)

    @skill
    def smart_process(self, state: State[Query]) -> State[SimpleResponse | DetailedResponse]:
        if is_complex(state.data):
            return State(DetailedResponse(answer="Detailed..."))
        return State(SimpleResponse(answer="Simple..."))
    ```
    """

    @wraps(func)
    def wrapper(self, state: State):
        # Get type hints
        hints = get_type_hints(func)

        # Extract the input type from State[T]
        state_type = hints["state"]
        if hasattr(state_type, "__origin__") and state_type.__origin__ is State:
            input_type = get_args(state_type)[0]
        else:
            raise TypeError(f"State type annotation must be State[T], got {state_type}")

        # Extract output type(s) from return type State[T]
        return_type = hints["return"]
        if hasattr(return_type, "__origin__") and return_type.__origin__ is State:
            output_type = get_args(return_type)[0]
            # Handle union types
            if hasattr(output_type, "__origin__") and output_type.__origin__ is Union:
                output_types = get_args(output_type)
            else:
                output_types = (output_type,)
        else:
            raise TypeError(f"Return type must be State[T], got {return_type}")

        # Validate input is a Pydantic model
        if not isinstance(state.data, BaseModel):
            raise TypeError(f"Input must be a Pydantic model, got {type(state.data)}")

        # Validate input matches expected type
        if not isinstance(state.data, input_type):
            raise TypeError(f"Expected input type {input_type}, got {type(state.data)}")

        # Execute skill
        result = func(self, state)

        # Validate output
        if not isinstance(result, State):
            raise TypeError(f"Skill must return a State, got {type(result)}")

        if not isinstance(result.data, BaseModel):
            raise TypeError(f"Output must be a Pydantic model, got {type(result.data)}")

        # Validate output matches one of the expected types
        if not isinstance(result.data, output_types):
            type_names = [t.__name__ for t in output_types]
            expected = (
                type_names[0]
                if len(type_names) == 1
                else f"one of: {', '.join(type_names)}"
            )
            raise TypeError(
                f"Output must be {expected}, got {type(result.data).__name__}"
            )

        return result

    # Store the input type on the wrapper for can_handle check
    hints = get_type_hints(func)
    state_type = hints["state"]
    if hasattr(state_type, "__origin__") and state_type.__origin__ is State:
        wrapper.input_type = get_args(state_type)[0]
    else:
        raise TypeError(f"State type annotation must be State[T], got {state_type}")

    return wrapper


class Skill:
    """Base class for skills that transform states."""

    def __init__(self, name: str = None):
        self.name = name or self.__class__.__name__
        self.agent = None

    def can_handle(self, state: State) -> bool:
        """Check if this skill can handle the given state."""
        execute = getattr(self, "execute")
        if hasattr(execute, "input_type"):
            return isinstance(state.data, execute.input_type)
        return True  # If no type info, assume it can handle it

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
