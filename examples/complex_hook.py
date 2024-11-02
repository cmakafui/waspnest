# examples/complex_hook.py
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


class SimpleResponse(BaseModel):
    answer: str
    confidence: float


class DetailedResponse(BaseModel):
    answer: str
    explanation: str
    confidence: float
    references: list[str]


# Smart skill that gives simple or detailed responses
class SmartAnswerSkill(Skill):
    @skill
    def execute(self, state: State[Query]) -> State[SimpleResponse | DetailedResponse]:
        # Analyze query complexity first
        complexity = self.analyze_complexity(state.data.text)

        if complexity > 0.7:  # Complex query needs detailed response
            result = self.ask(
                prompt=f"Give a detailed answer with explanation and references for: {state.data.text}",
                response_model=DetailedResponse,
                system_prompt="You are a helpful expert. Provide detailed answers with explanations and references.",
            )
        else:  # Simple query gets simple response
            result = self.ask(
                prompt=state.data.text,
                response_model=SimpleResponse,
                system_prompt="You are a helpful assistant. Provide clear, concise answers.",
            )

        return State(result, context=state.context)

    def analyze_complexity(self, text: str) -> float:
        """Simple complexity analysis based on text length and question words."""
        complexity_words = {
            "why",
            "how",
            "explain",
            "describe",
            "compare",
            "analyze",
            "difference",
        }
        words = text.lower().split()

        # Check length and presence of complexity indicators
        has_complexity_words = any(word in complexity_words for word in words)
        is_long = len(words) > 6

        return 0.8 if (has_complexity_words and is_long) else 0.5


# Hook functions
def log_execution_start(state: State):
    print(f"\n[{datetime.now()}] Starting execution with query: {state.data.text}")
    print(f"Initial context: {state.context}")


def log_skill_start(skill: Skill, state: State):
    print(f"\n[{datetime.now()}] Starting skill: {skill.name}")
    print(f"Current step: {state.context.get('current_step', 'initial')}")


def log_skill_end(skill: Skill, state: State):
    print(f"\n[{datetime.now()}] Completed skill: {skill.name}")
    if isinstance(state.data, DetailedResponse):
        print(
            f"Generated detailed response with {len(state.data.references)} references"
        )
        print(f"Confidence: {state.data.confidence}")
    else:
        print(f"Generated simple response with confidence: {state.data.confidence}")


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
    agent = Agent(skills=[SmartAnswerSkill()], client=client)

    # Register hooks
    agent.hooks.on(HookPoint.PRE_EXECUTE, log_execution_start)
    agent.hooks.on(HookPoint.SKILL_START, log_skill_start)
    agent.hooks.on(HookPoint.SKILL_END, log_skill_end)
    # agent.hooks.on(HookPoint.LLM_REQUEST, log_llm_request)
    agent.hooks.on(HookPoint.ERROR, log_error)

    # Test with a simple query
    simple_state = State(
        Query(text="What time is it in New York?"),
        context={"user_id": "123", "priority": "low"},
    )

    # Test with a complex query
    complex_state = State(
        Query(
            text="Can you explain how quantum computers work and their impact on cryptography?"
        ),
        context={"user_id": "456", "priority": "high"},
    )

    print("\n=== Testing Simple Query ===")
    simple_result = agent.execute(simple_state)
    print("\nSimple Result:")
    print(f"Answer: {simple_result.data.answer}")
    print(f"Confidence: {simple_result.data.confidence}")

    print("\n=== Testing Complex Query ===")
    complex_result = agent.execute(complex_state)
    print("\nComplex Result:")
    print(f"Answer: {complex_result.data.answer}")
    if isinstance(complex_result.data, DetailedResponse):
        print(f"Explanation: {complex_result.data.explanation}")
        print(f"References: {', '.join(complex_result.data.references)}")
    print(f"Confidence: {complex_result.data.confidence}")


if __name__ == "__main__":
    main()
