# UI Guide — User Task Walkthroughs

## Overview

This guide provides detailed walkthroughs for the core user tasks in the Argument Graph Builder. Each task includes step-by-step instructions, expected outcomes, and common issues.

---

## Task 1: Generate an Argument Graph from Text

**Goal:** Transform input text into an interactive argument graph.

**Who:** Any user wanting to understand the structure of an argumentative text.

**Prerequisites:** None—this is the starting point.

### Step-by-Step Instructions

#### Step 1: Access the Application

1. Open your web browser
2. Navigate to `http://localhost:8501` (or the deployed URL)
3. You should see the welcome screen with "Argument Graph Builder" title

#### Step 2: Choose Input Method

You have three options:

**Option A: Load Example Text**
1. Look at the left sidebar under "📝 Input Text"
2. Find the "Load example text" dropdown
3. Select either:
   - "Death Penalty Argument" (recommended for first use)
   - "AI Regulation Argument"
4. Click the **"Load Example"** button
5. The text will appear in the text area below

**Option B: Paste Your Own Text**
1. Click inside the large text area in the sidebar
2. Paste or type your argumentative text
   - **Tip:** Works best with 500-3000 words
   - **Tip:** Should contain clear claims and supporting/opposing reasoning
3. No additional action needed—proceed to Step 3

**Option C: Upload PDF (Mockup Only)**
1. Click **"📄 Or upload a PDF"** button
2. Select a PDF file from your computer
3. ⚠️ **Note:** In the current mockup, PDF text extraction is simulated—the system will generate a placeholder graph

#### Step 3: Run Extraction

1. Click the large **"🚀 Run Extraction"** button (blue, at bottom of sidebar)
2. **Wait for status feedback:**
   - First: "⏳ Extracting argument components..." (with spinner)
   - Then: "✅ Done! Found X nodes, Y relations"
3. Extraction takes ~2 seconds in mockup

#### Step 4: View the Graph

1. The main panel automatically switches to "📊 Argument Graph" view
2. You'll see an interactive network visualization with:
   - **Nodes** (circles): Argument components
   - **Edges** (arrows): Relations between components
   - **Colors** (see legend):
     - 🔵 Blue = Claims
     - 🟢 Green = Premises
     - 🔴 Red = Objections
     - 🟡 Yellow = Replies

3. **Interact with the graph:**
   - **Pan**: Click and drag on empty space
   - **Zoom**: Scroll or pinch
   - **Hover**: See node label in tooltip
   - **Click**: Select a node (see Task 2)

### Expected Outcomes

✅ **Success Indicators:**
- Graph displays with multiple nodes and edges
- Node colors match the legend
- Hovering shows labels
- Status message confirms extraction completed

❌ **Common Issues:**

| Problem | Solution |
|---------|----------|
| **Graph doesn't appear** | Refresh the page and try again; check browser console for errors |
| **Only 1-2 nodes** | Expected for custom text in mockup; full implementation would improve this |
| **"Extraction failed" error** | In mockup: report as bug; if implementing real extraction: check API keys |
| **Graph too cluttered** | Use filter controls (see Task 4) or zoom out |

### Next Steps

After generating a graph, you can:
- Inspect individual nodes (Task 2)
- Ask questions about the argument (Task 3)
- Filter or edit the graph (Task 4 & 5)

---

## Task 2: Inspect and Understand a Specific Node

**Goal:** Explore detailed information about an argument component.

**Prerequisites:** A graph has been generated (Task 1 completed).

### Step-by-Step Instructions

#### Step 1: Select a Node

Choose one of two methods:

**Method A: Click on Node**
1. Locate a node of interest in the graph visualization
2. Click directly on the node (the colored circle, not just the label)
3. The node will be highlighted

**Method B: Use Dropdown**
1. Find the **"Select a node"** dropdown above the graph
2. Click to open the list of all nodes
3. Select a node by its label
4. The graph will highlight the selected node

#### Step 2: View Node Detail Panel

1. Look at the **right side** of the screen
2. The **"Node Details"** panel appears (or updates if already open)
3. You'll see two tabs:
   - **📋 Details** (default)
   - **✏️ Edit**

#### Step 3: Examine Node Information

In the **Details** tab, review:

**1. Node Type Badge**
- At the top: colored badge showing type (Claim/Premise/Objection/Reply)
- Color matches the graph visualization

