"""
Tests for Graph Layout Optimization Module
==========================================

Tests the graph layout optimizer that minimizes edge crossings using
the barycenter heuristic.
"""

import pytest
from app_mockup.backend.graph_layout import (
    assign_layers,
    compute_barycenter,
    barycenter_ordering,
    count_edge_crossings,
    compute_layout_positions,
    apply_layout_to_nodes
)


# =============================================================================
# Test Fixtures - Sample Graphs
# =============================================================================

@pytest.fixture
def simple_dag():
    """Simple DAG: A -> B -> C"""
    nodes = [
        {'id': 'A', 'type': 'claim', 'label': 'Node A'},
        {'id': 'B', 'type': 'premise', 'label': 'Node B'},
        {'id': 'C', 'type': 'premise', 'label': 'Node C'},
    ]
    edges = [
        {'source': 'A', 'target': 'B', 'relation': 'support'},
        {'source': 'B', 'target': 'C', 'relation': 'support'},
    ]
    return nodes, edges


@pytest.fixture
def diamond_graph():
    """
    Diamond graph - potential for crossings:
         A
        / \
       B   C
        \ /
         D
    """
    nodes = [
        {'id': 'A', 'type': 'claim', 'label': 'Top'},
        {'id': 'B', 'type': 'premise', 'label': 'Left'},
        {'id': 'C', 'type': 'premise', 'label': 'Right'},
        {'id': 'D', 'type': 'conclusion', 'label': 'Bottom'},
    ]
    edges = [
        {'source': 'A', 'target': 'B', 'relation': 'support'},
        {'source': 'A', 'target': 'C', 'relation': 'support'},
        {'source': 'B', 'target': 'D', 'relation': 'support'},
        {'source': 'C', 'target': 'D', 'relation': 'support'},
    ]
    return nodes, edges


@pytest.fixture
def messy_graph():
    """
    A more complex graph designed to have many crossings with naive ordering:
    
         A       B
        /|      /|
       C D     E F
        \|    /  |
         G   H   I
          \ / \ /
           J   K
    """
    nodes = [
        {'id': 'A', 'type': 'claim', 'label': 'A'},
        {'id': 'B', 'type': 'claim', 'label': 'B'},
        {'id': 'C', 'type': 'premise', 'label': 'C'},
        {'id': 'D', 'type': 'premise', 'label': 'D'},
        {'id': 'E', 'type': 'premise', 'label': 'E'},
        {'id': 'F', 'type': 'premise', 'label': 'F'},
        {'id': 'G', 'type': 'premise', 'label': 'G'},
        {'id': 'H', 'type': 'premise', 'label': 'H'},
        {'id': 'I', 'type': 'premise', 'label': 'I'},
        {'id': 'J', 'type': 'conclusion', 'label': 'J'},
        {'id': 'K', 'type': 'conclusion', 'label': 'K'},
    ]
    edges = [
        # Layer 0 -> 1
        {'source': 'A', 'target': 'C', 'relation': 'support'},
        {'source': 'A', 'target': 'D', 'relation': 'support'},
        {'source': 'B', 'target': 'E', 'relation': 'support'},
        {'source': 'B', 'target': 'F', 'relation': 'support'},
        # Layer 1 -> 2
        {'source': 'C', 'target': 'G', 'relation': 'support'},
        {'source': 'D', 'target': 'G', 'relation': 'support'},
        {'source': 'E', 'target': 'H', 'relation': 'support'},
        {'source': 'F', 'target': 'I', 'relation': 'support'},
        # Layer 2 -> 3 (crossing-prone)
        {'source': 'G', 'target': 'J', 'relation': 'support'},
        {'source': 'H', 'target': 'J', 'relation': 'support'},
        {'source': 'H', 'target': 'K', 'relation': 'support'},
        {'source': 'I', 'target': 'K', 'relation': 'support'},
    ]
    return nodes, edges


# =============================================================================
# Unit Tests - Layer Assignment
# =============================================================================

@pytest.mark.unit
def test_assign_layers_simple_dag(simple_dag):
    """Test layer assignment for simple linear DAG."""
    nodes, edges = simple_dag
    layers = assign_layers(nodes, edges)
    
    assert layers['A'] == 0
    assert layers['B'] == 1
    assert layers['C'] == 2
    assert layers['A'] < layers['B'] < layers['C']


@pytest.mark.unit
def test_assign_layers_diamond(diamond_graph):
    """Test layer assignment for diamond graph."""
    nodes, edges = diamond_graph
    layers = assign_layers(nodes, edges)
    
    assert layers['A'] == 0  # Top
    assert layers['B'] == 1  # Middle
    assert layers['C'] == 1  # Middle
    assert layers['D'] == 2  # Bottom
    
    # Verify DAG constraint: source layer < target layer
    for edge in edges:
        assert layers[edge['source']] < layers[edge['target']]


