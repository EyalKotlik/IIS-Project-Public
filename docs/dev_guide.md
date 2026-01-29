# Developer Guide

## Overview

This guide helps developers understand the repository structure, make changes safely, and contribute to the Argument Graph Builder project.

---

## Repository Structure

```
IIS-Project/
├── README.md                          # Quickstart guide, project overview
├── ROADMAP.md                         # Milestone-based development plan
├── requirements.txt                   # Python dependencies
├── .gitignore                         # Ignored files (venv, cache, etc.)
│
├── app_mockup/                        # Main application code
│   ├── app.py                         # Streamlit entry point
│   ├── extractor_stub.py              # Mock extraction backend
│   ├── components/                    # Custom Streamlit components
│   │   └── vis_network_select/        # Interactive graph component
│   └── sample_data/                   # Pre-generated sample graphs
│       ├── sample_text_1.txt
│       ├── sample_text_2.txt
│       ├── sample_graph_1.json
│       └── sample_graph_2.json
│
├── docs/                              # Comprehensive documentation
│   ├── architecture.md                # System design and components
│   ├── intelligence_design.md         # Extraction and Q&A algorithms
│   ├── ui_guide.md                    # User task walkthroughs
│   ├── hai_design_principles.md       # HAI guidelines implementation
│   ├── evaluation_plan.md             # Evaluation methodology
│   ├── final_report_outline.md        # Report template
│   ├── dev_guide.md                   # This file
│   └── data_formats.md                # Graph schema documentation
│
├── milestones/                        # Milestone deliverables
│   ├── milestone2_initial_mockup.md
│   ├── m2_walkthrough_script.md
│   └── m2_screenshots/
│
├── scripts/                           # Utility scripts
│   └── capture_screenshots.py         # Screenshot automation
│
└── .github/                           # GitHub configuration
    └── PULL_REQUEST_TEMPLATE.md       # PR checklist
```

---

## Getting Started

### Prerequisites

- Python 3.9+
- pip
- Git
- Code editor (VS Code, PyCharm, etc.)

### Setup Development Environment

```bash
# 1. Clone the repository
git clone https://github.com/EyalKotlik/IIS-Project.git
cd IIS-Project

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. (Optional) Install development dependencies
pip install pytest black flake8 mypy

# 5. Run the application
streamlit run app_mockup/app.py
```

### Running Tests

Currently, no formal test suite exists. To add tests:

```bash
# Create test directory
mkdir tests
touch tests/__init__.py
touch tests/test_extractor.py

# Run tests
pytest tests/
```

---

## Key Files and Their Purposes

### `app_mockup/app.py`

**Purpose:** Main Streamlit application. Handles UI rendering, user input, and state management.

**Key sections:**
- **Page configuration** (lines 27-32): Set page title, icon, layout
- **Session state initialization** (search for `st.session_state`): Manage graph data, selections
- **Sidebar: Input controls** (search for `st.sidebar`): Text input, example loading, extraction button
- **Main panel: Graph visualization** (search for `vis_network_select`): Render interactive graph
- **Right panel: Node details & Q&A** (search for `st.tabs`): Display details and Q&A interface

**When to modify:**
- Adding new UI features (filters, export options)
- Changing layout or styling
- Adding new pages or views

**Dependencies:**
- `extractor_stub.py` for extraction logic
- `components/vis_network_select` for graph rendering
- Streamlit session state for data persistence

### `app_mockup/extractor_stub.py`

**Purpose:** Mock extraction backend. Simulates extraction process with pre-generated graphs.

**Key functions:**
- `extract_arguments(text)`: Main extraction function (returns graph data)
- `get_sample_texts()`: Returns available example texts
- `load_sample_text(filename)`: Loads sample text file
- `get_mock_qa_answer(question, node_ids, graph_data)`: Generates mock Q&A answer

**When to modify:**
- Implementing real extraction pipeline (replace stub with actual LLM calls)
- Adding new sample data
- Changing graph data structure

