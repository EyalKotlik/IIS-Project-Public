# Milestone 2: Initial Mockup — Argument Graph Builder

## 1. Project Summary

The **Argument Graph Builder** is an intelligent interactive system that transforms dense philosophical and argumentative texts into visual, explorable argument graphs. The system addresses a significant challenge in academic and analytical work: understanding complex argumentative structures buried in lengthy texts.

Users can input text (via paste or PDF upload), and the system extracts argument components—claims, premises, objections, and replies—along with their logical relationships (support/attack). These are rendered as an interactive graph where users can:

- **Explore** the argument structure visually
- **Inspect** individual nodes to see original text spans and AI-generated paraphrases
- **Ask questions** about specific nodes or subgraphs using natural language
- **Edit and correct** the system's outputs when errors occur

The system targets students, researchers, and educators who need to analyze complex arguments efficiently. By combining automated extraction with transparent, user-controllable interfaces, we aim to augment human understanding rather than replace human judgment.

---

## 2. Design Principles (HAI Guidelines)

Our design is guided by three key Human-AI Interaction (HAI) guidelines from Google's PAIR framework and Microsoft's HAI guidelines.

### Guideline 1: Make clear what the system can do (G1 - PAIR)

**Principle:** Users should understand the system's capabilities and limitations from the start.

**Implementation:**
- The **welcome screen** explicitly lists what the system does: extracting components, visualizing graphs, explaining nodes, and answering questions
- **Status feedback** ("Extracting...", "Done! X nodes, Y relations") keeps users informed about system actions
- **Confidence badges** on nodes and answers indicate certainty levels, signaling where the system is less sure
- The **legend** clearly explains node types and color coding before users interact with the graph

### Guideline 2: Support efficient correction (G16 - PAIR)

**Principle:** When AI makes errors, users should be able to correct them quickly and efficiently.

**Implementation:**
- Each node has an **Edit panel** accessible via a tab, allowing users to modify node type, label, and paraphrase
- A **"Mark as Incorrect"** button lets users flag problematic extractions for review
- Changes are reflected immediately in the interface (session-based in mockup, persistent in production)
- The **Export JSON** feature allows users to save corrected graphs for downstream use

### Guideline 3: Show contextually relevant information (G9 - PAIR)

**Principle:** Display information relevant to the user's current task and context.

**Implementation:**
- The **Node Detail Panel** appears only when a node is selected, showing relevant information (original span, paraphrase, relations) without cluttering the main view
- **Q&A answers** include source spans used, directly connecting responses to the original text
- **Relation lists** in the detail panel highlight connected nodes, helping users understand local context
- **Graph filtering** by node type lets users focus on specific aspects of the argument

---

## 3. Interface Design and Instruction

### User Task 1: Generate a Graph from Pasted Text

**Goal:** Transform input text into an interactive argument graph.

**Steps:**
1. On the **Input screen**, either:
   - Select an example from the "Load example text" dropdown and click "Load Example"
   - Paste your own text into the text area
   - Upload a PDF file (extraction mocked in prototype)
2. Click the **"🚀 Run Extraction"** button
3. Observe the **status feedback** ("Extracting..." → "✅ Done! X nodes, Y relations")
4. The **Graph screen** displays the extracted argument graph

**Screenshots:**
- [Before extraction (input screen)](m2_screenshots/task1_before.png)
- [After extraction (graph displayed)](m2_screenshots/task1_after.png)

### User Task 2: Inspect and Understand a Specific Node

**Goal:** Explore a node's details including original text, paraphrase, and relationships.

**Steps:**
1. On the **Graph screen**, click on a node in the visualization OR use the "Select a node" dropdown
2. The **Node Detail Panel** opens on the right side
3. View the node's:
   - Type badge (Claim/Premise/Objection/Reply)
   - Confidence score
   - Original text span (quoted from source)
   - LLM paraphrase (simplified explanation)
   - Relations (what supports/attacks this node)
4. Optionally, click the **Edit tab** to modify incorrect information

**Screenshots:**
- [Graph with node selected](m2_screenshots/task2_graph.png)
- [Node detail panel showing information](m2_screenshots/task2_detail.png)

### User Task 3: Ask Questions About Selected Nodes

**Goal:** Get AI-generated answers about specific parts of the argument.

