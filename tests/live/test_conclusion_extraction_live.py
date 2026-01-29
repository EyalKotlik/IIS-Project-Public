"""
Live Test for Conclusion Extraction
====================================

Tests that the enhanced llm_extractor properly extracts conclusion nodes
and enforces constraints using real OpenAI API calls.

These tests are SKIPPED by default and require explicit opt-in:
    RUN_LIVE_API_TESTS=1 pytest -m live_api -s

IMPORTANT: These tests make real API calls and consume credits!
"""

import pytest
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'app_mockup'))

from llm_extractor import extract_arguments_real


# Skip unless explicitly enabled
pytestmark = pytest.mark.skipif(
    os.environ.get("RUN_LIVE_API_TESTS") != "1",
    reason="Live API tests require RUN_LIVE_API_TESTS=1"
)


@pytest.mark.live_api
def test_extract_conclusion_node_live():
    """
    Live test: Extract a graph with an explicit conclusion node.
    
    Uses a small text with clear conclusion markers to minimize cost.
    """
    # Text with explicit conclusion marker
    text = """
    Electric vehicles reduce pollution. They produce zero direct emissions.
    Studies show they are better for air quality. Therefore, we should adopt electric cars.
    """
    
    # Check API key is available
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        pytest.skip("OPENAI_API_KEY not set")
    
    print(f"\n{'='*60}")
    print("LIVE TEST: Conclusion Extraction")
    print(f"{'='*60}\n")
    print(f"Input text:\n{text}\n")
    
    # Run extraction
    result = extract_arguments_real(text)
    
    # Verify result structure
    assert result is not None, "Extraction failed"
    assert "nodes" in result
    assert "edges" in result
    assert "meta" in result
    
    print(f"\n{'='*60}")
    print("EXTRACTION RESULTS")
    print(f"{'='*60}\n")
    
    # Print nodes
    print(f"Nodes ({len(result['nodes'])}):")
    for node in result["nodes"]:
        print(f"  - {node['id']} ({node['type']}): {node['label']}")
        print(f"    Span: {node['span'][:60]}...")
        print(f"    Confidence: {node['confidence']}")
    
    print(f"\nEdges ({len(result['edges'])}):")
    for edge in result["edges"]:
        print(f"  - {edge['source']} --{edge['relation']}--> {edge['target']} (conf: {edge['confidence']})")
    
    print(f"\nMetadata:")
    print(f"  - Model: {result['meta']['model_version']}")
    print(f"  - Components: {result['meta'].get('connected_components', 'N/A')}")
    
    # ====================================================================
    # ASSERTIONS
    # ====================================================================
    
    # 1. Should have at least one conclusion node
    conclusion_nodes = [n for n in result["nodes"] if n["type"] == "conclusion"]
    assert len(conclusion_nodes) >= 1, "No conclusion node found"
    
    print(f"\n✓ Found {len(conclusion_nodes)} conclusion node(s)")
    
    # 2. Check conclusion constraint: no conclusion -> non-conclusion edges
    conclusion_ids = {n["id"] for n in conclusion_nodes}
    non_conclusion_ids = {n["id"] for n in result["nodes"] if n["type"] != "conclusion"}
    
    invalid_edges = []
    for edge in result["edges"]:
        if edge["source"] in conclusion_ids and edge["target"] in non_conclusion_ids:
            invalid_edges.append(edge)
    
    assert len(invalid_edges) == 0, f"Found {len(invalid_edges)} invalid conclusion edges: {invalid_edges}"
    
    print(f"✓ Conclusion constraint satisfied (no conclusion -> non-conclusion edges)")
    
    # 3. Check connectivity (prefer 1-2 components)
    components = result["meta"].get("connected_components", 999)
    assert components <= 2, f"Too many disconnected components: {components}"
    
    print(f"✓ Good connectivity: {components} component(s)")
    
    # 4. Check model version is correct
    assert result["meta"]["model_version"] == "gpt-4o-mini", "Wrong model version in metadata"
    
    print(f"✓ Correct model version: {result['meta']['model_version']}")
    
    print(f"\n{'='*60}")
    print("✓ ALL ASSERTIONS PASSED")
    print(f"{'='*60}\n")


@pytest.mark.live_api
def test_extract_minimal_budget_safe():
    """
    Live test: Minimal extraction to verify basic functionality.
    
    Uses the shortest possible text to minimize API costs.
    """
    # Minimal text (< 20 words)
    text = "Smoking is harmful. It causes cancer. Therefore, we should quit."
    
    # Check API key
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        pytest.skip("OPENAI_API_KEY not set")
    
    print(f"\n{'='*60}")
    print("LIVE TEST: Minimal Budget-Safe Extraction")
    print(f"{'='*60}\n")
    
    # Run extraction
    result = extract_arguments_real(text)
    
    # Basic checks
    assert result is not None
    assert len(result["nodes"]) >= 2, "Should extract at least 2 nodes"
    assert result["meta"]["model_version"] == "gpt-4o-mini"
    
    print(f"✓ Extracted {len(result['nodes'])} nodes, {len(result['edges'])} edges")
    print(f"✓ Model: {result['meta']['model_version']}")
    
    print(f"\n{'='*60}")
    print("✓ MINIMAL TEST PASSED")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    # Run with: RUN_LIVE_API_TESTS=1 pytest tests/live/test_conclusion_extraction_live.py -v -s
    pytest.main([__file__, "-v", "-s"])