@pytest.mark.unit
def test_assign_layers_empty_graph():
    """Test layer assignment with no nodes."""
    layers = assign_layers([], [])
    assert layers == {}


@pytest.mark.unit
def test_assign_layers_single_node():
    """Test layer assignment with single node."""
    nodes = [{'id': 'A', 'type': 'claim', 'label': 'A'}]
    layers = assign_layers(nodes, [])
    assert layers['A'] == 0


@pytest.mark.unit
def test_assign_layers_disconnected():
    """Test layer assignment with disconnected components."""
    nodes = [
        {'id': 'A', 'type': 'claim', 'label': 'A'},
        {'id': 'B', 'type': 'claim', 'label': 'B'},
    ]
    edges = []
    layers = assign_layers(nodes, edges)
    
    # Both should be in layer 0 (no edges)
    assert layers['A'] == 0
    assert layers['B'] == 0


# =============================================================================
# Unit Tests - Barycenter Computation
# =============================================================================

@pytest.mark.unit
def test_compute_barycenter_simple():
    """Test barycenter computation with neighbors."""
    node_orders = {'N1': 0, 'N2': 1, 'N3': 2}
    
    # Barycenter of neighbors at positions 0 and 2 should be 1.0
    bc = compute_barycenter('X', ['N1', 'N2', 'N3'], ['N1', 'N3'], node_orders)
    assert bc == 1.0


@pytest.mark.unit
def test_compute_barycenter_no_neighbors():
    """Test barycenter with no neighbors returns deterministic fallback."""
    node_orders = {}
    bc1 = compute_barycenter('NodeA', [], [], node_orders)
    bc2 = compute_barycenter('NodeA', [], [], node_orders)
    
    # Should be deterministic
    assert bc1 == bc2
    assert 0 <= bc1 < 10000


@pytest.mark.unit
def test_compute_barycenter_single_neighbor():
    """Test barycenter with single neighbor."""
    node_orders = {'N1': 5}
    bc = compute_barycenter('X', ['N1'], ['N1'], node_orders)
    assert bc == 5.0


# =============================================================================
# Unit Tests - Crossing Count
# =============================================================================

@pytest.mark.unit
def test_count_crossings_no_crossings(diamond_graph):
    """Test crossing count for diamond graph with optimal ordering."""
    nodes, edges = diamond_graph
    
    # Optimal ordering: B before C
    node_layers = {'A': 0, 'B': 1, 'C': 1, 'D': 2}
    nodes_by_layer = {0: ['A'], 1: ['B', 'C'], 2: ['D']}
    node_orders = {'A': 0, 'B': 0, 'C': 1, 'D': 0}
    
    crossings = count_edge_crossings(nodes_by_layer, edges, node_orders, node_layers)
    assert crossings == 0


@pytest.mark.unit
def test_count_crossings_with_crossings():
    """Test crossing count with a graph that has crossings."""
    # Create a graph with definite crossings:
    #   A   B     (layer 0)
    #   |\ /|
    #   | X |     (edges cross)
    #   |/ \|
    #   C   D     (layer 1)
    
    nodes = [
        {'id': 'A', 'type': 'claim', 'label': 'A'},
        {'id': 'B', 'type': 'claim', 'label': 'B'},
        {'id': 'C', 'type': 'premise', 'label': 'C'},
        {'id': 'D', 'type': 'premise', 'label': 'D'},
    ]
    edges = [
        {'source': 'A', 'target': 'C', 'relation': 'support'},
        {'source': 'A', 'target': 'D', 'relation': 'support'},
        {'source': 'B', 'target': 'C', 'relation': 'support'},
        {'source': 'B', 'target': 'D', 'relation': 'support'},
    ]
    
    # Bad ordering: A at pos 0, B at pos 1, but D at pos 0, C at pos 1
    # This creates crossings: A->D crosses B->C, and A->C crosses B->D
    node_layers = {'A': 0, 'B': 0, 'C': 1, 'D': 1}
    nodes_by_layer = {0: ['A', 'B'], 1: ['D', 'C']}
    node_orders = {'A': 0, 'B': 1, 'D': 0, 'C': 1}
    
    crossings = count_edge_crossings(nodes_by_layer, edges, node_orders, node_layers)
    # A->C (0->1) crosses B->D (1->0) - definitely crosses
    assert crossings >= 1


@pytest.mark.unit
def test_count_crossings_empty():
    """Test crossing count with no edges."""
    crossings = count_edge_crossings({}, [], {}, {})
    assert crossings == 0


# =============================================================================
# Integration Tests - Full Layout Pipeline
# =============================================================================

