"""
Q&A Module for Graph-Grounded Question Answering
=================================================

Provides question-answering capabilities that:
1. Focus on user's selected nodes (selection-first policy)
2. Include local neighborhood context (1-2 hops)
3. Include global graph overview (main components, relations)
4. Maintain chat memory for follow-up questions
5. Provide grounded answers with citations

Model: gpt-4o-mini (configurable via LLMConfig)
"""

import logging
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from pydantic import BaseModel, Field

from .llm_client import LLMClient, get_llm_client
from .llm_config import LLMConfig

logger = logging.getLogger(__name__)


# ============================================================================
# Pydantic Schemas
# ============================================================================

class QaResponse(BaseModel):
    """Response from Q&A system."""
    
    answer: str = Field(
        description="Plain text answer to the question"
    )
    cited_node_ids: List[str] = Field(
        default_factory=list,
        description="List of node IDs that support the answer"
    )
    confidence: float = Field(
        ge=0.0, le=1.0,
        description="Confidence in the answer (0.0 to 1.0)"
    )
    followups: List[str] = Field(
        default_factory=list,
        description="Suggested follow-up questions (2-4)"
    )
    notes: Optional[str] = Field(
        default=None,
        description="Optional notes about uncertainty or limitations"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "answer": "The main claim argues that capital punishment should be abolished...",
                "cited_node_ids": ["n1", "n2", "n3"],
                "confidence": 0.85,
                "followups": [
                    "What evidence supports this claim?",
                    "Are there any objections to this argument?"
                ],
                "notes": None
            }
        }


@dataclass
class QaContext:
    """Internal context structure for Q&A."""
    
    # Selected nodes (tier 1)
    selected_nodes: List[Dict[str, Any]] = field(default_factory=list)
    
    # Neighborhood nodes (tier 2)
    neighborhood_nodes: List[Dict[str, Any]] = field(default_factory=list)
    
    # Graph overview (tier 3)
    graph_overview: Dict[str, Any] = field(default_factory=dict)
    
    # All relevant edges
    edges: List[Dict[str, Any]] = field(default_factory=list)
    
    # Question and history
    question: str = ""
    history_summary: str = ""
    
    def to_prompt_text(self) -> str:
        """Convert context to formatted prompt text."""
        parts = []
        
        # Graph overview
        parts.append("=== GRAPH OVERVIEW ===")
        overview = self.graph_overview
        parts.append(f"Total nodes: {overview.get('total_nodes', 0)}")
        parts.append(f"Node types: {overview.get('node_type_counts', {})}")
        parts.append(f"Total edges: {overview.get('total_edges', 0)}")
        parts.append(f"Relation types: {overview.get('relation_type_counts', {})}")
        
        if overview.get('main_hubs'):
            parts.append(f"\nMain hub nodes (by degree): {overview['main_hubs']}")
        
        # Selected nodes (tier 1)
        if self.selected_nodes:
            parts.append("\n=== SELECTED NODES (PRIMARY FOCUS) ===")
            for node in self.selected_nodes:
                parts.append(f"\nNode {node['id']} ({node['type']}):")
                parts.append(f"  Label: {node['label']}")
                parts.append(f"  Paraphrase: {node['paraphrase']}")
                parts.append(f"  Original text: {node['span']}")
                parts.append(f"  Confidence: {node['confidence']:.2f}")
        
        # Neighborhood nodes (tier 2)
        if self.neighborhood_nodes:
            parts.append("\n=== NEIGHBORHOOD NODES (SUPPORTING CONTEXT) ===")
            for node in self.neighborhood_nodes:
                parts.append(f"\nNode {node['id']} ({node['type']}):")
                parts.append(f"  Label: {node['label']}")
                parts.append(f"  Paraphrase: {node['paraphrase']}")
                parts.append(f"  Confidence: {node['confidence']:.2f}")
        
        # Edges
        if self.edges:
            parts.append("\n=== RELATIONS ===")
            for edge in self.edges:
                parts.append(
                    f"{edge['source']} --[{edge['relation']}]--> {edge['target']} "
                    f"(confidence: {edge['confidence']:.2f})"
                )
        
        # History
        if self.history_summary:
            parts.append("\n=== CONVERSATION HISTORY ===")
            parts.append(self.history_summary)
        
        return "\n".join(parts)


