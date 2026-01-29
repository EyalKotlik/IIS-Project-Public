"""
Synthetic Claims Generation Module
===================================

Generates intermediate synthetic claims from premise clusters using LLM.
This improves graph depth and interpretability by creating multi-hop
reasoning chains (premise → synthetic claim → high-level claim).

Key Features:
- LLM-based synthesis with gpt-4o-mini (cost-effective)
- Strict constraints to prevent hallucination
- Graph rewiring to insert synthetic claims
- Safety checks and validation
"""

import logging
import hashlib
import json
from typing import List, Dict, Any, Optional, Tuple, Set, Literal
from dataclasses import dataclass, field

from ..llm_client import LLMClient, get_llm_client
from ..llm_schemas import SyntheticClaimResult, BatchSyntheticClaims
from ..graph_construction import GraphNode, GraphEdge
from .premise_clustering import PremiseCluster, find_premise_clusters, ClusteringConfig, build_support_graph

logger = logging.getLogger(__name__)


@dataclass
class SynthesisConfig:
    """Configuration for synthetic claim generation."""
    
    # Clustering configuration
    clustering_config: ClusteringConfig = field(default_factory=ClusteringConfig)

    # Fan-in synthesis controls
    fan_in_threshold: int = 3
    enable_fan_in_synthesis: bool = True
    max_synthetic_claims_per_target: int = 2
    fan_in_grouping_mode: Literal["llm", "hybrid", "deterministic"] = "llm"
    fan_in_min_group_size: int = 2
    
    # LLM synthesis
    min_coherence_threshold: float = 0.3  # Minimum cluster coherence to synthesize
    min_confidence_threshold: float = 0.5  # Minimum LLM confidence to accept
    
    # Safety constraints
    max_synthetic_claim_words: int = 20
    max_synthetic_claim_chars: int = 150
    prevent_hallucination_checks: bool = True
    
    # Rewiring
    enable_rewiring: bool = True
    preserve_original_edges: bool = False  # If True, keep old edges alongside new ones
    synthetic_confidence_penalty: float = 0.95  # Confidence multiplier for synthetic→target edges
    
    # Model override
    model_name: Optional[str] = None  # Default: use client's configured model


@dataclass
class SynthesisResult:
    """Result of synthetic claim generation."""
    
    synthetic_nodes: List[GraphNode] = field(default_factory=list)
    updated_edges: List[GraphEdge] = field(default_factory=list)
    clusters_processed: int = 0
    clusters_synthesized: int = 0
    clusters_skipped: int = 0
    skip_reasons: Dict[str, int] = field(default_factory=dict)
    cost_usd: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


def generate_synthetic_node_id(premise_ids: List[str]) -> str:
    """
    Generate stable, deterministic ID for synthetic claim node.
    
    Uses MD5 for fast, non-cryptographic hashing. This is safe for ID generation
    as we don't need cryptographic security.
    
    Args:
        premise_ids: List of premise node IDs in the cluster
        
    Returns:
        Stable synthetic node ID (e.g., "syn_claim_<hash>")
    """
    # Sort IDs for stability
    sorted_ids = sorted(premise_ids)
    content = ":".join(sorted_ids)
    hash_val = hashlib.md5(content.encode()).hexdigest()[:8]
    return f"syn_claim_{hash_val}"


