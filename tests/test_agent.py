# tests/test_agent.py
from waspnest.core.agent import Agent
from waspnest.core.state import State
from waspnest.core.skill import Skill
from waspnest.hooks import HookPoint

from conftest import QueryInput, IntermediateOutput, FinalOutput

def test_agent_initialization(sample_agent, analyzer_skill, responder_skill):
    """Test agent initialization and skill attachment"""
    assert len(sample_agent.skills) == 2
    assert sample_agent.skills[0] == analyzer_skill
    assert sample_agent.skills[1] == responder_skill
    assert analyzer_skill.agent == sample_agent
    assert responder_skill.agent == sample_agent

def test_agent_execution_single_skill(mock_client, analyzer_skill, sample_state):
    """Test execution with single skill"""
    agent = Agent(skills=[analyzer_skill], client=mock_client)
    final_state = agent.execute(sample_state)
    
    assert isinstance(final_state.data, IntermediateOutput)
    assert final_state.data.analysis == f"Analyzed: {sample_state.data.text}"
    assert "execution_started_at" in final_state.context
    assert "execution_completed_at" in final_state.context
    assert final_state.context["total_steps"] == 1

def test_agent_execution_skill_chain(sample_agent, sample_state):
    """Test execution with multiple skills"""
    final_state = sample_agent.execute(sample_state)
    
    assert isinstance(final_state.data, FinalOutput)
    assert "Analyzed: test query" in final_state.data.response
    assert final_state.context["total_steps"] == 2

def test_agent_context_preservation(sample_agent, sample_state):
    """Test context preservation through execution chain"""
    final_state = sample_agent.execute(sample_state)
    
    # Verify original context is preserved
    assert final_state.context["user_id"] == "123"
    
    # Verify execution metadata was added
    assert "execution_started_at" in final_state.context
    assert "execution_completed_at" in final_state.context
    assert "total_steps" in final_state.context

def test_agent_max_steps(sample_agent, sample_state):
    """Test max steps limitation"""
    final_state = sample_agent.execute(sample_state, max_steps=1)
    
    assert isinstance(final_state.data, IntermediateOutput)
    assert final_state.context["total_steps"] == 1

def test_agent_hooks(sample_agent, sample_state):
    """Test hook system integration"""
    hook_calls = []
    
    def sample_hook(**kwargs):
        hook_calls.append(kwargs)
    
    # Register hooks
    sample_agent.hooks.on(HookPoint.PRE_EXECUTE, sample_hook)
    sample_agent.hooks.on(HookPoint.POST_EXECUTE, sample_hook)
    sample_agent.hooks.on(HookPoint.SKILL_START, sample_hook)
    sample_agent.hooks.on(HookPoint.SKILL_END, sample_hook)
    
    sample_agent.execute(sample_state)
    
    assert len(hook_calls) >= 6

def test_agent_error_handling(mock_client, sample_state):
    """Test error handling during execution"""
    class ErrorSkill(Skill[QueryInput, FinalOutput]):
        def execute(self, state: State[QueryInput]) -> State[FinalOutput]:
            raise ValueError("Test error")
    
    agent = Agent(skills=[ErrorSkill()], client=mock_client)
    final_state = agent.execute(sample_state)
    
    assert "error" in final_state.context
    assert final_state.context["error"] == "Test error"
    assert final_state.context["error_skill"] == "ErrorSkill"

def test_agent_empty_skills(mock_client, sample_state):
    """Test agent behavior with no skills"""
    agent = Agent(skills=[], client=mock_client)
    final_state = agent.execute(sample_state)
    
    assert final_state.data == sample_state.data
    assert "execution_completed_at" in final_state.context

def test_agent_metadata_handling(sample_agent, sample_state):
    """Test metadata preservation through execution chain"""
    final_state = sample_agent.execute(sample_state)
    assert final_state.metadata == sample_state.metadata
    
    intermediate_state = sample_agent.execute(sample_state, max_steps=1)
    assert intermediate_state.metadata == sample_state.metadata