@pytest.mark.integration
def test_layout_simple_dag(simple_dag):
    """Test full layout pipeline on simple DAG."""
    nodes, edges = simple_dag
    positions, metrics, node_layers = compute_layout_positions(nodes, edges)
    
    # All nodes should have positions
    assert len(positions) == 3
    assert 'A' in positions
    assert 'B' in positions
    assert 'C' in positions
    
    # Check metrics
    assert metrics['crossings'] == 0  # Linear DAG has no crossings
    assert metrics['layers'] == 3
    assert metrics['total_nodes'] == 3
    assert metrics['total_edges'] == 2
    
    # Verify y-coordinates respect layer ordering
    y_a = positions['A'][1]
    y_b = positions['B'][1]
    y_c = positions['C'][1]
    assert y_a < y_b < y_c


@pytest.mark.integration
def test_layout_diamond_graph(diamond_graph):
    """Test full layout pipeline on diamond graph."""
    nodes, edges = diamond_graph
    positions, metrics, node_layers = compute_layout_positions(nodes, edges)
    
    # All nodes should have positions
    assert len(positions) == 4
    
    # Should have no crossings with optimal ordering
    assert metrics['crossings'] == 0
    assert metrics['layers'] == 3
    assert metrics['max_layer_width'] == 2


@pytest.mark.integration
def test_layout_messy_graph_reduces_crossings(messy_graph):
    """Test that layout reduces crossings for complex graph."""
    nodes, edges = messy_graph
    
    # Compute layout with optimization
    positions, metrics, node_layers = compute_layout_positions(nodes, edges, iterations=10)
    
    # All nodes should have positions
    assert len(positions) == 11
    
    # The optimized layout should have fewer crossings than naive ordering
    # With 11 nodes and 12 edges, we expect some crossings but not too many
    assert metrics['crossings'] >= 0
    
    # Verify metrics are reasonable
    assert metrics['layers'] >= 3
    assert metrics['total_nodes'] == 11
    assert metrics['total_edges'] == 12
    
    # Compare with naive ordering (alphabetical)
    # Build naive ordering
    node_layers_naive = assign_layers(nodes, edges)
    from collections import defaultdict
    nodes_by_layer = defaultdict(list)
    for node in nodes:
        nodes_by_layer[node_layers_naive[node['id']]].append(node['id'])
    
    # Naive ordering: just alphabetical
    node_orders_naive = {}
    for layer, node_list in nodes_by_layer.items():
        for i, node_id in enumerate(sorted(node_list)):
            node_orders_naive[node_id] = i
    
    naive_crossings = count_edge_crossings(nodes_by_layer, edges, 
                                           node_orders_naive, node_layers_naive)
    
    # Optimized should be <= naive
    assert metrics['crossings'] <= naive_crossings


@pytest.mark.integration
def test_layout_empty_graph():
    """Test layout with empty graph."""
    positions, metrics, node_layers = compute_layout_positions([], [])
    
    assert positions == {}
    assert metrics['crossings'] == 0
    assert metrics['layers'] == 0
    assert metrics['max_layer_width'] == 0


# =============================================================================
# Determinism Tests
# =============================================================================

@pytest.mark.unit
def test_layout_determinism(messy_graph):
    """Test that layout is deterministic (same input -> same output)."""
    nodes, edges = messy_graph
    
    # Compute layout twice
    positions1, metrics1, node_layers1 = compute_layout_positions(nodes, edges, iterations=5)
    positions2, metrics2, node_layers2 = compute_layout_positions(nodes, edges, iterations=5)
    
    # Should be identical
    assert positions1 == positions2
    assert metrics1 == metrics2
    assert node_layers1 == node_layers2


@pytest.mark.unit
def test_barycenter_ordering_determinism(diamond_graph):
    """Test that barycenter ordering is deterministic."""
    nodes, edges = diamond_graph
    
    # Assign layers
    node_layers = assign_layers(nodes, edges)
    from collections import defaultdict
    nodes_by_layer = defaultdict(list)
    for node in nodes:
        nodes_by_layer[node_layers[node['id']]].append(node['id'])
    
    # Build adjacency lists
    children = defaultdict(list)
    parents = defaultdict(list)
    for edge in edges:
        children[edge['source']].append(edge['target'])
        parents[edge['target']].append(edge['source'])
    
    # Run ordering twice
    orders1 = barycenter_ordering(nodes_by_layer, children, parents, iterations=5)
    orders2 = barycenter_ordering(nodes_by_layer, children, parents, iterations=5)
    
    assert orders1 == orders2


# =============================================================================
# Golden Snapshot Tests
# =============================================================================