**2. Confidence Score**
- Percentage badge (e.g., "79% confident")
- Color coding:
  - 🟢 Green (80-100%): High confidence
  - 🟡 Yellow (60-80%): Moderate confidence
  - 🟠 Orange (40-60%): Low confidence—review recommended
  - 🔴 Red (0-40%): Very uncertain—likely error

**3. Node Label**
- Short summary (shown in graph)
- Usually 3-8 words

**4. Original Text Span**
- Section titled "📄 Original Text Span"
- The exact text from the source document
- **Key feature:** Verify what the system extracted
- Quoted and highlighted for easy reference

**5. LLM Paraphrase**
- Section titled "🤖 LLM Paraphrase"
- Simplified explanation in plain language
- Helps understand complex or jargon-heavy components
- ⚠️ May occasionally miss nuance—always verify against original span

**6. Relations**
- Section titled "🔗 Relations"
- Shows how this node connects to others:
  - **Supports:** Nodes this one provides evidence for
  - **Attacks:** Nodes this one challenges
  - **Supported by:** Nodes that provide evidence for this one
  - **Attacked by:** Nodes that challenge this one
- Click relation names to jump to those nodes

#### Step 4: Interpret the Information

**Understanding Support Relations:**
- If Node A supports Node B, A provides reasoning/evidence for B
- Green arrows in graph point from support to target

**Understanding Attack Relations:**
- If Node A attacks Node B, A challenges or refutes B
- Red dashed arrows in graph point from attacker to target

**Understanding Confidence:**
- High confidence (>80%): System is fairly sure about classification
- Low confidence (<60%): System is uncertain—**verify carefully**
- You can edit nodes to correct errors (Task 5)

### Expected Outcomes

✅ **Success Indicators:**
- Node detail panel displays all sections
- Original text span matches your memory of the source
- Relations make logical sense given the argument
- Confidence score seems reasonable

❌ **Common Issues:**

| Problem | Solution |
|---------|----------|
| **Node not selecting** | Click directly on circle, not label; or use dropdown |
| **Details panel empty** | Try selecting a different node; refresh page if persists |
| **Paraphrase doesn't match original** | Possible hallucination—use Edit tab to flag or correct (Task 5) |
| **Missing relations** | Extraction may have missed some links; full implementation would improve this |

### Next Steps

After inspecting nodes, you can:
- Edit incorrect information (Task 5)
- Ask questions about selected nodes (Task 3)
- Select multiple nodes to compare them

---

## Task 3: Ask Questions About Selected Nodes

**Goal:** Get AI-generated answers about specific parts of the argument.

**Prerequisites:** 
- A graph has been generated (Task 1)
- At least one node selected

### Step-by-Step Instructions

#### Step 1: Select Nodes for Context

1. Use the **"Select nodes for Q&A"** multi-select dropdown
2. You can select:
   - **One node:** For questions about that specific component
   - **Multiple nodes:** For questions comparing or relating components
   - **Entire subgraph:** For broader questions
3. Selected nodes are highlighted in the dropdown

**Tips:**
- For "Why is this premise important?", select the premise node
- For "How does X relate to Y?", select both X and Y
- For "What's the main argument?", select the main claim and its immediate supporters

#### Step 2: Switch to Q&A Panel

1. In the right sidebar (where node details are), look for tabs at the top
2. Click the **"💬 Q&A Panel"** tab
3. You'll see:
   - List of selected nodes
   - Question input field
   - Previous Q&A history (if any)

#### Step 3: Type Your Question

1. Click in the **"Ask a question..."** text input field
2. Type a natural language question

**Good Question Examples:**
- "Why doesn't the deterrence argument succeed?"
- "What evidence supports the main claim?"
- "How does the author respond to this objection?"
- "What is the key disagreement in this argument?"
- "Summarize the selected nodes."

**Tips for Better Answers:**
- Be specific: "Why does Node 3 fail?" is better than "Why?"
- Use argumentative language: "support", "attack", "refute", "defend"
- Reference the graph: "How do these nodes relate?"

#### Step 4: Submit Question

1. Click the **"Ask Question"** button
2. Wait for the spinner (usually 2-5 seconds in mockup)

#### Step 5: Review the Answer

The answer panel displays:

**1. Answer Text**
- Natural language response to your question
- Should be grounded in the selected nodes

**2. Confidence Badge**
- Percentage showing system confidence
- Same color coding as node confidence
- Lower confidence = verify more carefully

