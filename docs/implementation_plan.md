# 2–3 Day Implementation Plan

Plan for rapidly moving the Argument Graph Builder from mockup to functional demo within ~2–3 days, with two engineers (1 junior, 1 senior/mid).

## Current State (Baseline)
- UI mockup exists (Streamlit).
- Extraction and Q&A are stubbed; no real NLP/LLM integration.
- Documentation is comprehensive; no automated tests yet.

## Objectives for This Sprint
1. Deliver a minimal but real extraction and Q&A path for the demo.
2. Preserve the existing mockup as a fallback.
3. Produce updated documentation and demo-ready walkthroughs.

## Work Split & Parallelization
- **Senior/Mid Engineer (S):** Owns backend spikes, integration, and risk mitigation.
- **Junior Engineer (J):** Owns data prep, UI wiring, docs, and testing support.

## Day-by-Day Plan

### Day 0 (Prep – 1–2 hrs)
- **S:** Confirm API access (OpenAI/Anthropic). Set secrets locally. Draft minimal prompt templates for component classification & relation extraction.
- **J:** Pull latest code; verify mockup runs; review data formats and sample graphs to ensure schema familiarity.
- **Secrets setup:** Use `OPENAI_API_KEY`/`ANTHROPIC_API_KEY` via environment or `.streamlit/secrets.toml`.

### Day 1 (Core Extraction Spike)
- **S:** Implement minimal `extractor.py` with:
  - Sentence segmentation (spaCy/NLTK or simple split fallback).
  - LLM call for component typing + paraphrase; simple confidence heuristic (e.g., accept if model score/confidence ≥0.5; downgrade/flag otherwise).
  - Relation extraction limited to adjacent sentences to control cost.
  - Fallback to stub if API key missing or call fails.
- **J (parallel):**
  - Create 3–5 short sample texts + expected light graphs (JSON) for smoke tests.
  - Add a toggle in `app.py` (mock vs. real extraction) or detect availability of API key.

### Day 2 (Stabilize + Q&A)
- **S:** Add lightweight Q&A path:
  - Context = selected node(s) + neighbors; single LLM answer with source spans.
  - Basic error handling and timeouts.
- **J:** Wire UI for Q&A tab to call real backend when enabled; keep stub as fallback. Add minimal test harness (manual or simple script) to exercise sample texts end-to-end.

### Day 3 (Polish & Demo-Ready)
- **S:** Performance/cost pass (batching, low-temp); log key metrics; ensure graceful degradation to stub.
- **Caching note:** In-memory/session cache with short TTL (≤30 min) during dev to avoid stale results; clear on app reload.
- **J:** Update docs (README quickstart, ui_guide note, dev_guide for toggles), refresh screenshots/walkthrough script if UI changed. Run smoke tests on sample texts.

## Concrete Task List
- [ ] Add `app_mockup/extractor.py` with minimal real pipeline (S)
- [ ] Add fallback gate: if no API key or error → use `extractor_stub` (S)
- [ ] Add sample texts + graphs for smoke testing (J)
- [ ] Add UI toggle or auto-detect for real vs. mock extraction (J)
- [ ] Implement basic Q&A using selected nodes as context (S)
- [ ] Wire Q&A UI to choose real vs. stub (J)
- [ ] Document setup, toggles, and smoke test steps (J)
- [ ] Refresh demo walkthrough/screenshots if UI changes (J)
- [ ] Quick cost/latency sanity check + logging (S)

## Risks & Mitigations
- **API availability/cost:** Keep stub fallback; use short texts; cache per-session responses.
- **Accuracy:** Restrict relations to nearby sentences; prefer high-precision prompts.
- **Time:** Prioritize extraction > Q&A > polish. Drop noncritical UI changes if slipping.

## Definition of Done (for this sprint)
- App can run with real extraction and Q&A when API key is present; otherwise seamlessly falls back to stub.
- 3–5 smoke-test texts succeed end-to-end.
- README/dev_guide/ui_guide updated for toggles and setup.
- Demo walkthrough ready using new path (or stub fallback if API missing).
