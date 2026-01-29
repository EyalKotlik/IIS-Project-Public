# Argument Graph Builder

**An intelligent interactive system that transforms dense argumentative text into visual, explorable argument graphs.**

[![Milestone 2](https://img.shields.io/badge/Milestone-2%20Initial%20Mockup-blue)](milestones/milestone2_initial_mockup.md)

## Overview

Understanding complex philosophical and argumentative texts is challenging—claims, premises, objections, and counter-arguments are often intertwined in dense prose. The Argument Graph Builder solves this by automatically extracting argument components and visualizing them as interactive graphs, enabling students, researchers, and educators to explore and analyze argumentative structure efficiently. What makes this unique is the combination of automated extraction with transparent, user-controllable interfaces that show original text spans, confidence scores, and enable direct correction of AI outputs.

### Key Features

The Argument Graph Builder helps users understand complex texts by:

1. **Extracting** argument components (claims, premises, objections, replies) using hybrid NLP/LLM analysis
2. **Visualizing** them as an interactive graph with color-coded nodes and typed relations
3. **Explaining** each component with original text spans and AI-generated paraphrases
4. **Answering** natural language questions about the argument structure or specific subgraphs
5. **Enabling corrections** through direct node editing and flagging capabilities
6. **Exporting** graphs as JSON for further analysis or integration with other tools

## Quickstart Guide

### Prerequisites

- **Python 3.9 or higher** (Python 3.10 recommended for best compatibility)
- **pip** (Python package installer) OR **conda** (Anaconda/Miniconda)
- **Web browser** (Chrome, Firefox, or Safari)

### Installation Steps

**Option A: Using Conda (Recommended for Reproducibility)**

1. **Clone the repository:**
   ```bash
   git clone https://github.com/EyalKotlik/IIS-Project.git
   cd IIS-Project
   ```

2. **Create and activate the conda environment:**
   ```bash
   conda env create -f environment.yml
   conda activate argument-graph-builder
   ```

3. **Run the application:**
   ```bash
   streamlit run app_mockup/app.py
   ```

4. **Open your browser:**
   - Streamlit will automatically open `http://localhost:8501`
   - If not, manually navigate to that URL

**To update the environment when dependencies change:**
```bash
conda env update -f environment.yml --prune
```

**Option B: Using pip and venv**

1. **Clone the repository:**
   ```bash
   git clone https://github.com/EyalKotlik/IIS-Project.git
   cd IIS-Project
   ```

2. **Create a virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application:**
   ```bash
   streamlit run app_mockup/app.py
   ```

5. **Open your browser:**
   - Streamlit will automatically open `http://localhost:8501`
   - If not, manually navigate to that URL

### Environment Variables / Secrets

**For LLM-based extraction (optional but recommended):**

The application now supports real LLM-based extraction using OpenAI's GPT models. To enable this:

1. **Set your OpenAI API key** (required for LLM extraction):
   ```bash
   export OPENAI_API_KEY='your-api-key-here'
   ```
   
   Or create a `.streamlit/secrets.toml` file:
   ```toml
   OPENAI_API_KEY = "your-api-key-here"
   ```

2. **Optional LLM Configuration** (with sensible defaults):
   - `OPENAI_MODEL` - Model to use (default: `gpt-4o-mini`)
   - `LLM_TEMPERATURE` - Temperature setting (default: `0.0` for deterministic results)
   - `LLM_BUDGET_USD` - Total budget cap in USD (default: `20.0`)
   - `LLM_BUDGET_STOP_AT_USD` - Stop making calls at this threshold (default: 90% of budget)
   - `LLM_CACHE_ENABLED` - Enable response caching (default: `true`)
   - `LLM_TIMEOUT_SEC` - Request timeout in seconds (default: `60`)

3. **How caching works:**
   - LLM responses are cached locally in `.cache/llm_cache.db` (SQLite)
   - Identical requests reuse cached responses (no API cost)
   - Cache persists across runs to save money
   - To disable caching: `export LLM_CACHE_ENABLED=false`
   - To clear cache: delete the `.cache/` directory

4. **Budget enforcement:**
   - All LLM usage is tracked in `.cache/llm_usage.json`
   - Estimated costs are calculated using OpenAI's pricing
   - When budget threshold is reached, further LLM calls are refused
   - Budget tracking persists across sessions

**Without API key:**
- The app falls back to mock/stub extraction (pre-generated graphs)
- All UI features work, but extraction is not real

**Getting an API key:**
- Sign up at [platform.openai.com](https://platform.openai.com/)
- Generate an API key under API keys section
- Keep it secret and never commit it to version control

### Preprocessing Configuration

**Sentence Segmentation:**

The preprocessing pipeline uses **spaCy** for industrial-grade sentence segmentation:
- **No model download required** - Uses spaCy's fast `sentencizer` component
- **Automatic fallback** - Falls back to regex-based segmentation if spaCy is unavailable
- **Deterministic** - Same input always produces same output

**Optional Configuration:**
- `PREPROCESS_USE_SPACY` - Enable/disable spaCy (default: `true`)
  - Set to `false` to force regex fallback: `export PREPROCESS_USE_SPACY=false`

**What happens during preprocessing:**
1. Text is split into paragraphs (double newline)
2. Each paragraph is segmented into sentences using spaCy
3. Character offsets are computed for each sentence
4. Discourse markers are detected (e.g., "because", "however")
5. Sentences are flagged as argument candidates based on heuristics

**Note:** The spaCy sentencizer handles abbreviations (Dr., Mr.), decimals, and complex punctuation better than regex-based methods.

### How to Use (Basic Workflow)

1. **Input Text**
   - Select an example from the "Load example text" dropdown, OR
   - Paste your own argumentative text into the text area, OR
   - **Upload a PDF file** for automatic text extraction

2. **PDF Upload** (NEW!)
   - Click "Or upload PDF" to select a PDF file
   - The system extracts text using PyMuPDF (robust text extraction)
   - View extraction stats: page count, character count, text density
   - See warnings if the PDF is likely scanned or has low text content
   - Preview the extracted text (first 500 characters)
   - Click "Use PDF Text for Extraction" to analyze the PDF content
   - **Note**: OCR for scanned PDFs is not available - only text-based PDFs are supported

3. **Extract Graph**
   - Click "🚀 Run Extraction"
   - Watch the status feedback ("Extracting..." → "✅ Done!")

4. **Explore the Graph**
   - View the interactive visualization with color-coded nodes
   - Use the legend to understand node types (Claim, Premise, Objection, Reply)
   - Hover over nodes for quick labels
   - Click nodes to select them

5. **Inspect Node Details**
   - Click a node or use the "Select a node" dropdown
   - View the Node Detail Panel showing:
     - Node type and confidence score
     - Original text span from the source
     - AI-generated paraphrase
     - Relations (what supports/attacks this node)

6. **Ask Questions (NEW!)**
   - Navigate to the "Q&A Panel" tab
   - **Selection-first**: Select one or more nodes from the graph to focus answers on specific parts
   - Type a natural language question (e.g., "What is the main claim?", "What evidence supports this?")
   - Click "Ask Question" and review the AI-generated answer
   - **Features**:
     - Grounded answers with **citations** (cited node IDs that exist in the graph)
     - **Confidence scores** indicating answer reliability
     - **Follow-up suggestions** (2-4 relevant questions to explore further)
     - **Conversation history** with expandable cards
     - **Clickable citations**: Click cited node IDs to select/highlight them in the graph
     - **Chat memory**: The system remembers previous exchanges for better follow-ups

7. **Edit or Export**
   - Use the "Edit" tab in node details to correct errors
   - Click "Export JSON" to save the graph for further use

## Project Structure

```
/app_mockup/                    # Main application directory
  app.py                        # Streamlit UI (main entry point)
  llm_extractor.py              # Real LLM-based extraction pipeline
  extractor_stub.py             # Mock extraction fallback (no API key needed)
  
  /backend/                     # Backend modules
    preprocessing.py            # Text preprocessing (segmentation, markers)
    llm_client.py               # LLM API client (with caching & budget tracking)
    llm_config.py               # Configuration management
    llm_cache.py                # SQLite-based response caching
    llm_budget.py               # API cost tracking
    llm_schemas.py              # Pydantic schemas for structured outputs
    llm_exceptions.py           # Custom error handling
    qa_module.py                # Graph-grounded Q&A
    graph_construction.py       # Graph node/edge data structures
    pdf_extraction.py           # PDF text extraction (NEW!)
    
    /extraction/                # Advanced extraction features
      synthetic_claims.py       # Implicit claim generation
      premise_clustering.py     # Premise grouping
      conclusion_inference.py   # Conclusion node detection
  
  /components/                  # Custom Streamlit components
    vis_network_select/         # Interactive graph visualization
  
  /sample_data/                 # Sample texts and graphs
    sample_text_*.txt           # Example argumentative texts
    sample_graph_*.json         # Pre-extracted graphs

/tests/                         # Test suite
  test_preprocessing.py         # Preprocessing tests (57 tests)
  test_llm_extractor.py         # Extraction pipeline tests
  test_qa_module.py             # Q&A module tests (26 tests)
  test_synthetic_claims.py      # Synthetic claims tests
  test_conclusion_inference.py  # Conclusion detection tests
  test_pdf_extraction.py        # PDF extraction tests (NEW!)
  /data/                        # Test fixtures (NEW!)
    sample_argument.pdf         # Test PDF with argumentative text
    scanned_low_text.pdf        # Test PDF for scanned detection
  /live/                        # Live API tests (opt-in only)

/milestones/                    # Milestone deliverables
  milestone2_initial_mockup.md  # Milestone 2 writeup
  m2_walkthrough_script.md      # Video walkthrough script
  m2_screenshots/               # UI screenshots for documentation

/scripts/                       # Development utilities
  verify_*.py                   # Verification scripts
  capture_*.py                  # Screenshot automation

/.github/                       # GitHub configuration
  copilot-instructions.md       # Development guidelines

environment.yml                 # Conda environment (recommended)
requirements.txt                # pip requirements (alternative)
README.md                       # This file
ROADMAP.md                      # Development roadmap
```

## Milestone Artifacts

| Deliverable | Location |
|-------------|----------|
| **Milestone 1 Proposal** | [Milestone 1 Project Proposal.pdf](Milestone%201%20Project%20Proposal.pdf) |
| **Milestone 2 Writeup** | [milestones/milestone2_initial_mockup.md](milestones/milestone2_initial_mockup.md) |
| **Walkthrough Script** | [milestones/m2_walkthrough_script.md](milestones/m2_walkthrough_script.md) |
| **Screenshots** | [milestones/m2_screenshots/](milestones/m2_screenshots/) |
| **Runnable Prototype** | [app_mockup/app.py](app_mockup/app.py) |
| **Sample Data** | [app_mockup/sample_data/](app_mockup/sample_data/) |
| **Roadmap** | [ROADMAP.md](ROADMAP.md) |

## Contributing

This project follows milestone-based development. Before submitting changes:

1. Update relevant documentation in `/docs/` if behavior changes
2. **Run tests** to ensure your changes don't break existing functionality
3. Run the app locally to verify functionality
4. Update the ROADMAP.md if completing planned tasks
5. Follow the PR template checklist (see `.github/PULL_REQUEST_TEMPLATE.md`)

## Testing

This project uses **pytest** for automated testing. Tests cover the preprocessing pipeline (sentence segmentation, discourse marker detection, candidate flagging) with comprehensive unit, integration, and regression tests.

### Running Tests

```bash
# Run all tests
pytest

# Run tests with verbose output
pytest -v

# Run specific test categories
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests only
pytest -m regression    # Regression tests with golden outputs
pytest -m negative      # Edge cases and error conditions

# Run tests with coverage report
pytest --cov=app_mockup --cov-report=term

# Run human-readable demo test
pytest -k demo_pipeline -s

# Run live API tests (COSTS REAL MONEY - see below)
RUN_LIVE_API_TESTS=1 pytest -m live_api -s
```

### Test Structure

Tests are organized in the `tests/` directory:
- **test_preprocessing.py** - 57 tests for preprocessing pipeline (upgraded with spaCy)
  - Sentence segmentation (offsets, paragraphs, punctuation, abbreviations)
  - spaCy-specific tests (abbreviations, decimals, complex punctuation)
  - Fallback tests (env variable, regex fallback validation)
  - Determinism tests (consistent results with spaCy)
  - Discourse marker detection (case-insensitive, multi-word, punctuation tolerance)
  - Candidate flagging (heuristics, boundary conditions)
  - Negative tests (unicode, whitespace, edge cases)
  - Regression tests with golden outputs
- **test_qa_module.py** - 26 tests for Q&A module
  - Context building (selection-first, neighborhood expansion, global overview)
  - Prompt generation (grounding rules, citations)
  - Chat memory (history management, summarization)
  - Integration tests (mocked LLM calls)
  - Determinism tests
- **test_llm_extractor.py** - Tests for main extraction pipeline
- **test_synthetic_claims.py** - Tests for implicit claim generation
- **test_conclusion_inference.py** - Tests for conclusion node detection
- **test_llm_integration.py** - Tests for LLM integration (all mocked, no API calls)
- **tests/live/** - Live API tests (require opt-in)
  - test_openai_live.py - Live extraction tests
  - test_qa_live.py - Live Q&A tests
  - test_synthetic_claims_live.py - Live synthetic claims tests
  - test_conclusion_extraction_live.py - Live conclusion detection tests

### Live API Tests (⚠️ CAUTION: Real Costs)

The project includes **minimal live tests** that make real OpenAI API calls. These are **skipped by default** to prevent accidental costs.

**To run live tests:**
1. Set your OpenAI API key: `export OPENAI_API_KEY=sk-...`
2. Explicitly opt-in: `export RUN_LIVE_API_TESTS=1`
3. Run: `pytest -m live_api -s`

**Safety controls:**
- Only 3 minimal API calls total (~$0.0002 USD estimated cost)
- Forces `gpt-4o-mini` (cheapest model)
- Uses `temperature=0` (deterministic)
- Small token limits (200-500 max output tokens)
- Tests are skipped without explicit opt-in

**What the tests verify:**
- LLM client smoke test (basic connectivity, usage tracking)
- Structured output end-to-end (ComponentClassificationResult schema)
- Q&A end-to-end (QaResponse schema, citation validation, confidence scoring)

⚠️ **Important:** Live tests consume real OpenAI credits. Only run when needed for integration verification.

### Test Requirements

- All tests are **deterministic** (no flaky tests)
- No network calls or large model downloads (except live tests with opt-in)
- Tests complete in under 1 second (except live tests)
- **All tests must pass** before merging PRs (excluding live tests in CI)

For detailed testing guidelines, see `.github/copilot-instructions.md`.

## LLM Integration

The project includes a production-ready LLM integration layer using **LangChain + OpenAI**:

### Features
- **Structured outputs** - Pydantic schemas ensure type-safe LLM responses
- **Response caching** - SQLite-based persistent cache reduces API costs
- **Budget tracking** - Automatic cost tracking with hard budget caps
- **Error handling** - Graceful degradation when API errors occur
- **Configuration** - Environment variables and Streamlit secrets support

### Usage Example

```python
from app_mockup.backend.llm_client import get_llm_client
from app_mockup.backend.llm_schemas import ComponentClassificationResult

# Get configured client
client = get_llm_client()

# Make a call with structured output
result = client.call_llm(
    task_name="classify_component",
    system_prompt="You are an argument mining expert...",
    user_prompt="Classify this text: ...",
    schema=ComponentClassificationResult
)

# Access typed result
classification = result["result"]
print(f"Label: {classification.label}")
print(f"Confidence: {classification.confidence}")
```

### Cost Control
- Default model: **gpt-4o-mini** (~$0.15 per 1M input tokens)
- Budget cap: $20 total (configurable)
- Caching: Identical requests incur no API cost
- Token estimation: Automatic usage tracking

### Switching Models
To use a different model:
```bash
export OPENAI_MODEL='gpt-4o'  # More capable but more expensive
```

See `scripts/demo_llm_integration.py` for a complete working example.



## Team

HAI Course Project — Winter 2025

**Course:** Intelligent Interactive Systems  
**Repository:** [github.com/EyalKotlik/IIS-Project](https://github.com/EyalKotlik/IIS-Project)

## License

This project is for educational purposes as part of the Intelligent Interactive Systems course.

## Known Limitations & Troubleshooting

### Current Mockup Limitations

- **Stubbed Extraction**: The current version uses pre-generated graphs for sample texts and creates placeholder graphs for custom input. Real NLP/LLM extraction is not yet implemented.
- **No Persistence**: Edits to nodes are session-based only and not saved between runs.
- **PDF Upload**: PDF upload UI exists but extraction is mocked—files are not actually parsed.
- **Limited Sample Data**: Only two pre-extracted examples are available (Death Penalty and AI Regulation arguments).

### Common Issues

**Issue:** Streamlit app won't start
- **Solution:** Ensure Python 3.9+ is installed: `python3 --version`
- **Solution:** Check if dependencies are installed: `pip list | grep streamlit`
- **Solution:** Try reinstalling: `pip install --upgrade -r requirements.txt`

**Issue:** Browser doesn't open automatically
- **Solution:** Manually navigate to `http://localhost:8501`
- **Solution:** Check if port 8501 is already in use: try `streamlit run app_mockup/app.py --server.port 8502`

**Issue:** Custom text produces minimal/placeholder graphs
- **Expected behavior** in mockup—full extraction requires the production backend
- The system will still demonstrate the UI with basic node structure

**Issue:** Graph visualization doesn't render
- **Solution:** Clear browser cache and reload
- **Solution:** Try a different browser (Chrome/Firefox recommended)
- **Solution:** Check browser console for JavaScript errors

**Issue:** Node selection doesn't work
- **Solution:** Ensure you're clicking directly on the node circle, not the label
- **Alternative:** Use the "Select a node" dropdown instead of clicking

### PDF Upload Issues

**Issue:** PDF upload fails with "PDF extraction module not available"
- **Solution:** Install PyMuPDF: `pip install pymupdf`
- **Solution:** If using conda, run: `conda env update -f environment.yml --prune`

**Issue:** PDF extracted but shows warning "Likely scanned PDF"
- **Cause:** The PDF contains images of text rather than actual text
- **Solution:** Use a text-based PDF (not a scan or image)
- **Solution:** If you have the original document, export it as PDF from the source application
- **Workaround:** Copy text manually from the PDF and paste into the text area
- **Future:** OCR support is planned but not yet implemented

**Issue:** PDF extracts but text is garbled or nonsensical
- **Cause:** PDF may have unusual encoding or complex layout
- **Solution:** Try copying text manually from the PDF instead
- **Solution:** Use a different PDF viewer to export text, then paste into text area

**Issue:** PDF extraction shows very low character count
- **Cause:** PDF may be mostly images or have protection settings
- **Solution:** Check if the PDF allows text selection/copying
- **Solution:** Try opening the PDF in a viewer and copying text manually

**Issue:** PDF extracted text has formatting issues (extra spaces, broken words)
- **Explanation:** Text cleanup is applied automatically but may not be perfect
- **Review:** Use the "Preview extracted text" expander to check quality
- **Workaround:** If text quality is poor, consider manual copy-paste instead

### Production Issues (Future)

### Potential Issues with Real Extraction (If Implemented)

**Missing API Keys**
- Symptom: Extraction fails immediately or returns generic errors
- Solution: Set required environment variables in `.streamlit/secrets.toml`

**Parsing Failures**
- Symptom: Graph contains only 1-2 nodes or extraction times out
- Possible causes: Text too long, ambiguous structure, or complex nested arguments
- Solution: Break text into smaller sections or simplify input

## Documentation

For comprehensive documentation, see the [`/docs/`](docs/) directory:

- **[Architecture](docs/architecture.md)** — System components and data flow
- **[Intelligence Design](docs/intelligence_design.md)** — How extraction and Q&A work
- **[UI Guide](docs/ui_guide.md)** — Detailed user task walkthroughs
- **[HAI Design Principles](docs/hai_design_principles.md)** — Human-AI interaction guidelines
- **[Evaluation Plan](docs/evaluation_plan.md)** — Plans for user and LLM-based evaluation
- **[Final Report Outline](docs/final_report_outline.md)** — Template for project report
- **[Developer Guide](docs/dev_guide.md)** — Repo structure and development workflow
- **[Data Formats](docs/data_formats.md)** — Graph schema and export formats

See also: **[ROADMAP.md](ROADMAP.md)** for milestone-based development plan.

## Team

HAI Course Project — Winter 2025

## License

This project is for educational purposes as part of the Intelligent Interactive Systems course.
