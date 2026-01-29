import os
import json
from datetime import datetime
from typing import List, Literal, Optional
from pydantic import BaseModel, Field
from openai import OpenAI
import logging

# Import preprocessing module
from backend.preprocessing import preprocess_text

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==========================================
# CONFIGURATION
# ==========================================

# Your OpenAI API Key
# NEVER hardcode API keys in code. Use environment variables or secure vaults.
# # ==========================================
# Data Models
# ==========================================

class GraphNode(BaseModel):
    id: str = Field(description="Unique ID (e.g., 'n1', 'n2')")
    type: Literal["claim", "premise", "objection", "reply", "conclusion"] = Field(description="The role of this component")
    label: str = Field(description="A short summary (3-8 words)")
    span: str = Field(description="The exact text from the source")
    paraphrase: str = Field(description="Simple explanation")
    confidence: float = Field(description="Confidence score between 0.0 and 1.0")
    
    # Synthetic claim metadata (optional)
    is_synthetic: Optional[bool] = Field(default=False, description="Whether this is a synthetic claim")
    source_premise_ids: Optional[List[str]] = Field(default=None, description="Source premise IDs for synthetic claims")
    synthesis_method: Optional[str] = Field(default=None, description="Method used for synthesis")

class GraphEdge(BaseModel):
    source: str = Field(description="Source node ID")
    target: str = Field(description="Target node ID")
    relation: Literal["support", "attack"] = Field(description="Logical relation")
    confidence: float = Field(description="Confidence score between 0.0 and 1.0")

class ArgumentGraph(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]

class QAResponse(BaseModel):
    answer: str = Field(description="Direct answer to the user's question based on the graph")
    confidence: float = Field(description="Confidence score 0.0-1.0")
    explanation: str = Field(description="Brief explanation of how the answer was derived")
    source_ids: List[str] = Field(description="List of node IDs used to answer")

# ==========================================
# Core Logic
# ==========================================

def get_client():
    """Helper to get OpenAI client with the correct key."""
    api_key = os.environ.get("OPENAI_API_KEY")
    
    if not api_key:
        print("Error: No API key provided.")
        return None
        
    return OpenAI(api_key=api_key)


def _format_candidates_for_llm(preprocessed) -> str:
    """Format preprocessed candidates as structured input for LLM."""
    from backend.preprocessing import get_candidates
    
    candidates = get_candidates(preprocessed)
    if not candidates:
        return "No candidate sentences found."
    
    formatted_lines = []
    for sent in candidates:
        # Format: "S{id} (p{para}): {text}"
        para_id = sent.paragraph_id if hasattr(sent, 'paragraph_id') else 0
        formatted_lines.append(f"S{sent.id} (p{para_id}): {sent.text}")
    
    return "\n".join(formatted_lines)


def _validate_and_repair_edges(nodes: List[GraphNode], edges: List[GraphEdge]) -> List[GraphEdge]:
    """
    Validate and repair edges according to constraints.
    
    Rules:
    1. Drop edges with missing endpoints
    2. Drop self-loops
    3. Enforce conclusion constraint: conclusion nodes cannot support/attack non-conclusion nodes
    """
    node_ids = {node.id for node in nodes}
    conclusion_ids = {node.id for node in nodes if node.type == "conclusion"}
    
    valid_edges = []
    
    for edge in edges:
        # Rule 1: Drop edges with missing endpoints
        if edge.source not in node_ids or edge.target not in node_ids:
            logger.warning(f"Dropping edge {edge.source} -> {edge.target}: missing endpoint")
            continue
        
        # Rule 2: Drop self-loops
        if edge.source == edge.target:
            logger.warning(f"Dropping self-loop edge: {edge.source} -> {edge.target}")
            continue
        
        # Rule 3: Enforce conclusion constraint
        if edge.source in conclusion_ids and edge.target not in conclusion_ids:
            logger.warning(f"Dropping invalid edge: conclusion {edge.source} -> non-conclusion {edge.target}")
            continue
        
        valid_edges.append(edge)
    
    return valid_edges


def _compute_connected_components(nodes: List[GraphNode], edges: List[GraphEdge]) -> List[set]:
    """Compute connected components treating graph as undirected."""
    from collections import defaultdict, deque
    
    # Build adjacency list (undirected)
    adj = defaultdict(set)
    for edge in edges:
        adj[edge.source].add(edge.target)
        adj[edge.target].add(edge.source)
    
    visited = set()
    components = []
    
    for node in nodes:
        if node.id not in visited:
            # BFS to find component
            component = set()
            queue = deque([node.id])
            while queue:
                current = queue.popleft()
                if current in visited:
                    continue
                visited.add(current)
                component.add(current)
                for neighbor in adj[current]:
                    if neighbor not in visited:
                        queue.append(neighbor)
            components.append(component)
    
    return components