**Production replacement:**
Replace this file with:
- `extractor.py`: Real extraction using LLM APIs
- `qa_engine.py`: Real Q&A using RAG
- `graph_builder.py`: Graph construction algorithms

### `app_mockup/components/vis_network_select/`

**Purpose:** Custom Streamlit component for interactive graph visualization.

**Technology:** Wraps vis-network.js (JavaScript library) in Streamlit component.

**When to modify:**
- Changing graph layout algorithm
- Adding node/edge styling
- Implementing new interactions (drag-to-connect, right-click menus)

**Note:** Requires knowledge of Streamlit component API and JavaScript.

### `docs/*.md`

**Purpose:** Comprehensive project documentation.

**When to modify:**
- After adding new features (update architecture.md, ui_guide.md)
- After making design decisions (update hai_design_principles.md)
- After evaluation (update evaluation_plan.md with results)
- Before final submission (write final_report_outline.md)

**Best practice:** Update docs in the same PR as code changes.

---

## Common Development Tasks

### Task 1: Add a New Sample Text

**Files to modify:**
1. `app_mockup/sample_data/sample_text_3.txt` (new file)
2. `app_mockup/sample_data/sample_graph_3.json` (new file)
3. `app_mockup/extractor_stub.py`

**Steps:**
1. Create `sample_text_3.txt` with your text
2. Manually create `sample_graph_3.json` following the schema (see [data_formats.md](data_formats.md))
3. Update `get_sample_texts()` in `extractor_stub.py`:
   ```python
   def get_sample_texts() -> dict:
       return {
           "Death Penalty Argument": "sample_text_1.txt",
           "AI Regulation Argument": "sample_text_2.txt",
           "Your New Text": "sample_text_3.txt",  # Add this line
       }
   ```
4. Update `extract_arguments()` to detect and load your new sample

### Task 2: Implement Real Extraction (Replace Stub)

**High-level approach:**

1. **Create new module:** `app_mockup/extractor.py`
2. **Implement functions:**
   ```python
   def extract_arguments(text: str, api_key: str) -> dict:
       """Real extraction using LLM API."""
       # Stage 1: Preprocessing
       sentences = preprocess(text)
       
       # Stage 2: Classification
       nodes = []
       for sent in sentences:
           node = classify_component(sent, api_key)
           if node['confidence'] > 0.5:
               nodes.append(node)
       
       # Stage 3: Relation extraction
       edges = extract_relations(nodes, api_key)
       
       # Stage 4: Graph construction
       graph = build_graph(nodes, edges)
       
       return graph
   ```
3. **Replace imports in `app.py`:**
   ```python
   # Old
   from extractor_stub import extract_arguments
   
   # New
   from extractor import extract_arguments
   ```
4. **Add API key management (if needed):**
   - Use `st.secrets` for Streamlit secrets
   - Or environment variables: `os.getenv('OPENAI_API_KEY')`

**See [intelligence_design.md](intelligence_design.md) for detailed algorithm design.**

### Task 3: Add a New UI Feature (e.g., Graph Filtering)

**Example: Filter by node type**

**Steps:**

1. **Add UI controls in `app.py`:**
   ```python
   # In sidebar or main panel
   st.subheader("Filter Graph")
   show_claims = st.checkbox("Show Claims", value=True)
   show_premises = st.checkbox("Show Premises", value=True)
   show_objections = st.checkbox("Show Objections", value=True)
   show_replies = st.checkbox("Show Replies", value=True)
   ```

