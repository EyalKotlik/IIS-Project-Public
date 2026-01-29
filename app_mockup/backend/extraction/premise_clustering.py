"""
Premise Clustering Module
==========================

Identifies clusters of related premises that share a theme and support
the same target claim. These clusters are candidates for synthetic claim
generation.

Clustering Strategy:
1. Same paragraph or within sentence window
2. High lexical/semantic similarity
3. Same target claim
4. Minimum cluster size threshold
"""

import logging
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from collections import defaultdict

from ..graph_construction import GraphNode, GraphEdge

# Try to import RapidFuzz for text similarity
try:
    from rapidfuzz import fuzz
    RAPIDFUZZ_AVAILABLE = True
except ImportError:
    RAPIDFUZZ_AVAILABLE = False
    logging.warning("RapidFuzz not available for premise clustering, falling back to Jaccard similarity")

logger = logging.getLogger(__name__)


@dataclass
class PremiseCluster:
    """A cluster of related premises."""
    
    cluster_id: str
    premise_ids: List[str]
    premise_texts: List[str]
    target_claim_id: Optional[str] = None
    target_claim_text: Optional[str] = None
    coherence_score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ClusteringConfig:
    """Configuration for premise clustering."""
    
    # Window-based clustering
    max_sentence_distance: int = 3  # Max distance between premises in same cluster
    same_paragraph_only: bool = False
    
    # Similarity thresholds
    min_text_similarity: float = 0.3  # Lower than merge threshold (0.85)
    use_similarity_clustering: bool = True
    
    # Cluster size constraints
    min_cluster_size: int = 2  # Minimum premises per cluster
    max_cluster_size: int = 10  # Maximum premises per cluster
    
    # Target claim constraints
    require_same_target: bool = True  # Premises must support same target
    
    # Node type filtering
    only_cluster_premises: bool = True  # Only cluster nodes of type "premise"


def normalize_text(text: str) -> str:
    """
    Normalize text for similarity comparison.
    
    Args:
        text: Input text
        
    Returns:
        Normalized text (lowercase, stripped, compressed whitespace)
    """
    import re
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)  # Remove punctuation
    text = re.sub(r'\s+', ' ', text)     # Compress whitespace
    return text.strip()


def compute_text_similarity(text1: str, text2: str) -> float:
    """
    Compute similarity between two texts.
    
    Uses RapidFuzz token_sort_ratio if available, otherwise simple Jaccard.
    
    Args:
        text1: First text
        text2: Second text
        
    Returns:
        Similarity score (0-1)
    """
    if RAPIDFUZZ_AVAILABLE:
        # Use RapidFuzz token sort ratio (handles word order differences)
        return fuzz.token_sort_ratio(text1, text2) / 100.0
    else:
        # Fallback to simple Jaccard similarity
        tokens1 = set(text1.lower().split())
        tokens2 = set(text2.lower().split())
        if not tokens1 or not tokens2:
            return 0.0
        intersection = len(tokens1 & tokens2)
        union = len(tokens1 | tokens2)
        return intersection / union if union > 0 else 0.0


def extract_sentence_number(node_id: str) -> Optional[int]:
    """
    Extract sentence number from node ID or sentence_id.
    
    Args:
        node_id: Node ID (e.g., "n_abc123") or sentence_id (e.g., "s5")
        
    Returns:
        Sentence number or None if not extractable
    """
    # Try to extract from formats like "s5" or similar
    import re
    match = re.search(r's(\d+)', node_id.lower())
    if match:
        return int(match.group(1))
    return None


def build_support_graph(nodes: List[GraphNode], edges: List[GraphEdge]) -> Dict[str, Set[str]]:
    """
    Build a mapping of node_id -> set of target_ids it supports.
    
    Args:
        nodes: List of graph nodes
        edges: List of graph edges
        
    Returns:
        Dictionary mapping node_id to set of target node IDs
    """
    support_map = defaultdict(set)
    
    for edge in edges:
        if edge.relation == "support":
            support_map[edge.source].add(edge.target)
    
    return support_map


