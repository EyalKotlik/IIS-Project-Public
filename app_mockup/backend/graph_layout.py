"""
Graph Layout Optimization Module
==================================

Implements server-side graph layout to minimize edge crossings in hierarchical
directed acyclic graphs (DAGs). Uses the barycenter heuristic with bidirectional
sweeps to improve node ordering within layers.

Key Features:
- Layer assignment based on topological sorting
- Barycenter/median heuristic for crossing minimization
- Deterministic ordering (stable sorts, tiebreaking by node ID)
- Crossing count metric for layout quality assessment
- Compatible with vis-network hierarchical layout

Algorithm Overview:
1. Assign nodes to layers using topological sort (longest path)
2. Initialize node ordering within each layer
3. Iteratively sweep top-down and bottom-up:
   - Reorder nodes by barycenter of neighbors in adjacent layer
   - Use stable sorting with node ID tiebreaking for determinism
4. Compute final x/y positions based on layer and order
5. Return layout with quality metrics

This is a layout-only module - it does not change graph construction,
extraction, or semantics.
"""

from typing import List, Dict, Set, Tuple, Optional, Any
from collections import defaultdict, deque
import statistics


# Constants
HASH_FALLBACK_RANGE = 10000  # Range for hash-based tiebreaking in barycenter computation


