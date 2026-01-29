"""
Argument Graph Builder - Interactive Mockup
============================================

A Streamlit-based prototype for visualizing philosophical/argumentative text
as interactive argument graphs with node explanations and Q&A functionality.

This is a UI mockup for Milestone 2 - the backend extraction is mocked
unless the real LLM extractor is available.
"""

import streamlit as st
import json
from datetime import datetime

# Import custom vis-network component for click-to-select
from components.vis_network_select import vis_network_select

# Import node type configuration (single source of truth)
from node_type_config import (
    get_node_color, 
    get_node_label, 
    get_node_description,
    get_all_node_types,
    NODE_TYPE_CONFIG,
    get_edge_color,
    get_edge_label,
    get_edge_description,
    get_all_edge_relations,
    EDGE_RELATION_CONFIG
)

# --- Extraction Logic Setup ---

# 1. Import helpers and the mock extractor (renamed to 'extract_mock')
from extractor_stub import (
    get_sample_texts,
    load_sample_text,
    get_mock_qa_answer,
    extract_arguments as extract_mock
)

# 2. Try to import the real LLM extractor
try:
    from llm_extractor import extract_arguments_real
except ImportError:
    extract_arguments_real = None

# 3. Try to import the real Q&A module
try:
    from backend.qa_module import answer_question, ChatTurn, QaResponse
    from backend.llm_client import get_llm_client
    qa_module_available = True
except ImportError as e:
    print(f"Q&A module not available: {e}")
    qa_module_available = False

# 4. Define the main wrapper function
def extract_arguments(text, simulate_delay=True):
    """
    Main extraction entry point.
    Tries to use Real OpenAI first. If it fails (no key/error), falls back to Mock.
    """
    # Try Real Extraction first
    if extract_arguments_real:
        print("Attempting Real LLM Extraction...")
        result = extract_arguments_real(text)
        if result:
            return result
            
    # Fallback to Mock if real extraction failed or isn't available
    print("Falling back to Mock Extraction...")
    return extract_mock(text, simulate_delay)

# --- End of Extraction Setup ---


