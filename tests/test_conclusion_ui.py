"""
Unit Tests for Conclusion Node Rendering
==========================================

Tests to verify that conclusion nodes are properly supported in the UI.
"""

import pytest
import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app_mockup'))

from node_type_config import get_node_color, get_all_node_types, NODE_TYPE_CONFIG


@pytest.mark.unit
class TestConclusionNodeSupport:
    """Tests for conclusion node type support in UI."""
    
    def test_node_type_config_includes_conclusion(self):
        """Test that node type config includes conclusion mapping."""
        color = get_node_color("conclusion")
        assert color is not None
        assert color != "#6b7280"  # Should not use fallback gray
        assert color == "#8b5cf6"  # Should be purple
    
    def test_all_five_node_types_in_config(self):
        """Test that all 5 node types are in the configuration."""
        all_types = get_all_node_types()
        expected_types = ["claim", "premise", "objection", "reply", "conclusion"]
        
        assert len(all_types) == 5, f"Expected 5 types, got {len(all_types)}"
        for expected in expected_types:
            assert expected in all_types, f"Missing node type: {expected}"
    
    def test_node_type_config_structure(self):
        """Test that NODE_TYPE_CONFIG has proper structure for all types."""
        expected_types = ["claim", "premise", "objection", "reply", "conclusion"]
        
        for node_type in expected_types:
            assert node_type in NODE_TYPE_CONFIG, f"Missing {node_type} in config"
            config = NODE_TYPE_CONFIG[node_type]
            
            # Each type must have color, label, and description
            assert "color" in config, f"{node_type} missing 'color'"
            assert "label" in config, f"{node_type} missing 'label'"
            assert "description" in config, f"{node_type} missing 'description'"
            
            # Color should be a valid hex code
            assert config["color"].startswith("#"), f"{node_type} color not hex"
            assert len(config["color"]) == 7, f"{node_type} color not 6-digit hex"
    
    def test_all_node_types_have_distinct_colors(self):
        """Test that all node types have distinct colors."""
        node_types = ["claim", "premise", "objection", "reply", "conclusion"]
        colors = [get_node_color(t) for t in node_types]
        
        # All colors should be unique
        assert len(colors) == len(set(colors)), f"Duplicate colors found: {colors}"
        
        # No color should be the fallback gray
        for color in colors:
            assert color != "#6b7280", f"Node type uses fallback color: {color}"
    
    def test_unknown_node_type_uses_fallback(self):
        """Test that unknown node types use fallback color."""
        color = get_node_color("unknown_type")
        assert color == "#6b7280"  # Should use fallback gray
    
    def test_conclusion_test_fixture_is_valid(self):
        """Test that the conclusion test fixture is valid JSON with expected structure."""
        fixture_path = os.path.join(
            os.path.dirname(__file__), 
            '..', 
            'app_mockup', 
            'sample_data', 
            'sample_graph_conclusion_test.json'
        )
        
        # Load and parse fixture
        with open(fixture_path, 'r') as f:
            graph = json.load(f)
        
        # Verify structure
        assert "nodes" in graph
        assert "edges" in graph
        assert "meta" in graph
        
        # Verify conclusion node exists
        conclusion_nodes = [n for n in graph["nodes"] if n["type"] == "conclusion"]
        assert len(conclusion_nodes) > 0, "Test fixture should contain at least one conclusion node"
        
        # Verify conclusion node has required fields
        conclusion = conclusion_nodes[0]
        assert "id" in conclusion
        assert "type" in conclusion
        assert conclusion["type"] == "conclusion"
        assert "label" in conclusion
        assert "span" in conclusion
        assert "paraphrase" in conclusion
        assert "confidence" in conclusion
        
        # Verify edges to/from conclusion
        conclusion_id = conclusion["id"]
        edges_to_conclusion = [e for e in graph["edges"] if e["target"] == conclusion_id]
        assert len(edges_to_conclusion) > 0, "Conclusion node should have incoming edges"


@pytest.mark.integration
class TestConclusionNodeRendering:
    """Integration tests for conclusion node rendering."""
    
    def test_conclusion_node_in_fixture(self):
        """Test that conclusion node fixture can be loaded."""
        from extractor_stub import load_sample_graph
        
        graph = load_sample_graph("sample_graph_conclusion_test.json")
        
        # Verify graph structure
        assert "nodes" in graph
        assert "edges" in graph
        
        # Find conclusion node
        conclusion_nodes = [n for n in graph["nodes"] if n["type"] == "conclusion"]
        assert len(conclusion_nodes) == 1
        
        conclusion = conclusion_nodes[0]
        assert conclusion["id"] == "n4"
        assert conclusion["label"] == "Therefore, abolish capital punishment"
        
        # Verify edges
        edges_to_conclusion = [e for e in graph["edges"] if e["target"] == conclusion["id"]]
        assert len(edges_to_conclusion) == 1
        assert edges_to_conclusion[0]["source"] == "n1"
        assert edges_to_conclusion[0]["relation"] == "support"
    
    def test_all_five_types_fixture(self):
        """Test that the all-types fixture includes all 5 node types."""
        from extractor_stub import load_sample_graph
        
        graph = load_sample_graph("sample_graph_all_types.json")
        
        # Verify graph structure
        assert "nodes" in graph
        assert "edges" in graph
        assert "meta" in graph
        
        # Collect all node types present
        node_types = {n["type"] for n in graph["nodes"]}
        
        # Verify all 5 types are present
        expected_types = {"claim", "premise", "objection", "reply", "conclusion"}
        assert node_types == expected_types, f"Expected {expected_types}, got {node_types}"
        
        # Verify each type appears exactly once
        type_counts = {}
        for node in graph["nodes"]:
            node_type = node["type"]
            type_counts[node_type] = type_counts.get(node_type, 0) + 1
        
        for expected_type in expected_types:
            assert type_counts[expected_type] == 1, f"Expected 1 {expected_type}, got {type_counts[expected_type]}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
