# WaspNest Framework

A type-safe, state-centric framework for building AI applications that learn. WaspNest provides clean abstractions for building complex AI workflows while maintaining strict type safety and runtime validation.

## Features

- 🔒 **Enhanced Type Safety**: Full static and runtime type checking with the `@skill` decorator
- 🧩 **State-Centric Architecture**: Clear data flow and transformations
- 🛠 **Clean Skill Composition**: Build complex workflows from simple parts
- 🤝 **First-Class LLM Integration**: Built on top of Instructor for structured outputs
- 🔍 **Built-in Monitoring**: Comprehensive hook system for debugging and observability
- 📦 **Zero Magic**: Explicit, understandable, and debuggable
- 🎯 **Runtime Validation**: Automatic input/output validation with the skill decorator

## Installation

```bash
pip install waspnest
```

Required dependencies:

- Python 3.10+
- Instructor
- Pydantic v2

## Quick Start

```python
from pydantic import BaseModel
from waspnest import State, Skill, Agent, skill
import instructor
from openai import OpenAI

# 1. Define your states as Pydantic models
class Query(BaseModel):
    text: str

class Response(BaseModel):
    answer: str
    confidence: float

# 2. Define your skill with type-safe decorator
class AnswerGenerator(Skill):
    @skill  # New! Provides runtime type checking
    def execute(self, state: State[Query]) -> State[Response]:
        result = self.ask(
            prompt=state.data.text,
            response_model=Response,
            system_prompt="Generate a helpful response."
        )
        return State(result)

# 3. Create agent and run
client = instructor.from_openai(OpenAI())
agent = Agent([AnswerGenerator()], client=client)

response = await agent.execute(
    State(Query(text="How do I reset my password?"))
)

print(f"Answer: {response.data.answer}")
print(f"Confidence: {response.data.confidence}")
```

## Core Concepts

### Enhanced Type Safety with @skill Decorator

The new `@skill` decorator provides automatic runtime type validation:

```python
class AnalyzeQuery(Skill):
    @skill  # Validates input/output types at runtime
    def execute(self, state: State[Query]) -> State[Analysis]:
        # Will raise TypeError if input/output don't match declared types
        result = self.ask(
            prompt=state.data.text,
            response_model=Analysis
        )
        return State(result)

# The decorator ensures:
# 1. Input state matches declared type
# 2. Output state matches declared type
# 3. Proper error messages for type mismatches
```

### States as Pydantic Models

States are simple Pydantic models that represent data at each step:

```python
class OrderState(BaseModel):
    order_id: str
    items: List[Item]
    total: Decimal
    status: str

# States are immutable and type-safe
state = State(OrderState(...))
```

### Type-Safe Skills

Skills are transformers between states with guaranteed type safety:

```python
class ProcessOrder(Skill):
    @skill
    def execute(self, state: State[OrderState]) -> State[ProcessedOrder]:
        result = self.ask(
            prompt=str(state.data),
            response_model=ProcessedOrder,
            system_prompt="Process this order."
        )
        return State(result)
```

### Comprehensive Hook System

Monitor and debug your workflow with hooks:

```python
def log_skill_execution(skill: Skill, state: State):
    print(f"[{datetime.now()}] Executing {skill.name}")
    print(f"Input: {state.data}")

# Register hooks with agent
agent.hooks.on(HookPoint.SKILL_START, log_skill_execution)

Available hook points:
* PRE_EXECUTE: Before execution starts
* POST_EXECUTE: After execution completes
* SKILL_START: Before each skill execution
* SKILL_END: After each skill execution
* ERROR: When errors occur
* LLM_REQUEST: Before LLM calls
```

## Complex Example

Here's a more complex example showing state transitions with type safety:

```python
from pydantic import BaseModel
from waspnest import State, Skill, Agent, skill

# States
class Query(BaseModel):
    text: str
    user_id: str

class Analysis(BaseModel):
    intent: str
    sentiment: float
    query: str  # Preserve original query

class Response(BaseModel):
    message: str
    confidence: float

# Skills with runtime type validation
class QueryAnalyzer(Skill):
    @skill
    def execute(self, state: State[Query]) -> State[Analysis]:
        result = self.ask(
            prompt=state.data.text,
            response_model=Analysis
        )
        return State(result)

class ResponseGenerator(Skill):
    @skill
    def execute(self, state: State[Analysis]) -> State[Response]:
        result = self.ask(
            prompt=f"""
            Query: {state.data.query}
            Intent: {state.data.intent}
            Sentiment: {state.data.sentiment}
            """,
            response_model=Response
        )
        return State(result)

# Usage with automatic type checking
agent = Agent([QueryAnalyzer(), ResponseGenerator()], client=client)

final_state = await agent.execute(
    State(Query(
        text="I've waited 3 days for my order!",
        user_id="123"
    ))
)
```

## Type Safety Features

WaspNest provides multiple layers of type safety:

1. **Static Type Checking**:

   - Full type hints for IDE support
   - Mypy compatibility
   - Clear type errors during development

2. **Runtime Validation** (New!):

   - `@skill` decorator ensures type consistency
   - Automatic validation of input/output states
   - Clear error messages for type mismatches

3. **State Immutability**:
   - States are immutable by default
   - Context updates create new states
   - Prevents accidental state mutation

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
        query="Test query"
    )

    analyzer.agent = Agent([], client=mock_client)
    result = analyzer.execute(initial_state)

    assert result.data.intent == "test"
    assert result.data.sentiment == 0.5
```

## Project Structure

```
waspnest/
├── core/
│   ├── state.py    # State management
│   ├── skill.py    # Skill base class & decorator
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

- [Instructor](https://github.com/instructor-ai/instructor)
- [Pydantic](https://github.com/pydantic/pydantic)
- [OpenAI](https://platform.openai.com/docs/api-reference)