**3. Source Spans**
- Section titled "📚 Sources Used"
- Shows which node text was used to generate the answer
- Each source includes:
  - Node ID (e.g., "Node n3")
  - Excerpt from original text span
- **Key feature:** Verify answer against these sources

**4. Explanation**
- Section titled "🧠 How this answer was generated"
- Describes the reasoning process
- Useful for understanding system behavior

#### Step 6: Verify and Iterate

1. **Check sources:** Do the cited spans actually support the answer?
2. **Assess confidence:** Is the confidence score appropriate?
3. **Refine if needed:**
   - Ask a follow-up question
   - Rephrase for clarity
   - Select different/additional nodes for better context

### Expected Outcomes

✅ **Success Indicators:**
- Answer is relevant to the question
- Sources are cited with node IDs and spans
- Answer doesn't introduce information not in the graph
- Confidence score seems calibrated to answer quality

❌ **Common Issues:**

| Problem | Solution |
|---------|----------|
| **Generic/vague answer** | Select more specific nodes; rephrase question more precisely |
| **"I don't have enough information"** | Select additional context nodes; check if question is too broad |
| **Answer contradicts sources** | Possible hallucination—flag as incorrect; report in feedback |
| **Low confidence on good answer** | Confidence scoring is conservative; still useful |

### Next Steps

After getting answers:
- Ask follow-up questions
- Edit nodes if errors are discovered (Task 5)
- Export the graph and Q&A history (Task 6)

---

## Task 4: Filter and Navigate the Graph (Optional)

**Goal:** Focus on specific parts of the argument by filtering node types.

### Instructions

1. Look for **filter controls** near the graph (implementation may vary)
2. Toggle checkboxes to show/hide node types:
   - Claims
   - Premises
   - Objections
   - Replies
3. The graph updates in real-time
4. Use to reduce clutter or focus on specific argumentative structures

**Use Cases:**
- Show only Claims + Objections to see challenges
- Hide Replies to see original argument before defenses
- Show only Premises to see evidential structure

---

## Task 5: Edit or Correct Node Information (Optional)

**Goal:** Fix extraction errors to improve graph accuracy.

### Instructions

1. Select a node (Task 2)
2. In the node detail panel, click the **✏️ Edit** tab
3. You can modify:
   - **Node Type:** Change classification (dropdown)
   - **Label:** Edit the short summary
   - **Paraphrase:** Improve the explanation
4. Click **"Save Changes"** button
5. Optionally, click **"Mark as Incorrect"** to flag for review

**Note:** In current mockup, edits are session-only (not saved). Production will persist edits.

---

## Task 6: Export Graph for Further Use (Optional)

**Goal:** Save the graph as JSON for external analysis or sharing.

### Instructions

1. Look for the **"Export JSON"** button (usually near bottom of sidebar)
2. Click the button
3. A JSON file downloads to your computer
4. The file contains:
   - All nodes (type, label, span, paraphrase, confidence)
   - All edges (source, target, relation, confidence)
   - Metadata (extraction timestamp, model version)

**Use Cases:**
- Share graph with collaborators
- Import into other tools (Obsidian, Notion, etc.)
- Archive for later reference
- Programmatic analysis with custom scripts

---

## Tips for Effective Use

### For Students
- Start with example texts to learn the interface
- Use Q&A to check your understanding of arguments
- Compare your mental model of the argument to the graph

### For Researchers
- Upload academic papers or philosophical texts
- Use the graph to identify logical gaps or weak premises
- Export graphs for inclusion in publications (convert to images)

### For Educators
- Create graphs for teaching argumentative structure
- Have students identify errors in extracted graphs (critical thinking exercise)
- Use Q&A to generate discussion questions

---

## Keyboard Shortcuts (Future)

| Shortcut | Action |
|----------|--------|
| `Space` | Recenter graph |
| `Esc` | Deselect node |
| `Tab` | Cycle through nodes |
| `Ctrl+E` | Export JSON |
| `Ctrl+F` | Search nodes |

(Not yet implemented in mockup)

---

## Accessibility Features (Future)

- High-contrast mode for color blindness
- Screen reader support for graph navigation
- Keyboard-only navigation
- Adjustable font sizes

---

## Related Documentation

- [HAI Design Principles](hai_design_principles.md) — Why the UI is designed this way
- [Architecture](architecture.md) — Technical implementation details
- [Evaluation Plan](evaluation_plan.md) — User study tasks and metrics
