"""
Live OpenAI API Integration Tests
==================================

IMPORTANT: These tests make REAL API calls and consume REAL tokens.
They are SKIPPED by default to prevent accidental costs.

To enable:
  1. Set OPENAI_API_KEY environment variable
  2. Set RUN_LIVE_API_TESTS=1 environment variable

Usage:
    RUN_LIVE_API_TESTS=1 pytest -m live_api -s

Safety Controls:
  - Requires explicit opt-in via RUN_LIVE_API_TESTS=1
  - Requires OPENAI_API_KEY to be set
  - Forces model to gpt-4o-mini (cheapest option)
  - Sets temperature=0 (deterministic)
  - Uses tight token limits (small max_output_tokens)
  - Limited to 2 API calls total (minimal cost)
"""

import os
import pytest
import sys
import tempfile
import shutil

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from app_mockup.backend.llm_config import LLMConfig
from app_mockup.backend.llm_client import LLMClient
from app_mockup.backend.llm_schemas import ComponentClassificationResult


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
    - Uses small max_output_tokens (200)
    - Uses temporary cache dir
    """
    return LLMConfig(
        provider="openai",
        model="gpt-4o-mini",  # Force cheapest model
        temperature=0.0,  # Deterministic
        timeout_sec=30,
        max_output_tokens=200,  # Small token limit for safety
        budget_usd=10.0,
        budget_stop_at_usd=9.0,
        cache_enabled=True,
        cache_dir=temp_cache_dir,
        api_key=os.getenv("OPENAI_API_KEY")
    )


# ============================================================================
# Live API Tests (minimal, budget-safe)
# ============================================================================

@pytest.mark.live_api
@pytest.mark.skipif(skip_live, reason=skip_reason or "Live API tests disabled")
class TestOpenAILiveAPI:
    """
    Live API tests that make real OpenAI calls.
    
    COST ESTIMATE: ~$0.0001 USD total (2 minimal calls with gpt-4o-mini)
    """
    
    def test_llm_client_smoke_test(self, live_config):
        """
        Test A: LLM client smoke test with minimal prompt.
        
        Makes 1 real API call with:
        - Tiny prompt (~20 tokens)
        - Tiny JSON schema (simple dict)
        - gpt-4o-mini
        - temperature=0
        
        Asserts:
        - No exceptions
        - Returns valid response
        - Returns usage info (tokens, cost)
        - Cost is tracked
        """
        client = LLMClient(live_config)
        
        # Minimal prompts
        system_prompt = "You are a helpful assistant. Reply in JSON."
        user_prompt = "Say 'hello'"
        
        # Make the call (no schema, just text response)
        result = client.call_llm(
            task_name="smoke_test",
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            schema=None  # No schema for this test
        )
        
        # Assertions
        assert result is not None, "Result should not be None"
        assert "result" in result, "Result should contain 'result' key"
        assert "usage" in result, "Result should contain 'usage' key"
        assert "cache_hit" in result, "Result should contain 'cache_hit' key"
        
        # Check usage info
        usage = result["usage"]
        assert "input_tokens" in usage, "Usage should contain input_tokens"
        assert "output_tokens" in usage, "Usage should contain output_tokens"
        assert "estimated_cost_usd" in usage, "Usage should contain estimated_cost_usd"
        
        # Verify tokens were used
        assert usage["input_tokens"] > 0, "Should have consumed input tokens"
        assert usage["output_tokens"] > 0, "Should have generated output tokens"
        
        # Verify cost is tracked (and reasonable for gpt-4o-mini)
        assert usage["estimated_cost_usd"] > 0, "Should have non-zero cost"
        assert usage["estimated_cost_usd"] < 0.01, "Cost should be < $0.01 for this tiny call"
        
        # Verify not a cache hit (first call)
        assert result["cache_hit"] is False, "First call should not be cache hit"
        
        # Verify result is a string
        assert isinstance(result["result"], str), "Result should be a string"
        assert len(result["result"]) > 0, "Result should not be empty"
        
        print(f"\n✓ Smoke test passed:")
        print(f"  - Input tokens: {usage['input_tokens']}")
        print(f"  - Output tokens: {usage['output_tokens']}")
        print(f"  - Cost: ${usage['estimated_cost_usd']:.6f}")
        print(f"  - Response: {result['result'][:100]}")
    
    def test_structured_output_end_to_end(self, live_config):
        """
        Test B: Structured output with ComponentClassificationResult schema.
        
        Makes 1 real API call with:
        - Short sentence (~15 tokens)
        - ComponentClassificationResult schema
        - gpt-4o-mini
        - temperature=0
        
        Asserts:
        - Parses to valid Pydantic model
        - Label is in allowed set
        - Confidence is in [0, 1]
        - Returns usage info
        """
        client = LLMClient(live_config)
        
        # Minimal classification task
        system_prompt = """You are an expert in argumentative analysis.