def _repair_connectivity(nodes: List[GraphNode], edges: List[GraphEdge]) -> List[GraphEdge]:
    """
    Attempt to connect disconnected components with heuristic bridging edges.
    
    Strategy:
    - Connect nodes in same paragraph
    - Connect premise -> claim
    - Connect claim -> conclusion
    Uses low confidence (0.4) for synthetic edges.
    """
    components = _compute_connected_components(nodes, edges)
    
    if len(components) <= 1:
        logger.info("Graph is connected, no repair needed")
        return edges
    
    logger.info(f"Found {len(components)} disconnected components, attempting repair")
    
    # Build node lookup
    node_map = {node.id: node for node in nodes}
    
    # Create bridging edges
    new_edges = list(edges)  # Copy existing edges
    
    # Sort components by size (largest first)
    components = sorted(components, key=len, reverse=True)
    main_component = components[0]
    
    for component in components[1:]:
        # Try to connect this component to main component
        bridged = False
        
        # Strategy 1: Same paragraph proximity
        for node_id in component:
            node = node_map[node_id]
            node_para = getattr(node, 'paragraph_id', None)
            
            if node_para is not None:
                for main_node_id in main_component:
                    main_node = node_map[main_node_id]
                    main_para = getattr(main_node, 'paragraph_id', None)
                    
                    if node_para == main_para:
                        # Connect based on type heuristic
                        if node.type == "premise" and main_node.type in ["claim", "conclusion"]:
                            new_edges.append(GraphEdge(
                                source=node_id,
                                target=main_node_id,
                                relation="support",
                                confidence=0.4
                            ))
                            logger.info(f"Added bridge edge: {node_id} (premise) -> {main_node_id} ({main_node.type})")
                            bridged = True
                            break
                        elif node.type == "claim" and main_node.type == "conclusion":
                            new_edges.append(GraphEdge(
                                source=node_id,
                                target=main_node_id,
                                relation="support",
                                confidence=0.4
                            ))
                            logger.info(f"Added bridge edge: {node_id} (claim) -> {main_node_id} (conclusion)")
                            bridged = True
                            break
            
            if bridged:
                break
        
        # Strategy 2: Fallback - connect any premise to any claim
        if not bridged:
            for node_id in component:
                node = node_map[node_id]
                if node.type == "premise":
                    for main_node_id in main_component:
                        main_node = node_map[main_node_id]
                        if main_node.type in ["claim", "conclusion"]:
                            new_edges.append(GraphEdge(
                                source=node_id,
                                target=main_node_id,
                                relation="support",
                                confidence=0.3
                            ))
                            logger.info(f"Added fallback bridge: {node_id} -> {main_node_id}")
                            bridged = True
                            break
                if bridged:
                    break
    
    return new_edges


