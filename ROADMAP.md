# Project Roadmap

## Overview

This roadmap helps team members understand what's been done and what work remains for the Argument Graph Builder course project. Tasks are organized by priority and workstream to make it easy to see where help is needed.

**Current Phase:** Post-Milestone 2 → Preparing for Milestone 3 (Demo Video) and Milestone 4 (Final Prototype + Report)

**Recent Update (2026-01-27):** ✅ **Repository Cleanup Complete** - Removed ~5,000 lines of unused code, consolidated around `app.py` and `llm_extractor.py` as single sources of truth. See [IMPLEMENTATION_COMPLETE_CLEANUP.md](IMPLEMENTATION_COMPLETE_CLEANUP.md) for details.

---

## Milestone Status

| Milestone | Status | Deliverables |
|-----------|--------|-------------|
| **M1: Proposal** | ✅ Complete | Project proposal document |
| **M2: Initial Mockup** | ✅ Complete | Runnable UI prototype, mockup writeup, demo video |
| **M3: Demo Video** | 📋 Next Up | 3-min demo video showcasing key features |
| **M4: Final Prototype** | 🔜 Upcoming | Real extraction, evaluation results, final report |

---

## Workstream Breakdown

### 🎨 Workstream 1: UI/UX Refinement

**Goal:** Polish the user interface based on feedback and usability testing.

**Priority:** Medium (nice-to-have for final demo)

#### Tasks (in priority order)

- [ ] **Enhance filtering controls**
  - [ ] Filter by node type (Claims, Premises, Objections, Replies)
  - [ ] Filter by confidence threshold (hide low-confidence nodes)
  - [ ] Search/filter by text content
  
- [ ] **Improve graph layout algorithm**
  - Current: Basic hierarchical layout sometimes cluttered
  - Target: Better node spacing, fewer edge crossings

- [ ] **Add graph interaction features**
  - [ ] Right-click context menu for nodes (edit, delete, etc.)
  - [ ] Drag-and-drop to create relations manually
  - [ ] Keyboard shortcuts (Tab to cycle nodes, Esc to deselect)

- [ ] **Add onboarding tutorial**
  - [ ] Interactive walkthrough for first-time users
  - [ ] Tooltips on key UI elements
  - [ ] Help panel or FAQ section

- [ ] **Responsive design**
  - [ ] Ensure usability on tablets and smaller screens
  - [ ] Adjust layout for different resolutions

---

### 🤖 Workstream 2: Extraction Backend

**Goal:** Replace stubbed extraction with real NLP/LLM-based extraction pipeline.

**Priority:** HIGH (critical for final milestone)

**Note:** Currently using pre-generated sample graphs. Real extraction is optional but would significantly enhance the project.

#### Tasks (in priority order)

- [x] **Set up LLM API integration**
  - [x] Choose provider (OpenAI via LangChain)
  - [x] Set up API key management using environment variables and Streamlit secrets
  - [x] Implement configuration module with sensible defaults
  - [x] Implement error handling with custom exceptions
  - [x] **Add structured output support** (Pydantic schemas for ComponentClassificationResult, RelationExtractionResult)
  - [x] **Implement request caching** (SQLite-based persistent cache in `.cache/`)
  - [x] **Implement budget tracking and guardrails** (token usage, cost estimation, budget enforcement)
  - [x] **Comprehensive test suite** (35 tests covering config, cache, budget, schemas, client)
  - [x] **Documentation** (README updated with API key setup, cache/budget configuration)
  - [x] Create example integration module showing how to use LLM client

- [x] **Implement preprocessing stage** ✅ **UPGRADED TO v2.0**
  - [x] Sentence segmentation (spaCy-based with regex fallback, handles abbreviations and punctuation)
  - [x] **Industrial-grade segmentation** using spaCy's sentencizer (no model download required)
  - [x] **Automatic fallback** to regex if spaCy unavailable (PREPROCESS_USE_SPACY config)
  - [x] **Accurate offset preservation** (all offsets verified to point to exact substrings)
  - [x] Discourse marker detection (rule-based, case-insensitive, multi-word markers)
  - [x] Candidate flagging (heuristics: markers, length, verb patterns)
  - [x] **Comprehensive pytest test suite** (57 tests: unit, integration, regression, negative cases, spaCy-specific)
  - [x] **spaCy test coverage** (6 segmentation tests, 2 fallback tests, 2 determinism tests, 4 edge cases)
  - [x] **Human-readable terminal demo test** (run with `pytest -k demo_pipeline -s`)
  - [x] **Testing discipline enforced** (GitHub Copilot instructions require tests for all changes)
  - [x] **Documentation updated** (README preprocessing section, IMPLEMENTATION_COMPLETE entry)
  - **Implementation:** `backend/preprocessing.py` (v2.0 with spaCy integration)
  - **Status:** Production-ready with deterministic behavior, full backward compatibility

