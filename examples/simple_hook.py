# examples/simple_hook.py
from waspnest import State, Skill, Agent, skill
from waspnest.hooks import HookPoint
from pydantic import BaseModel
import instructor
from openai import OpenAI
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()


# State definitions
class Query(BaseModel):
    text: str


class Response(BaseModel):
    answer: str
    confidence: float


# Skill definition
class AnswerSkill(Skill):
    @skill
    def execute(self, state: State[Query]) -> State[Response]:
        result = self.ask(
            prompt=state.data.text,
            response_model=Response,
            system_prompt="You are a helpful assistant.",
        )
        return State(result, context=state.context)


# Hook functions
def log_execution_start(state: State):
    print(f"\n[{datetime.now()}] Starting execution with query: {state.data.text}")
    print(f"Initial context: {state.context}")


def log_skill_start(skill: Skill, state: State):
    print(f"\n[{datetime.now()}] Starting skill: {skill.name}")
    print(f"Step {state.context.get('current_step', 'initial')}")


def log_skill_end(skill: Skill, state: State):
    print(f"\n[{datetime.now()}] Completed skill: {skill.name}")
    print(f"Result confidence: {state.data.confidence}")


def log_llm_request(**kwargs):
    print(f"\n[{datetime.now()}] LLM Request:")
    print(f"System prompt: {kwargs['messages'][0]['content']}")
    print(f"User prompt: {kwargs['messages'][1]['content']}")


def log_error(exception: Exception, skill: Skill, state: State):
    print(f"\n[{datetime.now()}] Error in skill {skill.name}:")
    print(f"Error: {str(exception)}")
    print(f"State context: {state.context}")


def main():
    # Create instructor client
    client = instructor.from_openai(OpenAI())

    # Create agent with skill
    agent = Agent(skills=[AnswerSkill()], client=client)

    # Register hooks
    agent.hooks.on(HookPoint.PRE_EXECUTE, log_execution_start)
    agent.hooks.on(HookPoint.SKILL_START, log_skill_start)
    agent.hooks.on(HookPoint.SKILL_END, log_skill_end)
    agent.hooks.on(HookPoint.LLM_REQUEST, log_llm_request)
    agent.hooks.on(HookPoint.ERROR, log_error)

    # Create initial state
    initial_state = State(
        data=Query(text="How do I reset my password?"),
        context={"user_id": "123", "priority": "high"},
    )

    # Execute
    final_state = agent.execute(initial_state)

    # Print final result
    print(f"\nFinal Answer: {final_state.data.answer}")
    print(f"Final Context: {final_state.context}")


if __name__ == "__main__":
    main()
