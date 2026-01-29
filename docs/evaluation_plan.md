# Evaluation Plan

## Overview

This document outlines plans for evaluating the Argument Graph Builder through both human-user studies and LLM-as-user evaluation. **No evaluation has been conducted yet—this document contains only plans and templates.**

---

## Part 1: Human-User Evaluation

### Objectives

1. **Usability:** Can users effectively navigate and interact with the system?
2. **Utility:** Does the system help users understand arguments better?
3. **Trust:** Do users appropriately calibrate trust based on confidence scores?
4. **Errors:** Can users identify and correct extraction errors efficiently?

### Evaluation Design

#### Participants

**Target sample:**
- **N = 12-15 participants**
- Mix of:
  - Undergraduate students (philosophy, computer science, or related fields)
  - Graduate students or researchers who read argumentative texts
  - Educators who teach critical thinking or argumentation

**Recruitment:**
- Course announcement / email list
- Compensation: $15 gift card or course credit (15-20 minutes)

**Inclusion criteria:**
- Familiar with reading argumentative texts
- No prior exposure to this system
- Fluent in English

#### Study Protocol

**Location:** Remote (video call) or in-person lab  
**Duration:** 15-20 minutes per participant  
**Materials:** 
- Pre-loaded Argument Graph Builder on `localhost` or demo server
- 2 sample texts (not previously seen by participants)
- Task worksheet
- Post-task questionnaire

**Procedure:**

1. **Introduction (2 min)**
   - "We're testing a system that extracts argument graphs from text. Your feedback will help improve it."
   - "Think aloud as you work—tell us what you're thinking."
   - Emphasize: "We're testing the system, not you."

2. **Tutorial (2 min)**
   - Show how to load example, run extraction, click nodes
   - Let participant try once with death penalty example

3. **Task 1: Graph Generation & Exploration (5 min)**
   - Provide a new sample text (e.g., AI regulation argument)
   - Ask: "Generate a graph and explore it. Tell us what you notice."
   - Observe: Do they understand the visualization? Do they use the legend?

4. **Task 2: Node Inspection (3 min)**
   - Ask: "Find the main claim and examine its details."
   - Metrics: Time to locate, successful identification, use of detail panel
   - Ask: "How confident are you in this extraction? Why?"

5. **Task 3: Q&A Interaction (3 min)**
   - Ask: "Select two nodes that seem related and ask a question about how they connect."
   - Observe: Quality of question, interpretation of answer, use of source spans

6. **Task 4: Error Correction (3 min)**
   - Provide a graph with a planted error (e.g., misclassified premise as objection)
   - Ask: "One node is incorrectly classified. Can you find and fix it?"
   - Metrics: Time to identify error, time to correct, successful correction

7. **Post-Task Questionnaire (2 min)**
   - See questionnaire template below

#### Metrics & Data Collection

**Quantitative:**

| Metric | How Measured | Target |
|--------|-------------|--------|
| Task completion rate | % successfully completing each task | >80% |
| Task completion time | Stopwatch during tasks | <5 min per task |
| Error identification accuracy | % correctly identifying planted error | >70% |
| Correction efficiency | Time to fix planted error | <30 seconds |
| System Usability Scale (SUS) | Post-task questionnaire | >70 (above average) |
| Trust calibration | Difference in reliance on high vs. low confidence | Significant (p<0.05) |

**Qualitative:**
- Think-aloud transcripts
- Observed confusion or delight moments
- Open-ended feedback on questionnaire

### Post-Task Questionnaire Template

**Section A: Usability (5-point Likert scale)**

1. The system was easy to use.  
   [ ] Strongly Disagree — [ ] Disagree — [ ] Neutral — [ ] Agree — [ ] Strongly Agree

2. I understood what the system could do.  
   [ ] Strongly Disagree — [ ] Disagree — [ ] Neutral — [ ] Agree — [ ] Strongly Agree

3. The graph visualization helped me understand the argument structure.  
   [ ] Strongly Disagree — [ ] Disagree — [ ] Neutral — [ ] Agree — [ ] Strongly Agree

4. Confidence scores helped me know when to verify the system's output.  
   [ ] Strongly Disagree — [ ] Disagree — [ ] Neutral — [ ] Agree — [ ] Strongly Agree

5. Editing incorrect nodes was straightforward.  
   [ ] Strongly Disagree — [ ] Disagree — [ ] Neutral — [ ] Agree — [ ] Strongly Agree

**Section B: Utility**

6. Compared to reading the text alone, the graph made it:  
   [ ] Much harder — [ ] Harder — [ ] About the same — [ ] Easier — [ ] Much easier