- [x] **Implement component classification (LLM)** ✅ **COMPLETE**
  - [x] Design and test prompt templates for classification
  - [x] Send candidates to LLM with context (discourse markers)
  - [x] Parse responses and extract confidence scores
  - [x] Schema-validated structured outputs with retry logic
  - [x] Unit tests (5 tests) + live API test (1 minimal call, gated)
  - **Implementation:** `backend/extraction/component_classification.py`
  - **Status:** Fully implemented with temperature=0, caching, budget tracking

- [x] **Implement relation extraction (LLM)** ✅ **COMPLETE**
  - [x] Design prompt for pairwise relation detection
  - [x] Implement heuristic pruning (±2 sentence window, skip non_argument)
  - [x] Extract support/attack relations with confidence
  - [x] Schema-validated structured outputs with retry logic
  - [x] Unit tests (7 tests) + live API test (1 minimal call, gated)
  - **Implementation:** `backend/extraction/relation_extraction.py`
  - **Status:** Fully implemented with windowing, cost-aware pruning

- [x] **Implement paraphrase generation (LLM)** ✅ **COMPLETE**
  - [x] Design prompt template for paraphrasing
  - [x] Quality checks (length ≤120 chars, meaning drift detection)
  - [x] Fallback to trimmed original on validation failure
  - [x] Schema-validated structured outputs with retry logic
  - [x] Unit tests (10 tests) + live API test (1 minimal call, gated)
  - **Implementation:** `backend/extraction/paraphrase_generation.py`
  - **Status:** Fully implemented with validation and fallback

- [x] **Implement pipeline orchestration** ✅ **COMPLETE**
  - [x] Unified pipeline function connecting all stages
  - [x] Proper error handling and graceful degradation
  - [x] Integration test (1 test)
  - [x] Updated demo pipeline showing all stages
  - **Implementation:** `backend/extraction/pipeline.py`
  - **Status:** Full end-to-end extraction pipeline operational

- [x] **Implement graph construction** ✅ **COMPLETE**
  - [x] Merge duplicate nodes (text similarity using RapidFuzz)
  - [x] Validate graph consistency (remove cycles, orphans, invalid edges)
  - [x] Compute hierarchical layout (topological layers + ordering)
  - [x] Schema matching UI format (GraphNode, GraphEdge, Graph)
  - [x] Comprehensive unit tests (32 tests covering all features)
  - [x] Golden snapshot test for deterministic output
  - [x] Integration with extraction pipeline
  - **Implementation:** `backend/graph_construction.py`
  - **Status:** Fully operational with deduplication, consistency checks, and layout

- [x] **Enhanced LLM extraction with conclusion support** ✅ **COMPLETE** (Jan 2026)
  - [x] ~~Added `conclusion` node type to schema and classification~~ **DEPRECATED**
  - [x] Split extraction into 2-call approach (classification → relations)
  - [x] Strengthened system prompts with explicit definitions and constraints
  - [x] Post-processing validation (edge validation, conclusion constraint enforcement)
  - [x] Connectivity repair with heuristic bridging
  - [x] Structured input formatting using preprocessing output
  - [x] Fixed metadata to reflect gpt-4o-mini model
  - [x] Comprehensive test suite (15 unit tests + 2 live tests)
  - **Implementation:** `llm_extractor.py` (2-call extraction with validation)
  - **Status:** Production-ready with improved connectivity and constraint enforcement