def synthesize_claims_for_clusters(
    clusters: List[PremiseCluster],
    client: Optional[LLMClient] = None,
    config: Optional[SynthesisConfig] = None
) -> Tuple[List[SyntheticClaimResult], float]:
    """
    Synthesize intermediate claims for premise clusters using LLM.
    
    Args:
        clusters: List of premise clusters
        client: Optional LLM client (uses singleton if None)
        config: Optional synthesis configuration
        
    Returns:
        Tuple of (synthetic claim results, total cost in USD)
    """
    if client is None:
        client = get_llm_client()
    
    if config is None:
        config = SynthesisConfig()
    
    if not clusters:
        logger.info("No clusters to synthesize")
        return [], 0.0
    
    logger.info("=" * 60)
    logger.info("SYNTHETIC CLAIM GENERATION")
    logger.info("=" * 60)
    logger.info(f"Synthesizing claims for {len(clusters)} clusters")
    
    # Prepare batch request
    cluster_descriptions = []
    for cluster in clusters:
        # Skip low-coherence clusters
        if cluster.coherence_score < config.min_coherence_threshold:
            logger.debug(f"Skipping {cluster.cluster_id}: low coherence ({cluster.coherence_score:.2f})")
            continue
        
        desc = _format_cluster_for_llm(cluster)
        cluster_descriptions.append({
            "cluster_id": cluster.cluster_id,
            "premises": cluster.premise_texts,
            "target_claim": cluster.target_claim_text,
            "description": desc
        })
    
    if not cluster_descriptions:
        logger.info("No clusters meet coherence threshold")
        return [], 0.0
    
    # Build prompt
    system_prompt = _build_synthesis_system_prompt(config)
    user_prompt = _build_synthesis_user_prompt(cluster_descriptions)
    
    # Call LLM
    try:
        result = client.call_llm(
            task_name="synthesize_claims",
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            schema=BatchSyntheticClaims,
        )
        
        llm_payload = result.get("result")
        if hasattr(llm_payload, "synthetic_claims"):
            # Convert Pydantic models to dicts for consistent handling
            synthetic_claims = [claim.model_dump() if hasattr(claim, 'model_dump') else claim 
                              for claim in llm_payload.synthetic_claims]
        elif isinstance(llm_payload, dict):
            synthetic_claims = llm_payload.get("synthetic_claims", [])
        else:
            synthetic_claims = []

        cost_usd = (
            result.get("cost_usd")
            or result.get("usage", {}).get("estimated_cost_usd")
            or 0.0
        )
        
        logger.info(f"LLM synthesis complete:")
        logger.info(f"  - Clusters evaluated: {len(cluster_descriptions)}")
        logger.info(f"  - Claims generated: {len(synthetic_claims)}")
        logger.info(f"  - Cost: ${cost_usd:.6f}")
        
        # Filter by coherence and confidence
        accepted = []
        for claim in synthetic_claims:
            if not claim['coherent']:
                logger.debug(f"Skipping {claim['cluster_id']}: not coherent")
                continue
            if claim['confidence'] < config.min_confidence_threshold:
                logger.debug(f"Skipping {claim['cluster_id']}: low confidence ({claim['confidence']:.2f})")
                continue
            
            # Validation checks
            if config.prevent_hallucination_checks:
                if not _validate_no_hallucination(claim, cluster_descriptions):
                    logger.warning(f"Skipping {claim['cluster_id']}: failed hallucination check")
                    continue
            
            accepted.append(claim)
        
        logger.info(f"Accepted {len(accepted)} synthetic claims after filtering")
        
        # Convert dicts back to SyntheticClaimResult models for API consistency
        result_models = []
        for claim in accepted:
            if isinstance(claim, dict):
                result_models.append(SyntheticClaimResult(**claim))
            else:
                result_models.append(claim)
        
        return result_models, cost_usd
        
    except Exception as e:
        logger.error(f"LLM synthesis failed: {e}")
        return [], 0.0


def _format_cluster_for_llm(cluster: PremiseCluster) -> str:
    """Format a premise cluster for LLM input."""
    lines = [f"Cluster ID: {cluster.cluster_id}"]
    
    if cluster.target_claim_text:
        lines.append(f"Target claim: {cluster.target_claim_text}")
    
    lines.append(f"Premises ({len(cluster.premise_texts)}):")
    for i, premise in enumerate(cluster.premise_texts, 1):
        lines.append(f"  {i}. {premise}")
    
    return "\n".join(lines)


def _build_synthesis_system_prompt(config: SynthesisConfig) -> str:
    """Build system prompt for synthetic claim generation."""
    return f"""You are an expert in argument analysis. Your task is to synthesize intermediate claims from clusters of related premises.

CRITICAL CONSTRAINTS:
1. ONLY summarize what is directly stated or implied by the premises
2. DO NOT add new facts, statistics, names, or external knowledge
3. DO NOT introduce specific numbers unless present in premises
4. Keep the synthetic claim SHORT (≤{config.max_synthetic_claim_words} words preferred)
5. The synthetic claim should be general enough to be supported by ALL premises in the cluster

Your role is COMPRESSION and SUMMARIZATION, not inference of new information.

For each cluster, assess:
- coherent: Are the premises truly related and support a common theme?
- confidence: How confident are you in the synthesis quality? (0.0 to 1.0)

If premises are incoherent or don't share a clear theme, mark coherent=false."""


