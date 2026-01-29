# Intelligence Design

## Overview

The Argument Graph Builder uses a **hybrid AI pipeline** combining rule-based heuristics, traditional NLP, and large language models (LLMs) to extract and visualize argument structures. This document details how the intelligence components work, their inputs/outputs, and failure modes.

---

## Extraction Pipeline

### Stage 1: Preprocessing & Candidate Detection

**Goal:** Identify sentences/clauses that potentially contain argument components.

#### Inputs
- Raw text (pasted, uploaded PDF, or sample)

#### Techniques

**1. Text Normalization**
- Remove extra whitespace, normalize line breaks
- Preserve paragraph structure for context

**2. Sentence Segmentation**
- Use spaCy or NLTK for sentence boundary detection
- Handle edge cases: abbreviations, quotes, lists

**3. Discourse Marker Detection (Heuristic)**

Identify sentences containing argumentative discourse markers:

| Marker Type | Examples | Suggests |
|-------------|----------|----------|
| **Conclusion** | "therefore", "thus", "hence", "consequently" | Claim or conclusion |
| **Support** | "because", "since", "for", "given that" | Premise or evidence |
| **Contrast** | "however", "but", "although", "nevertheless" | Objection or counter-argument |
| **Example** | "for instance", "such as", "for example" | Supporting premise |
| **Causation** | "leads to", "results in", "causes" | Premise-claim relation |

**4. Coreference Resolution**
- Resolve pronouns to entities ("it", "this", "that" → original referent)
- Maintain argument chain coherence across sentences

**5. Named Entity Recognition (NER)**
- Extract key concepts, people, organizations
- Helps identify what the argument is *about*

#### Outputs
- List of candidate sentences with metadata:
  - Position in text
  - Discourse markers present
  - Resolved coreferences
  - Named entities

#### Rationale
Fast, interpretable preprocessing that doesn't require expensive LLM calls for every sentence. Reduces the candidate set to focus expensive processing.

---

### Stage 2: Component Classification (LLM-based)

**Goal:** Classify each candidate sentence as a specific argument component type.

#### Inputs
- Candidate sentence
- Surrounding context (±2 sentences)
- Detected discourse markers

#### LLM Prompt Template

```
You are an expert in argumentation analysis. Given a sentence from a philosophical text, classify it as one of the following:

1. **Claim**: A central assertion or thesis being argued for
2. **Premise**: Evidence or reasoning that supports a claim
3. **Objection**: A challenge or counterargument against a claim or premise
4. **Reply**: A defense or response to an objection
5. **Other**: Not a significant argument component

---

**Sentence:** "{sentence}"

**Context Before:** "{context_before}"
**Context After:** "{context_after}"

**Discourse Markers Detected:** {markers}

---

Respond in JSON format:
{
  "type": "<Claim|Premise|Objection|Reply|Other>",
  "confidence": <0.0-1.0>,
  "rationale": "Brief explanation of classification",
  "label": "Short label (max 8 words) summarizing the component"
}
```

#### Processing
- Send prompt to LLM API (e.g., OpenAI GPT-4, Anthropic Claude)
- Parse JSON response
- Validate `type` and `confidence` fields

#### Confidence Scoring

Confidence is a combination of:
1. **LLM-reported confidence** (from model or prompt engineering)
2. **Discourse marker match** (high confidence if markers align with type)
3. **Length heuristic** (very short or very long sentences get reduced confidence)

**Formula:**
```
final_confidence = 0.6 * llm_confidence + 0.3 * marker_alignment + 0.1 * length_score
```

#### Outputs
- For each candidate:
  - `type`: Claim, Premise, Objection, Reply, or Other
  - `label`: Short summary
  - `span`: Original text
  - `confidence`: 0.0-1.0

#### Failure Modes

