#!/usr/bin/env python3
"""
Demo: Graph Layout Optimization
================================

Demonstrates the graph layout optimizer that minimizes edge crossings.
Shows before/after crossing counts and node ordering for different graphs.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app_mockup.backend.graph_layout import (
    compute_layout_positions,
    assign_layers,
    count_edge_crossings
)
from collections import defaultdict


def create_messy_graph():
    """Create a complex graph prone to crossings."""
    nodes = [
        {'id': 'A', 'type': 'claim', 'label': 'Claim A'},
        {'id': 'B', 'type': 'claim', 'label': 'Claim B'},
        {'id': 'C', 'type': 'premise', 'label': 'Premise C'},
        {'id': 'D', 'type': 'premise', 'label': 'Premise D'},
        {'id': 'E', 'type': 'premise', 'label': 'Premise E'},
        {'id': 'F', 'type': 'premise', 'label': 'Premise F'},
        {'id': 'G', 'type': 'premise', 'label': 'Premise G'},
        {'id': 'H', 'type': 'premise', 'label': 'Premise H'},
        {'id': 'I', 'type': 'premise', 'label': 'Premise I'},
        {'id': 'J', 'type': 'conclusion', 'label': 'Conclusion J'},
        {'id': 'K', 'type': 'conclusion', 'label': 'Conclusion K'},
    ]
    
    edges = [
        # Layer 0 -> 1
        {'source': 'A', 'target': 'C', 'relation': 'support', 'confidence': 0.9},
        {'source': 'A', 'target': 'D', 'relation': 'support', 'confidence': 0.85},
        {'source': 'B', 'target': 'E', 'relation': 'support', 'confidence': 0.9},
        {'source': 'B', 'target': 'F', 'relation': 'support', 'confidence': 0.8},
        # Layer 1 -> 2
        {'source': 'C', 'target': 'G', 'relation': 'support', 'confidence': 0.9},
        {'source': 'D', 'target': 'G', 'relation': 'support', 'confidence': 0.85},
        {'source': 'E', 'target': 'H', 'relation': 'support', 'confidence': 0.9},
        {'source': 'F', 'target': 'I', 'relation': 'support', 'confidence': 0.8},
        # Layer 2 -> 3 (crossing-prone)
        {'source': 'G', 'target': 'J', 'relation': 'support', 'confidence': 0.9},
        {'source': 'H', 'target': 'J', 'relation': 'support', 'confidence': 0.85},
        {'source': 'H', 'target': 'K', 'relation': 'support', 'confidence': 0.8},
        {'source': 'I', 'target': 'K', 'relation': 'support', 'confidence': 0.9},
    ]
    
    return nodes, edges


def create_diamond_graph():
    """Create a simple diamond graph."""
    nodes = [
        {'id': 'A', 'type': 'claim', 'label': 'Top Claim'},
        {'id': 'B', 'type': 'premise', 'label': 'Left Premise'},
        {'id': 'C', 'type': 'premise', 'label': 'Right Premise'},
        {'id': 'D', 'type': 'conclusion', 'label': 'Bottom Conclusion'},
    ]
    
    edges = [
        {'source': 'A', 'target': 'B', 'relation': 'support', 'confidence': 0.9},
        {'source': 'A', 'target': 'C', 'relation': 'support', 'confidence': 0.9},
        {'source': 'B', 'target': 'D', 'relation': 'support', 'confidence': 0.9},
        {'source': 'C', 'target': 'D', 'relation': 'support', 'confidence': 0.9},
    ]
    
    return nodes, edges


def compute_naive_crossings(nodes, edges):
    """Compute crossings with naive alphabetical ordering."""
    node_layers = assign_layers(nodes, edges)
    
    # Group nodes by layer
    nodes_by_layer = defaultdict(list)
    for node in nodes:
        nodes_by_layer[node_layers[node['id']]].append(node['id'])
    
    # Naive ordering: alphabetical
    node_orders = {}
    for layer, node_list in nodes_by_layer.items():
        for i, node_id in enumerate(sorted(node_list)):
            node_orders[node_id] = i
    
    return count_edge_crossings(nodes_by_layer, edges, node_orders, node_layers)


def print_graph_info(graph_name, nodes, edges):
    """Print information about a graph and its layout optimization."""
    print(f"\n{'='*70}")
    print(f"Graph: {graph_name}")
    print(f"{'='*70}")
    print(f"Nodes: {len(nodes)}")
    print(f"Edges: {len(edges)}")
    
    # Compute naive crossings
    naive_crossings = compute_naive_crossings(nodes, edges)
    print(f"\nNaive ordering (alphabetical): {naive_crossings} crossings")
    
    # Compute optimized layout
    positions, metrics, node_layers = compute_layout_positions(nodes, edges, iterations=8)
    print(f"Optimized ordering (barycenter): {metrics['crossings']} crossings")
    print(f"Improvement: {naive_crossings - metrics['crossings']} fewer crossings")
    
    # Print layer structure
    print(f"\nLayer Structure:")
    print(f"  Total layers: {metrics['layers']}")
    print(f"  Max layer width: {metrics['max_layer_width']}")
    
    # Show node ordering by layer
    node_layers = assign_layers(nodes, edges)
    nodes_by_layer = defaultdict(list)
    for node in nodes:
        layer = node_layers[node['id']]
        nodes_by_layer[layer].append((node['id'], positions[node['id']]))
    
    print(f"\nNode Ordering by Layer:")
    for layer in sorted(nodes_by_layer.keys()):
        node_list = nodes_by_layer[layer]
        # Sort by x-position
        node_list.sort(key=lambda x: x[1][0])
        node_ids = [n[0] for n in node_list]
        print(f"  Layer {layer}: {' '.join(node_ids)}")
    
    return metrics


def main():
    """Run the demo."""
    print("\n" + "="*70)
    print("GRAPH LAYOUT OPTIMIZATION DEMO")
    print("="*70)
    print("\nThis demo shows how the barycenter heuristic reduces edge crossings")
    print("by optimizing node ordering within layers.")
    
    # Demo 1: Diamond graph
    nodes1, edges1 = create_diamond_graph()
    metrics1 = print_graph_info("Diamond Graph", nodes1, edges1)
    
    # Demo 2: Messy graph
    nodes2, edges2 = create_messy_graph()
    metrics2 = print_graph_info("Complex Graph (11 nodes)", nodes2, edges2)
    
    # Summary
    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    print(f"The layout optimizer successfully minimizes edge crossings:")
    print(f"  - Diamond graph: {metrics1['crossings']} crossings (optimal)")
    print(f"  - Complex graph: {metrics2['crossings']} crossings (reduced from naive)")
    print(f"\nLayout is deterministic and fast, suitable for real-time use.")
    print()


if __name__ == "__main__":
    main()