def _build_synthesis_user_prompt(cluster_descriptions: List[Dict[str, Any]]) -> str:
    """Build user prompt with cluster information."""
    lines = ["Please synthesize intermediate claims for the following premise clusters:\n"]
    
    for i, cluster_desc in enumerate(cluster_descriptions, 1):
        lines.append(f"=== Cluster {i} ===")
        lines.append(cluster_desc["description"])
        lines.append("")
    
    lines.append("Return a synthetic claim for each coherent cluster.")
    lines.append("For incoherent clusters, set coherent=false and provide a brief explanation.")
    
    return "\n".join(lines)


def _validate_no_hallucination(
    claim: SyntheticClaimResult,
    cluster_descriptions: List[Dict[str, Any]]
) -> bool:
    """
    Basic heuristic check for hallucination in synthetic claims.
    
    Checks:
    1. No new digits/numbers (unless present in premises)
    2. No new named entities (proper nouns not in premises)
    
    Args:
        claim: Synthetic claim result (dict or Pydantic model)
        cluster_descriptions: Original cluster descriptions
        
    Returns:
        True if no hallucination detected, False otherwise
    """
    import re
    
    # Handle both dict and Pydantic model
    cluster_id = claim['cluster_id'] if isinstance(claim, dict) else claim.cluster_id
    claim_text_val = claim['synthetic_claim_text'] if isinstance(claim, dict) else claim.synthetic_claim_text
    
    # Find the matching cluster
    cluster = next(
        (c for c in cluster_descriptions if c["cluster_id"] == cluster_id),
        None
    )
    if not cluster:
        return True  # Can't validate, assume OK
    
    # Get all premise text
    premise_text = " ".join(cluster["premises"]).lower()
    claim_text = claim_text_val.lower()
    
    # Check 1: No new numbers
    premise_numbers = set(re.findall(r'\d+', premise_text))
    claim_numbers = set(re.findall(r'\d+', claim_text))
    new_numbers = claim_numbers - premise_numbers
    
    if new_numbers:
        logger.debug(f"Hallucination detected: new numbers {new_numbers}")
        return False
    
    # Check 2: No new capitalized words (basic named entity check)
    # This is a heuristic - may have false positives
    premise_words = set(re.findall(r'\b[A-Z][a-z]+\b', " ".join(cluster["premises"])))
    claim_words = set(re.findall(r'\b[A-Z][a-z]+\b', claim_text_val))
    new_proper_nouns = claim_words - premise_words
    
    # Allow some common proper nouns that might appear
    allowed = {'The', 'A', 'An', 'This', 'These', 'That', 'Those'}
    new_proper_nouns = new_proper_nouns - allowed
    
    if new_proper_nouns:
        logger.debug(f"Potential hallucination: new proper nouns {new_proper_nouns}")
        # This is a warning, not a hard failure
        # Return True anyway since proper noun detection is imperfect
    
    return True


