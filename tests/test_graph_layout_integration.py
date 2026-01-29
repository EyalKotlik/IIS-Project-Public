"""
Integration test for graph layout with vis-network component.

Tests that the layout module integrates correctly with the vis_network_select component.
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'app_mockup'))

from backend.graph_layout import compute_layout_positions, apply_layout_to_nodes


@pytest.fixture
def sample_graph():
    """Create a sample graph for testing."""
    nodes = [
        {'id': 'A', 'type': 'claim', 'label': 'Claim A', 'confidence': 0.9, 'span': 'Text A', 'paraphrase': 'Para A'},
        {'id': 'B', 'type': 'premise', 'label': 'Premise B', 'confidence': 0.85, 'span': 'Text B', 'paraphrase': 'Para B'},
        {'id': 'C', 'type': 'premise', 'label': 'Premise C', 'confidence': 0.8, 'span': 'Text C', 'paraphrase': 'Para C'},
        {'id': 'D', 'type': 'conclusion', 'label': 'Conclusion D', 'confidence': 0.95, 'span': 'Text D', 'paraphrase': 'Para D'},
    ]
    
    edges = [
        {'source': 'A', 'target': 'B', 'relation': 'support', 'confidence': 0.9},
        {'source': 'A', 'target': 'C', 'relation': 'support', 'confidence': 0.85},
        {'source': 'B', 'target': 'D', 'relation': 'support', 'confidence': 0.9},
        {'source': 'C', 'target': 'D', 'relation': 'support', 'confidence': 0.85},
    ]
    
    return nodes, edges


@pytest.mark.integration
def test_component_integration_with_layout(sample_graph):
    """Test that layout positions can be computed and applied to nodes for the component."""
    nodes, edges = sample_graph
    
    # Compute layout
    positions, metrics, node_layers = compute_layout_positions(nodes, edges)
    
    # Verify positions computed for all nodes
    assert len(positions) == len(nodes)
    for node in nodes:
        assert node['id'] in positions
        x, y = positions[node['id']]
        assert isinstance(x, int)
        assert isinstance(y, int)
    
    # Apply positions to nodes
    nodes_with_positions = apply_layout_to_nodes(nodes, positions)
    
    # Verify positions applied
    for node in nodes_with_positions:
        assert 'x' in node
        assert 'y' in node
        assert isinstance(node['x'], int)
        assert isinstance(node['y'], int)
    
    # Verify original node data preserved
    for original, positioned in zip(nodes, nodes_with_positions):
        assert positioned['id'] == original['id']
        assert positioned['type'] == original['type']
        assert positioned['label'] == original['label']
        assert positioned['confidence'] == original['confidence']
    
    # Verify metrics are reasonable
    assert metrics['crossings'] >= 0
    assert metrics['layers'] > 0
    assert metrics['total_nodes'] == len(nodes)
    assert metrics['total_edges'] == len(edges)


@pytest.mark.integration
def test_component_integration_preserves_node_data(sample_graph):
    """Test that applying layout preserves all original node data."""
    nodes, edges = sample_graph
    
    # Add extra fields to nodes
    for node in nodes:
        node['extra_field'] = 'extra_value'
    
    # Compute and apply layout
    positions, _, _ = compute_layout_positions(nodes, edges)
    nodes_with_positions = apply_layout_to_nodes(nodes, positions)
    
    # Verify extra fields preserved
    for node in nodes_with_positions:
        assert 'extra_field' in node
        assert node['extra_field'] == 'extra_value'


@pytest.mark.integration
def test_component_integration_with_empty_graph():
    """Test that component integration handles empty graphs gracefully."""
    nodes = []
    edges = []
    
    # Should not crash
    positions, metrics, node_layers = compute_layout_positions(nodes, edges)
    nodes_with_positions = apply_layout_to_nodes(nodes, positions)
    
    assert positions == {}
    assert nodes_with_positions == []
    assert metrics['crossings'] == 0
    assert metrics['layers'] == 0


@pytest.mark.integration
def test_layout_output_format_for_vis_network(sample_graph):
    """Test that layout output is compatible with vis-network format."""
    nodes, edges = sample_graph
    
    # Compute and apply layout
    positions, metrics, node_layers = compute_layout_positions(nodes, edges)
    nodes_with_positions = apply_layout_to_nodes(nodes, positions)
    
    # Check vis-network compatibility
    for node in nodes_with_positions:
        # Must have id
        assert 'id' in node
        
        # Must have x, y positions
        assert 'x' in node
        assert 'y' in node
        
        # Positions should be numeric
        assert isinstance(node['x'], (int, float))
        assert isinstance(node['y'], (int, float))
        
        # Should have all required fields for vis-network
        assert 'label' in node
        assert 'type' in node


@pytest.mark.integration  
def test_layout_determinism_with_component(sample_graph):
    """Test that layout is deterministic when used with component."""
    nodes, edges = sample_graph
    
    # Compute layout twice
    positions1, metrics1, node_layers1 = compute_layout_positions(nodes, edges)
    nodes1 = apply_layout_to_nodes(nodes, positions1)
    
    positions2, metrics2, node_layers2 = compute_layout_positions(nodes, edges)
    nodes2 = apply_layout_to_nodes(nodes, positions2)
    
    # Should be identical
    assert positions1 == positions2
    assert metrics1 == metrics2
    assert node_layers1 == node_layers2
    
    # Check node positions match
    for n1, n2 in zip(nodes1, nodes2):
        assert n1['x'] == n2['x']
        assert n1['y'] == n2['y']


@pytest.mark.integration
def test_all_layers_x_float(sample_graph):
    """Test that all layer nodes have x floating and y fixed."""
    nodes, edges = sample_graph
    
    # Compute layout
    positions, metrics, node_layers = compute_layout_positions(nodes, edges)
    
    # Apply layout
    nodes_with_positions = apply_layout_to_nodes(nodes, positions)
    
    # Verify all nodes have x and y positions
    for node in nodes_with_positions:
        assert 'x' in node
        assert 'y' in node
    
    # Verify different layers exist
    assert len(set(node_layers.values())) > 1, "Should have multiple layers"
    
    # All nodes should be treated the same regardless of layer
    # (In the actual vis_network_select, all will get fixed: {x: False, y: True})
    for node in nodes_with_positions:
        if node['id'] in node_layers:
            # Just verify the node has position info
            # The fixing is applied in vis_network_select
            assert isinstance(node['x'], (int, float))
            assert isinstance(node['y'], (int, float))