def extract_arguments_real(text: str) -> Optional[dict]:
    """
    Performs real argument extraction using OpenAI API with 2-call approach.
    
    Process:
    1. Preprocessing: sentence segmentation, discourse markers, candidate flagging
    2. LLM Call 1: Component classification (identify argumentative units and types)
    3. LLM Call 2: Relation extraction (identify support/attack relations)
    4. Post-processing: validation and connectivity repair
    """
    # STEP 1: Preprocessing
    logger.info("=" * 60)
    logger.info("STEP 1: PREPROCESSING")
    logger.info("=" * 60)
    
    preprocessed = preprocess_text(text)
    logger.info(f"Preprocessing complete: {len(preprocessed.sentences)} sentences, "
                f"{preprocessed.metadata.get('candidate_count', 0)} candidates")
    
    client = get_client()
    if not client:
        return None

    try:
        # ====================================================================
        # STEP 2: Component Classification (LLM Call 1)
        # ====================================================================
        logger.info("\n" + "=" * 60)
        logger.info("STEP 2: COMPONENT CLASSIFICATION (LLM CALL 1)")
        logger.info("=" * 60)
        
        classification_system_prompt = """You are an argument-mining engine that classifies sentences into argumentative components.

You MUST follow these rules:
- Output ONLY valid JSON (no markdown, no commentary).
- Use node types: CLAIM, PREMISE, OBJECTION, REPLY, or mark as non-argumentative.
- DO NOT use CONCLUSION - conclusions will be inferred later based on graph structure.

Node definitions:
- PREMISE: evidence/reason/examples/causal justification for or against another node.
- CLAIM: arguable stance/position (includes statements that may appear to be final takeaways - these will be identified as conclusions later based on their structural role in the graph).
- OBJECTION: counters/undermines another node.
- REPLY: responds to an OBJECTION (usually attacks the objection and/or supports the defended point).

Classify each sentence and provide a confidence score (0.0-1.0).
Be concise: rationales (if provided) must be <= 1 sentence.
"""
        
        # Format input as structured list
        candidates_str = _format_candidates_for_llm(preprocessed)
        classification_user_prompt = f"""Classify these sentences into argumentative components:

{candidates_str}

Return JSON with nodes array containing: id (use S{id}), type, label (3-8 word summary), span (original text), paraphrase (simple explanation), confidence."""
        
        logger.info("Calling LLM for component classification...")
        
        class NodeClassification(BaseModel):
            nodes: List[GraphNode]
        
        classification_completion = client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            temperature=0,
            messages=[
                {"role": "system", "content": classification_system_prompt},
                {"role": "user", "content": classification_user_prompt},
            ],
            response_format=NodeClassification,
        )
        
        nodes_result = classification_completion.choices[0].message.parsed
        nodes = nodes_result.nodes
        
        logger.info(f"Classification complete: {len(nodes)} nodes identified")
        
        # ====================================================================
        # STEP 3: Relation Extraction (LLM Call 2)
        # ====================================================================
        logger.info("\n" + "=" * 60)
        logger.info("STEP 3: RELATION EXTRACTION (LLM CALL 2)")
        logger.info("=" * 60)
        
        if not nodes:
            logger.warning("No nodes found, skipping relation extraction")
            edges = []
        else:
            relation_system_prompt = """You are an argument-mining engine that extracts relations between argumentative components.

You MUST follow these rules:
- Output ONLY valid JSON (no markdown, no commentary).
- Relations: SUPPORT or ATTACK
- Edge direction: source SUPPORTS/ATTACKS target (source is the reason/counter-reason about target).

Conclusion constraint:
- A CONCLUSION must NOT support/attack any non-conclusion node.
- CONCLUSION -> CONCLUSION edges are allowed.
- Other node types may support/attack a CONCLUSION.

Connectivity objective:
- Prefer one main connected graph.
- Avoid isolated nodes. If unsure, attach with a low-confidence edge rather than leaving a node disconnected.
- Every non-conclusion node should have at least one edge (incoming or outgoing) unless truly standalone.
- Every conclusion should have ≥1 incoming edge (unless the text genuinely provides no reasons).
- Keep confidence in [0,1]. Use lower confidence for implicit/uncertain links.

No self-loops. Only reference node IDs that exist.
Be concise: rationales (if requested) must be <= 1 sentence.
"""
            
            # Format nodes for relation extraction
            nodes_str = "\n".join([
                f"- {node.id} ({node.type}): {node.span}"
                for node in nodes
            ])
            
            relation_user_prompt = f"""Given these argumentative components, identify support/attack relations:

{nodes_str}

Return JSON with edges array containing: source (node ID), target (node ID), relation (support or attack), confidence."""
            
            logger.info("Calling LLM for relation extraction...")
            
            class EdgeExtraction(BaseModel):
                edges: List[GraphEdge]
            
            relation_completion = client.beta.chat.completions.parse(
                model="gpt-4o-mini",
                temperature=0,
                messages=[
                    {"role": "system", "content": relation_system_prompt},
                    {"role": "user", "content": relation_user_prompt},
                ],
                response_format=EdgeExtraction,
            )
            
            edges_result = relation_completion.choices[0].message.parsed
            edges = edges_result.edges
            
            logger.info(f"Relation extraction complete: {len(edges)} edges identified")
        
        # ====================================================================
        # STEP 4: Post-processing Validation & Repair
        # ====================================================================
        logger.info("\n" + "=" * 60)
        logger.info("STEP 4: VALIDATION & CONNECTIVITY REPAIR")
        logger.info("=" * 60)
        
        # Validate and repair edges
        logger.info(f"Before validation: {len(edges)} edges")
        edges = _validate_and_repair_edges(nodes, edges)
        logger.info(f"After validation: {len(edges)} edges")
        
        # Check connectivity and repair if needed
        edges = _repair_connectivity(nodes, edges)
        logger.info(f"After connectivity repair: {len(edges)} edges")
        
        # ====================================================================
        # STEP 4.5: Post-hoc Conclusion Inference
        # ====================================================================
        logger.info("\n" + "=" * 60)
        logger.info("STEP 4.5: CONCLUSION INFERENCE (POST-HOC)")
        logger.info("=" * 60)
        
        # Convert to dict format for conclusion inference
        nodes_dicts = [node.model_dump() for node in nodes]
        edges_dicts = [edge.model_dump() for edge in edges]
        
        try:
            from backend.extraction.conclusion_inference import infer_conclusions, ConclusionInferenceConfig
            
            # Run conclusion inference
            conclusion_config = ConclusionInferenceConfig()
            conclusion_result = infer_conclusions(nodes_dicts, edges_dicts, config=conclusion_config)
            
            # Update nodes with new types
            node_type_map = {n["id"]: n["type"] for n in nodes_dicts}
            for node in nodes:
                node.type = node_type_map[node.id]
            
            # Update edges (some may have been removed)
            edge_set = {(e["source"], e["target"], e["relation"]) for e in edges_dicts}
            edges = [e for e in edges if (e.source, e.target, e.relation) in edge_set]
            
            logger.info(f"Conclusion inference complete:")
            logger.info(f"  - Candidates evaluated: {len(conclusion_result.candidates)}")
            logger.info(f"  - Conclusions selected: {len(conclusion_result.selected_conclusions)}")
            logger.info(f"  - Nodes relabeled: {conclusion_result.relabeled_count}")
            logger.info(f"  - Edges removed: {conclusion_result.edges_removed}")
            
            conclusion_meta = {
                "method": conclusion_result.method,
                "candidates_count": len(conclusion_result.candidates),
                "conclusions_selected": len(conclusion_result.selected_conclusions),
                "nodes_relabeled": conclusion_result.relabeled_count,
                "edges_removed": conclusion_result.edges_removed
            }
        except Exception as e:
            logger.warning(f"Conclusion inference failed: {e}")
            conclusion_meta = {"error": str(e)}
        
        # ====================================================================
        # STEP 5: Synthetic Claims Generation (post-conclusion)
        # ====================================================================
        logger.info("\n" + "=" * 60)
        logger.info("STEP 5: SYNTHETIC CLAIMS GENERATION (POST-CONCLUSION)")
        logger.info("=" * 60)
        
        synthetic_meta = {"enabled": False}
        try:
            from backend.graph_construction import GraphNode as GCGraphNode, GraphEdge as GCGraphEdge
            from backend.extraction.synthetic_claims import add_synthetic_claims_to_graph, SynthesisConfig
            
            # Convert llm_extractor nodes/edges to graph_construction format
            gc_nodes = []
            for node in nodes:
                gc_node = GCGraphNode(
                    id=node.id,
                    type=node.type,
                    label=node.label,
                    span=node.span,
                    paraphrase=node.paraphrase,
                    confidence=node.confidence,
                    sentence_id=node.id  # Use node ID as sentence ID
                )
                gc_nodes.append(gc_node)
            
            gc_edges = []
            for edge in edges:
                gc_edge = GCGraphEdge(
                    source=edge.source,
                    target=edge.target,
                    relation=edge.relation,
                    confidence=edge.confidence
                )
                gc_edges.append(gc_edge)
            
            # Run synthetic claims generation
            synthesis_config = SynthesisConfig()
            updated_gc_nodes, updated_gc_edges, synthetic_stats = add_synthetic_claims_to_graph(
                gc_nodes, gc_edges, client=None, config=synthesis_config
            )
            
            logger.info(f"Synthetic claims complete:")
            logger.info(f"  - Clusters found: {synthetic_stats['clusters_found']}")
            logger.info(f"  - Synthetic claims added: {synthetic_stats['synthetic_nodes_added']}")
            logger.info(f"  - Edges: {synthetic_stats['edges_before']} → {synthetic_stats['edges_after']}")
            logger.info(f"  - Cost: ${synthetic_stats['cost_usd']:.6f}")
            
            # Convert back to llm_extractor format
            nodes = []
            for gc_node in updated_gc_nodes:
                node = GraphNode(
                    id=gc_node.id,
                    type=gc_node.type,
                    label=gc_node.label,
                    span=gc_node.span,
                    paraphrase=gc_node.paraphrase,
                    confidence=gc_node.confidence,
                    is_synthetic=gc_node.is_synthetic,
                    source_premise_ids=gc_node.source_premise_ids,
                    synthesis_method=gc_node.synthesis_method
                )
                nodes.append(node)
            
            edges = []
            for gc_edge in updated_gc_edges:
                edge = GraphEdge(
                    source=gc_edge.source,
                    target=gc_edge.target,
                    relation=gc_edge.relation,
                    confidence=gc_edge.confidence
                )
                edges.append(edge)
            
            synthetic_meta = {
                "enabled": True,
                "clusters_found": synthetic_stats["clusters_found"],
                "synthetic_claims_added": synthetic_stats["synthetic_nodes_added"],
                "cost_usd": synthetic_stats["cost_usd"]
            }
            
        except Exception as e:
            logger.warning(f"Synthetic claims generation failed: {e}")
            synthetic_meta = {"enabled": False, "error": str(e)}
        
        # Stable ordering for rendering/layout
        nodes = sorted(nodes, key=lambda n: n.id)
        edges = sorted(edges, key=lambda e: (e.source, e.target, e.relation))

        # Convert to dict format
        graph_data = {
            "nodes": [node.model_dump() for node in nodes],
            "edges": [edge.model_dump() for edge in edges],
            "meta": {
                "source": "llm_real",
                "created_at": datetime.now().isoformat(),
                "model_version": "gpt-4o-mini",
                "note": "Generated by OpenAI with 2-call extraction + synthetic claims + post-hoc conclusion inference",
                "preprocessing": {
                    "sentence_count": len(preprocessed.sentences),
                    "candidate_count": preprocessed.metadata.get('candidate_count', 0),
                    "paragraph_count": preprocessed.paragraph_count,
                    "marker_counts": preprocessed.metadata.get('marker_counts', {})
                },
                "connected_components": len(_compute_connected_components(nodes, edges)),
                "synthetic_claims": synthetic_meta,
                "conclusion_inference": conclusion_meta
            }
        }
        
        logger.info("=" * 60)
        logger.info("EXTRACTION COMPLETE")
        logger.info(f"Final graph: {len(nodes)} nodes, {len(edges)} edges, "
                   f"{graph_data['meta']['connected_components']} component(s)")
        logger.info("=" * 60)
        
        return graph_data

    except Exception as e:
        logger.error(f"Error during extraction: {e}", exc_info=True)
        return None