7. The Q&A feature was helpful for understanding specific parts of the argument.  
   [ ] Strongly Disagree — [ ] Disagree — [ ] Neutral — [ ] Agree — [ ] Strongly Agree

**Section C: Trust**

8. I would trust high-confidence (>80%) extractions without verifying them.  
   [ ] Strongly Disagree — [ ] Disagree — [ ] Neutral — [ ] Agree — [ ] Strongly Agree

9. I felt the system was transparent about its limitations.  
   [ ] Strongly Disagree — [ ] Disagree — [ ] Neutral — [ ] Agree — [ ] Strongly Agree

**Section D: Open-Ended**

10. What did you like most about the system?  
    [Free text]

11. What was most frustrating or confusing?  
    [Free text]

12. What would you change or improve?  
    [Free text]

### Data Analysis Plan

**Usability:**
- Compute mean SUS score (standard formula)
- Benchmark against 68 (average usability)
- Identify low-scoring items for improvement

**Utility:**
- Compare task completion with graph vs. text-only control (if time permits)
- Analyze think-aloud for insights into how graph aids understanding

**Trust Calibration:**
- Code think-aloud for trust-related statements
- Compare reliance on high vs. low confidence nodes (within-subjects)

**Qualitative Themes:**
- Thematic analysis of open-ended responses
- Identify recurring issues, feature requests, delights

### Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| **Recruitment failure** | Not enough participants | Start recruiting early; offer higher incentive; use convenience sample if needed |
| **Technical issues during study** | Session wasted | Pre-test setup; have backup device; record screen |
| **Participant confusion** | Poor data quality | Clearer tutorial; allow practice time; intervene if stuck >1 min |
| **Hawthorne effect** | Overly positive feedback | Emphasize "testing system, not you"; ask for critique specifically |

---

## Part 2: LLM-as-User Evaluation

### Objectives

Simulate user interactions using an LLM to:
1. **Scale evaluation:** Test more scenarios than feasible with human users
2. **Identify edge cases:** Find failure modes humans might miss
3. **Measure bias:** Detect if system favors certain argument types
4. **Benchmark usefulness:** Assess if outputs are coherent and grounded

**Note:** This is complementary to human evaluation, not a replacement.

### Evaluation Strategy

#### Setup

**LLM Choice:** GPT-4 (or Claude 3 Opus) for high reasoning capability

**Evaluation Modes:**

**Mode 1: Graph Quality Critique**
- Input: Generated graph (nodes, edges, original text)
- Task: LLM evaluates accuracy and completeness
- Output: Scores + critique

**Mode 2: Q&A Usefulness**
- Input: Graph + Q&A exchanges
- Task: LLM assesses answer quality, grounding, and coherence
- Output: Scores + issues

**Mode 3: Adversarial Inputs**
- Input: Deliberately challenging texts (ambiguous, implicit, sarcastic)
- Task: LLM critiques extraction failures
- Output: Failure mode taxonomy

#### Prompt Template: Graph Quality Critique

```
You are an expert in argumentation analysis and critical thinking. You will evaluate the quality of an automatically extracted argument graph.

**Original Text:**
{text}

**Extracted Graph:**
Nodes:
{for each node:}
- {id}: [{type}] {label}
  Original span: "{span}"
  Paraphrase: "{paraphrase}"
  Confidence: {confidence}

Edges:
{for each edge:}
- {source} → {target} [{relation}] (confidence: {confidence})

---

**Evaluation Task:**

1. **Accuracy:** Are nodes correctly classified? Are spans accurate?
   - Score: 1-5 (1=many errors, 5=highly accurate)
   - Issues: [List specific misclassifications]

2. **Completeness:** Are important argument components missing?
   - Score: 1-5 (1=major gaps, 5=comprehensive)
   - Missing: [List omitted components]

3. **Relations:** Are support/attack relations correct?
   - Score: 1-5 (1=many errors, 5=highly accurate)
   - Issues: [List incorrect or missing relations]

4. **Paraphrase Quality:** Are paraphrases clear and accurate?
   - Score: 1-5 (1=misleading, 5=excellent)
   - Issues: [List problematic paraphrases]

5. **Overall Usefulness:** Would this graph help a user understand the argument?
   - Score: 1-5 (1=not useful, 5=very useful)
   - Rationale: [Explain]

**Output Format:**
JSON with scores and issues for each criterion.
```

#### Prompt Template: Q&A Usefulness Critique

