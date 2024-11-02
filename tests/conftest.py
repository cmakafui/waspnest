# tests/conftest.py
import pytest
from unittest.mock import Mock
from pydantic import BaseModel
from waspnest import State, Skill, Agent, skill


# Shared Models
class QueryInput(BaseModel):
    text: str


class IntermediateOutput(BaseModel):
    analysis: str
    confidence: float


class FinalOutput(BaseModel):
    response: str
    confidence: float


# Shared Skills
class AnalyzerSkill(Skill):
    @skill
    def execute(self, state: State[QueryInput]) -> State[IntermediateOutput]:
        result = IntermediateOutput(
            analysis=f"Analyzed: {state.data.text}", confidence=0.9
        )
        return State(data=result, context=state.context, metadata=state.metadata)


class ResponderSkill(Skill):
    @skill
    def execute(self, state: State[IntermediateOutput]) -> State[FinalOutput]:
        result = FinalOutput(
            response=f"Response for: {state.data.analysis}", confidence=0.95
        )
        return State(data=result, context=state.context, metadata=state.metadata)


# Shared Fixtures
@pytest.fixture
def mock_client():
    """Mock LLM client for testing"""
    client = Mock()
    client.chat.completions.create.return_value = FinalOutput(
        response="test response", confidence=0.8
    )
    return client


@pytest.fixture
def analyzer_skill():
    """Sample analyzer skill"""
    return AnalyzerSkill()


@pytest.fixture
def responder_skill():
    """Sample responder skill"""
    return ResponderSkill()


@pytest.fixture
def sample_agent(mock_client, analyzer_skill, responder_skill):
    """Preconfigured agent with both skills"""
    return Agent(skills=[analyzer_skill, responder_skill], client=mock_client)


@pytest.fixture
def sample_state():
    """Sample initial state"""
    return State(
        data=QueryInput(text="test query"),
        context={"user_id": "123"},
        metadata={"source": "test"},
    )