def get_graph_qa_answer_real(question: str, selected_nodes: list, graph_data: dict) -> Optional[dict]:
    """
    Performs real Q&A using OpenAI API based on the graph context.
    """
    client = get_client()
    if not client:
        return None

    # Prepare Context (Convert graph/selection to text)
    context_str = "Argument Graph Data:\n"
    
    # If nodes are selected, prioritize them, otherwise use all
    target_nodes = []
    if selected_nodes:
        target_nodes = [n for n in graph_data["nodes"] if n["id"] in selected_nodes]
    else:
        target_nodes = graph_data["nodes"]

    for node in target_nodes:
        context_str += f"- Node {node['id']} ({node['type']}): {node['label']}\n"
        context_str += f"  Full text: {node['span']}\n"

    # Add edges context
    context_str += "\nRelationships:\n"
    for edge in graph_data["edges"]:
        context_str += f"- {edge['source']} {edge['relation']} {edge['target']}\n"

    # Define System Prompt
    system_prompt = f"""
    You are an intelligent assistant analyzing an argument graph.
    Answer the user's question based ONLY on the provided graph context.
    
    Context:
    {context_str}
    
    Guidelines:
    - Be concise and direct.
    - Cite the specific nodes you used in the 'source_ids' field.
    - If the question cannot be answered from the graph, state that clearly.
    """

    try:
        print("Sending question to OpenAI...")
        completion = client.beta.chat.completions.parse(
            model="gpt-4o-mini", 
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question},
            ],
            response_format=QAResponse,
        )

        result = completion.choices[0].message.parsed
        
        # Format for UI (Map source_ids back to full source objects)
        sources_list = []
        for nid in result.source_ids:
            # Find the node in the original graph data
            node = next((n for n in graph_data["nodes"] if n["id"] == nid), None)
            if node:
                sources_list.append({"node_id": nid, "span": node["span"]})

        return {
            "answer": result.answer,
            "confidence": result.confidence,
            "sources": sources_list,
            "explanation": result.explanation
        }

    except Exception as e:
        print(f"QA Failed: {e}")
        return None


# Self-test block (runs only if you execute this file directly)
if __name__ == "__main__":
    test_text = "Electric cars are the future because they reduce pollution. However, batteries are expensive."
    result = extract_arguments_real(test_text)
    print(json.dumps(result, indent=2))
