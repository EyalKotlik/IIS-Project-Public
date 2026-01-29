#!/usr/bin/env python3
"""
Manual verification script for conclusion node rendering.

This script loads the conclusion test fixture and verifies that:
1. Conclusion nodes have proper color mapping
2. All node types are distinct
3. The fixture loads correctly
"""

import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app_mockup'))

from app import get_node_color
from components.vis_network_select import _get_node_color as vis_get_node_color
from extractor_stub import load_sample_graph, get_sample_texts

# Constants
SPAN_TRUNCATE_LENGTH = 60

def test_color_mappings():
    """Test that color mappings are correct."""
    print("=" * 60)
    print("Testing Color Mappings")
    print("=" * 60)
    
    node_types = ["claim", "premise", "objection", "reply", "conclusion", "other"]
    
    print("\napp.py color mappings:")
    for node_type in node_types:
        color = get_node_color(node_type)
        print(f"  {node_type:12s} -> {color}")
    
    print("\nvis_network_select color mappings:")
    for node_type in node_types:
        color = vis_get_node_color(node_type)
        print(f"  {node_type:12s} -> {color}")
    
    # Verify conclusion has purple color
    conclusion_color = get_node_color("conclusion")
    assert conclusion_color == "#8b5cf6", f"Expected #8b5cf6, got {conclusion_color}"
    print("\n✅ Conclusion node has purple color (#8b5cf6)")
    
    # Verify all colors are distinct
    colors = [get_node_color(t) for t in ["claim", "premise", "objection", "reply", "conclusion"]]
    assert len(colors) == len(set(colors)), "Colors are not distinct!"
    print("✅ All node type colors are distinct")


def test_fixture_loading():
    """Test that the conclusion fixture loads correctly."""
    print("\n" + "=" * 60)
    print("Testing Conclusion Fixture Loading")
    print("=" * 60)
    
    # Load the fixture
    graph = load_sample_graph("sample_graph_conclusion_test.json")
    
    print(f"\nLoaded graph with {len(graph['nodes'])} nodes and {len(graph['edges'])} edges")
    
    # Find conclusion nodes
    conclusion_nodes = [n for n in graph["nodes"] if n["type"] == "conclusion"]
    print(f"Found {len(conclusion_nodes)} conclusion node(s)")
    
    assert len(conclusion_nodes) > 0, "No conclusion nodes found!"
    
    # Display conclusion node details
    for node in conclusion_nodes:
        print(f"\nConclusion Node Details:")
        print(f"  ID:         {node['id']}")
        print(f"  Label:      {node['label']}")
        print(f"  Span:       {node['span'][:SPAN_TRUNCATE_LENGTH]}...")
        print(f"  Confidence: {node['confidence']:.2f}")
    
    # Find edges to/from conclusion
    for conclusion in conclusion_nodes:
        edges_to = [e for e in graph["edges"] if e["target"] == conclusion["id"]]
        edges_from = [e for e in graph["edges"] if e["source"] == conclusion["id"]]
        print(f"\n  Edges TO conclusion: {len(edges_to)}")
        for edge in edges_to:
            print(f"    {edge['source']} --{edge['relation']}--> {conclusion['id']}")
        print(f"  Edges FROM conclusion: {len(edges_from)}")
        for edge in edges_from:
            print(f"    {conclusion['id']} --{edge['relation']}--> {edge['target']}")
    
    print("\n✅ Conclusion fixture loads correctly")


def test_sample_texts():
    """Test that sample texts include conclusion test."""
    print("\n" + "=" * 60)
    print("Testing Sample Texts Menu")
    print("=" * 60)
    
    samples = get_sample_texts()
    print(f"\nAvailable sample texts:")
    for name in samples.keys():
        print(f"  - {name}")
    
    assert "Conclusion Test" in samples, "Conclusion Test not in sample texts!"
    print("\n✅ Conclusion Test is available in sample texts menu")


def main():
    """Run all verification tests."""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║  CONCLUSION NODE RENDERING - MANUAL VERIFICATION       ║")
    print("╚" + "=" * 58 + "╝")
    
    try:
        test_color_mappings()
        test_fixture_loading()
        test_sample_texts()
        
        print("\n" + "=" * 60)
        print("✅ ALL VERIFICATIONS PASSED")
        print("=" * 60)
        print("\nConclusion nodes should now render correctly in the UI!")
        print("\nTo test in the UI:")
        print("  1. Run: streamlit run app_mockup/app.py")
        print("  2. Select 'Conclusion Test' from the dropdown")
        print("  3. Click 'Load Example' and 'Run Extraction'")
        print("  4. Verify the purple conclusion node appears in the graph")
        print("  5. Click the conclusion node to verify details panel works")
        print()
        
        return 0
    except Exception as e:
        print(f"\n❌ VERIFICATION FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
