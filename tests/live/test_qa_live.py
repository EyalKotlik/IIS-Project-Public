"""
Live Q&A API Integration Tests
================================

IMPORTANT: These tests make REAL API calls and consume REAL tokens.
They are SKIPPED by default to prevent accidental costs.

To enable:
  1. Set OPENAI_API_KEY environment variable
  2. Set RUN_LIVE_API_TESTS=1 environment variable

Usage:
    RUN_LIVE_API_TESTS=1 pytest tests/live/test_qa_live.py -m live_api -s

Safety Controls:
  - Requires explicit opt-in via RUN_LIVE_API_TESTS=1
  - Requires OPENAI_API_KEY to be set
  - Forces model to gpt-4o-mini (cheapest option)
  - Sets temperature=0 (deterministic)
  - Uses tight token limits
  - Limited to 1 API call total (minimal cost)
"""

import os
import pytest
import sys
import tempfile
import shutil

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from app_mockup.backend.llm_config import LLMConfig
from app_mockup.backend.llm_client import LLMClient
from app_mockup.backend.qa_module import answer_question, QaResponse


# ============================================================================
# Skip Conditions
# ============================================================================

def should_skip_live_tests():
    """Determine if live tests should be skipped."""
    # Must have API key
    if not os.getenv("OPENAI_API_KEY"):
        return True, "OPENAI_API_KEY not set"
    
    # Must explicitly opt-in
    if os.getenv("RUN_LIVE_API_TESTS") != "1":
        return True, "RUN_LIVE_API_TESTS not set to 1 (set to opt-in)"
    
    return False, None


skip_live, skip_reason = should_skip_live_tests()


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def temp_cache_dir():
    """Create a temporary cache directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def live_config(temp_cache_dir):
    """
    Create a live configuration for OpenAI API calls.
    
    Safety controls:
    - Forces gpt-4o-mini (cheapest model)
    - Sets temperature=0 (deterministic)
    - Uses small max_output_tokens (500)
    - Uses temporary cache dir
    """
    return LLMConfig(
        provider="openai",
        model="gpt-4o-mini",
        temperature=0.0,
        max_output_tokens=500,
        budget_usd=1.0,
        budget_stop_at_usd=0.9,
        cache_enabled=True,
        cache_dir=temp_cache_dir,
        api_key=os.getenv("OPENAI_API_KEY")
    )


@pytest.fixture
def tiny_graph():
    """Create a tiny graph for testing."""
    return {
        'nodes': [
            {
                'id': 'n1',
                'type': 'claim',
                'label': 'Climate action needed',
                'span': 'We must take immediate action on climate change.',
                'paraphrase': 'Urgent climate response is required',
                'confidence': 0.95
            },
            {
                'id': 'n2',
                'type': 'premise',
                'label': 'Temperature rising',
                'span': 'Global temperatures have risen 1.2°C since pre-industrial times.',
                'paraphrase': 'Temperature increase of 1.2 degrees',
                'confidence': 0.92
            },
            {
                'id': 'n3',
                'type': 'premise',
                'label': 'Extreme weather',
                'span': 'Extreme weather events are becoming more frequent.',
                'paraphrase': 'More frequent extreme weather',
                'confidence': 0.90
            }
        ],
        'edges': [
            {'source': 'n2', 'target': 'n1', 'relation': 'support', 'confidence': 0.9},
            {'source': 'n3', 'target': 'n1', 'relation': 'support', 'confidence': 0.88}
        ],
        'meta': {}
    }


# ============================================================================
# Live API Tests
# ============================================================================

@pytest.mark.live_api
@pytest.mark.skipif(skip_live, reason=skip_reason)
class TestQaLiveAPI:
    """Live API tests for Q&A module."""
    
    def test_answer_question_live(self, live_config, tiny_graph):
        """
        Test Q&A with real OpenAI API call.
        
        This makes ONE real API call to validate end-to-end Q&A behavior.
        """
        print("\n" + "="*60)
        print("LIVE API TEST: Q&A Module")
        print("="*60)
        print(f"Model: {live_config.model}")
        print(f"Temperature: {live_config.temperature}")
        print(f"Max output tokens: {live_config.max_output_tokens}")
        print()
        
        # Create client
        client = LLMClient(config=live_config)
        
        # Ask a question with selected nodes
        question = "What is the main claim and what evidence supports it?"
        selected_nodes = ['n1']  # Select the claim node
        
        print(f"Question: {question}")
        print(f"Selected nodes: {selected_nodes}")
        print()
        
        # Call answer_question
        response = answer_question(
            graph=tiny_graph,
            selected_node_ids=selected_nodes,
            question=question,
            history=[],
            client=client
        )
        
        # Print response
        print("Response:")
        print(f"  Answer: {response.answer}")
        print(f"  Cited nodes: {response.cited_node_ids}")
        print(f"  Confidence: {response.confidence}")
        print(f"  Follow-ups: {response.followups}")
        print(f"  Notes: {response.notes}")
        print()
        
        # Assertions
        assert isinstance(response, QaResponse)
        assert len(response.answer) > 10, "Answer should be substantial"
        assert len(response.cited_node_ids) > 0, "Should cite at least one node"
        assert 0.0 <= response.confidence <= 1.0, "Confidence should be in [0, 1]"
        
        # Verify cited nodes exist in graph
        node_ids = {node['id'] for node in tiny_graph['nodes']}
        for cited_id in response.cited_node_ids:
            assert cited_id in node_ids, f"Cited node {cited_id} should exist in graph"
        
        # Since we selected n1 (claim), it should likely be cited
        # This is a soft check - not guaranteed but very likely
        if 'n1' in response.cited_node_ids:
            print("✓ Selected node n1 was cited in response")
        
        # Check budget tracking
        total_spend = client.budget_tracker.get_total_spend()
        print(f"\nTotal spend: ${total_spend:.4f}")
        assert total_spend > 0, "Should have recorded some cost"
        assert total_spend < 0.1, "Should be very cheap (gpt-4o-mini)"
        
        print("\n" + "="*60)
        print("LIVE TEST PASSED ✓")
        print("="*60)