# Page configuration
st.set_page_config(
    page_title="Argument Graph Builder",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1rem;
        color: #8b92a5;
        margin-bottom: 2rem;
    }
    .node-type-claim {
        background-color: rgba(59, 130, 246, 0.1);
        border-left: 4px solid #3b82f6;
        padding: 0.5rem 1rem;
        border-radius: 4px;
    }
    .node-type-premise {
        background-color: rgba(16, 185, 129, 0.1);
        border-left: 4px solid #10b981;
        padding: 0.5rem 1rem;
        border-radius: 4px;
    }
    .node-type-objection {
        background-color: rgba(239, 68, 68, 0.1);
        border-left: 4px solid #ef4444;
        padding: 0.5rem 1rem;
        border-radius: 4px;
    }
    .node-type-reply {
        background-color: rgba(245, 158, 11, 0.1);
        border-left: 4px solid #f59e0b;
        padding: 0.5rem 1rem;
        border-radius: 4px;
    }
    .node-type-conclusion {
        background-color: rgba(139, 92, 246, 0.1);
        border-left: 4px solid #8b5cf6;
        padding: 0.5rem 1rem;
        border-radius: 4px;
    }
    .confidence-badge {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 500;
    }
    .confidence-high {
        background-color: rgba(16, 185, 129, 0.2);
        color: #10b981;
    }
    .confidence-medium {
        background-color: rgba(245, 158, 11, 0.2);
        color: #f59e0b;
    }
    .confidence-low {
        background-color: rgba(239, 68, 68, 0.2);
        color: #ef4444;
    }
    /* THIS IS THE FIX FOR THE TEXT BLOCKS: */
    .source-span {
        background-color: rgba(128, 128, 128, 0.1); 
        border-radius: 4px;
        padding: 0.75rem;
        font-style: italic;
        border-left: 3px solid #9ca3af;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 8px 16px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "graph_data" not in st.session_state:
    st.session_state.graph_data = None
if "selected_node" not in st.session_state:
    st.session_state.selected_node = None
if "selected_nodes" not in st.session_state:
    st.session_state.selected_nodes = []
if "input_text" not in st.session_state:
    st.session_state.input_text = ""
if "extraction_status" not in st.session_state:
    st.session_state.extraction_status = None
if "qa_history" not in st.session_state:
    st.session_state.qa_history = []
if "pdf_metadata" not in st.session_state:
    st.session_state.pdf_metadata = None
# Focus mode UI flags
if "focus_mode" not in st.session_state:
    st.session_state.focus_mode = False
if "show_input_panel" not in st.session_state:
    st.session_state.show_input_panel = True
# Layout options
if "use_server_layout" not in st.session_state:
    st.session_state.use_server_layout = False


# get_node_color is now imported from node_type_config.py (single source of truth)


def get_confidence_class(confidence: float) -> str:
    """Return CSS class based on confidence level."""
    if confidence >= 0.8:
        return "confidence-high"
    elif confidence >= 0.6:
        return "confidence-medium"
    else:
        return "confidence-low"


def run_extraction():
    """Run the extraction process and update session state."""
    with st.spinner("Extracting arguments..."):
        graph_data = extract_arguments(st.session_state.input_text)
        
        # Add PDF metadata to graph if available
        if st.session_state.pdf_metadata and graph_data:
            if "meta" not in graph_data:
                graph_data["meta"] = {}
            graph_data["meta"].update(st.session_state.pdf_metadata)
        
        st.session_state.graph_data = graph_data
        st.session_state.extraction_status = "done"
        st.session_state.selected_nodes = []
        st.session_state.qa_history = []
        st.rerun()


def render_graph_and_handle_selection(filtered_graph: dict, graph_data: dict, height: int):
    """Render the graph component and handle selection updates.
    
    Args:
        filtered_graph: The filtered graph data to display
        graph_data: The full graph data (for looking up node details)
        height: Height of the graph component in pixels
        
    Returns:
        The selection from the graph component
    """
    selection = vis_network_select(
        nodes=filtered_graph["nodes"],
        edges=filtered_graph["edges"],
        selected_nodes=st.session_state.selected_nodes,
        key="graph_select",
        height=height,
        use_server_layout=st.session_state.use_server_layout,
    )
    
    # Update session state based on graph selection
    if selection:
        new_selected = selection.get("selected", [])
        last_clicked = selection.get("last_clicked")
        
        # Only update if selection changed
        if set(new_selected) != set(st.session_state.selected_nodes):
            st.session_state.selected_nodes = new_selected
            
            # Update selected_node for the Details panel
            if last_clicked:
                st.session_state.selected_node = next(
                    (n for n in graph_data["nodes"] if n["id"] == last_clicked), None
                )
            elif new_selected:
                # Use first selected node if no last_clicked
                st.session_state.selected_node = next(
                    (n for n in graph_data["nodes"] if n["id"] == new_selected[0]), None
                )
            else:
                st.session_state.selected_node = None
            
            st.rerun()
    
    return selection


def render_node_detail_panel(node: dict, graph_data: dict):
    """Render the node detail side panel."""
    
    # Check if this is a synthetic node
    is_synthetic = node.get("is_synthetic", False)
    
    # Node type badge (with synthetic indicator)
    type_class = f"node-type-{node['type']}"
    type_label = node['type'].upper()
    if is_synthetic:
        type_label += " 🔮"
    
    st.markdown(f"""
    <div class="{type_class}">
        <strong>{type_label}</strong>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"### {node['label']}")
    
    # Confidence indicator
    conf_class = get_confidence_class(node["confidence"])
    st.markdown(f"""
    <span class="confidence-badge {conf_class}">
        Confidence: {node['confidence']:.0%}
    </span>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Original text span
    st.markdown("**Original Text Span**")
    st.markdown(f"""
    <div class="source-span">
        "{node['span']}"
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("")
    
    # LLM Paraphrase
    st.markdown("**LLM Paraphrase**")
    st.info(node["paraphrase"])
    
    # Show source premises for synthetic claims
    is_synthetic = node.get("is_synthetic", False)
    if is_synthetic:
        source_premise_ids = node.get("source_premise_ids", [])
        synthesis_method = node.get("synthesis_method", "unknown")
        
        st.markdown("")
        st.markdown("""
        <div style="background-color: rgba(168, 85, 247, 0.15); 
                    border-left: 4px solid #a855f7; 
                    padding: 0.5rem 1rem; 
                    border-radius: 4px; 
                    margin: 0.5rem 0;">
            <strong>🔮 Synthetic Claim</strong><br>
            <small>Generated by LLM to summarize premise cluster</small>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("**Synthesis Information**")
        st.markdown(f"- **Method:** {synthesis_method.upper()}")
        st.markdown(f"- **Source premises:** {len(source_premise_ids)}")
        
        if source_premise_ids:
            with st.expander("View source premises"):
                for premise_id in source_premise_ids:
                    premise_node = next((n for n in graph_data["nodes"] if n["id"] == premise_id), None)
                    if premise_node:
                        st.markdown(f"**{premise_node['label']}**")
                        st.markdown(f"> {premise_node['span'][:150]}...")
                        st.markdown("")
    
    st.markdown("---")
    
    # Relations
    st.markdown("**Relations**")
    
    # Find incoming and outgoing edges
    incoming = [e for e in graph_data["edges"] if e["target"] == node["id"]]
    outgoing = [e for e in graph_data["edges"] if e["source"] == node["id"]]
    
    if incoming:
        st.markdown("*Supported/Attacked by:*")
        for edge in incoming:
            source_node = next((n for n in graph_data["nodes"] if n["id"] == edge["source"]), None)
            if source_node:
                relation_symbol = "[+]" if edge["relation"] == "support" else "[-]"
                st.markdown(f"- {relation_symbol} **{source_node['label'][:40]}...** ({edge['relation']})")
    
    if outgoing:
        st.markdown("*Supports/Attacks:*")
        for edge in outgoing:
            target_node = next((n for n in graph_data["nodes"] if n["id"] == edge["target"]), None)
            if target_node:
                relation_symbol = "[+]" if edge["relation"] == "support" else "[-]"
                st.markdown(f"- {relation_symbol} **{target_node['label'][:40]}...** ({edge['relation']})")
    
    if not incoming and not outgoing:
        st.markdown("*No direct relations*")


def render_qa_panel(graph_data: dict, selected_nodes: list):
    """Render the Q&A panel for asking questions about nodes."""
    
    st.markdown("### 💬 Graph Q&A")
    st.caption("Ask questions about the argument graph. Select nodes to focus the answer on specific parts.")
    
    # Show selected nodes if any
    if selected_nodes:
        st.markdown(f"**Selected nodes:** {len(selected_nodes)}")
        cols = st.columns(min(len(selected_nodes), 3))
        for idx, node_id in enumerate(selected_nodes[:3]):
            node = next((n for n in graph_data["nodes"] if n["id"] == node_id), None)
            if node:
                with cols[idx % 3]:
                    st.markdown(f"**{node_id}** ({node['type']})")
                    st.caption(node['label'][:40] + "..." if len(node['label']) > 40 else node['label'])
        if len(selected_nodes) > 3:
            st.caption(f"... and {len(selected_nodes) - 3} more")
    else:
        st.info("💡 **Tip:** Select nodes from the graph to focus answers on specific components. "
                "Without selection, answers will cover the whole graph.")
    
    st.markdown("---")
    
    # Question input
    question = st.text_input(
        "Your question:",
        placeholder="e.g., What is the main claim? What evidence supports this? Are there objections?",
        key="qa_question",
        help="Ask about the argument structure, evidence, objections, or relationships between nodes."
    )
    
    if st.button("Ask Question", type="primary", disabled=not question):
        with st.spinner("🤔 Generating answer..."):
            
            # --- QA Logic ---
            answer_data = None
            error_msg = None
            
            # 1. Try Real Q&A with new module
            if qa_module_available:
                try:
                    # Convert old history format to ChatTurn objects
                    history_turns = []
                    for qa in st.session_state.qa_history:
                        # Handle both old and new format
                        if isinstance(qa.get('answer'), dict):
                            # Old format
                            history_turns.append(ChatTurn(
                                question=qa['question'],
                                answer=qa['answer'].get('answer', ''),
                                cited_node_ids=qa['answer'].get('sources', [])
                            ))
                        else:
                            # New format
                            history_turns.append(ChatTurn(
                                question=qa['question'],
                                answer=qa['answer'],
                                cited_node_ids=qa.get('cited_node_ids', [])
                            ))
                    
                    # Call answer_question
                    client = get_llm_client()
                    response = answer_question(
                        graph=graph_data,
                        selected_node_ids=selected_nodes,
                        question=question,
                        history=history_turns,
                        client=client
                    )
                    
                    # Convert to UI format
                    answer_data = {
                        "answer": response.answer,
                        "confidence": response.confidence,
                        "cited_node_ids": response.cited_node_ids,
                        "followups": response.followups,
                        "notes": response.notes
                    }
                    
                except Exception as e:
                    import traceback
                    error_msg = str(e)
                    print(f"Q&A module error: {e}")
                    print(traceback.format_exc())
            
            # 2. Fallback to Mock
            if not answer_data:
                if error_msg:
                    st.warning(f"⚠️ Real Q&A failed ({error_msg}), using mock fallback.")
                answer_data = get_mock_qa_answer(question, selected_nodes, graph_data)
            
            # Store in history (new format)
            st.session_state.qa_history.append({
                "question": question,
                "answer": answer_data.get('answer', answer_data) if isinstance(answer_data.get('answer'), str) else answer_data['answer'],
                "confidence": answer_data.get('confidence', 0.75),
                "cited_node_ids": answer_data.get('cited_node_ids', []),
                "followups": answer_data.get('followups', []),
                "notes": answer_data.get('notes'),
                "timestamp": datetime.now().isoformat()
            })
            st.rerun()
    
    # Display Q&A history
    if st.session_state.qa_history:
        st.markdown("---")
        st.markdown("### 📜 Conversation History")
        
        for i, qa in enumerate(reversed(st.session_state.qa_history)):
            with st.expander(f"Q: {qa['question'][:60]}...", expanded=(i == 0)):
                st.markdown(f"**A:** {qa.get('answer', 'N/A')}")
                
                # Confidence
                conf_class = get_confidence_class(qa.get('confidence', 0.5))
                st.markdown(f"""
                <span class="confidence-badge {conf_class}">
                    Confidence: {qa.get('confidence', 0.5):.0%}
                </span>
                """, unsafe_allow_html=True)
                
                # Cited nodes (new format)
                cited_ids = qa.get('cited_node_ids', [])
                if cited_ids:
                    st.markdown("**📌 Cited nodes:**")
                    cited_cols = st.columns(min(len(cited_ids), 4))
                    for idx, node_id in enumerate(cited_ids):
                        node = next((n for n in graph_data["nodes"] if n["id"] == node_id), None)
                        if node:
                            with cited_cols[idx % 4]:
                                # Make cited node IDs clickable (button to select them)
                                if st.button(
                                    f"{node_id}: {node['type'][:4]}",
                                    key=f"cite_{i}_{node_id}",
                                    help=f"Click to select: {node['label'][:40]}"
                                ):
                                    # Select this node
                                    if node_id not in st.session_state.selected_nodes:
                                        st.session_state.selected_nodes.append(node_id)
                                        st.session_state.selected_node = node
                                    st.rerun()
                
                # Follow-up suggestions (new format)
                followups = qa.get('followups', [])
                if followups:
                    st.markdown("**💡 Follow-up suggestions:**")
                    for fu in followups[:3]:  # Show max 3
                        st.caption(f"• {fu}")
                
                # Notes (new format)
                notes = qa.get('notes')
                if notes:
                    st.caption(f"ℹ️ {notes}")


def render_edit_panel(node: dict):
    """Render the edit panel for correcting node information."""
    
    st.markdown("### Edit Node")
    
    # Edit form
    with st.form("edit_node_form"):
        new_type = st.selectbox(
            "Node Type",
            options=["claim", "premise", "objection", "reply", "conclusion", "other"],
            index=["claim", "premise", "objection", "reply", "conclusion", "other"].index(node["type"])
        )
        
        new_label = st.text_input("Label", value=node["label"])
        new_paraphrase = st.text_area("Paraphrase", value=node["paraphrase"])
        
        col1, col2 = st.columns(2)
        with col1:
            submitted = st.form_submit_button("Save Changes", type="primary")
        with col2:
            mark_incorrect = st.form_submit_button("Mark as Incorrect", type="secondary")
        
        if submitted:
            # Update node in session state (mock - doesn't persist)
            for n in st.session_state.graph_data["nodes"]:
                if n["id"] == node["id"]:
                    n["type"] = new_type
                    n["label"] = new_label
                    n["paraphrase"] = new_paraphrase
                    break
            st.success("Node updated! (Changes are session-only in this mockup)")
            st.rerun()
        
        if mark_incorrect:
            st.warning("Node flagged for review. In production, this would be logged for model improvement.")


# =============================================================================
# MAIN APPLICATION
# =============================================================================

def main():
    # Header
    st.markdown('<p class="main-header">Argument Graph Builder</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Transform dense argumentative text into interactive knowledge graphs</p>', unsafe_allow_html=True)
    
    # Sidebar - Input Controls
    with st.sidebar:
        st.markdown("## Input")
        
        # Toggle to hide/show input controls in sidebar
        show_input = st.toggle(
            "Show input controls",
            value=st.session_state.show_input_panel,
            key="show_input_toggle",
            help="Hide input controls to reduce clutter while exploring the graph. Controls remain accessible in the main area."
        )
        if show_input != st.session_state.show_input_panel:
            st.session_state.show_input_panel = show_input
        
        if st.session_state.show_input_panel:
            # Example texts dropdown
            sample_texts = get_sample_texts()
            example_choice = st.selectbox(
                "Load example text:",
                options=["-- Select --"] + list(sample_texts.keys()),
                key="example_dropdown"
            )
            
            if example_choice != "-- Select --" and example_choice in sample_texts:
                if st.button("Load Example"):
                    st.session_state.input_text = load_sample_text(sample_texts[example_choice])
                    st.rerun()
            
            st.markdown("---")
            
            # Text input
            input_text = st.text_area(
                "Paste your text:",
                value=st.session_state.input_text,
                height=200,
                placeholder="Paste philosophical or argumentative text here...",
                key="text_input"
            )
            
            # PDF upload
            uploaded_file = st.file_uploader(
                "Or upload PDF:",
                type=["pdf"],
                help="Upload a PDF to extract and analyze its text"
            )
            
            # Handle PDF upload
            if uploaded_file is not None:
                try:
                    from backend.pdf_extraction import extract_text_from_pdf
                    import hashlib
                    
                    # Read PDF bytes
                    pdf_bytes = uploaded_file.read()
                    
                    # Cache extraction by file hash (using SHA256 for consistency)
                    @st.cache_data(show_spinner=False)
                    def cached_pdf_extraction(pdf_bytes_data, pdf_hash):
                        """Cache PDF extraction by hash to avoid re-extraction."""
                        return extract_text_from_pdf(pdf_bytes_data)
                    
                    # Compute hash for cache key
                    pdf_hash = hashlib.sha256(pdf_bytes).hexdigest()
                    
                    with st.spinner("Extracting text from PDF..."):
                        pdf_result = cached_pdf_extraction(pdf_bytes, pdf_hash)
                    
                    # Show extraction stats and warnings
                    st.success(f"✅ PDF extracted: {pdf_result.page_count} pages, {pdf_result.stats['char_count']} characters")
                    
                    if pdf_result.warnings:
                        for warning in pdf_result.warnings:
                            st.warning(f"⚠️ {warning}")
                    
                    # Show text preview
                    with st.expander("📄 Preview extracted text (first 500 chars)"):
                        preview_text = pdf_result.text[:500]
                        if len(pdf_result.text) > 500:
                            preview_text += "..."
                        st.text(preview_text)
                        st.caption(f"Total: {len(pdf_result.text)} characters")
                    
                    # Button to use PDF text
                    if st.button("Use PDF Text for Extraction"):
                        st.session_state.input_text = pdf_result.text
                        # Store PDF metadata for later use
                        st.session_state.pdf_metadata = {
                            "source_type": "pdf",
                            "page_count": pdf_result.page_count,
                            "pdf_extraction_engine": "PyMuPDF",
                            "pdf_extraction_warnings": pdf_result.warnings,
                            "stats": pdf_result.stats
                        }
                        st.rerun()
                    
                except ImportError:
                    st.error("PDF extraction module not available. Install pymupdf: `pip install pymupdf`")
                except Exception as e:
                    st.error(f"Failed to extract PDF: {e}")
                    import logging
                    logging.exception("PDF extraction error")
            
            st.markdown("---")
            
            # Sync input text from widget to session state
            if input_text:
                st.session_state.input_text = input_text
            
            # Get the text to use for extraction
            text_to_extract = st.session_state.input_text
            
            # Run extraction button
            if st.button("Run Extraction", type="primary", disabled=not text_to_extract):
                st.session_state.extraction_status = "extracting"
                st.rerun()
            
            # Status feedback
            if st.session_state.extraction_status == "extracting":
                run_extraction()
            
            if st.session_state.extraction_status == "done" and st.session_state.graph_data:
                n_nodes = len(st.session_state.graph_data["nodes"])
                n_edges = len(st.session_state.graph_data["edges"])
                st.success(f"Done! {n_nodes} nodes, {n_edges} relations")
            
            st.markdown("---")
            
            # Layout options
            if st.session_state.graph_data:
                st.markdown("**Graph Layout**")
                use_server_layout = st.checkbox(
                    "Optimize layout (minimize edge crossings)",
                    value=st.session_state.use_server_layout,
                    key="layout_checkbox",
                    help="Enable server-side layout optimization using the barycenter heuristic to reduce edge crossings and overlaps."
                )
                if use_server_layout != st.session_state.use_server_layout:
                    st.session_state.use_server_layout = use_server_layout
                    st.rerun()
                
                # Show layout metrics if available
                if st.session_state.use_server_layout and 'graph_layout_metrics' in st.session_state:
                    metrics = st.session_state.graph_layout_metrics
                    st.caption(f"📊 Layout quality: {metrics['crossings']} edge crossings, {metrics['layers']} layers")
            
            st.markdown("---")
            
            # Export button
            if st.session_state.graph_data:
                graph_json = json.dumps(st.session_state.graph_data, indent=2)
                st.download_button(
                    "Export Graph JSON",
                    data=graph_json,
                    file_name="argument_graph.json",
                    mime="application/json"
                )
        else:
            # When input controls are hidden, show brief status
            st.caption("Input controls hidden. Toggle above to show.")
            if st.session_state.extraction_status == "done" and st.session_state.graph_data:
                n_nodes = len(st.session_state.graph_data["nodes"])
                n_edges = len(st.session_state.graph_data["edges"])
                st.success(f"{n_nodes} nodes, {n_edges} relations")
    
    # Main content area
    if st.session_state.graph_data is None:
        # Welcome screen
        st.markdown("""
        ## Welcome!
        
        This tool helps you understand complex argumentative texts by:
        
        1. **Extracting** argument components (claims, premises, objections, replies)
        2. **Visualizing** them as an interactive graph
        3. **Explaining** each component with original spans and paraphrases
        4. **Answering** your questions about the argument structure
        
        ### Getting Started
        
        1. Use the sidebar to paste text or load an example
        2. Click "Run Extraction" to generate the argument graph
        3. Click on nodes to explore details
        4. Select nodes to ask questions about them
        
        ---
        
        ### Legend
        """)
        
        # Render legend with color swatches for all node types
        legend_cols = st.columns(5)
        for idx, node_type in enumerate(get_all_node_types()):
            with legend_cols[idx]:
                color = get_node_color(node_type)
                label = get_node_label(node_type)
                description = get_node_description(node_type)
                
                # Display color swatch + label + description
                st.markdown(
                    f'<div style="display: flex; align-items: center; gap: 8px; margin-bottom: 4px;">'
                    f'<div style="width: 20px; height: 20px; background-color: {color}; '
                    f'border-radius: 3px; flex-shrink: 0;"></div>'
                    f'<strong>{label}</strong>'
                    f'</div>'
                    f'<div style="font-size: 0.85em; color: #666; margin-left: 28px;">{description}</div>',
                    unsafe_allow_html=True
                )
        
        # Add edge/arrow color legend
        st.markdown("---")
        st.markdown("**Arrows:**")
        edge_cols = st.columns(2)
        for idx, relation in enumerate(get_all_edge_relations()):
            with edge_cols[idx]:
                color = get_edge_color(relation)
                label = get_edge_label(relation)
                description = get_edge_description(relation)
                
                # Display arrow color indicator + label + description
                st.markdown(
                    f'<div style="display: flex; align-items: center; gap: 8px; margin-bottom: 4px;">'
                    f'<div style="width: 30px; height: 3px; background-color: {color}; '
                    f'border-radius: 1px; flex-shrink: 0;"></div>'
                    f'<strong>{label}</strong>'
                    f'</div>'
                    f'<div style="font-size: 0.85em; color: #666; margin-left: 38px;">{description}</div>',
                    unsafe_allow_html=True
                )
        
    else:
        # Graph view
        graph_data = st.session_state.graph_data
        
        # When sidebar input is hidden, provide access to extraction controls in main area
        if not st.session_state.show_input_panel:
            with st.expander("Input & Extraction", expanded=False):
                sample_texts = get_sample_texts()
                exp_col1, exp_col2 = st.columns([2, 1])
                with exp_col1:
                    example_choice_main = st.selectbox(
                        "Load example text:",
                        options=["-- Select --"] + list(sample_texts.keys()),
                        key="example_dropdown_main"
                    )
                with exp_col2:
                    if example_choice_main != "-- Select --" and example_choice_main in sample_texts:
                        if st.button("Load Example", key="load_example_main"):
                            st.session_state.input_text = load_sample_text(sample_texts[example_choice_main])
                            st.rerun()
                
                input_text_main = st.text_area(
                    "Paste your text:",
                    value=st.session_state.input_text,
                    height=150,
                    placeholder="Paste philosophical or argumentative text here...",
                    key="text_input_main"
                )
                if input_text_main:
                    st.session_state.input_text = input_text_main
                
                if st.button("Run Extraction", type="primary", disabled=not st.session_state.input_text, key="run_extraction_main"):
                    st.session_state.extraction_status = "extracting"
                    st.rerun()
                
                if st.session_state.extraction_status == "extracting":
                    run_extraction()
        
        # Tabs for different views
        tab1, tab2 = st.tabs(["Graph View", "Q&A Panel"])
        
        with tab1:
            # Graph controls - first row
            ctrl_col1, ctrl_col2, ctrl_col3, ctrl_col4 = st.columns([2, 2, 1, 1])
            
            with ctrl_col1:
                # Legend with color swatches
                legend_html = '<div style="display: flex; gap: 12px; flex-wrap: wrap; align-items: center;">'
                legend_html += '<strong style="margin-right: 4px;">Legend:</strong>'
                
                # Node types
                for node_type in get_all_node_types():
                    color = get_node_color(node_type)
                    label = get_node_label(node_type)
                    legend_html += (
                        f'<div style="display: inline-flex; align-items: center; gap: 4px;">'
                        f'<div style="width: 12px; height: 12px; background-color: {color}; '
                        f'border-radius: 2px;"></div>'
                        f'<span style="font-size: 0.9em;">{label}</span>'
                        f'</div>'
                    )
                
                # Separator
                legend_html += '<span style="margin: 0 8px; color: #ccc;">•</span>'
                
                # Edge relations (arrows)
                for relation in get_all_edge_relations():
                    color = get_edge_color(relation)
                    label = get_edge_label(relation)
                    legend_html += (
                        f'<div style="display: inline-flex; align-items: center; gap: 4px;">'
                        f'<div style="width: 20px; height: 2px; background-color: {color}; '
                        f'border-radius: 1px;"></div>'
                        f'<span style="font-size: 0.9em;">{label}</span>'
                        f'</div>'
                    )
                
                legend_html += '</div>'
                st.markdown(legend_html, unsafe_allow_html=True)
            
            with ctrl_col2:
                # Filter by node type - use dynamic list from config
                all_types = get_all_node_types() + ["other"]
                filter_types = st.multiselect(
                    "Filter by type:",
                    options=all_types,
                    default=all_types,
                    key="type_filter"
                )
            
            with ctrl_col3:
                # Clear selection
                if st.button("Clear Selection", help="Clear all selected nodes"):
                    st.session_state.selected_nodes = []
                    st.session_state.selected_node = None
                    st.rerun()
            
            with ctrl_col4:
                # Focus mode toggle
                focus_mode = st.toggle(
                    "Focus mode",
                    value=st.session_state.focus_mode,
                    key="focus_mode_toggle",
                    help="Maximizes graph canvas by hiding the details panel. Details become accessible in an expander below the graph."
                )
                if focus_mode != st.session_state.focus_mode:
                    st.session_state.focus_mode = focus_mode
            
            # Filter graph data
            filtered_graph = {
                "nodes": [n for n in graph_data["nodes"] if n["type"] in filter_types],
                "edges": graph_data["edges"],
                "meta": graph_data["meta"]
            }
            
            # Track hidden selections for feedback
            original_selected = set(st.session_state.selected_nodes)
            filtered_node_ids = {n["id"] for n in filtered_graph["nodes"]}
            new_selected_nodes = [
                node_id for node_id in st.session_state.selected_nodes 
                if node_id in filtered_node_ids
            ]
            hidden_selections = original_selected - set(new_selected_nodes)
            
            # Remove hidden nodes from selection due to filtering
            if hidden_selections:
                st.session_state.selected_nodes = new_selected_nodes
                # Show brief, non-alarming feedback when nodes are hidden by filters
                st.toast("Some selected nodes were hidden by filters and removed from selection.", icon="info")
            
            # Clear selected_node if it was hidden by filter
            if st.session_state.selected_node and st.session_state.selected_node["id"] not in filtered_node_ids:
                st.session_state.selected_node = None
            
            # Helper function to get selection summary text
            def get_selection_summary():
                if not st.session_state.selected_nodes:
                    return "No nodes selected"
                count = len(st.session_state.selected_nodes)
                primary_node = st.session_state.selected_node
                if primary_node:
                    label = primary_node['label'][:30] + "..." if len(primary_node['label']) > 30 else primary_node['label']
                    return f"Selected: {count} node(s) (primary: {label})"
                return f"Selected: {count} node(s)"
            
            # Determine graph height based on focus mode
            graph_height = 900 if st.session_state.focus_mode else 650
            
            if st.session_state.focus_mode:
                # FOCUS MODE: Full width graph with details below in expander
                
                # Focus mode indicator
                st.caption("Focus mode: ON - details panel hidden, graph maximized")
                
                st.markdown("### Argument Graph")
                
                # Render graph at full width with increased height
                render_graph_and_handle_selection(filtered_graph, graph_data, graph_height)
                
                st.caption("Tip: Click a node to select it. Use Ctrl/Cmd-click for multi-select. Click empty canvas to clear selection.")
                
                # Selection summary always visible
                st.caption(f"{get_selection_summary()}")
                
                # Details/Edit panel as collapsible expander below graph
                with st.expander("Details / Edit", expanded=False):
                    if st.session_state.selected_node:
                        node = st.session_state.selected_node
                        
                        # Use columns for side-by-side layout in expander
                        detail_col, edit_col = st.columns(2)
                        
                        with detail_col:
                            st.markdown("#### Node Details")
                            render_node_detail_panel(node, graph_data)
                        
                        with edit_col:
                            st.markdown("#### Edit Node")
                            render_edit_panel(node)
                    else:
                        st.info("Select a node from the graph to see details")
                        
                        # Show graph statistics
                        st.markdown("#### Graph Statistics")
                        
                        stats_col1, stats_col2 = st.columns(2)
                        with stats_col1:
                            type_counts = {}
                            for n in graph_data["nodes"]:
                                type_counts[n["type"]] = type_counts.get(n["type"], 0) + 1
                            
                            for node_type, count in type_counts.items():
                                st.markdown(f"- **{node_type.capitalize()}:** {count}")
                        
                        with stats_col2:
                            relation_counts = {"support": 0, "attack": 0}
                            for e in graph_data["edges"]:
                                relation_counts[e["relation"]] = relation_counts.get(e["relation"], 0) + 1
                            
                            st.markdown(f"- **Support relations:** {relation_counts.get('support', 0)}")
                            st.markdown(f"- **Attack relations:** {relation_counts.get('attack', 0)}")
            
            else:
                # NORMAL MODE: Two-column layout (graph + side panel)
                graph_col, panel_col = st.columns([3, 2])
                
                with graph_col:
                    st.markdown("### Argument Graph")
                    
                    # Render interactive graph using custom bidirectional component
                    render_graph_and_handle_selection(filtered_graph, graph_data, graph_height)
                    
                    st.caption("Tip: Click a node to select it. Use Ctrl/Cmd-click for multi-select. Click empty canvas to clear selection.")
                
                with panel_col:
                    if st.session_state.selected_node:
                        node = st.session_state.selected_node
                        
                        # Detail panel tabs
                        detail_tab1, detail_tab2 = st.tabs(["Details", "Edit"])
                        
                        with detail_tab1:
                            render_node_detail_panel(node, graph_data)
                        
                        with detail_tab2:
                            render_edit_panel(node)
                    else:
                        st.info("Select a node from the graph to see details")
                        
                        # Show graph statistics
                        st.markdown("### Graph Statistics")
                        
                        type_counts = {}
                        for n in graph_data["nodes"]:
                            type_counts[n["type"]] = type_counts.get(n["type"], 0) + 1
                        
                        for node_type, count in type_counts.items():
                            st.markdown(f"- **{node_type.capitalize()}:** {count}")
                        
                        relation_counts = {"support": 0, "attack": 0}
                        for e in graph_data["edges"]:
                            relation_counts[e["relation"]] = relation_counts.get(e["relation"], 0) + 1
                        
                        st.markdown(f"- **Support relations:** {relation_counts.get('support', 0)}")
                        st.markdown(f"- **Attack relations:** {relation_counts.get('attack', 0)}")
        
        with tab2:
            render_qa_panel(graph_data, st.session_state.selected_nodes)
    
    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: #9ca3af; font-size: 0.8rem;'>"
        "Argument Graph Builder - Milestone 2 Mockup | "
        "IIS Course Project 2025"
        "</div>",
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()