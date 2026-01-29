"""
Live Synthetic Claims Integration Tests
========================================

IMPORTANT: These tests make REAL API calls and consume REAL tokens.
They are SKIPPED by default to prevent accidental costs.

To enable:
  1. Set OPENAI_API_KEY environment variable
  2. Set RUN_LIVE_API_TESTS=1 environment variable

Usage:
    RUN_LIVE_API_TESTS=1 pytest tests/live/test_synthetic_claims_live.py -m live_api -s

Safety Controls:
  - Requires explicit opt-in via RUN_LIVE_API_TESTS=1
  - Requires OPENAI_API_KEY to be set
  - Forces model to gpt-4o-mini (cheapest option)
  - Sets temperature=0 (deterministic)
  - Uses tight token limits
  - Limited to 1 API call total (minimal cost ~$0.0001)
"""

import os
import pytest
import sys
import tempfile
import shutil
import re

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from app_mockup.backend.llm_config import LLMConfig
from app_mockup.backend.llm_client import LLMClient
from app_mockup.backend.graph_construction import GraphNode, GraphEdge
from app_mockup.backend.extraction.premise_clustering import (
    PremiseCluster,
    ClusteringConfig,
    find_premise_clusters
)
from app_mockup.backend.extraction.synthetic_claims import (
    SynthesisConfig,
    synthesize_claims_for_clusters,
    add_synthetic_claims_to_graph
)


# ============================================================================
# Skip Conditions
# ============================================================================