- [x] **Post-hoc conclusion inference (v2.0)** ✅ **COMPLETE** (Jan 2026)
  - [x] Removed `conclusion` from classification schema (prevents premature labeling)
  - [x] Updated classification prompts to forbid conclusion outputs
  - [x] Implemented deterministic conclusion inference based on graph structure
  - [x] Scoring algorithm: incoming support count, unique sources, sink-like position
  - [x] Hard constraint: conclusions MUST have ≥1 incoming SUPPORT edge
  - [x] Constraint enforcement: removed conclusion→non-conclusion edges
  - [x] Integrated into graph construction pipeline (Step 4.5)
  - [x] Comprehensive test suite (24 tests: scoring, candidates, selection, constraints, integration, edge cases)
  - [x] Demo script showing end-to-end behavior
  - [x] Metadata tracking for inference decisions and scores
  - **Implementation:** `backend/extraction/conclusion_inference.py`
  - **Status:** Production-ready; eliminates isolated conclusions and improves claim/conclusion separation

- [x] **Synthetic claims generation** ✅ **COMPLETE** (Jan 2026)
  - [x] Extended GraphNode schema with `is_synthetic`, `source_premise_ids`, `synthesis_method` fields
  - [x] Implemented premise clustering using heuristics (proximity, similarity, shared targets)
  - [x] LLM-based synthesis with gpt-4o-mini (strict "no hallucination" constraints)
  - [x] Graph rewiring to create 2-hop chains (premise → synthetic → high-level claim)
  - [x] Hallucination detection (regex-based checks for new numbers/names)
  - [x] Coherence validation and confidence filtering
  - [x] Integrated into graph construction pipeline (Step 4.3, after consistency checks)
  - [x] UI updates: synthetic node badges, source premise display
  - [x] Comprehensive test suite (25 unit + 5 integration + 3 edge case + 1 live test)
  - [x] Configurable enable/disable with multiple tuning options
  - **Implementation:** `backend/extraction/premise_clustering.py`, `backend/extraction/synthetic_claims.py`
  - **Status:** Production-ready; addresses "flat graph" problem by adding intermediate reasoning layers
  - **Cost:** ~$0.0001-0.001 USD per document with gpt-4o-mini

- [ ] **Optimize for cost and speed**
  - [x] Cache LLM responses (implemented with SQLite)
  - [ ] Batch API calls where possible
  - [ ] Profile and optimize slow stages

**Key Risks:**
- LLM API costs may add up quickly → **Mitigated** with caching and budget guardrails
- Extraction accuracy might be lower than expected
- Debugging can be time-consuming

**Mitigation strategies:**
- Test on small examples first
- ✅ Caching implemented early to control costs
- Keep mockup as fallback for demo

---

### 💬 Workstream 3: Q&A Module

**Goal:** Replace stubbed Q&A with real RAG-based question answering.

**Priority:** MEDIUM (enhances utility, but not core to extraction)

#### Tasks (in priority order)

- [x] **Design Q&A prompt template** ✅ **COMPLETE** (Jan 2026)
  - [x] Include instructions for grounding in sources
  - [x] Request source attribution (cited_node_ids)
  - [x] Add confidence scoring and follow-up suggestions
  - [x] JSON-only output with QaResponse schema
  - **Implementation:** `backend/qa_module.py` (_build_system_prompt, _build_user_prompt)

- [x] **Implement context retrieval** ✅ **COMPLETE** (Jan 2026)
  - [x] Selection-first policy: prioritize selected nodes
  - [x] 3-tier context: selected nodes → neighborhood (1-2 hops) → global overview
  - [x] Fallback to question-based retrieval (lexical matching) when no selection
  - [x] Adjacency-based BFS neighborhood expansion with max_nodes limit
  - [x] Graph overview with node/edge counts, type distributions, main hubs
  - **Implementation:** `backend/qa_module.py` (build_qa_context, 3-tier retrieval)

- [x] **Implement Q&A generation** ✅ **COMPLETE** (Jan 2026)
  - [x] Integration with existing LLM client (caching, budget, retries)
  - [x] Structured output parsing with QaResponse schema
  - [x] Error handling with fallback response
  - [x] Citation tracking (cited_node_ids must exist in graph)
  - [x] Confidence scoring in [0, 1] range
  - [x] Follow-up question generation (2-4 suggestions)
  - **Implementation:** `backend/qa_module.py` (answer_question)
  - **Model:** gpt-4o-mini (temperature=0 for determinism)