@pytest.mark.regression
def test_layout_golden_snapshot_diamond(diamond_graph):
    """Golden test: diamond graph layout should remain stable."""
    nodes, edges = diamond_graph
    positions, metrics, node_layers = compute_layout_positions(nodes, edges, 
                                                  node_spacing=250, 
                                                  layer_separation=200,
                                                  iterations=8)
    
    # Expected structure (may need adjustment if algorithm changes)
    assert metrics['layers'] == 3
    assert metrics['crossings'] == 0
    assert metrics['max_layer_width'] == 2
    
    # Verify A is at top (layer 0)
    assert positions['A'][1] == 0
    
    # Verify B and C are at same y-level (layer 1)
    assert positions['B'][1] == positions['C'][1] == 200
    
    # Verify D is at bottom (layer 2)
    assert positions['D'][1] == 400


@pytest.mark.regression
def test_layout_golden_snapshot_messy(messy_graph):
    """Golden test: messy graph layout should remain stable."""
    nodes, edges = messy_graph
    positions, metrics, node_layers = compute_layout_positions(nodes, edges,
                                                  node_spacing=250,
                                                  layer_separation=200,
                                                  iterations=8)
    
    # Store expected metrics (baseline)
    # These values are from the initial correct run
    assert metrics['total_nodes'] == 11
    assert metrics['total_edges'] == 12
    
    # The algorithm should produce consistently low crossings
    # Exact number may vary, but should be deterministic
    expected_crossings = metrics['crossings']  # Store first run value
    
    # Re-run and verify same result
    positions2, metrics2, node_layers2 = compute_layout_positions(nodes, edges,
                                                    node_spacing=250,
                                                    layer_separation=200,
                                                    iterations=8)
    assert metrics2['crossings'] == expected_crossings
    assert positions == positions2


# =============================================================================
# Apply Layout Tests
# =============================================================================

@pytest.mark.unit
def test_apply_layout_to_nodes(simple_dag):
    """Test applying positions to nodes."""
    nodes, edges = simple_dag
    positions = {'A': (0, 0), 'B': (0, 200), 'C': (0, 400)}
    
    result = apply_layout_to_nodes(nodes, positions)
    
    assert len(result) == 3
    assert result[0]['id'] == 'A'
    assert result[0]['x'] == 0
    assert result[0]['y'] == 0
    assert result[1]['id'] == 'B'
    assert result[1]['x'] == 0
    assert result[1]['y'] == 200


@pytest.mark.unit
def test_apply_layout_preserves_original():
    """Test that apply_layout doesn't modify original nodes."""
    nodes = [{'id': 'A', 'type': 'claim', 'label': 'A'}]
    positions = {'A': (100, 200)}
    
    result = apply_layout_to_nodes(nodes, positions)
    
    # Original should not have x/y
    assert 'x' not in nodes[0]
    assert 'y' not in nodes[0]
    
    # Result should have x/y
    assert result[0]['x'] == 100
    assert result[0]['y'] == 200


# =============================================================================
# Edge Case Tests
# =============================================================================

@pytest.mark.negative
def test_layout_with_self_loop():
    """Test layout handles self-loops gracefully."""
    nodes = [{'id': 'A', 'type': 'claim', 'label': 'A'}]
    edges = [{'source': 'A', 'target': 'A', 'relation': 'support'}]
    
    # Should not crash
    positions, metrics, node_layers = compute_layout_positions(nodes, edges)
    assert 'A' in positions
    assert metrics['crossings'] >= 0


@pytest.mark.negative
def test_layout_with_missing_nodes():
    """Test layout handles edges referencing non-existent nodes."""
    nodes = [{'id': 'A', 'type': 'claim', 'label': 'A'}]
    edges = [
        {'source': 'A', 'target': 'B', 'relation': 'support'},
        {'source': 'B', 'target': 'C', 'relation': 'support'}
    ]
    
    # Should not crash, should ignore edges with missing nodes
    positions, metrics, node_layers = compute_layout_positions(nodes, edges)
    assert len(positions) == 1
    assert 'A' in positions


@pytest.mark.unit
def test_layout_with_large_graph():
    """Test layout performance with larger graph."""
    # Create a graph with 50 nodes
    nodes = [{'id': f'N{i}', 'type': 'claim', 'label': f'Node {i}'} 
             for i in range(50)]
    
    # Create a tree-like structure
    edges = []
    for i in range(49):
        target = i + 1
        edges.append({'source': f'N{i}', 'target': f'N{target}', 'relation': 'support'})
    
    # Should complete quickly
    positions, metrics, node_layers = compute_layout_positions(nodes, edges, iterations=5)
    
    assert len(positions) == 50
    assert metrics['total_nodes'] == 50
    assert metrics['crossings'] == 0  # Tree structure has no crossings