**Steps:**
1. Select one or more nodes using the multi-select dropdown
2. Switch to the **Q&A Panel** tab
3. Type a question in natural language (e.g., "Why is this premise important?")
4. Click **"Ask Question"**
5. View the answer along with:
   - Confidence score
   - Source spans used to generate the answer
   - Explanation of how the answer was derived

**Screenshots:**
- [Selecting nodes for Q&A](m2_screenshots/task3_select.png)
- [Q&A response with sources](m2_screenshots/task3_answer.png)

**Walkthrough Script:** [m2_walkthrough_script.md](m2_walkthrough_script.md)

---

## 4. Theoretical Basis

Our interface design is grounded in established cognitive and learning theories:

### Cognitive Load Theory (Sweller, 1988)

**Theory:** Working memory has limited capacity; interfaces should minimize extraneous cognitive load.

**Application:**
- **Progressive disclosure**: Details are hidden until a node is selected, avoiding overwhelming users with all information at once
- **Hierarchical graph layout**: Automatically organized to show logical flow from claims to supporting elements
- **Filtering controls**: Users can hide node types they're not currently interested in
- **Side panel**: Keeps detail information separate from the main visualization

### Dual Coding Theory (Paivio, 1971)

**Theory:** Information is better retained when presented in both verbal and visual forms.

**Application:**
- **Visual graph representation**: Argument structure shown as nodes and edges with meaningful colors
- **Textual details**: Original spans and paraphrases provide verbal encoding
- **Color coding**: Node types (claim=blue, premise=green, objection=red, reply=yellow) create visual distinction
- **Relation visualization**: Support (solid green arrows) vs. attack (dashed red arrows) relations

### Transparency and User Control (Shneiderman, 2020; Amershi et al., 2019)

**Theory:** Users should understand AI decisions and maintain meaningful control over the system.

**Application:**
- **Source attribution**: Every node shows the original text span it was extracted from
- **Confidence indicators**: Percentage scores show extraction certainty
- **Edit capabilities**: Users can correct any extraction error
- **Q&A explanations**: Answers include "why this answer" and source spans used

---

## 5. Intelligence Design Approach

The Argument Graph Builder employs a **hybrid pipeline** combining multiple AI techniques:

### Stage 1: Candidate Detection (Heuristic + NLP)

**Approach:** Use rule-based heuristics and traditional NLP to identify potential argument components.

- Sentence boundary detection and segmentation
- Discourse markers identification ("however", "therefore", "because")
- Coreference resolution for argument chain tracking
- Named entity recognition for key concepts

**Rationale:** Fast, interpretable preprocessing that doesn't require expensive API calls for every sentence.

### Stage 2: Role Classification (LLM-based)

**Approach:** Use large language models to classify candidate segments and determine relations.

- Classify segments as: Claim, Premise, Objection, Reply, or Other
- Determine relations: Support, Attack, or None
- Generate paraphrases for each identified component
- Produce confidence scores based on model uncertainty

**Rationale:** LLMs excel at nuanced understanding of argumentative roles and can generate helpful paraphrases.

### Stage 3: Graph Construction (Deterministic)

**Approach:** Apply deterministic algorithms for graph cleanup and layout.

- Remove duplicate/redundant nodes
- Validate relation consistency (no circular attacks, etc.)
- Compute hierarchical layout for visualization
- Calculate aggregate confidence scores

**Rationale:** Deterministic post-processing ensures consistent, valid graph structures regardless of LLM variability.

### Q&A Module (RAG-based)

**Approach:** Retrieval-Augmented Generation for answering user questions.

- Retrieve relevant nodes and their context based on user selection
- Construct prompts with node content and relations
- Generate answers grounded in source material
- Return source attribution for transparency

**Rationale:** RAG combines retrieval precision with generative fluency, enabling accurate, attributable answers.

---

## Appendix: Mockup Artifacts

| Artifact | Location |
|----------|----------|
| Runnable prototype | `/app_mockup/app.py` |
| Sample data | `/app_mockup/sample_data/` |
| Screenshots | `/milestones/m2_screenshots/` |
| Walkthrough script | `/milestones/m2_walkthrough_script.md` |
| This document | `/milestones/milestone2_initial_mockup.md` |