2. **Filter graph data before rendering:**
   ```python
   # After loading graph_data
   filtered_nodes = [
       n for n in graph_data['nodes']
       if (n['type'] == 'claim' and show_claims) or
          (n['type'] == 'premise' and show_premises) or
          (n['type'] == 'objection' and show_objections) or
          (n['type'] == 'reply' and show_replies)
   ]
   
   # Filter edges to only include nodes still visible
   visible_node_ids = {n['id'] for n in filtered_nodes}
   filtered_edges = [
       e for e in graph_data['edges']
       if e['source'] in visible_node_ids and e['target'] in visible_node_ids
   ]
   
   filtered_graph = {
       'nodes': filtered_nodes,
       'edges': filtered_edges,
       'meta': graph_data['meta']
   }
   ```

3. **Pass filtered graph to visualization:**
   ```python
   vis_network_select(filtered_graph)
   ```

4. **Update documentation:**
   - Add filtering to [ui_guide.md](ui_guide.md) (Task 4)
   - Update screenshots if necessary

### Task 4: Add User Editing Capability (Beyond Current Edit Tab)

**Example: Let users add new nodes manually**

**Steps:**

1. **Add UI in node detail panel:**
   ```python
   with st.expander("➕ Add New Node"):
       new_type = st.selectbox("Type", ["Claim", "Premise", "Objection", "Reply"])
       new_label = st.text_input("Label (short summary)")
       new_span = st.text_area("Text span")
       new_paraphrase = st.text_area("Paraphrase (optional)")
       
       if st.button("Add Node"):
           new_node = {
               "id": f"n{len(st.session_state.graph_data['nodes']) + 1}",
               "type": new_type.lower(),
               "label": new_label,
               "span": new_span,
               "paraphrase": new_paraphrase or "[User-provided]",
               "confidence": 1.0  # User-added = full confidence
           }
           st.session_state.graph_data['nodes'].append(new_node)
           st.success(f"Added node {new_node['id']}")
           st.rerun()
   ```

2. **Persist edits (optional enhancement):**
   - Save to JSON file
   - Track edit history for analysis

### Task 5: Export Graph to New Format

**Example: Export as Markdown**

**Steps:**

1. **Create export function:**
   ```python
   def export_as_markdown(graph_data: dict) -> str:
       md = "# Argument Graph\n\n"
       
       # Nodes
       md += "## Nodes\n\n"
       for node in graph_data['nodes']:
           md += f"### {node['label']} ({node['type']})\n\n"
           md += f"**Original:** {node['span']}\n\n"
           md += f"**Paraphrase:** {node['paraphrase']}\n\n"
       
       # Edges
       md += "## Relations\n\n"
       for edge in graph_data['edges']:
           src = next(n for n in graph_data['nodes'] if n['id'] == edge['source'])
           tgt = next(n for n in graph_data['nodes'] if n['id'] == edge['target'])
           md += f"- **{src['label']}** {edge['relation']} **{tgt['label']}**\n"
       
       return md
   ```

2. **Add export button in UI:**
   ```python
   md_content = export_as_markdown(st.session_state.graph_data)
   st.download_button(
       label="📄 Export as Markdown",
       data=md_content,
       file_name="argument_graph.md",
       mime="text/markdown"
   )
   ```

---

## Best Practices

### Code Style

**Python:**
- Follow PEP 8 guidelines
- Use type hints: `def func(arg: str) -> dict:`
- Max line length: 88 characters (Black default)
- Docstrings for all functions

**Example:**
```python
def classify_component(sentence: str, context: str, api_key: str) -> dict:
    """
    Classify a sentence as an argument component.
    
    Args:
        sentence: The sentence to classify
        context: Surrounding sentences for context
        api_key: LLM API key
        
    Returns:
        Dict with keys: type, label, confidence, paraphrase
    """
    # Implementation
    pass
```

**Formatting tools:**
```bash
# Auto-format code
black app_mockup/

# Check style
flake8 app_mockup/

# Type checking
mypy app_mockup/
```

### Git Workflow

**Branching:**
- `main`: Stable, deployable code
- `develop`: Integration branch (optional)
- `feature/feature-name`: Feature branches
- `fix/bug-name`: Bug fix branches