```
You are evaluating the quality of a Q&A system for argument analysis.

**Context:**
User selected nodes: {node_ids}
Node details: {node_spans_and_paraphrases}

**User Question:** "{question}"

**System Answer:**
"{answer}"
Confidence: {confidence}
Sources: {source_spans}

---

**Evaluation Task:**

1. **Relevance:** Does the answer address the question?
   - Score: 1-5
   - Issues: [If not fully relevant, why?]

2. **Grounding:** Is the answer supported by the provided sources?
   - Score: 1-5
   - Issues: [Any unsupported claims? Hallucinations?]

3. **Coherence:** Is the answer well-structured and clear?
   - Score: 1-5
   - Issues: [Confusing phrasing? Contradictions?]

4. **Completeness:** Does the answer fully address the question?
   - Score: 1-5
   - Issues: [Missing information? Too shallow?]

5. **Bias Detection:** Does the answer exhibit bias or unfair framing?
   - Score: 1-5 (1=high bias, 5=neutral)
   - Issues: [Examples of biased language or framing]

**Output Format:**
JSON with scores and issues.
```

#### Evaluation Corpus

**Sample Texts (10-15 examples):**
- Philosophical arguments (Kant, Rawls, etc.)
- Op-eds on contemporary issues
- Scientific abstracts with claims and evidence
- Legal arguments (if applicable)
- **Edge cases:**
  - Highly implicit premises
  - Sarcastic or ironic arguments
  - Arguments with cultural context dependency

#### Data Collection & Analysis

**Per Text:**
- Run extraction
- Generate graph
- Submit graph + text to LLM critique
- Run 3-5 Q&A interactions
- Submit Q&A exchanges to LLM critique

**Aggregate Metrics:**
- Mean accuracy score across texts
- Mean completeness score
- Mean usefulness score
- Frequency of specific error types (misclassification, missing nodes, hallucinations)

**Failure Mode Taxonomy:**
- Categorize errors identified by LLM
- Prioritize by frequency and severity

**Bias Analysis:**
- Compare LLM bias scores across argument topics (death penalty, AI regulation, etc.)
- Check for systematic differences

### Limitations of LLM-as-User

**⚠️ LLM evaluation is not ground truth:**
- LLMs can be wrong or biased themselves
- May not reflect real user needs or confusion
- Should be validated with human evaluation

**Use cases for LLM eval:**
- **Supplementary:** After human pilot, test more scenarios
- **Iterative development:** Quick feedback during development
- **Bias detection:** Flag potentially problematic outputs for human review

---

## Part 3: Comparative Evaluation (Optional, if time permits)

### Baseline Comparison

**Condition A: Graph-Assisted (our system)**
- Users complete comprehension tasks with the argument graph

**Condition B: Text-Only (control)**
- Users complete same tasks with just the original text
- Can highlight, take notes, but no graph

**Metrics:**
- Task completion time (faster with graph?)
- Comprehension accuracy (answer questions about argument structure)
- Subjective difficulty (NASA-TLX)

**Hypothesis:** Graph-assisted users will be faster and more accurate, especially for complex multi-layer arguments.

---

## Evaluation Timeline

| Phase | Duration | Tasks |
|-------|----------|-------|
| **Phase 1: Pilot** | Week 1 | 2-3 participants; refine protocol |
| **Phase 2: Main Study** | Week 2-3 | 12-15 participants; data collection |
| **Phase 3: LLM Eval** | Week 3 | Run LLM critique on 10-15 texts |
| **Phase 4: Analysis** | Week 4 | Thematic coding, statistical analysis |
| **Phase 5: Report** | Week 5 | Write findings for final report |

---

## Ethical Considerations

**Informed Consent:**
- Participants informed about data collection, video recording (if applicable)
- Right to withdraw at any time
- Data anonymized before analysis

**Privacy:**
- No personal identifiers stored with evaluation data
- Secure storage of recordings (deleted after analysis)

**Bias in Sampling:**
- Aim for diverse participant pool (gender, discipline, technical background)
- Report demographics and any limitations

---

## **IMPORTANT: No Fabricated Results**

**This section contains only plans and templates. No evaluation has been conducted yet.**

When evaluation is complete, results will be added to:
- **Final report** (see [final_report_outline.md](final_report_outline.md))
- **Separate evaluation results document**

**DO NOT:**
- Invent participant quotes
- Fabricate SUS scores or completion rates
- Claim user study was conducted if it wasn't

**DO:**
- Follow this plan to conduct actual evaluation
- Report findings honestly, including negative results
- Update this document with lessons learned after real evaluation

---

## Related Documentation

- [Final Report Outline](final_report_outline.md) — Where evaluation results will be reported
- [HAI Design Principles](hai_design_principles.md) — Principles being evaluated
- [UI Guide](ui_guide.md) — Tasks used in evaluation
- [ROADMAP](../ROADMAP.md) — Evaluation timeline in project plan