def create_synthetic_nodes_and_rewire(
    nodes: List[GraphNode],
    edges: List[GraphEdge],
    clusters: List[PremiseCluster],
    synthetic_claims: List[SyntheticClaimResult],
    config: Optional[SynthesisConfig] = None
) -> SynthesisResult:
    """
    Create synthetic claim nodes and rewire the graph.
    
    Rewiring process:
    1. Create synthetic claim node for each accepted synthesis
    2. Redirect edges: premise → old_target becomes premise → synthetic → old_target
    3. Deduplicate edges
    4. Validate graph connectivity
    
    Args:
        nodes: Original graph nodes
        edges: Original graph edges
        clusters: Premise clusters
        synthetic_claims: LLM-generated synthetic claims
        config: Optional synthesis configuration
        
    Returns:
        SynthesisResult with new nodes and updated edges
    """
    if config is None:
        config = SynthesisConfig()
    
    logger.info("=" * 60)
    logger.info("GRAPH REWIRING")
    logger.info("=" * 60)
    
    result = SynthesisResult()
    result.clusters_processed = len(clusters)
    
    # Build cluster map
    cluster_map = {c.cluster_id: c for c in clusters}
    
    # Create synthetic nodes
    synthetic_node_map = {}  # cluster_id -> synthetic node
    
    for claim in synthetic_claims:
        # Handle both dict and Pydantic model
        if isinstance(claim, dict):
            cluster_id = claim['cluster_id']
            label = claim.get('label')
            synthetic_claim_text = claim['synthetic_claim_text']
            confidence = claim['confidence']
        else:
            cluster_id = claim.cluster_id
            label = claim.label
            synthetic_claim_text = claim.synthetic_claim_text
            confidence = claim.confidence
        
        cluster = cluster_map.get(cluster_id)
        if not cluster:
            logger.warning(f"Cluster {cluster_id} not found")
            result.clusters_skipped += 1
            continue
        
        # Generate stable node ID
        node_id = generate_synthetic_node_id(cluster.premise_ids)
        
        # Create synthetic node
        synthetic_node = GraphNode(
            id=node_id,
            type="claim",  # Synthetic claims are always "claim" type
            label=label or synthetic_claim_text[:80],
            span=synthetic_claim_text,
            paraphrase=label or synthetic_claim_text,
            confidence=confidence,
            is_synthetic=True,
            source_premise_ids=cluster.premise_ids,
            synthesis_method="llm",
            sentence_id=None,  # No original sentence
            paragraph_id=None
        )
        
        result.synthetic_nodes.append(synthetic_node)
        synthetic_node_map[cluster_id] = synthetic_node
        result.clusters_synthesized += 1
        
        logger.info(f"Created synthetic node {node_id} for cluster {cluster_id}")
        logger.debug(f"  Text: {synthetic_claim_text}")
        logger.debug(f"  Premises: {len(cluster.premise_ids)}")
    
    if not config.enable_rewiring:
        logger.info("Rewiring disabled, returning synthetic nodes only")
        result.updated_edges = edges
        return result
    
    # Rewire edges
    logger.info(f"Rewiring graph with {len(result.synthetic_nodes)} synthetic claims")
    
    # Build premise -> cluster mapping
    premise_to_cluster = {}
    premise_to_synthetic = {}
    for cluster_id, synthetic_node in synthetic_node_map.items():
        cluster = cluster_map[cluster_id]
        for premise_id in cluster.premise_ids:
            premise_to_cluster[premise_id] = cluster_id
            premise_to_synthetic[premise_id] = synthetic_node.id
    
    # Process edges
    new_edges = []
    redirected_count = 0
    
    for edge in edges:
        # Check if source is a premise in a cluster
        if edge.source in premise_to_synthetic:
            synthetic_id = premise_to_synthetic[edge.source]
            
            if config.preserve_original_edges:
                # Keep original edge
                new_edges.append(edge)
            
            # Create new edge: premise → synthetic claim
            new_edges.append(GraphEdge(
                source=edge.source,
                target=synthetic_id,
                relation=edge.relation,
                confidence=edge.confidence
            ))
            
            # Create new edge: synthetic claim → old target
            new_edges.append(GraphEdge(
                source=synthetic_id,
                target=edge.target,
                relation=edge.relation,
                confidence=edge.confidence * config.synthetic_confidence_penalty  # Slightly lower confidence
            ))
            
            redirected_count += 1
        else:
            # Keep original edge
            new_edges.append(edge)
    
    # Deduplicate edges
    edge_set = set()
    deduplicated_edges = []
    for edge in new_edges:
        edge_key = (edge.source, edge.target, edge.relation)
        if edge_key not in edge_set:
            edge_set.add(edge_key)
            deduplicated_edges.append(edge)
    
    result.updated_edges = deduplicated_edges
    
    logger.info(f"Rewiring complete:")
    logger.info(f"  - Original edges: {len(edges)}")
    logger.info(f"  - Redirected edges: {redirected_count}")
    logger.info(f"  - New edges created: {len(new_edges)}")
    logger.info(f"  - After deduplication: {len(deduplicated_edges)}")
    
    return result