def find_premise_clusters(
    nodes: List[GraphNode],
    edges: List[GraphEdge],
    config: Optional[ClusteringConfig] = None
) -> List[PremiseCluster]:
    """
    Find clusters of related premises using heuristic-based approach.
    
    Clustering strategy:
    1. Filter to premise nodes only
    2. Group by target claim (what they support)
    3. Within each target group, cluster by proximity and similarity
    4. Apply size constraints
    
    Args:
        nodes: List of graph nodes
        edges: List of graph edges
        config: Optional clustering configuration
        
    Returns:
        List of premise clusters
    """
    if config is None:
        config = ClusteringConfig()
    
    logger.info("=" * 60)
    logger.info("PREMISE CLUSTERING")
    logger.info("=" * 60)
    
    # Filter to premise nodes
    if config.only_cluster_premises:
        premise_nodes = [n for n in nodes if n.type == "premise" and not n.is_synthetic]
    else:
        premise_nodes = [n for n in nodes if not n.is_synthetic]
    
    if len(premise_nodes) < config.min_cluster_size:
        logger.info(f"Insufficient premise nodes ({len(premise_nodes)}) for clustering")
        return []
    
    logger.info(f"Clustering {len(premise_nodes)} premise nodes")
    
    # Build support graph
    support_map = build_support_graph(nodes, edges)
    
    # Group premises by their target claims
    target_groups = defaultdict(list)
    for premise in premise_nodes:
        targets = support_map.get(premise.id, set())
        
        if not targets and config.require_same_target:
            # Skip premises with no targets
            continue
        
        # Use first target as grouping key (most premises support one main claim)
        target_key = next(iter(targets)) if targets else "no_target"
        target_groups[target_key].append(premise)
    
    logger.info(f"Grouped premises into {len(target_groups)} target groups")
    
    # Cluster within each target group
    all_clusters = []
    cluster_counter = 0
    
    for target_id, group_premises in target_groups.items():
        if len(group_premises) < config.min_cluster_size:
            logger.debug(f"Skipping target {target_id}: only {len(group_premises)} premises")
            continue
        
        # Get target claim node
        target_node = next((n for n in nodes if n.id == target_id), None)
        target_text = target_node.span if target_node else None
        
        # Cluster by proximity and similarity
        clusters = _cluster_by_proximity_and_similarity(
            group_premises, config
        )
        
        # Create PremiseCluster objects
        for cluster_premises in clusters:
            if len(cluster_premises) < config.min_cluster_size:
                continue
            
            if len(cluster_premises) > config.max_cluster_size:
                logger.debug(f"Cluster too large ({len(cluster_premises)}), skipping")
                continue
            
            cluster = PremiseCluster(
                cluster_id=f"cluster_{cluster_counter}",
                premise_ids=[p.id for p in cluster_premises],
                premise_texts=[p.span for p in cluster_premises],
                target_claim_id=target_id if target_id != "no_target" else None,
                target_claim_text=target_text,
                coherence_score=_compute_cluster_coherence(cluster_premises),
                metadata={
                    "size": len(cluster_premises),
                    "target": target_id
                }
            )
            
            all_clusters.append(cluster)
            cluster_counter += 1
    
    logger.info(f"Found {len(all_clusters)} premise clusters")
    for i, cluster in enumerate(all_clusters):
        logger.debug(f"  Cluster {i}: {len(cluster.premise_ids)} premises, "
                    f"coherence={cluster.coherence_score:.2f}")
    
    return all_clusters


def _cluster_by_proximity_and_similarity(
    premises: List[GraphNode],
    config: ClusteringConfig
) -> List[List[GraphNode]]:
    """
    Cluster premises by proximity and text similarity.
    
    Uses a greedy approach:
    1. Sort premises by position (if available)
    2. Start with first premise as seed
    3. Add nearby/similar premises to cluster
    4. Repeat with remaining premises
    
    Args:
        premises: List of premise nodes to cluster
        config: Clustering configuration
        
    Returns:
        List of premise clusters (each cluster is a list of nodes)
    """
    if not premises:
        return []
    
    # Extract sentence positions if available
    premise_positions = {}
    for premise in premises:
        sent_num = extract_sentence_number(premise.sentence_id or premise.id)
        if sent_num is not None:
            premise_positions[premise.id] = sent_num
    
    # Sort by position if available
    if premise_positions:
        premises = sorted(premises, key=lambda p: premise_positions.get(p.id, float('inf')))
    
    clusters = []
    remaining = premises.copy()
    
    while remaining:
        # Start new cluster with first remaining premise
        seed = remaining.pop(0)
        cluster = [seed]
        
        # Find premises to add to this cluster
        to_remove = []
        for i, premise in enumerate(remaining):
            # Check proximity
            if premise_positions:
                seed_pos = premise_positions.get(seed.id)
                prem_pos = premise_positions.get(premise.id)
                if seed_pos is not None and prem_pos is not None:
                    distance = abs(seed_pos - prem_pos)
                    if distance > config.max_sentence_distance:
                        continue
            
            # Check similarity if enabled
            if config.use_similarity_clustering:
                similarity = compute_text_similarity(
                    normalize_text(seed.span),
                    normalize_text(premise.span)
                )
                if similarity < config.min_text_similarity:
                    continue
            
            # Add to cluster
            cluster.append(premise)
            to_remove.append(i)
        
        # Remove added premises from remaining (in reverse to preserve indices)
        for i in reversed(to_remove):
            remaining.pop(i)
        
        clusters.append(cluster)
    
    return clusters


def _compute_cluster_coherence(premises: List[GraphNode]) -> float:
    """
    Compute coherence score for a cluster of premises.
    
    Simple heuristic: average pairwise similarity.
    
    Args:
        premises: List of premise nodes
        
    Returns:
        Coherence score (0-1)
    """
    if len(premises) < 2:
        return 1.0  # Single premise is perfectly coherent with itself
    
    similarities = []
    for i, p1 in enumerate(premises):
        for p2 in premises[i+1:]:
            sim = compute_text_similarity(
                normalize_text(p1.span),
                normalize_text(p2.span)
            )
            similarities.append(sim)
    
    return sum(similarities) / len(similarities) if similarities else 0.0


def get_clustering_stats(clusters: List[PremiseCluster]) -> Dict[str, Any]:
    """
    Compute statistics about premise clusters.
    
    Args:
        clusters: List of premise clusters
        
    Returns:
        Dictionary with clustering statistics
    """
    if not clusters:
        return {
            "total_clusters": 0,
            "total_premises": 0,
            "avg_cluster_size": 0.0,
            "min_cluster_size": 0,
            "max_cluster_size": 0,
            "avg_coherence": 0.0,
        }
    
    cluster_sizes = [len(c.premise_ids) for c in clusters]
    total_premises = sum(cluster_sizes)
    
    return {
        "total_clusters": len(clusters),
        "total_premises": total_premises,
        "avg_cluster_size": total_premises / len(clusters),
        "min_cluster_size": min(cluster_sizes),
        "max_cluster_size": max(cluster_sizes),
        "avg_coherence": sum(c.coherence_score for c in clusters) / len(clusters),
    }
