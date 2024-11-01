# nexus/core/agent.py
from datetime import datetime
from .skill import Skill
from .state import State
from ..hooks import Hooks, HookPoint


class Agent:
    """Coordinates skills and handles execution"""

    def __init__(self, skills: list[Skill], client: any, model: str = "gpt-4o-mini"):
        self.skills = skills
        self.client = client
        self.model = model
        self.hooks = Hooks()

        # Bridge to instructor hooks
        self.client.on(
            "completion:kwargs",
            lambda **kwargs: self.hooks.trigger(HookPoint.LLM_REQUEST, **kwargs),
        )
        self.client.on(
            "completion:error",
            lambda e: self.hooks.trigger(HookPoint.ERROR, exception=e),
        )

        # Attach agent to skills
        for skill in skills:
            skill.agent = self

    def execute(
        self, initial_state: State, max_steps: int = 10, context: dict | None = None
    ) -> State:
        """Execute skills on state"""

        current_state = initial_state
        if context:
            current_state = current_state.with_context(**context)

        # Add execution metadata
        current_state = current_state.with_context(
            execution_started_at=datetime.now().isoformat(), max_steps=max_steps
        )
        self.hooks.trigger(HookPoint.PRE_EXECUTE, state=initial_state)

        steps = 0
        while steps < max_steps:
            # Track if any skill was executed
            executed = False

            # Try each skill
            for skill in self.skills:
                # Only try skills that can handle current state
                if skill.can_handle(current_state):
                    try:
                        # Add pre-execution context
                        current_state = current_state.with_context(
                            current_step=steps,
                            current_skill=skill.name,
                            skill_started_at=datetime.now().isoformat(),
                        )
                        self.hooks.trigger(
                            HookPoint.SKILL_START, skill=skill, state=current_state
                        )

                        new_state = skill.execute(current_state)
                        if new_state is not None:
                            current_state = new_state
                            # Update metadata
                            current_state = new_state.with_context(
                                last_skill=skill.name,
                                last_step=steps,
                                skill_completed_at=datetime.now().isoformat(),
                            )
                            self.hooks.trigger(
                                HookPoint.SKILL_END, skill=skill, state=current_state
                            )
                            executed = True
                            break  # Move to next state once a skill succeeds

                    except Exception as e:
                        # Add Error context
                        current_state = current_state.with_context(
                            error=str(e), error_skill=skill.name, error_step=steps
                        )
                        self.hooks.trigger(
                            HookPoint.ERROR,
                            exception=e,
                            skill=skill,
                            state=current_state,
                        )
                        continue

            # If no skill could handle the state, we're done
            if not executed:
                break

            steps += 1

        # Add completion context
        current_state = current_state.with_context(
            execution_completed_at=datetime.now().isoformat(), total_steps=steps
        )
        self.hooks.trigger(HookPoint.POST_EXECUTE, state=current_state)

        return current_state