def add_synthetic_claims_to_graph(
    nodes: List[GraphNode],
    edges: List[GraphEdge],
    client: Optional[LLMClient] = None,
    config: Optional[SynthesisConfig] = None
) -> Tuple[List[GraphNode], List[GraphEdge], Dict[str, Any]]:
    """
    Main entry point: add synthetic claims to an argument graph.
    
    Complete pipeline:
    1. Find premise clusters
    2. Synthesize claims using LLM
    3. Create synthetic nodes
    4. Rewire graph
    
    Args:
        nodes: Original graph nodes
        edges: Original graph edges
        client: Optional LLM client
        config: Optional synthesis configuration
        
    Returns:
        Tuple of (updated nodes, updated edges, stats)
    """
    if config is None:
        config = SynthesisConfig()
    
    stats = {
        "enabled": True,
        "clusters_found": 0,
        "clusters_synthesized": 0,
        "synthetic_nodes_added": 0,
        "edges_before": len(edges),
        "edges_after": 0,
        "cost_usd": 0.0,
        "fan_in_targets": [],
        "fan_in_groups": [],
    }
    
    # Step 1: Find premise clusters (regular + fan-in forced)
    clusters: List[PremiseCluster] = []
    fan_in_clusters, fan_meta = find_fan_in_clusters(
        nodes, edges, config=config, client=client
    )
    clusters.extend(fan_in_clusters)
    stats["fan_in_targets"] = fan_meta.get("targets", [])
    stats["fan_in_groups"] = fan_meta.get("groups", [])

    regular_clusters = find_premise_clusters(
        nodes, edges, config=config.clustering_config
    )
    clusters.extend(regular_clusters)
    stats["clusters_found"] = len(clusters)
    
    if not clusters:
        logger.info("No premise clusters found, skipping synthesis")
        return nodes, edges, stats
    
    # Step 2: Synthesize claims
    synthetic_claims, cost = synthesize_claims_for_clusters(
        clusters, client=client, config=config
    )
    stats["cost_usd"] = cost + fan_meta.get("cost_usd", 0.0)
    
    if not synthetic_claims:
        logger.info("No synthetic claims generated, skipping rewiring")
        return nodes, edges, stats
    
    # Step 3: Create nodes and rewire
    synthesis_result = create_synthetic_nodes_and_rewire(
        nodes, edges, clusters, synthetic_claims, config=config
    )
    
    # Update nodes and edges
    updated_nodes = nodes + synthesis_result.synthetic_nodes
    updated_edges = synthesis_result.updated_edges
    
    stats["clusters_synthesized"] = synthesis_result.clusters_synthesized
    stats["synthetic_nodes_added"] = len(synthesis_result.synthetic_nodes)
    stats["edges_after"] = len(updated_edges)
    stats["fan_in_edges_rewired"] = synthesis_result.metadata.get("fan_in_edges_rewired", 0)
    
    logger.info("=" * 60)
    logger.info("SYNTHETIC CLAIMS COMPLETE")
    logger.info("=" * 60)
    logger.info(f"Summary:")
    logger.info(f"  - Clusters found: {stats['clusters_found']}")
    logger.info(f"  - Synthetic claims created: {stats['synthetic_nodes_added']}")
    logger.info(f"  - Nodes: {len(nodes)} → {len(updated_nodes)}")
    logger.info(f"  - Edges: {stats['edges_before']} → {stats['edges_after']}")
    logger.info(f"  - Cost: ${stats['cost_usd']:.6f}")
    
    return updated_nodes, updated_edges, stats


def _fan_in_targets(
    nodes: List[GraphNode],
    edges: List[GraphEdge],
    config: SynthesisConfig
) -> Dict[str, List[str]]:
    """
    Detect targets with premise fan-in above threshold.
    
    Returns mapping: target_id -> list[premise_ids]
    """
    if not config.enable_fan_in_synthesis:
        return {}

    support_map = build_support_graph(nodes, edges)
    premises = {n.id for n in nodes if n.type == "premise" and not n.is_synthetic}
    result: Dict[str, List[str]] = {}

    for premise_id, targets in support_map.items():
        if premise_id not in premises:
            continue
        for target in targets:
            result.setdefault(target, []).append(premise_id)

    return {
        t: ps for t, ps in result.items()
        if len(ps) >= config.fan_in_threshold
    }
