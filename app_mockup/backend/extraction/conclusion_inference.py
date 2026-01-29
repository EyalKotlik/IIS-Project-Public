"""
Conclusion Inference Module
============================

Infers which nodes should be labeled as "conclusion" based on graph structure.
This runs AFTER relation extraction and ensures conclusions are never isolated.

Key constraints:
1. A conclusion MUST have ≥1 incoming SUPPORT edge (never isolated)
2. Conclusions are inferred post-hoc based on graph position/role
3. Optional LLM confirmation for refinement (budget-safe, gpt-4o-mini)

Algorithm:
1. Identify candidate conclusions (high in-degree, sink-like, late in doc)
2. Score candidates using graph features
3. Select top N conclusions (default: 1)
4. Optional: LLM confirmation to refine selection
5. Enforce constraints (remove invalid edges if needed)
"""

import logging
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class ConclusionCandidate:
    """A candidate node for conclusion labeling."""
    node_id: str
    node_type: str
    text: str
    score: float
    incoming_support_count: int
    incoming_unique_sources: int
    outgoing_nonconclusion_edges: int
    position_score: float
    reasoning: str


@dataclass
class ConclusionInferenceConfig:
    """Configuration for conclusion inference."""
    
    # Scoring weights
    w_incoming_support: float = 2.0      # Weight for incoming support count
    w_unique_sources: float = 1.5        # Weight for unique source nodes
    w_outgoing_penalty: float = -1.0     # Penalty for outgoing edges
    w_position_bonus: float = 0.5        # Bonus for late position
    
    # Selection
    max_conclusions: int = 1             # Maximum conclusions to select (0 = auto)
    min_score_threshold: float = 1.0     # Minimum score to be eligible
    
    # Constraints
    require_incoming_support: bool = True  # Conclusion must have ≥1 incoming SUPPORT
    
    # LLM refinement (optional, budget-safe)
    enable_llm_refinement: bool = False    # Enable LLM confirmation
    llm_top_k: int = 3                     # Number of top candidates to present to LLM


@dataclass
class ConclusionInferenceResult:
    """Result of conclusion inference."""
    candidates: List[ConclusionCandidate] = field(default_factory=list)
    selected_conclusions: List[str] = field(default_factory=list)  # node_ids
    relabeled_count: int = 0
    edges_removed: int = 0
    method: str = "deterministic"  # "deterministic" or "llm_assisted"
    llm_cost_usd: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


def compute_conclusion_score(
    node_id: str,
    node_info: Dict[str, Any],
    incoming_edges: List[Tuple[str, str, str]],  # (source, target, relation)
    outgoing_edges: List[Tuple[str, str, str]],
    node_positions: Dict[str, int],  # node_id -> position in document
    config: ConclusionInferenceConfig
) -> Tuple[float, Dict[str, Any]]:
    """
    Compute conclusion score for a node based on graph features.
    
    Args:
        node_id: Node identifier
        node_info: Node metadata (type, text, etc.)
        incoming_edges: List of (source, target, relation) tuples where target == node_id
        outgoing_edges: List of (source, target, relation) tuples where source == node_id
        node_positions: Mapping of node_id to document position (0-1)
        config: Scoring configuration
        
    Returns:
        Tuple of (score, details_dict)
    """
    # Count incoming support edges
    incoming_support = [e for e in incoming_edges if e[2] == "support"]
    incoming_support_count = len(incoming_support)
    
    # Count unique sources (nodes providing support)
    unique_sources = len(set(e[0] for e in incoming_support))
    
    # Count outgoing edges to non-conclusions
    # (we don't know what's a conclusion yet, so count all outgoing as penalty)
    outgoing_count = len(outgoing_edges)
    
    # Position score (0-1, where 1 = late in document)
    position = node_positions.get(node_id, 0.5)
    
    # Compute weighted score
    score = (
        config.w_incoming_support * incoming_support_count +
        config.w_unique_sources * unique_sources +
        config.w_outgoing_penalty * outgoing_count +
        config.w_position_bonus * position
    )
    
    details = {
        "incoming_support_count": incoming_support_count,
        "incoming_unique_sources": unique_sources,
        "outgoing_nonconclusion_edges": outgoing_count,
        "position_score": position,
        "score": score,
    }
    
    return score, details