Classify the given text as one of: claim, premise, objection, reply, other."""
        
        user_prompt = "Studies show that exercise improves health."
        
        # Make the call with structured output
        result = client.call_llm(
            task_name="classify_test",
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            schema=ComponentClassificationResult
        )
        
        # Assertions
        assert result is not None, "Result should not be None"
        assert "result" in result, "Result should contain 'result' key"
        
        # Check that result is a Pydantic model instance
        classification = result["result"]
        assert isinstance(classification, ComponentClassificationResult), \
            "Result should be ComponentClassificationResult instance"
        
        # Validate schema fields
        assert classification.label in ["claim", "premise", "objection", "reply", "other"], \
            f"Label '{classification.label}' must be in allowed set"
        
        assert 0.0 <= classification.confidence <= 1.0, \
            f"Confidence {classification.confidence} must be in [0, 1]"
        
        # Check usage info
        usage = result["usage"]
        assert usage["input_tokens"] > 0, "Should have consumed input tokens"
        assert usage["output_tokens"] > 0, "Should have generated output tokens"
        assert usage["estimated_cost_usd"] > 0, "Should have non-zero cost"
        assert usage["estimated_cost_usd"] < 0.01, "Cost should be < $0.01 for this call"
        
        print(f"\n✓ Structured output test passed:")
        print(f"  - Label: {classification.label}")
        print(f"  - Confidence: {classification.confidence:.2f}")
        print(f"  - Rationale: {classification.rationale_short}")
        print(f"  - Input tokens: {usage['input_tokens']}")
        print(f"  - Output tokens: {usage['output_tokens']}")
        print(f"  - Cost: ${usage['estimated_cost_usd']:.6f}")


# ============================================================================
# Summary Test (informational only, not a real test)
# ============================================================================

@pytest.mark.live_api
@pytest.mark.skipif(skip_live, reason=skip_reason or "Live API tests disabled")
def test_live_api_summary(live_config):
    """
    Informational test that summarizes the live test configuration.
    
    This doesn't make any API calls, just validates the config.
    """
    SEPARATOR_WIDTH = 70
    separator = "=" * SEPARATOR_WIDTH
    
    print(f"\n{separator}")
    print("LIVE API TEST CONFIGURATION")
    print(separator)
    print(f"Model: {live_config.model}")
    print(f"Temperature: {live_config.temperature}")
    print(f"Max output tokens: {live_config.max_output_tokens}")
    print(f"Timeout: {live_config.timeout_sec}s")
    print(f"Cache enabled: {live_config.cache_enabled}")
    print(f"Budget: ${live_config.budget_usd}")
    print(f"Stop at: ${live_config.budget_stop_at_usd}")
    print(f"API key: {live_config.get_redacted_key()}")
    print(separator)
    print("ESTIMATED COST: ~$0.0001 USD for 2 minimal API calls")
    print(separator)
    
    # Just verify config is valid
    assert live_config.model == "gpt-4o-mini", "Must use gpt-4o-mini for safety"
    assert live_config.temperature == 0.0, "Must use temperature=0 for determinism"
    assert live_config.api_key is not None, "API key must be set"