def assign_layers(nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Assign nodes to layers using topological sorting with longest path.
    
    Each node is placed in the highest layer that respects the DAG constraint:
    for every edge (u, v), layer(u) < layer(v).
    
    Args:
        nodes: List of node dicts with 'id' field
        edges: List of edge dicts with 'source' and 'target' fields
        
    Returns:
        Dict mapping node_id -> layer_number (0 = top layer)
    """
    # Build adjacency lists
    children = defaultdict(list)  # node -> list of children
    parents = defaultdict(list)   # node -> list of parents
    in_degree = defaultdict(int)
    
    node_ids = {node['id'] for node in nodes}
    
    for edge in edges:
        src, tgt = edge['source'], edge['target']
        if src in node_ids and tgt in node_ids:
            children[src].append(tgt)
            parents[tgt].append(src)
            in_degree[tgt] += 1
    
    # Initialize all nodes with in-degree 0 if not already set
    for node in nodes:
        if node['id'] not in in_degree:
            in_degree[node['id']] = 0
    
    # Topological sort with layer assignment (longest path)
    layers = {}
    queue = deque()
    
    # Start with nodes that have no parents (sources)
    for node in nodes:
        if in_degree[node['id']] == 0:
            layers[node['id']] = 0
            queue.append(node['id'])
    
    # Process nodes in topological order
    while queue:
        node_id = queue.popleft()
        current_layer = layers[node_id]
        
        for child_id in children[node_id]:
            # Child must be in a layer below parent
            child_layer = max(layers.get(child_id, 0), current_layer + 1)
            layers[child_id] = child_layer
            
            # Decrease in-degree and add to queue when ready
            in_degree[child_id] -= 1
            if in_degree[child_id] == 0:
                queue.append(child_id)
    
    # Handle any remaining nodes not reached (cycles or disconnected components)
    # Place them in layer 0 by default
    for node in nodes:
        if node['id'] not in layers:
            layers[node['id']] = 0
    
    return layers


def compute_barycenter(node_id: str, layer_nodes: List[str], 
                       neighbors: List[str], node_orders: Dict[str, int]) -> float:
    """
    Compute barycenter (average position) of neighbors in adjacent layer.
    
    The barycenter is the mean of the positions of all neighbors.
    Used as a heuristic for node ordering to reduce edge crossings.
    
    Args:
        node_id: ID of the node to compute barycenter for
        layer_nodes: List of node IDs in the adjacent layer
        neighbors: List of neighbor node IDs in the adjacent layer
        node_orders: Dict mapping node_id -> order position in its layer
        
    Returns:
        Barycenter value (average neighbor position), or a default based on node_id
    """
    if not neighbors:
        # No neighbors: use node_id hash as tiebreaker for determinism
        return float(hash(node_id) % HASH_FALLBACK_RANGE) / HASH_FALLBACK_RANGE
    
    # Get positions of neighbors
    positions = [node_orders[n] for n in neighbors if n in node_orders]
    
    if not positions:
        return float(hash(node_id) % HASH_FALLBACK_RANGE) / HASH_FALLBACK_RANGE
    
    # Return mean position
    return statistics.mean(positions)


def order_bottom_layer_by_support(bottom_layer_nodes: List[str],
                                   parents: Dict[str, List[str]],
                                   parent_orders: Dict[str, int]) -> Dict[str, int]:
    """
    Order nodes in the bottom layer by grouping them according to what they support.
    
    Premises supporting the same parent node(s) should be positioned together as a block,
    and these blocks should be positioned under the nodes they support.
    
    Args:
        bottom_layer_nodes: List of node IDs in the bottom layer
        parents: Dict mapping node_id -> list of parent node IDs
        parent_orders: Dict mapping parent node_id -> order position in their layer
        
    Returns:
        Dict mapping node_id -> order position within the bottom layer
    """
    # Group nodes by their parents
    groups = defaultdict(list)
    
    for node_id in bottom_layer_nodes:
        parent_ids = parents.get(node_id, [])
        
        if not parent_ids:
            # Nodes with no parents go to a special group
            groups[('orphan',)].append(node_id)
        else:
            # Create a tuple of sorted parent IDs as the group key
            # This ensures nodes with the same set of parents are grouped together
            group_key = tuple(sorted(parent_ids))
            groups[group_key].append(node_id)
    
    # Sort groups by the position of their parents
    # Use the minimum parent position as the group position
    sorted_groups = []
    for group_key, group_nodes in groups.items():
        if group_key == ('orphan',):
            # Orphan nodes go to the end
            group_position = float('inf')
        else:
            # Get the average position of all parents this group supports
            parent_positions = [parent_orders.get(p, 0) for p in group_key if p in parent_orders]
            group_position = statistics.mean(parent_positions) if parent_positions else 0
        
        sorted_groups.append((group_position, group_key, group_nodes))
    
    # Sort groups by position
    sorted_groups.sort(key=lambda x: (x[0], x[1]))  # Sort by position, then by group key for determinism
    
    # Assign orders: iterate through sorted groups and their nodes
    node_orders = {}
    current_order = 0
    
    for _, _, group_nodes in sorted_groups:
        # Sort nodes within each group for determinism
        sorted_group_nodes = sorted(group_nodes)
        for node_id in sorted_group_nodes:
            node_orders[node_id] = current_order
            current_order += 1
    
    return node_orders


def barycenter_ordering(nodes_by_layer: Dict[int, List[str]], 
                        children: Dict[str, List[str]],
                        parents: Dict[str, List[str]],
                        iterations: int = 8) -> Dict[str, int]:
    """
    Optimize node ordering within layers using barycenter heuristic.
    
    Performs bidirectional sweeps (top-down and bottom-up) to minimize edge crossings.
    Each sweep reorders nodes based on the barycenter of their neighbors in the
    adjacent layer.
    
    Args:
        nodes_by_layer: Dict mapping layer_number -> list of node IDs
        children: Dict mapping node_id -> list of child node IDs
        parents: Dict mapping node_id -> list of parent node IDs
        iterations: Number of sweep iterations (default: 8)
        
    Returns:
        Dict mapping node_id -> order position within its layer
    """
    layer_numbers = sorted(nodes_by_layer.keys())
    
    # Initialize orders: sort nodes by ID for determinism
    node_orders = {}
    for layer, node_list in nodes_by_layer.items():
        sorted_nodes = sorted(node_list)  # Deterministic initial order
        for i, node_id in enumerate(sorted_nodes):
            node_orders[node_id] = i
    
    # Perform iterative sweeps
    for iteration in range(iterations):
        # Top-down sweep: order by barycenter of parents
        for layer_idx in range(len(layer_numbers)):
            layer = layer_numbers[layer_idx]
            layer_nodes = nodes_by_layer[layer]
            
            if layer_idx == 0 or len(layer_nodes) <= 1:
                continue  # Skip first layer or single-node layers
            
            # Compute barycenter for each node based on parents
            node_barycenters = []
            for node_id in layer_nodes:
                parent_ids = parents.get(node_id, [])
                bc = compute_barycenter(node_id, nodes_by_layer.get(layer - 1, []), 
                                       parent_ids, node_orders)
                node_barycenters.append((bc, node_id))
            
            # Sort by barycenter (stable sort), then assign new orders
            node_barycenters.sort(key=lambda x: (x[0], x[1]))  # Tiebreak by node_id
            for i, (_, node_id) in enumerate(node_barycenters):
                node_orders[node_id] = i
        
        # Bottom-up sweep: order by barycenter of children
        for layer_idx in range(len(layer_numbers) - 1, -1, -1):
            layer = layer_numbers[layer_idx]
            layer_nodes = nodes_by_layer[layer]
            
            if layer_idx == len(layer_numbers) - 1 or len(layer_nodes) <= 1:
                continue  # Skip last layer or single-node layers
            
            # Compute barycenter for each node based on children
            node_barycenters = []
            for node_id in layer_nodes:
                child_ids = children.get(node_id, [])
                bc = compute_barycenter(node_id, nodes_by_layer.get(layer + 1, []), 
                                       child_ids, node_orders)
                node_barycenters.append((bc, node_id))
            
            # Sort by barycenter (stable sort), then assign new orders
            node_barycenters.sort(key=lambda x: (x[0], x[1]))  # Tiebreak by node_id
            for i, (_, node_id) in enumerate(node_barycenters):
                node_orders[node_id] = i
    
    # After all iterations, apply special ordering to the bottom layer
    # The bottom layer should have premises grouped by what they support
    if layer_numbers:
        bottom_layer = layer_numbers[-1]
        bottom_layer_nodes = nodes_by_layer[bottom_layer]
        
        if len(bottom_layer_nodes) > 1:
            # Get the orders of the parent layer (layer above bottom)
            if len(layer_numbers) > 1:
                parent_layer = layer_numbers[-2]
                # Use the current node_orders for parent positions
                bottom_layer_orders = order_bottom_layer_by_support(
                    bottom_layer_nodes, parents, node_orders
                )
                # Update the orders for the bottom layer
                node_orders.update(bottom_layer_orders)
    
    return node_orders


def count_edge_crossings(nodes_by_layer: Dict[int, List[str]],
                         edges: List[Dict[str, Any]],
                         node_orders: Dict[str, int],
                         node_layers: Dict[str, int]) -> int:
    """
    Count the number of edge crossings in the current layout.
    
    Two edges (u1, v1) and (u2, v2) cross if they connect between the same
    pair of layers and their endpoints are in different relative orders:
    - u1 is left of u2, but v1 is right of v2, OR
    - u1 is right of u2, but v1 is left of v2
    
    Args:
        nodes_by_layer: Dict mapping layer_number -> list of node IDs
        edges: List of edge dicts with 'source' and 'target' fields
        node_orders: Dict mapping node_id -> order position in its layer
        node_layers: Dict mapping node_id -> layer_number
        
    Returns:
        Total number of edge crossings
    """
    layer_numbers = sorted(nodes_by_layer.keys())
    crossing_count = 0
    
    # Group edges by layer pairs they connect
    edges_by_layer_pair = defaultdict(list)
    for edge in edges:
        src, tgt = edge['source'], edge['target']
        if src not in node_layers or tgt not in node_layers:
            continue
        src_layer = node_layers[src]
        tgt_layer = node_layers[tgt]
        if src_layer < tgt_layer:
            edges_by_layer_pair[(src_layer, tgt_layer)].append((src, tgt))
    
    # Count crossings for each layer pair
    for (layer1, layer2), edge_list in edges_by_layer_pair.items():
        # Compare all pairs of edges
        for i in range(len(edge_list)):
            for j in range(i + 1, len(edge_list)):
                u1, v1 = edge_list[i]
                u2, v2 = edge_list[j]
                
                # Get orders
                u1_order = node_orders.get(u1, 0)
                u2_order = node_orders.get(u2, 0)
                v1_order = node_orders.get(v1, 0)
                v2_order = node_orders.get(v2, 0)
                
                # Check if edges cross
                if (u1_order < u2_order and v1_order > v2_order) or \
                   (u1_order > u2_order and v1_order < v2_order):
                    crossing_count += 1
    
    return crossing_count


def compute_layout_positions(nodes: List[Dict[str, Any]], 
                             edges: List[Dict[str, Any]],
                             node_spacing: int = 250,
                             layer_separation: int = 200,
                             iterations: int = 8) -> Tuple[Dict[str, Tuple[int, int]], Dict[str, Any], Dict[str, int]]:
    """
    Compute optimized x/y positions for nodes to minimize edge crossings.
    
    This is the main entry point for the layout optimization pipeline:
    1. Assign nodes to layers (topological sort)
    2. Optimize ordering within layers (barycenter heuristic)
    3. Compute final x/y positions
    4. Calculate quality metrics
    
    Args:
        nodes: List of node dicts with 'id' field
        edges: List of edge dicts with 'source' and 'target' fields
        node_spacing: Horizontal spacing between nodes (default: 250)
        layer_separation: Vertical spacing between layers (default: 200)
        iterations: Number of barycenter sweep iterations (default: 8)
        
    Returns:
        Tuple of:
        - Dict mapping node_id -> (x, y) position
        - Dict with layout metrics: {'crossings': int, 'layers': int, 'max_layer_width': int}
        - Dict mapping node_id -> layer number (for determining which nodes are in top layer)
    """
    if not nodes:
        return {}, {'crossings': 0, 'layers': 0, 'max_layer_width': 0}, {}
    
    # Step 1: Assign layers
    node_layers = assign_layers(nodes, edges)
    
    # Group nodes by layer
    nodes_by_layer = defaultdict(list)
    for node in nodes:
        layer = node_layers[node['id']]
        nodes_by_layer[layer].append(node['id'])
    
    # Build adjacency lists for barycenter computation
    children = defaultdict(list)
    parents = defaultdict(list)
    node_ids = {node['id'] for node in nodes}
    
    for edge in edges:
        src, tgt = edge['source'], edge['target']
        if src in node_ids and tgt in node_ids:
            children[src].append(tgt)
            parents[tgt].append(src)
    
    # Step 2: Optimize ordering with barycenter heuristic
    node_orders = barycenter_ordering(nodes_by_layer, children, parents, iterations)
    
    # Step 3: Compute x/y positions
    positions = {}
    max_layer_width = 0
    
    for layer, node_list in nodes_by_layer.items():
        layer_width = len(node_list)
        max_layer_width = max(max_layer_width, layer_width)
        
        # Sort nodes by their optimized order
        sorted_nodes = sorted(node_list, key=lambda n: node_orders[n])
        
        # Center the layer horizontally
        total_width = (layer_width - 1) * node_spacing
        start_x = -total_width // 2 if layer_width > 1 else 0
        
        for i, node_id in enumerate(sorted_nodes):
            x = start_x + i * node_spacing
            y = layer * layer_separation
            positions[node_id] = (x, y)
    
    # Step 4: Compute quality metrics
    crossings = count_edge_crossings(nodes_by_layer, edges, node_orders, node_layers)
    
    metrics = {
        'crossings': crossings,
        'layers': len(nodes_by_layer),
        'max_layer_width': max_layer_width,
        'total_nodes': len(nodes),
        'total_edges': len(edges)
    }
    
    return positions, metrics, node_layers


def apply_layout_to_nodes(nodes: List[Dict[str, Any]], 
                          positions: Dict[str, Tuple[int, int]]) -> List[Dict[str, Any]]:
    """
    Apply computed positions to node list.
    
    Adds 'x' and 'y' fields to each node dict based on the computed layout.
    
    Args:
        nodes: List of node dicts with 'id' field
        positions: Dict mapping node_id -> (x, y) position
        
    Returns:
        List of nodes with x/y positions added (creates new dicts, doesn't modify originals)
    """
    result = []
    for node in nodes:
        node_copy = node.copy()
        if node['id'] in positions:
            x, y = positions[node['id']]
            node_copy['x'] = x
            node_copy['y'] = y
        result.append(node_copy)
    return result
