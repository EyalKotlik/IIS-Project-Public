"""
Live Extraction API Tests
==========================

IMPORTANT: These tests make REAL API calls and consume REAL tokens.
They are SKIPPED by default to prevent accidental costs.

To enable:
  1. Set OPENAI_API_KEY environment variable
  2. Set RUN_LIVE_API_TESTS=1 environment variable

Usage:
    RUN_LIVE_API_TESTS=1 pytest -m live_api tests/live/test_extraction_live.py -s

Safety Controls:
  - Requires explicit opt-in via RUN_LIVE_API_TESTS=1
  - Requires OPENAI_API_KEY to be set
  - Forces model to gpt-4o-mini (cheapest option)
  - Sets temperature=0 (deterministic)
  - Uses tight token limits (small max_output_tokens)
  - Each test makes EXACTLY ONE API call
  - Minimal prompts and inputs

COST ESTIMATE: ~$0.0003 USD total (3 minimal calls with gpt-4o-mini)
"""

import os
import pytest
import sys
import tempfile
import shutil

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from app_mockup.backend.llm_config import LLMConfig
from app_mockup.backend.llm_client import LLMClient
from app_mockup.backend.preprocessing import preprocess_text, SentenceUnit
from app_mockup.backend.extraction import (
    classify_components,
    extract_relations,
    generate_paraphrases,
    ClassifiedComponent,
)


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
    - Uses small max_output_tokens (150)
    - Uses temporary cache dir
    """
    return LLMConfig(
        provider="openai",
        model="gpt-4o-mini",  # Force cheapest model
        temperature=0.0,  # Deterministic
        timeout_sec=30,
        max_output_tokens=150,  # Small token limit for safety
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
class TestExtractionLiveAPI:
    """
    Live API tests for extraction modules.
    
    COST ESTIMATE: ~$0.0003 USD total (3 minimal calls with gpt-4o-mini)
    """
    
    def test_live_component_classification_minimal(self, live_config):
        """
        Test 1: Component classification with minimal input.
        
        Makes 1 real API call with:
        - 1-2 short sentences (~30 tokens)
        - BatchComponentClassification schema
        - gpt-4o-mini
        - temperature=0
        
        Asserts:
        - Schema-valid output
        - Labels in allowed set
        - Confidence in [0, 1]
        """
        client = LLMClient(live_config)
        
        # Minimal test text (2 short sentences)
        text = "Capital punishment is wrong. This is because it violates human rights."
        
        # Preprocess
        doc = preprocess_text(text)
        
        # Classify (should make exactly 1 API call)
        print("\n🔵 Making classification API call...")
        classifications = classify_components(
            doc,
            client=client,
            candidates_only=True
        )
        
        # Assertions
        assert len(classifications) > 0, "Should classify at least one component"
        
        for comp in classifications:
            # Verify schema fields
            assert comp.sentence_id is not None, "sentence_id must be set"
            assert comp.text, "text must be non-empty"
            assert comp.label in ["claim", "premise", "objection", "reply", "non_argument"], \
                f"Label '{comp.label}' must be in allowed set"
            assert 0.0 <= comp.confidence <= 1.0, \
                f"Confidence {comp.confidence} must be in [0, 1]"
        
        # Get client stats
        stats = client.get_stats()
        
        print(f"\n✓ Classification test passed:")
        print(f"  - Components classified: {len(classifications)}")
        print(f"  - Labels: {[c.label for c in classifications]}")
        print(f"  - Confidences: {[f'{c.confidence:.2f}' for c in classifications]}")
        print(f"  - Total cost: ${stats['budget']['total_spend_usd']:.6f}")
        print(f"  - Total tokens: {stats['budget']['total_tokens']}")
        
        # Verify cost is reasonable
        assert stats['budget']['total_spend_usd'] < 0.01, "Cost should be < $0.01"
    
    def test_live_relation_extraction_minimal(self, live_config):
        """
        Test 2: Relation extraction with minimal input.
        
        Makes 1 real API call with:
        - 2 components that clearly relate (~40 tokens)
        - BatchRelationExtraction schema
        - gpt-4o-mini
        - temperature=0
        
        Asserts:
        - Schema-valid output
        - Relation types are support/attack
        - Confidence in [0, 1]
        """
        client = LLMClient(live_config)
        
        # Create simple classifications that should obviously relate
        classifications = [
            ClassifiedComponent(
                sentence_id="s1",
                text="Exercise is good for health.",
                label="claim",
                confidence=0.9
            ),
            ClassifiedComponent(
                sentence_id="s2",
                text="Studies show exercise reduces heart disease.",
                label="premise",
                confidence=0.9
            ),
        ]
        
        # Extract relations (should make exactly 1 API call)
        print("\n🔵 Making relation extraction API call...")
        relations = extract_relations(
            classifications,
            client=client,
            window_size=2
        )
        
        # Assertions
        # Note: LLM might not find relations, that's okay for this minimal test
        # We just verify that if relations are returned, they're valid
        for rel in relations:
            assert rel.source_id in ["s1", "s2"], "source_id must be valid"
            assert rel.target_id in ["s1", "s2"], "target_id must be valid"
            assert rel.relation_type in ["support", "attack"], \
                f"Relation type '{rel.relation_type}' must be support or attack"
            assert 0.0 <= rel.confidence <= 1.0, \
                f"Confidence {rel.confidence} must be in [0, 1]"
        
        # Get client stats
        stats = client.get_stats()
        
        print(f"\n✓ Relation extraction test passed:")
        print(f"  - Relations found: {len(relations)}")
        if relations:
            for rel in relations:
                print(f"    {rel.source_id} --[{rel.relation_type}]--> {rel.target_id} (conf: {rel.confidence:.2f})")
        print(f"  - Total cost: ${stats['budget']['total_spend_usd']:.6f}")
        print(f"  - Total tokens: {stats['budget']['total_tokens']}")
        
        # Verify cost is reasonable
        assert stats['budget']['total_spend_usd'] < 0.01, "Cost should be < $0.01"
    
    def test_live_paraphrase_generation_minimal(self, live_config):
        """
        Test 3: Paraphrase generation with minimal input.
        
        Makes 1 real API call with:
        - 1 short component (~20 tokens)
        - BatchParaphrase schema
        - gpt-4o-mini
        - temperature=0
        
        Asserts:
        - Paraphrase is non-empty
        - Within length limit (≤120 chars)
        - Not identical to original (if possible, but allow fallback)
        """
        client = LLMClient(live_config)
        
        # Create simple classification
        classifications = [
            ClassifiedComponent(
                sentence_id="s1",
                text="Regular exercise improves cardiovascular health significantly.",
                label="premise",
                confidence=0.9
            ),
        ]
        
        # Generate paraphrases (should make exactly 1 API call)
        print("\n🔵 Making paraphrase generation API call...")
        paraphrases = generate_paraphrases(
            classifications,
            client=client,
            use_fallback_on_error=True
        )
        
        # Assertions
        assert len(paraphrases) == 1, "Should generate one paraphrase"
        
        para = paraphrases[0]
        assert para.sentence_id == "s1", "sentence_id must match"
        assert para.paraphrase, "Paraphrase must be non-empty"
        assert len(para.paraphrase) <= 120, \
            f"Paraphrase length {len(para.paraphrase)} must be ≤ 120 chars"
        
        # Get client stats
        stats = client.get_stats()
        
        print(f"\n✓ Paraphrase generation test passed:")
        print(f"  - Original: \"{para.original_text}\"")
        print(f"  - Paraphrase: \"{para.paraphrase}\"")
        print(f"  - Length: {len(para.paraphrase)} chars")
        print(f"  - Is fallback: {para.is_fallback}")
        if para.quality_flags:
            print(f"  - Quality flags: {para.quality_flags}")
        print(f"  - Total cost: ${stats['budget']['total_spend_usd']:.6f}")
        print(f"  - Total tokens: {stats['budget']['total_tokens']}")
        
        # Verify cost is reasonable
        assert stats['budget']['total_spend_usd'] < 0.01, "Cost should be < $0.01"


# ============================================================================
# Summary Test (informational only, not a real test)
# ============================================================================

@pytest.mark.live_api
@pytest.mark.skipif(skip_live, reason=skip_reason or "Live API tests disabled")
def test_live_extraction_summary(live_config):
    """
    Informational test that summarizes the live test configuration.
    
    This doesn't make any API calls, just validates the config.
    """
    SEPARATOR_WIDTH = 70
    separator = "=" * SEPARATOR_WIDTH
    
    print(f"\n{separator}")
    print("LIVE EXTRACTION API TEST CONFIGURATION")
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
    print("TESTS:")
    print("  1. Component classification (1-2 sentences)")
    print("  2. Relation extraction (2 components)")
    print("  3. Paraphrase generation (1 component)")
    print(separator)
    print("ESTIMATED COST: ~$0.0003 USD for 3 minimal API calls")
    print(separator)
    
    # Verify config is valid
    assert live_config.model == "gpt-4o-mini", "Must use gpt-4o-mini for safety"
    assert live_config.temperature == 0.0, "Must use temperature=0 for determinism"
    assert live_config.api_key is not None, "API key must be set"


if __name__ == "__main__":
    print("\n" + "="*70)
    print("LIVE EXTRACTION API TESTS")
    print("="*70)
    print("\nWARNING: These tests make REAL API calls and cost REAL money.")
    print("To run: RUN_LIVE_API_TESTS=1 pytest -m live_api tests/live/test_extraction_live.py -s")
    print("="*70 + "\n")
