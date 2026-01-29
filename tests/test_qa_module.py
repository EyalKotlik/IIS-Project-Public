"""
Unit tests for Q&A module.

Tests cover:
- Context building (selection-first, neighborhood expansion, global overview)
- Prompt generation (grounding rules, citations, JSON format)
- History management (trimming, summarization)
- Parsing and validation
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app_mockup.backend.qa_module import (
    QaResponse,
    QaContext,
    ChatTurn,
    build_qa_context,
    answer_question,
    add_to_history,
    _build_adjacency,
    _expand_neighborhood,
    _build_graph_overview,
    _retrieve_by_question,
    _summarize_history,
    _build_system_prompt,
    _build_user_prompt,
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def sample_graph():
    """Create a sample graph for testing."""
    return {
        'nodes': [
            {
                'id': 'n1',
                'type': 'claim',
                'label': 'Main claim',
                'span': 'This is the main claim of the argument.',
                'paraphrase': 'The primary assertion',
                'confidence': 0.9
            },
            {
                'id': 'n2',
                'type': 'premise',
                'label': 'Supporting premise',
                'span': 'This premise supports the main claim.',
                'paraphrase': 'Evidence for the claim',
                'confidence': 0.85
            },
            {
                'id': 'n3',
                'type': 'objection',
                'label': 'Counter argument',
                'span': 'However, there is an objection to consider.',
                'paraphrase': 'A counterpoint',
                'confidence': 0.8
            },
            {
                'id': 'n4',
                'type': 'reply',
                'label': 'Reply to objection',
                'span': 'The objection can be addressed as follows.',
                'paraphrase': 'Response to counterpoint',
                'confidence': 0.75
            },
            {
                'id': 'n5',
                'type': 'premise',
                'label': 'Another premise',
                'span': 'Additional evidence supporting the claim.',
                'paraphrase': 'More support',
                'confidence': 0.88
            }
        ],
        'edges': [
            {'source': 'n2', 'target': 'n1', 'relation': 'support', 'confidence': 0.9},
            {'source': 'n5', 'target': 'n1', 'relation': 'support', 'confidence': 0.85},
            {'source': 'n3', 'target': 'n1', 'relation': 'attack', 'confidence': 0.8},
            {'source': 'n4', 'target': 'n3', 'relation': 'attack', 'confidence': 0.75},
        ],
        'meta': {}
    }


@pytest.fixture
def sample_history():
    """Create sample chat history."""
    return [
        ChatTurn(
            question="What is the main claim?",
            answer="The main claim is about...",
            cited_node_ids=["n1"]
        ),
        ChatTurn(
            question="What evidence supports it?",
            answer="The evidence includes...",
            cited_node_ids=["n2", "n5"]
        )
    ]


# ============================================================================
# Schema Tests
# ============================================================================

@pytest.mark.unit
class TestQaResponse:
    """Test QaResponse Pydantic schema."""
    
    def test_valid_response(self):
        """Test creating valid QaResponse."""
        response = QaResponse(
            answer="Test answer",
            cited_node_ids=["n1", "n2"],
            confidence=0.85,
            followups=["Follow-up 1", "Follow-up 2"],
            notes="Some notes"
        )
        
        assert response.answer == "Test answer"
        assert response.cited_node_ids == ["n1", "n2"]
        assert response.confidence == 0.85
        assert len(response.followups) == 2
        assert response.notes == "Some notes"
    
    def test_minimal_response(self):
        """Test QaResponse with minimal fields."""
        response = QaResponse(
            answer="Minimal answer",
            confidence=0.5
        )
        
        assert response.answer == "Minimal answer"
        assert response.cited_node_ids == []
        assert response.followups == []
        assert response.notes is None
    
    def test_confidence_validation(self):
        """Test confidence must be in [0, 1]."""
        with pytest.raises(ValueError):
            QaResponse(answer="Test", confidence=-0.1)
        
        with pytest.raises(ValueError):
            QaResponse(answer="Test", confidence=1.5)


# ============================================================================
# Context Building Tests
# ============================================================================

@pytest.mark.unit
class TestContextBuilding:
    """Test context building functions."""
    
    def test_build_adjacency(self):
        """Test adjacency list building."""
        edges = [
            {'source': 'n1', 'target': 'n2', 'relation': 'support', 'confidence': 0.9},
            {'source': 'n2', 'target': 'n3', 'relation': 'attack', 'confidence': 0.8},
        ]
        
        adjacency = _build_adjacency(edges)
        
        assert 'n1' in adjacency['n2']
        assert 'n2' in adjacency['n1']
        assert 'n3' in adjacency['n2']
        assert 'n2' in adjacency['n3']
    
    def test_expand_neighborhood_one_hop(self, sample_graph):
        """Test neighborhood expansion with 1 hop."""
        edges = sample_graph['edges']
        adjacency = _build_adjacency(edges)
        
        neighbors = _expand_neighborhood(['n1'], adjacency, max_hops=1, max_nodes=10)
        
        # n1's direct neighbors: n2, n5, n3
        assert 'n2' in neighbors
        assert 'n5' in neighbors
        assert 'n3' in neighbors
        assert 'n1' not in neighbors  # Seed excluded
    
    def test_expand_neighborhood_two_hops(self, sample_graph):
        """Test neighborhood expansion with 2 hops."""
        edges = sample_graph['edges']
        adjacency = _build_adjacency(edges)
        
        neighbors = _expand_neighborhood(['n1'], adjacency, max_hops=2, max_nodes=10)
        
        # Should reach n4 through n3
        assert 'n4' in neighbors
    
    def test_expand_neighborhood_max_nodes_limit(self, sample_graph):
        """Test max_nodes limit in neighborhood expansion."""
        edges = sample_graph['edges']
        adjacency = _build_adjacency(edges)
        
        neighbors = _expand_neighborhood(['n1'], adjacency, max_hops=2, max_nodes=2)
        
        # Should stop at 2 neighbors
        assert len(neighbors) <= 2
    
    def test_build_graph_overview(self, sample_graph):
        """Test graph overview building."""
        nodes = {node['id']: node for node in sample_graph['nodes']}
        edges = sample_graph['edges']
        
        overview = _build_graph_overview(nodes, edges)
        
        assert overview['total_nodes'] == 5
        assert overview['total_edges'] == 4
        assert 'claim' in overview['node_type_counts']
        assert 'support' in overview['relation_type_counts']
        assert len(overview['main_hubs']) > 0
    
    def test_retrieve_by_question_lexical_match(self, sample_graph):
        """Test question-based retrieval with lexical matching."""
        nodes = {node['id']: node for node in sample_graph['nodes']}
        question = "What is the main claim of the argument?"
        
        retrieved = _retrieve_by_question(question, nodes, max_nodes=3)
        
        # Should retrieve n1 which contains "main claim"
        assert 'n1' in retrieved
        assert len(retrieved) <= 3
    
    def test_retrieve_by_question_no_match(self, sample_graph):
        """Test retrieval with no matches."""
        nodes = {node['id']: node for node in sample_graph['nodes']}
        question = "xyzabc nonexistent query"
        
        retrieved = _retrieve_by_question(question, nodes, max_nodes=3)
        
        # Should return empty or very few results
        assert len(retrieved) == 0


@pytest.mark.unit
class TestBuildQaContext:
    """Test build_qa_context function."""
    
    def test_with_selected_nodes(self, sample_graph):
        """Test context building with selected nodes."""
        context = build_qa_context(
            graph=sample_graph,
            selected_node_ids=['n1', 'n2'],
            question="What is the relationship?",
            history=[]
        )
        
        # Should have selected nodes
        assert len(context.selected_nodes) == 2
        assert context.selected_nodes[0]['id'] in ['n1', 'n2']
        
        # Should have neighborhood nodes
        assert len(context.neighborhood_nodes) > 0
        
        # Should have graph overview
        assert context.graph_overview['total_nodes'] == 5
        
        # Should have edges
        assert len(context.edges) > 0
    
    def test_without_selected_nodes(self, sample_graph):
        """Test context building without selected nodes (fallback)."""
        context = build_qa_context(
            graph=sample_graph,
            selected_node_ids=[],
            question="main claim",
            history=[]
        )
        
        # Should use question-based retrieval
        assert len(context.selected_nodes) > 0
        assert len(context.neighborhood_nodes) == 0  # No neighborhood for question-based
    
    def test_with_history(self, sample_graph, sample_history):
        """Test context building with chat history."""
        context = build_qa_context(
            graph=sample_graph,
            selected_node_ids=['n1'],
            question="What about objections?",
            history=sample_history
        )
        
        # Should have history summary
        assert context.history_summary != ""
        assert "main claim" in context.history_summary.lower()
    
    def test_context_to_prompt_text(self, sample_graph):
        """Test converting context to prompt text."""
        context = build_qa_context(
            graph=sample_graph,
            selected_node_ids=['n1'],
            question="Test question",
            history=[]
        )
        
        prompt_text = context.to_prompt_text()
        
        # Should contain key sections
        assert "GRAPH OVERVIEW" in prompt_text
        assert "SELECTED NODES" in prompt_text
        assert "NEIGHBORHOOD NODES" in prompt_text
        assert "RELATIONS" in prompt_text


# ============================================================================
# History Management Tests
# ============================================================================

@pytest.mark.unit
class TestHistoryManagement:
    """Test chat history management."""
    
    def test_summarize_history_empty(self):
        """Test summarizing empty history."""
        summary = _summarize_history([])
        assert summary == ""
    
    def test_summarize_history_one_turn(self, sample_history):
        """Test summarizing single turn."""
        summary = _summarize_history([sample_history[0]])
        assert "What is the main claim?" in summary
    
    def test_summarize_history_multiple_turns(self, sample_history):
        """Test summarizing multiple turns."""
        summary = _summarize_history(sample_history, max_full_turns=2)
        
        # Should include both recent turns
        assert "What is the main claim?" in summary
        assert "What evidence supports it?" in summary
    
    def test_summarize_history_truncation(self, sample_history):
        """Test history truncation with many turns."""
        # Create many turns
        many_turns = sample_history + [
            ChatTurn(f"Question {i}", f"Answer {i}", [])
            for i in range(10)
        ]
        
        summary = _summarize_history(many_turns, max_full_turns=2)
        
        # Should mention earlier turns briefly
        assert "Earlier in conversation" in summary
    
    def test_add_to_history(self, sample_history):
        """Test adding turn to history."""
        response = QaResponse(
            answer="New answer",
            cited_node_ids=["n3"],
            confidence=0.9
        )
        
        new_history = add_to_history(
            history=sample_history.copy(),
            question="New question?",
            response=response,
            max_turns=6
        )
        
        assert len(new_history) == 3
        assert new_history[-1].question == "New question?"
        assert new_history[-1].answer == "New answer"
    
    def test_add_to_history_max_turns(self):
        """Test history trimming at max_turns."""
        history = []
        
        # Add 10 turns
        for i in range(10):
            response = QaResponse(
                answer=f"Answer {i}",
                confidence=0.8
            )
            history = add_to_history(
                history=history,
                question=f"Question {i}?",
                response=response,
                max_turns=6
            )
        
        # Should be trimmed to 6
        assert len(history) == 6
        assert history[0].question == "Question 4?"  # Oldest kept


# ============================================================================
# Prompt Building Tests
# ============================================================================

@pytest.mark.unit
class TestPromptBuilding:
    """Test prompt generation."""
    
    def test_system_prompt_contains_rules(self):
        """Test system prompt contains key grounding rules."""
        system_prompt = _build_system_prompt()
        
        # Check for key rules
        assert "grounding" in system_prompt.lower() or "based on" in system_prompt.lower()
        assert "citation" in system_prompt.lower() or "node" in system_prompt.lower()
        assert "confidence" in system_prompt.lower()
        assert "json" in system_prompt.lower()
        assert "selected nodes" in system_prompt.lower()
    
    def test_user_prompt_format(self, sample_graph):
        """Test user prompt formatting."""
        context = build_qa_context(
            graph=sample_graph,
            selected_node_ids=['n1'],
            question="Test question?",
            history=[]
        )
        
        user_prompt = _build_user_prompt(context)
        
        # Should contain context and question
        assert "GRAPH OVERVIEW" in user_prompt
        assert "Test question?" in user_prompt
        assert "QaResponse" in user_prompt


# ============================================================================
# Integration Tests
# ============================================================================

@pytest.mark.integration
class TestQaIntegration:
    """Integration tests for full Q&A flow (mocked LLM)."""
    
    def test_answer_question_with_mock(self, sample_graph):
        """Test answer_question with mocked LLM client."""
        # Mock LLM client
        mock_client = Mock()
        mock_response = QaResponse(
            answer="The main claim argues that...",
            cited_node_ids=["n1", "n2"],
            confidence=0.85,
            followups=["What supports this?", "Any objections?"]
        )
        mock_result = {
            'result': mock_response,
            'usage': {'input_tokens': 100, 'output_tokens': 50, 'estimated_cost_usd': 0.001},
            'cache_hit': False
        }
        mock_client.call_llm = Mock(return_value=mock_result)
        
        # Call answer_question
        response = answer_question(
            graph=sample_graph,
            selected_node_ids=['n1'],
            question="What is the main claim?",
            history=[],
            client=mock_client
        )
        
        # Verify response
        assert response.answer == "The main claim argues that..."
        assert "n1" in response.cited_node_ids
        assert response.confidence == 0.85
        
        # Verify LLM was called with correct args
        assert mock_client.call_llm.called
        call_kwargs = mock_client.call_llm.call_args[1]
        assert call_kwargs['schema'] == QaResponse
        assert call_kwargs['task_name'] == "qa_generation"
    
    def test_answer_question_error_handling(self, sample_graph):
        """Test error handling in answer_question."""
        # Mock client that raises exception
        mock_client = Mock()
        mock_client.call_llm = Mock(side_effect=Exception("LLM error"))
        
        # Should return fallback response
        response = answer_question(
            graph=sample_graph,
            selected_node_ids=['n1'],
            question="Test question?",
            history=[],
            client=mock_client
        )
        
        # Should have error message
        assert "error" in response.answer.lower()
        assert response.confidence == 0.0
        assert response.notes is not None


# ============================================================================
# Determinism Tests
# ============================================================================

@pytest.mark.unit
class TestDeterminism:
    """Test deterministic behavior."""
    
    def test_context_building_deterministic(self, sample_graph):
        """Test context building is deterministic."""
        context1 = build_qa_context(
            graph=sample_graph,
            selected_node_ids=['n1', 'n2'],
            question="Test?",
            history=[]
        )
        
        context2 = build_qa_context(
            graph=sample_graph,
            selected_node_ids=['n1', 'n2'],
            question="Test?",
            history=[]
        )
        
        # Should produce same results
        assert len(context1.selected_nodes) == len(context2.selected_nodes)
        assert len(context1.neighborhood_nodes) == len(context2.neighborhood_nodes)
        assert context1.graph_overview == context2.graph_overview
    
    def test_prompt_text_deterministic(self, sample_graph):
        """Test prompt text generation is deterministic."""
        context = build_qa_context(
            graph=sample_graph,
            selected_node_ids=['n1'],
            question="Test?",
            history=[]
        )
        
        text1 = context.to_prompt_text()
        text2 = context.to_prompt_text()
        
        assert text1 == text2
