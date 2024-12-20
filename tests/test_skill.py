# tests/test_skill.py
import pytest
from waspnest import State, skill

from conftest import QueryInput, IntermediateOutput, FinalOutput, AnalyzerSkill


def test_skill_decorator():
    """Test skill decorator functionality"""

    @skill
    def execute_func(self, state: State[QueryInput]) -> State[IntermediateOutput]:
        return State(IntermediateOutput(analysis="test", confidence=0.9))

    assert hasattr(execute_func, "input_type")
    assert execute_func.input_type == QueryInput


def test_skill_type_validation(analyzer_skill, sample_state):
    """Test skill type validation"""
    # Valid input
    output = analyzer_skill.execute(sample_state)
    assert isinstance(output.data, IntermediateOutput)

    # Invalid input type
    invalid_state = State(FinalOutput(response="test", confidence=0.8))
    with pytest.raises(TypeError, match="Expected input type"):
        analyzer_skill.execute(invalid_state)


def test_skill_can_handle(analyzer_skill, sample_state):
    """Test skill state compatibility checking"""
    # Test with compatible state
    assert analyzer_skill.can_handle(sample_state)

    # Test with incompatible state
    incompatible_state = State(IntermediateOutput(analysis="test", confidence=0.9))
    assert not analyzer_skill.can_handle(incompatible_state)


def test_skill_execution(analyzer_skill, sample_state):
    """Test basic skill execution"""
    output_state = analyzer_skill.execute(sample_state)

    assert isinstance(output_state.data, IntermediateOutput)
    assert output_state.data.analysis == f"Analyzed: {sample_state.data.text}"
    assert output_state.data.confidence == 0.9
    assert output_state.context == sample_state.context
    assert output_state.metadata == sample_state.metadata


def test_skill_ask_without_agent(analyzer_skill):
    """Test ask() error when no agent attached"""
    with pytest.raises(RuntimeError, match="Skill must be attached to an agent"):
        analyzer_skill.ask("test prompt", IntermediateOutput)


def test_skill_ask_with_agent(analyzer_skill, sample_agent):
    """Test ask() functionality with attached agent"""
    result = analyzer_skill.ask(
        prompt="test prompt", response_model=FinalOutput, system_prompt="test system"
    )

    assert isinstance(result, FinalOutput)
    assert result.response == "test response"
    assert result.confidence == 0.8


def test_skill_name_customization():
    """Test skill name customization"""
    custom_skill = AnalyzerSkill(name="CustomAnalyzer")
    default_skill = AnalyzerSkill()

    assert custom_skill.name == "CustomAnalyzer"
    assert default_skill.name == "AnalyzerSkill"


def test_skill_context_preservation(analyzer_skill, sample_state):
    """Test context preservation through execution"""
    output_state = analyzer_skill.execute(sample_state)
    assert output_state.context == sample_state.context