- [x] **Add Q&A history and chat memory** ✅ **COMPLETE** (Jan 2026)
  - [x] ChatTurn dataclass for storing Q&A exchanges
  - [x] History summarization (last N turns, configurable)
  - [x] Context includes conversation history for follow-ups
  - [x] Session-level persistence in Streamlit session_state
  - [x] UI displays history with expandable cards
  - [x] Clickable cited node IDs to select/highlight nodes
  - [x] Follow-up suggestions displayed in history
  - **Implementation:** `backend/qa_module.py` (ChatTurn, add_to_history, _summarize_history)
  - **UI Integration:** `app.py` (render_qa_panel with enhanced chat interface)

- [x] **Testing** ✅ **COMPLETE** (Jan 2026)
  - [x] 26 unit/integration tests covering all Q&A functions
  - [x] Context building tests (selection-first, neighborhood expansion, global overview)
  - [x] Prompt generation tests (grounding rules, citations)
  - [x] History management tests (trimming, summarization)
  - [x] 1 gated live API test (@pytest.mark.live_api)
  - **Test files:** `tests/test_qa_module.py`, `tests/live/test_qa_live.py`

**Status:** ✅ **FULLY OPERATIONAL** - Graph-grounded Q&A with selection-first policy, chat memory, and citation tracking

---

### 🔬 Workstream 4: Evaluation

**Goal:** Conduct user evaluation and LLM-as-user evaluation per the evaluation plan.

**Priority:** HIGH (required for final report)

**Important:** Start recruitment early! This often takes longer than expected.

#### Human User Evaluation Tasks (in priority order)

- [ ] **Recruit participants**
  - [ ] Email course lists, post on bulletin boards
  - [ ] Aim for N=12-15 participants
  - [ ] Schedule sessions
  - **Note:** Start this ASAP as recruitment is the biggest bottleneck

- [ ] **Prepare study materials**
  - [ ] Finalize task instructions
  - [ ] Prepare consent forms
  - [ ] Set up recording/note-taking

- [ ] **Run pilot study**
  - [ ] 2-3 participants to test protocol
  - [ ] Refine tasks and questionnaire based on feedback

- [ ] **Conduct main study**
  - [ ] 12-15 sessions, 20 min each
  - [ ] Record think-aloud, task performance, questionnaire

- [ ] **Analyze results**
  - [ ] Compute SUS scores, task times, accuracy
  - [ ] Thematic analysis of qualitative feedback
  - [ ] Write up findings for report

#### LLM-as-User Evaluation Tasks (in priority order)

- [ ] **Prepare evaluation corpus**
  - [ ] Select 10-15 diverse texts (philosophical, op-eds, etc.)
  - [ ] Include edge cases (ambiguous, sarcastic, implicit)

- [ ] **Run extractions on corpus**
  - [ ] Extract graphs for all texts
  - [ ] Save outputs

- [ ] **Run LLM critique**
  - [ ] Use prompt template to evaluate each graph
  - [ ] Collect scores and issues

- [ ] **Analyze LLM feedback**
  - [ ] Aggregate scores
  - [ ] Categorize failure modes
  - [ ] Identify bias patterns

---

### 📄 Workstream 5: Documentation & Reporting

**Goal:** Keep documentation up-to-date and write the final report.

**Priority:** HIGH (required deliverables)

#### Completed ✅

- [x] README with quickstart
- [x] Architecture, intelligence design, UI guide
- [x] HAI principles, evaluation plan, final report outline
- [x] Developer guide, data formats
- [x] ROADMAP (this document)

#### Remaining Tasks (in priority order)

- [ ] **Create demo video (Milestone 3)**
  - [ ] Script walkthrough based on [m2_walkthrough_script.md](milestones/m2_walkthrough_script.md)
  - [ ] Record screen capture and voiceover
  - [ ] Edit to 3 minutes
  - **This is the next major deliverable!**

- [ ] **Write final report**
  - [ ] Follow [final_report_outline.md](docs/final_report_outline.md) template
  - [ ] Sections 1-6: Introduction, Related Work, Design, Implementation, Evaluation, Discussion
  - [ ] Section 9: **Reflection on LLM use** (MUST be written by team, not AI)

