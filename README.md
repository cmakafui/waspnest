# WaspNest Framework

A type-safe, state-centric framework for building AI applications. WaspNest provides clean abstractions for building complex AI workflows while maintaining simplicity and type safety.

## Features

- 🔒 **Type-safe by design**: Full type checking for your AI workflows
- 🧩 **State-centric architecture**: Clear data flow and transformations
- 🛠 **Clean skill composition**: Build complex workflows from simple parts
- 🤝 **First-class LLM integration**: Built on top of Instructor for structured outputs
- 🔍 **Built-in monitoring**: Hook system for debugging and observability
- 📦 **Zero magic**: Explicit, understandable, and debuggable

## Installation

```bash
pip install waspnest
```

Required dependencies:

- Python 3.9+
- Instructor
- Pydantic v2

## Quick Start

```python
from pydantic import BaseModel
from waspnest import State, Skill, Agent
from waspnest.hooks import HookPoint
import instructor
from openai import OpenAI
from datetime import datetime

# 1. Define your states
class Query(BaseModel):
    text: str

class Response(BaseModel):
    answer: str
    confidence: float

# 2. Define your skill
class AnswerGenerator(Skill[Query, Response]):
    def execute(self, state: State[Query]) -> State[Response]:
        result = self.ask(
            prompt=state.data.text,
            response_model=Response,
            system_prompt="Generate a helpful response."
        )
        return State(result, context=state.context)

# 3. Add monitoring hooks (optional)
def log_skill_execution(skill: Skill, state: State):
    print(f"[{datetime.now()}] Executing {skill.name}")
    print(f"Input: {state.data}")

# 4. Create agent and run
client = instructor.from_openai(OpenAI())
agent = Agent([AnswerGenerator()], client=client)

# Register hooks if needed
agent.hooks.on(HookPoint.SKILL_START, log_skill_execution)

response = agent.execute(
    State(Query(text="How do I reset my password?"))
)

print(f"Answer: {response.data.answer}")
print(f"Confidence: {response.data.confidence}")
```

## Core Concepts

### States

States are simple Pydantic models that represent data at each step:

```python
class OrderState(BaseModel):
    order_id: str
    items: List[Item]
    total: Decimal
    status: str
```

### Skills

Skills are type-safe transformers between states:

```python
class ProcessOrder(Skill[OrderState, ProcessedOrder]):
    def execute(self, state: State[OrderState]) -> State[ProcessedOrder]:
        result = self.ask(
            prompt=str(state.data),
            response_model=ProcessedOrder,
            system_prompt="Process this order."
        )
        return State(result)
```

### Hooks

Monitor and debug your workflow with hooks:

```python
# Define hooks for monitoring
def log_llm_request(**kwargs):
    print(f"LLM Request: {kwargs['messages']}")

def log_error(exception: Exception, skill: Skill, state: State):
    print(f"Error in {skill.name}: {str(exception)}")

# Register hooks with agent
agent.hooks.on(HookPoint.LLM_REQUEST, log_llm_request)
agent.hooks.on(HookPoint.ERROR, log_error)

Available hook points:

* PRE_EXECUTE: Before execution starts
* POST_EXECUTE: After execution completes
* SKILL_START: Before each skill execution
* SKILL_END: After each skill execution
* ERROR: When errors occur
* LLM_REQUEST: Before LLM calls
```

### Agents

Agents orchestrate skills and handle execution:

```python
agent = Agent(
    skills=[
        ValidateOrder(),
        ProcessOrder(),
        SendConfirmation()
    ],
    client=instructor.from_openai(OpenAI()),
    model="gpt-4o-mini"
)

result = agent.execute(initial_state)
```

## Complex Example

Here's a more complex example showing a multi-step workflow:

```python
# States
class Query(BaseModel):
    text: str
    user_id: str

class Analysis(BaseModel):
    intent: str
    sentiment: float
    priority: int
    query: str  # Preserve original query

class Response(BaseModel):
    message: str
    confidence: float

# Skills
class QueryAnalyzer(Skill[Query, Analysis]):
    def execute(self, state: State[Query]) -> State[Analysis]:
        result = self.ask(
            prompt=state.data.text,
            response_model=Analysis,
            system_prompt="Analyze query intent and sentiment.",
            query=state.data.text
        )
        return State(result)

class ResponseGenerator(Skill[Analysis, Response]):
    def execute(self, state: State[Analysis]) -> State[Response]:
        prompt = f"""
        Query: {state.data.query}
        Intent: {state.data.intent}
        Priority: {state.data.priority}
        Sentiment: {state.data.sentiment}
        """
        result = self.ask(
            prompt=prompt,
            response_model=Response,
            system_prompt="Generate an appropriate response."
        )
        return State(result)

# Usage
agent = Agent(
    skills=[QueryAnalyzer(), ResponseGenerator()],
    client=instructor.from_openai(OpenAI())
)

final_state = agent.execute(
    State(Query(
        text="I've waited 3 days for my order!",
        user_id="123"
    ))
)
```

## Type Safety

WaspNest provides type safety at both compile time and runtime:

- Skills declare their input and output types
- The agent ensures skills only receive compatible states
- Type hints provide IDE support and catch errors early
- Runtime checks prevent invalid state transitions

## Testing

Test your skills and workflows easily:

```python
def test_query_analyzer():
    analyzer = QueryAnalyzer()
    initial_state = State(Query(text="Test query"))

    # Mock the LLM client
    mock_client = Mock()
    mock_client.chat.completions.create.return_value = Analysis(
        intent="test",
        sentiment=0.5,
        priority=1,
        query="Test query"
    )

    analyzer.agent = Agent([], client=mock_client)
    result = analyzer.execute(initial_state)

    assert result.data.intent == "test"
    assert result.data.sentiment == 0.5
```

## Project Structure

```
nexus/
├── core/
│   ├── state.py    # State management
│   ├── skill.py    # Skill base class
│   └── agent.py    # Agent implementation
├── hooks.py        # Hook system
└── __init__.py
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

MIT License - See LICENSE file for details

## Acknowledgments

Built with ❤️ on top of:

- [Instructor](https://github.com/jxnl/instructor)
- [Pydantic](https://github.com/pydantic/pydantic)