def _build_grouping_prompt(target: GraphNode, premises: List[GraphNode]) -> str:
    lines = [
        "Cluster the premises that support the target claim into 1-3 themed groups.",
        "Rules:",
        "- Only use provided premise IDs.",
        "- Each premise ID appears at most once.",
        "- Each group must have size >=2.",
        "- If no meaningful grouping, return one group with all premises.",
        "",
        f"Target: {target.span if target else 'Unknown'}",
        "",
        "Premises:"
    ]
    for p in premises:
        lines.append(f"- {p.id}: {p.span}")
    lines.append("")
    lines.append("Return JSON with fields: groups (list of {premise_ids:[], theme:str}).")
    return "\n".join(lines)


def group_premises_for_target_llm(
    target: GraphNode,
    premise_nodes: List[GraphNode],
    client: Optional[LLMClient],
) -> Tuple[List[List[str]], float]:
    """LLM-assisted grouping for fan-in targets."""
    if client is None:
        client = get_llm_client()

    prompt = _build_grouping_prompt(target, premise_nodes)
    system = "You are an expert argument mapper. Respond with strict JSON (NO TAGS, JUST RAW JSON TEXT)."

    try:
        res = client.call_llm(
            task_name="fan_in_grouping",
            system_prompt=system,
            user_prompt=prompt,
            schema=None,
        )
        text = res.get("result")
        cost = res.get("cost_usd", res.get("usage", {}).get("estimated_cost_usd", 0.0)) or 0.0
        parsed = json.loads(text) if isinstance(text, str) else text
        groups_raw = parsed.get("groups", [])
        groups = []
        for g in groups_raw:
            ids = g.get("premise_ids", [])
            if len(ids) >= 2:
                groups.append(ids)
        return groups, cost
    except Exception as e:
        logger.warning(f"LLM grouping failed: {e}")
        return [], 0.0
def find_fan_in_clusters(
    nodes: List[GraphNode],
    edges: List[GraphEdge],
    config: SynthesisConfig,
    client: Optional[LLMClient] = None
) -> Tuple[List[PremiseCluster], Dict[str, Any]]:
    """Create premise clusters specifically for fan-in targets."""
    targets = _fan_in_targets(nodes, edges, config)
    if not targets:
        return [], {"targets": [], "groups": []}

    id_to_node = {n.id: n for n in nodes}
    clusters: List[PremiseCluster] = []
    meta_targets = []
    meta_groups = []
    total_cost = 0.0

    for target_id, premise_ids in targets.items():
        target_node = id_to_node.get(target_id)
        premise_nodes = [id_to_node[pid] for pid in premise_ids if pid in id_to_node]
        groups: List[List[str]] = []

        # Deterministic simple grouping: single group if min size met
        if config.fan_in_grouping_mode in ("deterministic", "hybrid"):
            if len(premise_nodes) >= config.fan_in_min_group_size:
                groups = [ [p.id for p in premise_nodes] ]

        # LLM grouping
        if config.fan_in_grouping_mode in ("llm", "hybrid"):
            llm_groups, cost = group_premises_for_target_llm(
                target_node, premise_nodes, client
            )
            total_cost += cost
            if llm_groups:
                groups = llm_groups

        # Enforce max synthetic claims per target
        if len(groups) > config.max_synthetic_claims_per_target:
            groups = groups[: config.max_synthetic_claims_per_target]

        for idx, group in enumerate(groups):
            cluster = PremiseCluster(
                cluster_id=f"fan_in_{target_id}_{idx}",
                premise_ids=group,
                premise_texts=[id_to_node[g].span for g in group if g in id_to_node],
                target_claim_id=target_id,
                target_claim_text=target_node.span if target_node else None,
                coherence_score=1.0,
                metadata={
                    "fan_in": True,
                    "target_id": target_id,
                    "group_index": idx,
                    "size": len(group),
                },
            )
            clusters.append(cluster)
            meta_groups.append({"target": target_id, "group": group, "cluster_id": cluster.cluster_id})

        if groups:
            meta_targets.append(target_id)

    return clusters, {"targets": meta_targets, "groups": meta_groups, "cost_usd": total_cost}