- [ ] **Update documentation as features are added**
  - [ ] Update architecture.md when extraction is implemented
  - [ ] Update ui_guide.md when new features are added
  - [ ] Keep dev_guide.md current with code changes

---

### 🛠️ Workstream 6: Infrastructure & Reliability

**Goal:** Improve system reliability and maintainability.

**Priority:** MEDIUM (improves quality, but not required for passing grade)

#### Completed ✅

- [x] **Comprehensive pytest test suite**
  - [x] 45+ tests covering preprocessing pipeline
  - [x] Unit tests for segmentation, markers, candidate flagging
  - [x] Integration tests for full pipeline
  - [x] Negative/edge case tests (unicode, whitespace, long texts)
  - [x] Regression tests with golden outputs for stability
  - [x] Human-readable demo test (run: `pytest -k demo_pipeline -s`)
  - [x] **35 tests for LLM integration** (config, caching, budget tracking, schemas, client)
  
- [x] **Testing discipline and workflow**
  - [x] pytest configuration (pytest.ini with markers and settings)
  - [x] GitHub Copilot instructions (.github/copilot-instructions.md)
  - [x] Automated testing requirements for all code changes
  - [x] ROADMAP.md update requirements enforced
  - [x] PR template integration

- [x] **LLM integration infrastructure**
  - [x] LangChain + OpenAI integration via `llm_client.py`
  - [x] Configuration management (env vars + Streamlit secrets)
  - [x] SQLite-based persistent caching in `.cache/`
  - [x] Budget tracking with cost estimation and hard caps
  - [x] Structured output schemas (Pydantic models)
  - [x] Custom exceptions for error handling
  - [x] Comprehensive test coverage (all mocked, no network calls)

- [x] **DevOps: Reproducible environment setup**
  - [x] Conda `environment.yml` with pinned dependencies and Python 3.10
  - [x] README updated with conda setup instructions (Option A)
  - [x] Agent instructions enforce keeping `environment.yml` in sync with dependencies
  - [x] Tested and verified: all 80 tests pass in conda environment

**Note:** Test suite focuses on preprocessing and LLM infrastructure. Future pipeline stages (classification, relation extraction) should follow the same testing patterns.

#### Remaining Tasks (in priority order)

- [ ] **Expand test coverage for future stages**
  - [ ] Tests for component classification (when implemented)
  - [ ] Tests for relation extraction (when implemented)
  - [ ] Tests for paraphrase generation (when implemented)
  - [ ] UI/integration tests for critical paths

- [ ] **Add error handling to UI**
  - [ ] Graceful failures for API errors
  - [ ] User-friendly error messages
  - [ ] Fallback to partial results if extraction fails mid-way

- [ ] **Add logging**
  - [x] Log API calls, errors, performance metrics (LLM client has logging)
  - [ ] Help with debugging and cost tracking in UI

- [ ] **Set up CI/CD** (optional)
  - [ ] GitHub Actions for automated testing
  - [ ] Auto-deploy to Streamlit Cloud on merge

---

## What to Work On Next

### Immediate Priorities (Do These First!)

1. **Start evaluation recruitment** - This takes the longest, so begin ASAP
   - Email course lists, post on bulletin boards
   - Target: N=12-15 participants

2. **Create demo video (Milestone 3)** - Next deliverable
   - Script based on [m2_walkthrough_script.md](milestones/m2_walkthrough_script.md)
   - Record and edit to 3 minutes

3. **Prepare evaluation materials**
   - Finalize task instructions
   - Create consent forms
   - Set up recording system

### High Priority (Start Soon)

4. **Decide on extraction approach**
   - Keep mockup only, OR
   - Implement real LLM-based extraction
   - Document decision in team meeting

5. **If implementing real extraction:**
   - Set up LLM API integration
   - Start with preprocessing (sentence segmentation, etc.)
   - Test on 1-2 sample texts before scaling up

6. **Run pilot evaluation**
   - 2-3 participants to test protocol
   - Refine based on feedback

### Medium Priority (After Above is Done)

7. **Conduct main evaluation study**
   - 12-15 participant sessions
   - Record results

8. **UI improvements** (if time permits)
   - Filtering controls
   - Better graph layout
   - Additional interactions

### Final Push