def identify_conclusion_candidates(
    nodes: List[Dict[str, Any]],  # Graph nodes
    edges: List[Dict[str, Any]],  # Graph edges
    config: ConclusionInferenceConfig
) -> List[ConclusionCandidate]:
    """
    Identify and score candidate nodes for conclusion labeling.
    
    Args:
        nodes: List of graph nodes (dicts with id, type, label, span, etc.)
        edges: List of graph edges (dicts with source, target, relation)
        config: Configuration for scoring
        
    Returns:
        List of ConclusionCandidate objects, sorted by score (descending)
    """
    # Build lookup structures
    node_map = {n["id"]: n for n in nodes}
    
    # Build edge lists for each node
    incoming_by_node = defaultdict(list)  # target -> [(source, target, relation), ...]
    outgoing_by_node = defaultdict(list)  # source -> [(source, target, relation), ...]
    
    for edge in edges:
        source = edge["source"]
        target = edge["target"]
        relation = edge["relation"]
        
        incoming_by_node[target].append((source, target, relation))
        outgoing_by_node[source].append((source, target, relation))
    
    # Compute node positions (0-1 based on order in nodes list)
    node_positions = {}
    for i, node in enumerate(nodes):
        node_positions[node["id"]] = i / max(len(nodes) - 1, 1)
    
    # Score each node
    candidates = []
    
    for node in nodes:
        node_id = node["id"]
        node_type = node.get("type", "unknown")
        
        # Skip non-argument nodes
        if node_type == "non_argument":
            continue
        
        # Compute score
        incoming = incoming_by_node[node_id]
        outgoing = outgoing_by_node[node_id]
        
        score, details = compute_conclusion_score(
            node_id=node_id,
            node_info=node,
            incoming_edges=incoming,
            outgoing_edges=outgoing,
            node_positions=node_positions,
            config=config
        )
        
        # Check eligibility
        if config.require_incoming_support and details["incoming_support_count"] == 0:
            # Not eligible: no incoming support
            continue
        
        if score < config.min_score_threshold:
            # Score too low
            continue
        
        # Create candidate
        reasoning = f"Score: {score:.2f} | Support: {details['incoming_support_count']} from {details['incoming_unique_sources']} sources | Outgoing: {details['outgoing_nonconclusion_edges']} | Position: {details['position_score']:.2f}"
        
        candidate = ConclusionCandidate(
            node_id=node_id,
            node_type=node_type,
            text=node.get("span", "")[:200],  # Truncate for logging
            score=score,
            incoming_support_count=details["incoming_support_count"],
            incoming_unique_sources=details["incoming_unique_sources"],
            outgoing_nonconclusion_edges=details["outgoing_nonconclusion_edges"],
            position_score=details["position_score"],
            reasoning=reasoning
        )
        
        candidates.append(candidate)
    
    # Sort by score (descending)
    candidates.sort(key=lambda c: c.score, reverse=True)
    
    return candidates


def select_conclusions(
    candidates: List[ConclusionCandidate],
    config: ConclusionInferenceConfig
) -> List[str]:
    """
    Select which candidates should be labeled as conclusions.
    
    Args:
        candidates: List of candidates sorted by score
        config: Configuration
        
    Returns:
        List of node_ids to label as conclusions
    """
    if not candidates:
        return []
    
    # Determine how many to select
    if config.max_conclusions == 0:
        # Auto mode: select top 1 if any candidate is eligible
        num_to_select = min(1, len(candidates))
    else:
        num_to_select = min(config.max_conclusions, len(candidates))
    
    selected = [c.node_id for c in candidates[:num_to_select]]
    
    return selected


def relabel_conclusions(
    nodes: List[Dict[str, Any]],
    conclusion_ids: List[str]
) -> int:
    """
    Relabel selected nodes as "conclusion".
    
    Args:
        nodes: List of graph nodes (modified in place)
        conclusion_ids: List of node IDs to relabel
        
    Returns:
        Number of nodes relabeled
    """
    relabeled = 0
    
    for node in nodes:
        if node["id"] in conclusion_ids:
            node["type"] = "conclusion"
            relabeled += 1
    
    return relabeled