| Issue | Symptom | Mitigation |
|-------|---------|-----------|
| **Ambiguous sentences** | Low confidence or "Other" | Require higher confidence threshold; show uncertainty in UI |
| **Context dependence** | Misclassification due to missing context | Include more surrounding sentences |
| **Implicit arguments** | Missing unstated premises | Heuristic: if claim has no support, generate "implied premise" placeholder |
| **Sarcasm/irony** | Incorrect polarity (support vs. attack) | Challenging; may require specialized prompt engineering or human correction |

---

### Stage 3: Paraphrase Generation (LLM-based)

**Goal:** Generate a simplified explanation of each component for better comprehension.

#### Inputs
- Classified component (type, label, span)
- Original text context

#### LLM Prompt Template

```
You are an assistant helping users understand complex arguments. Given an argument component, provide a clear, simplified paraphrase suitable for a general audience.

**Original Component:**
Type: {type}
Text: "{span}"

**Context:** {context}

**Instructions:**
- Paraphrase in simpler language (8th-grade reading level)
- Preserve the core meaning and argumentative role
- Keep it concise (1-2 sentences max)
- Do NOT introduce information not in the original text

Respond with only the paraphrase text, no preamble.
```

#### Outputs
- `paraphrase`: String (1-2 sentences)

#### Quality Checks
- Length: 10-100 words
- Semantic similarity: >0.7 (using sentence embeddings, optional)
- No hallucination: Manually validate during development

---

### Stage 4: Relation Extraction (LLM-based)

**Goal:** Determine how argument components relate to each other (support/attack).

#### Inputs
- Pairs of components (source, target)
- Full text for context

#### Relation Types
- **Support**: Source provides evidence/reasoning for target
- **Attack**: Source challenges or refutes target
- **None**: No direct relation

#### LLM Prompt Template

```
Given two argument components, determine if there is a logical relation between them.

**Component A ({type_a}):**
"{span_a}"

**Component B ({type_b}):**
"{span_b}"

**Full Context:** {text}

---

Does Component A have a logical relation to Component B?

Respond in JSON:
{
  "relation": "<Support|Attack|None>",
  "confidence": <0.0-1.0>,
  "explanation": "Why this relation exists or doesn't exist"
}
```

#### Optimization

**Pairwise Explosion Problem:**
- For N components, there are O(N²) possible pairs
- Not feasible to check all pairs with LLM

**Solutions:**
1. **Heuristic Pruning**:
   - Only check adjacent or nearby sentences (within ±3 positions)
   - Use discourse markers to predict likely relations
   - Skip "Other" type components

2. **Hierarchical Search**:
   - Start with claims (root nodes)
   - Find premises that support claims
   - Find objections to claims/premises
   - Find replies to objections

3. **Caching**:
   - Cache LLM responses for repeated pairs
   - Use embedding similarity to avoid redundant API calls

#### Outputs
- List of edges: `{source_id, target_id, relation, confidence}`

---

### Stage 5: Graph Construction (Deterministic)

**Goal:** Build a valid, consistent argument graph from nodes and edges.

#### Inputs
- Classified nodes (from Stage 2 & 3)
- Relations (from Stage 4)

#### Algorithm

```python
def construct_graph(nodes, edges):
    # 1. Initialize graph
    G = DirectedGraph()
    
    # 2. Add nodes
    for node in nodes:
        if node.confidence > CONFIDENCE_THRESHOLD:
            G.add_node(node.id, **node.attrs)
    
    # 3. Add edges
    for edge in edges:
        if edge.confidence > EDGE_THRESHOLD and \
           edge.source in G and edge.target in G:
            G.add_edge(edge.source, edge.target, **edge.attrs)
    
    # 4. Remove duplicates
    G = merge_duplicate_nodes(G)
    
    # 5. Validate consistency
    G = remove_cycles(G)  # Optional: arguments can have circular reasoning
    G = remove_orphans(G, keep_claims=True)
    
    # 6. Compute layout
    G = compute_hierarchical_layout(G)
    
    return G
```

#### Key Functions

**`merge_duplicate_nodes(G)`**
- Detect nodes with >80% text overlap (using edit distance or embeddings)
- Merge into single node, keeping highest-confidence version
- Consolidate incoming/outgoing edges