9. **Write final report**
   - Use [final_report_outline.md](docs/final_report_outline.md) template
   - Team collaboration required for Section 9 (LLM reflection)

10. **Analyze evaluation results**
    - Compute metrics
    - Thematic analysis
    - Write up findings

---

## Common Pitfalls & How to Avoid Them

| Risk | How Likely? | Impact | What to Do |
|------|-------------|--------|-----------|
| **Evaluation recruitment is slow** | Very likely | High - can't complete report without evaluation | Start recruiting NOW; offer small incentive (gift card); use friends/classmates if needed |
| **LLM API costs add up quickly** | Likely if using real extraction | Medium | Implement caching early; test on small examples; monitor costs daily |
| **Extraction accuracy is low** | Likely | Medium | Keep mockup as fallback for demo; set realistic expectations in report |
| **Running out of time before deadline** | Very likely (typical for course projects) | High | Focus on "Must Have" items only; drop nice-to-haves; split work among team |
| **Demo crashes during presentation** | Somewhat likely | High | Pre-record video; test setup multiple times; have backup device |
| **Team member gets sick/busy** | Possible | Medium | Keep documentation updated; make sure everyone knows where things are |

---

## Feature Prioritization (MoSCoW)

### Must Have (for final milestone)
- ✅ Runnable UI prototype (done)
- ✅ Comprehensive documentation (done)
- Real extraction backend (at least basic version)
- User evaluation with N=10+ participants
- Final report with all required sections
- Demo video (3 minutes)

### Should Have
- Q&A module (real RAG)
- LLM-as-user evaluation
- Error handling and graceful degradation
- UI improvements (filtering, better layout)

### Could Have
- Advanced graph interactions (drag-to-connect, right-click menus)
- Onboarding tutorial
- Tests and CI/CD
- Export to additional formats (Markdown, GraphML)

### Won't Have (Beyond Course Scope)
- Additional language support
- Mobile app version
- Persistent user accounts or data storage

---

## Success Criteria

**Minimum viable final milestone:**
- Extraction works on 80% of test cases (even if not perfect)
- User evaluation completed with N≥10
- Final report complete with all sections
- Demo video showcases core features

**Stretch goals:**
- Extraction accuracy >80% (vs. human gold standard)
- SUS score >75 (good usability)
- LLM-as-user eval shows <20% error rate

---

## Working Together

### Communication

- **Weekly check-ins:** Review progress and adjust priorities
- **Before milestone deadlines:** Make sure everyone knows what's due
- **After pilot study:** Discuss what worked and what didn't

### Where to Find Things

- **GitHub Issues:** Track specific bugs or tasks
- **This ROADMAP:** See big picture and priorities
- **docs/ folder:** Detailed documentation on architecture, design, etc.
- **milestones/ folder:** Previous milestone deliverables

### Dividing Work

Consider splitting responsibilities like:
- **Person A:** Evaluation (recruitment, running studies, analysis)
- **Person B:** Extraction/technical implementation
- **Person C:** Documentation, demo video, UI improvements
- **Everyone:** Final report (especially Section 9 on LLM use - must be written together)

---

## Questions? Need Help?

**If you're new to the project:**
1. Read this ROADMAP to understand what's done and what's next
2. Check [README.md](README.md) for how to run the app
3. Review [docs/architecture.md](docs/architecture.md) to understand the system
4. Look at [docs/dev_guide.md](docs/dev_guide.md) for development tips

**If you're stuck:**
- Check the documentation in docs/ folder
- Ask the team in your chat/meeting
- Create a GitHub Issue to track the problem

**If you want to contribute:**
- Pick a task from "What to Work On Next" section above
- Update this ROADMAP when you complete tasks
- Document any decisions or changes you make

---

## Related Documentation

- [Evaluation Plan](docs/evaluation_plan.md) — Detailed evaluation methodology
- [Final Report Outline](docs/final_report_outline.md) — Report structure and sections
- [Architecture](docs/architecture.md) — System design overview
- [Developer Guide](docs/dev_guide.md) — How to implement features
- [Implementation Plan](docs/implementation_plan.md) — 2–3 day execution plan and task split
- [Milestone 2 Writeup](milestones/milestone2_initial_mockup.md) — Current progress
