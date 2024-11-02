# tests/test_agent.py
from waspnest import Agent, State, Skill, skill
from waspnest.hooks import HookPoint
from conftest import QueryInput, IntermediateOutput, FinalOutput


def test_agent_initialization(sample_agent, analyzer_skill, responder_skill):
    """Test agent initialization and skill attachment"""
    assert len(sample_agent.skills) == 2
    assert sample_agent.skills[0] == analyzer_skill
    assert sample_agent.skills[1] == responder_skill
    assert analyzer_skill.agent == sample_agent
    assert responder_skill.agent == sample_agent


def test_agent_execution_chain(sample_agent, sample_state):
    """Test execution chain with multiple skills"""
    final_state = sample_agent.execute(sample_state)

    assert isinstance(final_state.data, FinalOutput)
    assert "execution_started_at" in final_state.context
    assert "execution_completed_at" in final_state.context
    assert final_state.context["total_steps"] == 2
    assert final_state.context["user_id"] == "123"


def test_agent_max_steps(sample_agent, sample_state):
    """Test max steps limitation"""
    final_state = sample_agent.execute(sample_state, max_steps=1)

    assert isinstance(final_state.data, IntermediateOutput)
    assert final_state.context["total_steps"] == 1


def test_agent_error_handling(mock_client):
    """Test error handling during execution"""

    class ErrorSkill(Skill):
        @skill
        def execute(self, state: State[QueryInput]) -> State[FinalOutput]:
            raise ValueError("Test error")

    agent = Agent(skills=[ErrorSkill()], client=mock_client)
    state = State(QueryInput(text="test"))

    final_state = agent.execute(state)

    assert "error" in final_state.context
    assert final_state.context["error"] == "Test error"
    assert final_state.context["error_skill"] == "ErrorSkill"


def test_agent_empty_skills(mock_client, sample_state):
    """Test agent behavior with no skills"""
    agent = Agent(skills=[], client=mock_client)
    final_state = agent.execute(sample_state)

    assert final_state.data == sample_state.data
    assert "execution_completed_at" in final_state.context


def test_agent_context_handling(sample_agent, sample_state):
    """Test context handling through execution"""
    custom_context = {"session_id": "test-session"}
    final_state = sample_agent.execute(sample_state, context=custom_context)

    assert final_state.context["session_id"] == "test-session"
    assert final_state.context["user_id"] == "123"  # Original context preserved


def test_agent_hook_integration(sample_agent, sample_state):
    """Test hook system integration"""
    hook_calls = []

    def test_hook(**kwargs):
        hook_calls.append(kwargs.get("state", None))

    sample_agent.hooks.on(HookPoint.PRE_EXECUTE, test_hook)
    sample_agent.hooks.on(HookPoint.POST_EXECUTE, test_hook)

    final_state = sample_agent.execute(sample_state)

    assert len(hook_calls) == 2
    assert hook_calls[0] == sample_state  # PRE_EXECUTE
    assert hook_calls[1] == final_state  # POST_EXECUTE