**`remove_cycles(G)`**
- Detect cycles in support/attack relations
- Optional: cycles may represent dialectical loops (valid in some argumentation theories)
- If removing: keep edge with highest confidence

**`remove_orphans(G, keep_claims=True)`**
- Remove nodes with no incoming or outgoing edges
- Exception: always keep Claim nodes (they're root assertions)

**`compute_hierarchical_layout(G)`**
- Assign levels: Claims at top, premises below, objections/replies at appropriate levels
- Use Sugiyama framework for hierarchical layout
- Output: (x, y) positions for each node

#### Outputs
- `Graph` object with:
  - Nodes: {id, type, label, span, paraphrase, confidence, position}
  - Edges: {source, target, relation, confidence}
  - Metadata: {created_at, model_version, node_count, edge_count}

---

## Q&A Module (RAG-based)

### Goal
Answer natural language questions about selected nodes or the full argument.

### Retrieval-Augmented Generation (RAG)

**Why RAG?**
- Pure generative models may hallucinate
- Pure retrieval (keyword search) lacks fluency
- RAG combines: retrieve relevant context, then generate grounded answer

### Process Flow

#### 1. Context Retrieval

**Inputs:**
- User question
- Selected node IDs (if any)
- Full graph data

**Strategy:**

If nodes are selected:
- Use selected nodes as primary context
- Include immediate neighbors (1 hop away)
- Include original text spans and paraphrases

If no nodes selected (asking about full graph):
- Retrieve top-k most relevant nodes using:
  - Keyword matching (TF-IDF)
  - Semantic similarity (embeddings, future)
- Include graph structure (how nodes connect)

**Outputs:**
- Context bundle: list of nodes with spans, types, relations

#### 2. Prompt Construction

```
You are an assistant helping users understand an argument graph extracted from philosophical text.

**User Question:** "{question}"

**Relevant Argument Components:**

{for each node in context:}
- **{type} (Node {id})**: {span}
  - Paraphrase: {paraphrase}
  - Relations: {list of edges}

**Graph Context:**
{high-level summary of graph structure}

---

**Instructions:**
- Answer the question based ONLY on the provided components
- Cite specific node IDs when making claims (e.g., "According to Node 3...")
- If information is not in the provided context, say so explicitly
- Keep answer concise (2-4 sentences)
- Provide a confidence score (0.0-1.0) for your answer

Respond in JSON:
{
  "answer": "Your answer here",
  "confidence": <0.0-1.0>,
  "source_nodes": ["node_id_1", "node_id_2"],
  "explanation": "How you derived this answer"
}
```

#### 3. LLM Generation

- Send prompt to LLM API
- Parse JSON response
- Validate fields

#### 4. Post-processing

**Source Attribution:**
- Extract mentioned node IDs from answer
- Link back to original text spans
- Display in UI for transparency

**Confidence Calibration:**
- Adjust LLM-reported confidence based on:
  - Number of source nodes used (more = higher confidence)
  - Relevance of retrieved context to question
  - Presence of hedging language ("might", "possibly")

**Formula:**
```
final_confidence = llm_confidence * context_relevance_score
```

#### Outputs

```json
{
  "answer": "The deterrence argument fails because...",
  "confidence": 0.78,
  "sources": [
    {"node_id": "n3", "span": "Studies show no correlation..."},
    {"node_id": "n5", "span": "The objection claims..."}
  ],
  "explanation": "This answer synthesizes Node 3 (evidence) and Node 5 (objection)"
}
```

### Failure Modes

| Issue | Symptom | Mitigation |
|-------|---------|-----------|
| **Irrelevant retrieval** | Answer not related to question | Improve retrieval with embeddings; use reranking |
| **Hallucination** | Answer cites information not in sources | Validate source spans; penalize confidence if mismatch |
| **Insufficient context** | "I don't know" even though info exists | Expand context window; include more neighbors |
| **Ambiguous questions** | Generic or vague answer | Prompt user to select specific nodes or rephrase |

---

## Confidence Scores & Uncertainty

### Why Show Confidence?

1. **Transparency**: Users should know when system is uncertain
2. **Calibration**: Helps users decide when to trust vs. verify
3. **Feedback**: Low-confidence nodes/edges are candidates for correction

### Confidence Ranges

| Range | Interpretation | UI Treatment |
|-------|---------------|-------------|
| 0.8-1.0 | High confidence | Green badge, normal display |
| 0.6-0.8 | Moderate confidence | Yellow badge, show in UI with note |
| 0.4-0.6 | Low confidence | Orange badge, flag for review |
| 0.0-0.4 | Very low confidence | Red badge, hide by default or mark as uncertain |

### Thresholds

**Node Inclusion:**
- Minimum confidence to include in graph: 0.5 (adjustable)
- Below threshold: node hidden or shown as "uncertain"

**Edge Inclusion:**
- Minimum confidence for edge: 0.4 (relaxed to preserve structure)
- Below threshold: edge shown as dotted line

---

## Model Selection & API Usage

### Current (Mockup)
- No actual LLM calls
- Stub functions return pre-generated data

### Production (Planned)

#### LLM Providers

| Provider | Model | Use Case | Cost (per 1M tokens) |
|----------|-------|----------|----------------------|
| OpenAI | GPT-4 Turbo | Classification, Paraphrase, Q&A | $10 input / $30 output |
| OpenAI | GPT-3.5 Turbo | Faster, cheaper for simple tasks | $0.50 input / $1.50 output |
| Anthropic | Claude 3 Opus | Long-context extraction | $15 input / $75 output |
| Anthropic | Claude 3 Sonnet | Balanced cost/quality | $3 input / $15 output |

**Recommendation:**
- Use GPT-4 Turbo or Claude 3 Sonnet for classification and relation extraction
- Use GPT-3.5 Turbo for paraphrasing (simpler task)
- Use Claude 3 Opus for very long texts (>10k words) due to larger context window

#### Cost Estimation

For a 2000-word article:
- Preprocessing: 0 cost (local)
- Classification: ~50 candidates × 500 tokens/call = 25k tokens ≈ $0.25
- Paraphrase: ~20 nodes × 300 tokens/call = 6k tokens ≈ $0.06
- Relations: ~30 pairs × 400 tokens/call = 12k tokens ≈ $0.12
- Q&A: 5 questions × 1000 tokens/call = 5k tokens ≈ $0.05

**Total per article:** ~$0.50
**Per user session:** ~$1-2 (with Q&A)

### Rate Limiting & Caching

- Implement exponential backoff for API retries
- Cache LLM responses by input hash (avoid redundant calls)
- Batch API calls where possible

---

## Evaluation & Validation

### Intrinsic Evaluation (Component Accuracy)

**Metrics:**
- **Node Classification Accuracy**: % correctly classified nodes (vs. gold standard)
- **Relation Precision/Recall**: Correctly identified support/attack relations
- **Paraphrase Quality**: BLEU/ROUGE scores vs. human paraphrases (if available)

**Baseline:**
- Random: ~20% accuracy (5 classes)
- Heuristic-only: ~50% accuracy
- Target (LLM-based): >80% accuracy

### Extrinsic Evaluation (User Task Performance)

See [evaluation_plan.md](evaluation_plan.md) for detailed user study design.

**Key Questions:**
- Do users understand arguments better with the graph vs. raw text?
- Can users answer comprehension questions faster/more accurately?
- Do users trust the system appropriately (calibrated to confidence scores)?

---

## Related Documentation

- [Architecture](architecture.md) — Overall system design
- [Evaluation Plan](evaluation_plan.md) — User and LLM-based evaluation strategies
- [Data Formats](data_formats.md) — Graph schema and JSON structure
- [HAI Design Principles](hai_design_principles.md) — Transparency and user control rationale
