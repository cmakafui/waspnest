# examples/simple.py
from pydantic import BaseModel
from waspnest import State, Skill, Agent, skill
import instructor
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


# State definitions
class Query(BaseModel):
    """Input query"""

    text: str


class Analysis(BaseModel):
    """Analyzed query"""

    intent: str
    query: str
    confidence: float


class Response(BaseModel):
    """Final response"""

    message: str
    confidence: float


# Skills
class QueryAnalyzer(Skill):
    @skill
    def execute(self, state: State[Query]) -> State[Analysis]:
        # Analyze the query
        result = self.ask(
            prompt=state.data.text,
            response_model=Analysis,
            system_prompt="Analyze the query for intent and confidence.",
        )
        return State(result)


class ResponseGenerator(Skill):
    @skill
    def execute(self, state: State[Analysis]) -> State[Response]:
        # Generate response using the analysis
        result = self.ask(
            # Use the original query stored in analysis
            prompt=f"Query: {state.data.query}\nIntent: {state.data.intent}",
            response_model=Response,
            system_prompt="Generate a helpful response.",
        )
        return State(result)


def main():
    # Create instructor client
    client = instructor.from_openai(OpenAI())

    # Create agent with skills
    agent = Agent(skills=[QueryAnalyzer(), ResponseGenerator()], client=client)

    # Create initial state
    initial_state = State(Query(text="How do I reset my password in Mac?"))

    # Execute
    final_state = agent.execute(initial_state)

    # Access results
    print(f"Response: {final_state.data.message}")
    print(f"Confidence: {final_state.data.confidence}")


if __name__ == "__main__":
    main()