**Commit messages:**
```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:** feat, fix, docs, style, refactor, test, chore

**Example:**
```
feat(extraction): Add LLM-based component classification

- Implement classify_component() using GPT-4 API
- Add prompt template for classification
- Handle API errors with retries

Closes #12
```

**PR process:**
1. Create feature branch from `main`
2. Make changes and test locally
3. Update documentation if needed
4. Open PR with descriptive title and PR template filled
5. Request review from team
6. Address feedback
7. Merge after approval

### Testing

**Unit tests (future):**
```python
# tests/test_extractor.py
import pytest
from app_mockup.extractor import classify_component

def test_classify_claim():
    sentence = "The death penalty should be abolished."
    result = classify_component(sentence, context="", api_key="fake")
    assert result['type'] == 'claim'
    assert result['confidence'] > 0.5
```

**Integration tests:**
```python
# tests/test_integration.py
def test_full_extraction():
    text = "Sample argumentative text..."
    graph = extract_arguments(text, api_key="fake")
    assert len(graph['nodes']) > 0
    assert len(graph['edges']) > 0
```

**UI tests (Streamlit):**
- Use Streamlit's testing framework (experimental)
- Manual testing with checklist (see [ui_guide.md](ui_guide.md) tasks)

### Documentation

**When to update docs:**
- After adding new features → update [architecture.md](architecture.md), [ui_guide.md](ui_guide.md)
- After making design decisions → update [hai_design_principles.md](hai_design_principles.md)
- After changing data formats → update [data_formats.md](data_formats.md)
- After evaluation → update [evaluation_plan.md](evaluation_plan.md)

**Use PR template checklist to remember!**

---

## Troubleshooting

### Issue: Streamlit won't start

**Solution:**
```bash
# Check Python version
python3 --version  # Should be 3.9+

# Reinstall dependencies
pip install --upgrade -r requirements.txt

# Try different port
streamlit run app_mockup/app.py --server.port 8502
```

### Issue: Graph visualization not rendering

**Possible causes:**
- Browser caching issue → Hard refresh (Ctrl+Shift+R)
- JavaScript error → Check browser console
- Graph data malformed → Validate JSON schema

**Debug:**
```python
# In app.py, add debug output
st.write("Graph data:", st.session_state.graph_data)
```

### Issue: Session state not persisting

**Cause:** Streamlit reruns script on every interaction, resetting variables not in session state.

**Solution:**
```python
# Initialize in session state, not as global
if 'graph_data' not in st.session_state:
    st.session_state.graph_data = None

# Use session state throughout
st.session_state.graph_data = extract_arguments(text)
```

---

## Deployment

### Local Deployment

```bash
streamlit run app_mockup/app.py
```

### Streamlit Cloud Deployment

1. Push code to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect GitHub repo
4. Select `app_mockup/app.py` as main file
5. Add secrets in dashboard (if needed)
6. Deploy

### Docker Deployment (optional)

```dockerfile
# Dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app_mockup/ ./app_mockup/
COPY docs/ ./docs/

EXPOSE 8501

CMD ["streamlit", "run", "app_mockup/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

```bash
# Build and run
docker build -t argument-graph-builder .
docker run -p 8501:8501 argument-graph-builder
```

---

## Contributing

See [ROADMAP.md](../ROADMAP.md) for planned features and tasks.

**Before contributing:**
1. Check roadmap for priority tasks
2. Discuss major changes in issues or team meeting
3. Follow code style and git workflow
4. Update documentation
5. Test locally before PR

---

## Related Documentation

- [Architecture](architecture.md) — System design details
- [Intelligence Design](intelligence_design.md) — Extraction algorithms
- [Data Formats](data_formats.md) — Graph schema reference
- [UI Guide](ui_guide.md) — User-facing features
- [ROADMAP](../ROADMAP.md) — Development timeline
- [Implementation Plan](implementation_plan.md) — Short-term 2–3 day execution plan