@dataclass
class ChatTurn:
    """Single turn in chat history."""
    question: str
    answer: str
    cited_node_ids: List[str]
    timestamp: Optional[str] = None


# ============================================================================
# Context Building
# ============================================================================

def build_qa_context(
    graph: Dict[str, Any],
    selected_node_ids: List[str],
    question: str,
    history: List[ChatTurn],
    *,
    config: Optional[LLMConfig] = None,
    max_neighborhood_nodes: int = 20,
    max_hops: int = 2
) -> QaContext:
    """
    Build Q&A context from graph, selections, and history.
    
    Args:
        graph: Full graph dict with 'nodes' and 'edges' keys
        selected_node_ids: List of currently selected node IDs
        question: Current question being asked
        history: List of previous Q&A turns
        config: Optional LLM config
        max_neighborhood_nodes: Max nodes to include in neighborhood
        max_hops: Max hop distance for neighborhood expansion
        
    Returns:
        QaContext with formatted context data
    """
    context = QaContext()
    context.question = question
    
    # Parse graph
    nodes = {node['id']: node for node in graph.get('nodes', [])}
    edges = graph.get('edges', [])
    
    # Build adjacency for graph traversal
    adjacency = _build_adjacency(edges)
    
    # Build graph overview (tier 3)
    context.graph_overview = _build_graph_overview(nodes, edges)
    
    # Tier 1: Selected nodes
    if selected_node_ids:
        context.selected_nodes = [
            nodes[nid] for nid in selected_node_ids if nid in nodes
        ]
        
        # Tier 2: Neighborhood expansion
        neighborhood_ids = _expand_neighborhood(
            selected_node_ids, adjacency, max_hops, max_neighborhood_nodes
        )
        # Exclude already-selected nodes
        neighborhood_ids = neighborhood_ids - set(selected_node_ids)
        context.neighborhood_nodes = [
            nodes[nid] for nid in neighborhood_ids if nid in nodes
        ]
        
        # Filter edges to relevant ones
        relevant_node_ids = set(selected_node_ids) | neighborhood_ids
        context.edges = [
            edge for edge in edges
            if edge['source'] in relevant_node_ids and edge['target'] in relevant_node_ids
        ]
    else:
        # No selection: use question-based retrieval
        retrieved_ids = _retrieve_by_question(question, nodes, max_neighborhood_nodes)
        context.selected_nodes = [
            nodes[nid] for nid in retrieved_ids if nid in nodes
        ]
        # Include edges between retrieved nodes
        context.edges = [
            edge for edge in edges
            if edge['source'] in retrieved_ids and edge['target'] in retrieved_ids
        ]
    
    # Build history summary
    context.history_summary = _summarize_history(history)
    
    return context


def _build_adjacency(edges: List[Dict[str, Any]]) -> Dict[str, Set[str]]:
    """Build adjacency list (both directions) from edges."""
    adjacency = {}
    for edge in edges:
        source = edge['source']
        target = edge['target']
        
        if source not in adjacency:
            adjacency[source] = set()
        if target not in adjacency:
            adjacency[target] = set()
        
        adjacency[source].add(target)
        adjacency[target].add(source)  # Undirected for neighborhood
    
    return adjacency