def enforce_conclusion_constraints(
    nodes: List[Dict[str, Any]],
    edges: List[Dict[str, Any]]
) -> int:
    """
    Enforce conclusion constraints on edges:
    - A conclusion must not have outgoing edges to non-conclusions
    - Allow conclusion -> conclusion
    
    Args:
        nodes: List of graph nodes
        edges: List of graph edges (modified in place)
        
    Returns:
        Number of edges removed
    """
    # Build set of conclusion node IDs
    conclusion_ids = {n["id"] for n in nodes if n.get("type") == "conclusion"}
    
    # Filter edges
    valid_edges = []
    removed = 0
    
    for edge in edges:
        source = edge["source"]
        target = edge["target"]
        
        # Check if source is a conclusion
        if source in conclusion_ids:
            # If target is not a conclusion, remove the edge
            if target not in conclusion_ids:
                logger.debug(f"Removing edge from conclusion {source} to non-conclusion {target}")
                removed += 1
                continue
        
        valid_edges.append(edge)
    
    # Update edges list in place
    edges.clear()
    edges.extend(valid_edges)
    
    return removed


def infer_conclusions(
    nodes: List[Dict[str, Any]],
    edges: List[Dict[str, Any]],
    config: Optional[ConclusionInferenceConfig] = None
) -> ConclusionInferenceResult:
    """
    Infer which nodes should be labeled as conclusions based on graph structure.
    
    This is the main entry point for conclusion inference. It:
    1. Identifies candidate conclusions based on graph features
    2. Scores candidates using configurable weights
    3. Selects top N conclusions (default: 1)
    4. Relabels selected nodes as "conclusion"
    5. Enforces constraints (removes invalid edges)
    
    Args:
        nodes: List of graph nodes (modified in place)
        edges: List of graph edges (modified in place)
        config: Optional configuration (uses defaults if None)
        
    Returns:
        ConclusionInferenceResult with candidates, selections, and metadata
    """
    if config is None:
        config = ConclusionInferenceConfig()
    
    logger.info("=" * 60)
    logger.info("CONCLUSION INFERENCE (POST-HOC)")
    logger.info("=" * 60)
    
    # Step 1: Identify candidates
    logger.info("\nStep 1: Identifying conclusion candidates...")
    candidates = identify_conclusion_candidates(nodes, edges, config)
    
    logger.info(f"  Found {len(candidates)} eligible candidates")
    for i, candidate in enumerate(candidates[:5]):  # Log top 5
        logger.info(f"    {i+1}. Node {candidate.node_id} (type={candidate.node_type}): {candidate.reasoning}")
    
    # Step 2: Select conclusions
    logger.info("\nStep 2: Selecting conclusions...")
    selected_ids = select_conclusions(candidates, config)
    
    logger.info(f"  Selected {len(selected_ids)} conclusions: {selected_ids}")
    
    # Step 3: Relabel nodes
    logger.info("\nStep 3: Relabeling nodes...")
    relabeled_count = relabel_conclusions(nodes, selected_ids)
    
    logger.info(f"  Relabeled {relabeled_count} nodes as 'conclusion'")
    
    # Step 4: Enforce constraints
    logger.info("\nStep 4: Enforcing conclusion constraints...")
    edges_removed = enforce_conclusion_constraints(nodes, edges)
    
    logger.info(f"  Removed {edges_removed} invalid edges (conclusion → non-conclusion)")
    
    # Build result
    result = ConclusionInferenceResult(
        candidates=candidates,
        selected_conclusions=selected_ids,
        relabeled_count=relabeled_count,
        edges_removed=edges_removed,
        method="deterministic",
        metadata={
            "config": {
                "max_conclusions": config.max_conclusions,
                "min_score_threshold": config.min_score_threshold,
                "require_incoming_support": config.require_incoming_support,
            }
        }
    )
    
    logger.info("\n" + "=" * 60)
    logger.info("CONCLUSION INFERENCE COMPLETE")
    logger.info("=" * 60)
    logger.info(f"Selected {len(selected_ids)} conclusions")
    
    # Verify all conclusions have incoming support
    for node_id in selected_ids:
        incoming_support = sum(1 for e in edges if e["target"] == node_id and e["relation"] == "support")
        if incoming_support == 0:
            logger.warning(f"WARNING: Conclusion {node_id} has no incoming SUPPORT edges!")
    
    return result