def should_skip_live_tests():
    """Determine if live tests should be skipped."""
    if not os.getenv("OPENAI_API_KEY"):
        return True, "OPENAI_API_KEY not set"
    
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
    Create a live configuration for OpenAI API calls with safety controls.
    """
    return LLMConfig(
        model="gpt-4o-mini",  # Force most cost-effective model
        temperature=0.0,      # Deterministic
        max_tokens=300,       # Small limit for synthesis
        cache_dir=temp_cache_dir,
        cache_enabled=True,
        budget_usd=1.0,       # Safety budget cap
        timeout_sec=30
    )


@pytest.fixture
def live_client(live_config):
    """Create a live LLM client with safety controls."""
    return LLMClient(live_config)


@pytest.fixture
def demographic_disparity_premises():
    """
    Sample premise nodes about demographic disparities in facial recognition.
    
    These are designed to cluster naturally and produce a coherent synthetic claim.
    """
    return [
        GraphNode(
            id="n_premise1",
            type="premise",
            label="Higher error rates for women",
            span="Facial recognition systems have significantly higher error rates for women and people with darker skin tones.",
            paraphrase="Higher error rates for women and darker-skinned individuals.",
            confidence=0.92,
            sentence_id="s1"
        ),
        GraphNode(
            id="n_premise2",
            type="premise",
            label="False positives affect minorities",
            span="False positive alerts disproportionately affect minority communities already subject to heightened scrutiny.",
            paraphrase="False positives target minority communities.",
            confidence=0.88,
            sentence_id="s2"
        ),
        GraphNode(
            id="n_premise3",
            type="premise",
            label="Bias amplification through automation",
            span="Automated systems can amplify existing biases in law enforcement practices.",
            paraphrase="Automation amplifies enforcement biases.",
            confidence=0.85,
            sentence_id="s3"
        ),
        GraphNode(
            id="n_claim1",
            type="claim",
            label="Ban facial recognition in policing",
            span="We should ban facial recognition technology in law enforcement.",
            paraphrase="Ban facial recognition in policing.",
            confidence=0.90,
            sentence_id="s10"
        ),
    ]


@pytest.fixture
def demographic_disparity_edges():
    """Support edges for demographic disparity premises."""
    return [
        GraphEdge(source="n_premise1", target="n_claim1", relation="support", confidence=0.85),
        GraphEdge(source="n_premise2", target="n_claim1", relation="support", confidence=0.83),
        GraphEdge(source="n_premise3", target="n_claim1", relation="support", confidence=0.80),
    ]


# ============================================================================
# Live Tests
# ============================================================================

@pytest.mark.live_api
@pytest.mark.skipif(skip_live, reason=skip_reason)
def test_live_synthesis_demographic_disparity(
    live_client,
    demographic_disparity_premises,
    demographic_disparity_edges
):
    """
    Test live synthesis of a synthetic claim from demographic disparity premises.
    
    Expected behavior:
    - Finds one cluster of 3 related premises
    - Generates a coherent synthetic claim about discriminatory outcomes
    - Does not hallucinate specific numbers or names
    - Creates proper 2-hop reasoning chain
    
    Cost estimate: ~$0.0001 USD for one synthesis call
    """
    print("\n" + "=" * 70)
    print("LIVE TEST: Synthetic Claim Generation")
    print("=" * 70)
    
    # Step 1: Find clusters
    print("\n1. Finding premise clusters...")
    config = ClusteringConfig(
        min_cluster_size=2,
        max_cluster_size=10,
        require_same_target=True
    )
    
    clusters = find_premise_clusters(
        demographic_disparity_premises,
        demographic_disparity_edges,
        config
    )
    
    print(f"   Found {len(clusters)} cluster(s)")
    assert len(clusters) >= 1, "Should find at least one cluster"
    
    cluster = clusters[0]
    print(f"   Cluster 0: {len(cluster.premise_ids)} premises")
    print(f"   Target: {cluster.target_claim_text}")
    
    # Step 2: Synthesize claims
    print("\n2. Synthesizing claims with LLM (gpt-4o-mini)...")
    synthesis_config = SynthesisConfig(
        min_coherence_threshold=0.3,
        min_confidence_threshold=0.5,
        model_name="gpt-4o-mini"  # Explicit safety control
    )
    
    synthetic_claims, cost = synthesize_claims_for_clusters(
        clusters,
        client=live_client,
        config=synthesis_config
    )
    
    print(f"   Generated {len(synthetic_claims)} synthetic claim(s)")
    print(f"   Cost: ${cost:.6f}")
    
    # Assertions
    assert len(synthetic_claims) >= 1, "Should generate at least one synthetic claim"
    assert cost > 0, "Cost should be non-zero for real API call"
    
    synthetic_claim = synthetic_claims[0]
    print(f"\n3. Analyzing synthetic claim:")
    print(f"   Cluster ID: {synthetic_claim.cluster_id}")
    print(f"   Text: {synthetic_claim.synthetic_claim_text}")
    print(f"   Label: {synthetic_claim.label}")
    print(f"   Confidence: {synthetic_claim.confidence:.2f}")
    print(f"   Coherent: {synthetic_claim.coherent}")
    
    # Validation checks
    assert synthetic_claim.coherent is True, "Cluster should be coherent"
    assert synthetic_claim.confidence >= 0.5, "Confidence should meet threshold"
    assert len(synthetic_claim.synthetic_claim_text) > 0, "Should have text"
    assert len(synthetic_claim.synthetic_claim_text) <= 150, "Should respect length limit"
    
    # Check for hallucination: no new numbers
    premise_text = " ".join([p.span for p in demographic_disparity_premises if p.type == "premise"])
    premise_numbers = set(re.findall(r'\d+', premise_text))
    claim_numbers = set(re.findall(r'\d+', synthetic_claim.synthetic_claim_text))
    new_numbers = claim_numbers - premise_numbers
    
    print(f"\n4. Hallucination check:")
    print(f"   Numbers in premises: {premise_numbers if premise_numbers else 'none'}")
    print(f"   Numbers in synthetic claim: {claim_numbers if claim_numbers else 'none'}")
    print(f"   New numbers (hallucinated): {new_numbers if new_numbers else 'none'}")
    
    assert len(new_numbers) == 0, f"Should not hallucinate new numbers: {new_numbers}"
    
    # Step 3: Test end-to-end with rewiring
    print("\n5. Testing end-to-end graph rewiring...")
    full_config = SynthesisConfig(
        enable_rewiring=True,
        preserve_original_edges=False,
        model_name="gpt-4o-mini"
    )
    
    updated_nodes, updated_edges, stats = add_synthetic_claims_to_graph(
        demographic_disparity_premises,
        demographic_disparity_edges,
        client=live_client,
        config=full_config
    )
    
    print(f"   Nodes: {len(demographic_disparity_premises)} → {len(updated_nodes)}")
    print(f"   Edges: {len(demographic_disparity_edges)} → {len(updated_edges)}")
    print(f"   Synthetic claims added: {stats['synthetic_nodes_added']}")
    
    # Check rewiring
    assert len(updated_nodes) > len(demographic_disparity_premises), "Should add synthetic nodes"
    assert stats['synthetic_nodes_added'] >= 1, "Should add at least one synthetic claim"
    
    # Find the synthetic node
    synthetic_nodes = [n for n in updated_nodes if n.is_synthetic]
    assert len(synthetic_nodes) >= 1, "Should have synthetic nodes"
    
    syn_node = synthetic_nodes[0]
    print(f"\n6. Synthetic node properties:")
    print(f"   ID: {syn_node.id}")
    print(f"   Type: {syn_node.type}")
    print(f"   Is synthetic: {syn_node.is_synthetic}")
    print(f"   Source premise IDs: {syn_node.source_premise_ids}")
    print(f"   Synthesis method: {syn_node.synthesis_method}")
    print(f"   Text: {syn_node.span}")
    
    assert syn_node.type == "claim", "Synthetic node should be a claim"
    assert syn_node.is_synthetic is True, "Should be marked as synthetic"
    assert len(syn_node.source_premise_ids) >= 2, "Should reference multiple premises"
    assert syn_node.synthesis_method == "llm", "Should indicate LLM synthesis"
    
    # Check 2-hop chain exists
    syn_id = syn_node.id
    edges_to_synthetic = [e for e in updated_edges if e.target == syn_id]
    edges_from_synthetic = [e for e in updated_edges if e.source == syn_id]
    
    print(f"\n7. Edge rewiring verification:")
    print(f"   Edges to synthetic: {len(edges_to_synthetic)}")
    print(f"   Edges from synthetic: {len(edges_from_synthetic)}")
    
    assert len(edges_to_synthetic) >= 2, "Premises should support synthetic claim"
    assert len(edges_from_synthetic) >= 1, "Synthetic should support higher claim"
    
    print("\n" + "=" * 70)
    print("✅ LIVE TEST PASSED: Synthetic claim generation working correctly")
    print("=" * 70)


def test_live_api_summary():
    """
    Summary test to document live API test coverage.
    
    This is not a live test itself, but documents what is tested.
    """
    if skip_live:
        pytest.skip(f"Live tests skipped: {skip_reason}")
    
    print("\n" + "=" * 70)
    print("LIVE API TEST SUMMARY: Synthetic Claims")
    print("=" * 70)
    print("\nTests included:")
    print("  ✓ test_live_synthesis_demographic_disparity")
    print("    - End-to-end synthesis with real LLM (gpt-4o-mini)")
    print("    - Clustering, synthesis, and graph rewiring")
    print("    - Hallucination detection")
    print("    - 2-hop reasoning chain validation")
    print("\nTotal API calls: 1")
    print("Estimated cost: ~$0.0001 USD (with gpt-4o-mini)")
    print("\nSafety controls:")
    print("  ✓ Requires explicit opt-in (RUN_LIVE_API_TESTS=1)")
    print("  ✓ Forces gpt-4o-mini model")
    print("  ✓ Temperature = 0 (deterministic)")
    print("  ✓ Token limits enforced")
    print("  ✓ Budget cap: $1.00")
    print("=" * 70)