def _expand_neighborhood(
    seed_ids: List[str],
    adjacency: Dict[str, Set[str]],
    max_hops: int,
    max_nodes: int
) -> Set[str]:
    """
    Expand neighborhood from seed nodes using BFS.
    
    Returns set of neighbor node IDs (excluding seeds).
    """
    visited = set()
    queue = [(nid, 0) for nid in seed_ids]  # (node_id, hop_distance)
    neighbors = set()
    
    while queue and len(neighbors) < max_nodes:
        node_id, distance = queue.pop(0)
        
        if node_id in visited:
            continue
        visited.add(node_id)
        
        # Don't include seed nodes in neighbors
        if distance > 0:
            neighbors.add(node_id)
        
        # Expand if within hop limit
        if distance < max_hops:
            for neighbor_id in adjacency.get(node_id, []):
                if neighbor_id not in visited:
                    queue.append((neighbor_id, distance + 1))
    
    return neighbors


def _build_graph_overview(
    nodes: Dict[str, Dict[str, Any]],
    edges: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Build compact graph overview."""
    # Count nodes by type
    node_type_counts = {}
    for node in nodes.values():
        node_type = node['type']
        node_type_counts[node_type] = node_type_counts.get(node_type, 0) + 1
    
    # Count edges by relation type
    relation_type_counts = {}
    for edge in edges:
        rel_type = edge['relation']
        relation_type_counts[rel_type] = relation_type_counts.get(rel_type, 0) + 1
    
    # Find main hubs (top nodes by degree)
    degree_counts = {}
    for edge in edges:
        degree_counts[edge['source']] = degree_counts.get(edge['source'], 0) + 1
        degree_counts[edge['target']] = degree_counts.get(edge['target'], 0) + 1
    
    # Sort by degree and take top 5
    main_hubs = sorted(degree_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    main_hubs = [f"{nid} (degree={deg})" for nid, deg in main_hubs]
    
    return {
        'total_nodes': len(nodes),
        'node_type_counts': node_type_counts,
        'total_edges': len(edges),
        'relation_type_counts': relation_type_counts,
        'main_hubs': main_hubs
    }


def _retrieve_by_question(
    question: str,
    nodes: Dict[str, Dict[str, Any]],
    max_nodes: int
) -> List[str]:
    """
    Retrieve relevant nodes based on question (lexical matching).
    
    Simple token overlap heuristic.
    """
    question_lower = question.lower()
    question_tokens = set(question_lower.split())
    
    # Score each node by token overlap
    scores = []
    for node_id, node in nodes.items():
        # Check label, paraphrase, and span
        text = (
            node.get('label', '') + ' ' +
            node.get('paraphrase', '') + ' ' +
            node.get('span', '')
        ).lower()
        text_tokens = set(text.split())
        
        # Count overlap
        overlap = len(question_tokens & text_tokens)
        
        # Also check for substring matches
        substring_matches = sum(1 for qt in question_tokens if qt in text)
        
        score = overlap + substring_matches * 0.5
        scores.append((node_id, score))
    
    # Sort by score and take top max_nodes
    scores.sort(key=lambda x: x[1], reverse=True)
    return [nid for nid, score in scores[:max_nodes] if score > 0]


def _summarize_history(history: List[ChatTurn], max_full_turns: int = 2) -> str:
    """
    Summarize chat history for context.
    
    Keep last max_full_turns as-is, summarize older turns briefly.
    """
    if not history:
        return ""
    
    parts = []
    
    # Older turns: brief summary
    if len(history) > max_full_turns:
        older_turns = history[:-max_full_turns]
        parts.append(f"Earlier in conversation: {len(older_turns)} question(s) asked about the graph.")
    
    # Recent turns: full detail
    recent_turns = history[-max_full_turns:] if len(history) > max_full_turns else history
    for i, turn in enumerate(recent_turns, 1):
        parts.append(f"\nPrevious Q{i}: {turn.question}")
        parts.append(f"Previous A{i}: {turn.answer[:200]}...")  # Truncate long answers
    
    return "\n".join(parts)


# ============================================================================
# Q&A Generation
# ============================================================================

def answer_question(
    graph: Dict[str, Any],
    selected_node_ids: List[str],
    question: str,
    history: List[ChatTurn],
    *,
    client: Optional[LLMClient] = None,
    config: Optional[LLMConfig] = None,
    **context_kwargs
) -> QaResponse:
    """
    Answer a question about the graph.
    
    Args:
        graph: Full graph dict
        selected_node_ids: List of currently selected node IDs
        question: Question to answer
        history: List of previous Q&A turns
        client: Optional LLM client
        config: Optional LLM config
        **context_kwargs: Additional kwargs for build_qa_context
        
    Returns:
        QaResponse with answer, citations, confidence, etc.
    """
    if client is None:
        client = get_llm_client(config)
    
    # Build context
    context = build_qa_context(
        graph, selected_node_ids, question, history,
        config=config, **context_kwargs
    )
    
    # Build prompt
    system_prompt = _build_system_prompt()
    user_prompt = _build_user_prompt(context)
    
    # Call LLM with structured output
    try:
        result = client.call_llm(
            task_name="qa_generation",
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            schema=QaResponse,
            retry_on_parse_error=True
        )
        return result['result']
    
    except Exception as e:
        logger.error(f"Q&A generation failed: {e}")
        # Return fallback response
        return QaResponse(
            answer=f"I encountered an error trying to answer your question: {str(e)}",
            cited_node_ids=[],
            confidence=0.0,
            followups=[],
            notes="Error occurred during answer generation"
        )


def _build_system_prompt() -> str:
    """Build system prompt for Q&A."""
    return """You are an expert argument analysis assistant. Your task is to answer questions about argument graphs based on provided context.

CRITICAL RULES:
1. **Grounding**: Answer ONLY based on information in the provided graph context. Do not invent facts.
2. **Citations**: Include node IDs in `cited_node_ids` for any nodes you reference in your answer.
3. **Selection Priority**: If selected nodes are provided, focus your answer primarily on those nodes. Use neighborhood and graph overview as supporting context only.
4. **Confidence**: Set confidence based on how well the graph supports your answer:
   - 0.9-1.0: Strong evidence in selected/neighborhood nodes
   - 0.7-0.9: Moderate evidence, some inference needed
   - 0.4-0.7: Weak evidence, significant uncertainty
   - 0.0-0.4: Very weak or no evidence
5. **Uncertainty**: If information is not in the graph, say so explicitly in your answer and/or in `notes`. Lower confidence accordingly.
6. **Follow-ups**: Suggest 2-4 relevant follow-up questions the user might ask.
7. **Output Format**: Respond ONLY with valid JSON matching the QaResponse schema. No additional text.

When the user asks a follow-up question (indicated by conversation history), consider the previous context but still ground your answer in the graph data."""


def _build_user_prompt(context: QaContext) -> str:
    """Build user prompt with context and question."""
    context_text = context.to_prompt_text()
    
    return f"""Based on the following argument graph context, please answer the question.

{context_text}

=== QUESTION ===
{context.question}

Provide your answer as JSON matching the QaResponse schema:
{{
    "answer": "your answer here",
    "cited_node_ids": ["n1", "n2", ...],
    "confidence": 0.85,
    "followups": ["follow-up question 1", "follow-up question 2"],
    "notes": "optional notes about limitations/uncertainty"
}}"""


# ============================================================================
# Chat Memory Management
# ============================================================================

def add_to_history(
    history: List[ChatTurn],
    question: str,
    response: QaResponse,
    max_turns: int = 6
) -> List[ChatTurn]:
    """
    Add a new turn to chat history and trim if needed.
    
    Args:
        history: Current history list
        question: Question asked
        response: QaResponse received
        max_turns: Maximum number of turns to keep
        
    Returns:
        Updated history list
    """
    new_turn = ChatTurn(
        question=question,
        answer=response.answer,
        cited_node_ids=response.cited_node_ids
    )
    
    history.append(new_turn)
    
    # Trim to max_turns
    if len(history) > max_turns:
        history = history[-max_turns:]
    
    return history
