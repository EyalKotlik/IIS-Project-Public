# HAI Design Principles

## Overview

The Argument Graph Builder is designed with Human-AI Interaction (HAI) best practices at its core. This document explains which guidelines we follow, why they matter, and how they're implemented in our interface.

Our design is primarily informed by **Google PAIR's HAI guidelines** and **Microsoft's HAI guidelines**, with additional considerations from Amershi et al. (2019) and Shneiderman (2020).

---

## Guideline 1: Make Clear What the System Can Do

**Source:** PAIR Guideline G1

### The Principle

**"Help users understand what the AI system can do."**

Users need to build an accurate mental model of the system's capabilities and limitations from the start. Unrealistic expectations lead to frustration; overly conservative expectations mean features go unused.

### Why It Matters for Argument Analysis

Argument extraction is a complex, nuanced task where AI can make errors. Users need to know:
- What types of arguments the system handles well (philosophical, analytical texts)
- What it struggles with (highly implicit arguments, irony, cultural context)
- How reliable the extractions are (confidence scores)
- What they can do when errors occur (editing, flagging)

### Implementation in Our System

#### 1. Welcome Screen Explanation

**Location:** Opening sidebar panel

**What we show:**
- **Clear capability statement:** "Extracts argument components (claims, premises, objections, replies) and visualizes them as an interactive graph"
- **Feature list with icons:**
  - 📊 Extract & visualize argument structure
  - 🔍 Inspect nodes with original text & AI explanations
  - 💬 Ask questions about the argument
  - ✏️ Edit and correct extractions
  - 📥 Export graphs as JSON

**Design choice:** Use concrete action verbs ("Extract", "Inspect", "Ask") rather than abstract capabilities.

#### 2. Status Feedback During Processing

**Location:** Sidebar during extraction

**What we show:**
- **Before:** "🚀 Run Extraction" button with clear label
- **During:** "⏳ Extracting argument components..." with spinner
- **After:** "✅ Done! Found X nodes, Y relations"

**Design choice:** Specific feedback ("Found 11 nodes, 10 relations") is more informative than generic "Complete."

**Example:**
```
⏳ Extracting argument components...
  └─ Analyzing text structure
  └─ Classifying components
  └─ Determining relations
✅ Done! Found 11 nodes, 10 relations
```

#### 3. Confidence Indicators Throughout

**Location:** Nodes, edges, Q&A answers

**What we show:**
- **Node badges:** "79% confident" in color-coded badges
  - 🟢 Green: 80-100% (high confidence)
  - 🟡 Yellow: 60-80% (moderate)
  - 🟠 Orange: 40-60% (low—review recommended)
  - 🔴 Red: 0-40% (very uncertain)
- **Q&A answers:** Confidence percentage for each answer

**Design choice:** Visual encoding (color) + explicit percentage makes uncertainty unmistakable.

#### 4. Legend and Type Explanations

**Location:** Next to graph visualization

**What we show:**
- **Node types:**
  - 🔵 Claim: Central assertion or thesis
  - 🟢 Premise: Evidence or reasoning
  - 🔴 Objection: Challenge or counterargument
  - 🟡 Reply: Response to an objection
- **Edge types:**
  - → Solid green: Support relation
  - ⇢ Dashed red: Attack relation

**Design choice:** Definitions are always visible, not hidden in tooltips.

#### 5. Limitations Disclosure

**Location:** README, Help section (future)

**What we show:**
- "Current mockup uses pre-generated graphs; real extraction would use LLM analysis"
- "Works best with 500-3000 word texts with explicit argument structure"
- "May struggle with highly implicit premises or non-Western argument styles"

### Evidence of Effectiveness

This guideline helps users calibrate their trust. In evaluation (see [evaluation_plan.md](evaluation_plan.md)), we'll measure:
- Do users correctly predict when the system will succeed vs. fail?
- Do users appropriately adjust their reliance on high vs. low confidence outputs?

---

## Guideline 2: Support Efficient Correction

**Source:** PAIR Guideline G16

### The Principle

**"Make it easy to edit, refine, or recover when the AI is wrong."**

AI systems make mistakes. The best interfaces acknowledge this and make correction efficient, preserving the benefits of automation while giving users control.

### Why It Matters for Argument Analysis

- **Extraction errors are inevitable:** Nuanced arguments are hard even for humans to parse
- **Downstream effects:** One misclassified node can distort the entire graph structure
- **User expertise:** Users are experts on the text they're analyzing—they should be able to share that expertise

### Implementation in Our System

#### 1. Direct Node Editing

**Location:** Node detail panel → Edit tab

**What users can do:**
- **Change node type:** Dropdown to reclassify (e.g., Premise → Claim)
- **Edit label:** Text field to improve the summary
- **Rewrite paraphrase:** Text area to fix or clarify explanations
- **Save changes:** Immediate update to graph visualization

**Design choice:** All editable fields are in one place (Edit tab), separate from read-only info (Details tab).

**Interaction flow:**
```
1. Click node → Details panel opens
2. Click "Edit" tab
3. Modify fields
4. Click "Save Changes"
5. Graph updates immediately
6. Edit history logged in session
```

#### 2. "Mark as Incorrect" Button

**Location:** Edit tab, below editable fields

**What it does:**
- Flags the node as problematic for review
- Optional: User can add a note explaining the issue

**Design choice:** Low-friction flagging for users who spot errors but don't want to fix them themselves.

#### 3. Relation Editing (Future Enhancement)

**Potential feature:** Ability to add, remove, or change edge types
- Drag-and-drop to create new relations
- Click edge to edit support/attack classification
- Delete spurious edges

**Why not in current version:** Requires more complex UI.

#### 4. Undo/Redo (Future Enhancement)

**Planned:** Standard undo/redo for all edits
- Keyboard shortcuts (Ctrl+Z, Ctrl+Shift+Z)
- History timeline showing all changes

#### 5. Export Edited Graphs

**Location:** Sidebar → Export JSON button

**What it includes:**
- Original extractions
- User edits marked clearly
- Timestamp and user ID (if applicable)

**Design choice:** Edited graphs are valuable outputs—make them easy to save and share.

### Efficiency Metrics

In evaluation, we'll measure:
- **Time to correct:** How long does it take to fix a misclassified node?
- **Error rate:** Do users introduce errors when editing?
- **Correction rate:** What % of low-confidence nodes do users review and fix?

**Target:** <30 seconds to correct a typical node misclassification.

---

## Guideline 3: Show Contextually Relevant Information

**Source:** PAIR Guideline G9

### The Principle

**"Show contextually relevant information, not everything all at once."**

Information overload is a key usability problem for AI systems, which often have rich outputs (explanations, alternatives, confidence, provenance). Progressive disclosure helps users focus on what matters now.

### Why It Matters for Argument Analysis

An argument graph contains:
- Node attributes (type, label, span, paraphrase, confidence)
- Edge attributes (source, target, relation, confidence)
- Metadata (extraction time, model version)
- Q&A history
- User edits

Showing all of this simultaneously would overwhelm users.

### Implementation in Our System

#### 1. Progressive Disclosure: Node Details

**Interaction pattern:**

**Step 1: Graph view (default)**
- Show: Node shapes, colors, labels (short)
- Hide: Full text spans, paraphrases, confidence, relations

**Step 2: Node selected**
- Show in detail panel:
  - Type badge + confidence
  - Label
  - Original text span
  - LLM paraphrase
  - Direct relations (supports X, attacked by Y)
- Hide: Full graph metadata, unrelated nodes

**Step 3: Edit mode (if needed)**
- Show: Editable fields
- Hide: Read-only information (temporarily)

**Design choice:** Users see increasing detail as they drill down, never more than needed for their current task.

#### 2. Contextual Q&A Answers

**Location:** Q&A panel

**What we show:**
- **Primary:** Answer text (most important)
- **Secondary:** Confidence badge (helps assess answer)
- **Tertiary:** Source spans (for verification)
- **Quaternary:** Explanation of how answer was generated (for curious users)

**Design choice:** Visual hierarchy (font size, color, spacing) guides attention to most important information first.

**Expandable sections (future):**
- "Show full source text" (collapsed by default)
- "How was this answer generated?" (collapsed by default)

#### 3. Relation Visualization

**In graph:**
- Show: Edge direction and type (color)
- Hide: Confidence scores (to reduce clutter)

**In node detail panel:**
- Show: List of relations with target node labels
- Include: Confidence scores for each relation
- Interaction: Click relation to jump to that node

**Design choice:** Confidence important for power users, but visual clutter for casual users. Show where relevant (detail panel), hide where distracting (graph view).

#### 4. Filtering for Focus

**Location:** Graph view controls

**What it does:**
- Toggle visibility of node types (Claims, Premises, Objections, Replies)
- Hide nodes below confidence threshold
- Focus on subgraph around selected node

**Design choice:** Let users customize their view for specific analytical tasks.

**Example use cases:**
- **"Show only Claims and Objections"** → See challenges without supporting details
- **"Hide low-confidence nodes"** → Focus on reliable extractions
- **"Show neighborhood of Node 3"** → Understand local context

### Cognitive Load Metrics

In evaluation, we'll assess:
- **Task completion time:** Is progressive disclosure faster than "show all"?
- **Error rate:** Do users miss important information because it's hidden?
- **Subjective workload:** NASA-TLX scores for perceived effort

---

## Additional HAI Considerations

### 4. Transparency and Explainability

**Principle:** Users should understand why the AI made a decision.

**Implementation:**
- **Source attribution:** Every node shows original text span
- **Paraphrase rationale:** LLM explains the component in plain language
- **Q&A explanations:** "How this answer was generated" section
- **Confidence scores:** Signal uncertainty explicitly

**References:**
- Amershi et al. (2019): "Explain AI decisions when users need to understand or act on them"
- PAIR G10: "Support efficient dismissal"

### 5. User Control and Autonomy

**Principle:** Users should feel in control, not dominated by the AI.

**Implementation:**
- **Optional automation:** Users can choose to review every node or trust high-confidence extractions
- **Edit any output:** No AI decision is final
- **Manual graph building:** Users can add nodes/edges manually (future)
- **Export for external use:** Graphs are portable, not locked in

**References:**
- Shneiderman (2020): "Human control with computer automation"
- PAIR G14: "Encourage granular feedback"

### 6. Learnability

**Principle:** The system should be easy to learn and remember.

**Implementation:**
- **Familiar patterns:** Drag-to-pan, scroll-to-zoom (standard graph interactions)
- **Consistent terminology:** "Node", "Edge", "Relation" used uniformly
- **Help text:** Tooltips on hover (future)
- **Example workflows:** Pre-loaded samples for learning

**Future:**
- Onboarding tutorial (interactive walkthrough)
- Video demonstrations (see [m2_walkthrough_script.md](../milestones/m2_walkthrough_script.md))

---

## Design Trade-offs and Decisions

### Trade-off 1: Simplicity vs. Power

**Tension:** More features = more capability, but also more complexity.

**Our approach:**
- **Default to simple:** Basic workflow (load → extract → view) requires no expertise
- **Progressive enhancement:** Advanced features (filtering, editing, Q&A) available but not required
- **Hide complexity:** Power features in tabs, menus, or expandable sections

**Example:** Q&A is in a separate tab, not forced on all users.

### Trade-off 2: Automation vs. Control

**Tension:** Full automation is efficient but can feel opaque; full manual control is transparent but tedious.

**Our approach:**
- **Automation first:** Extract graph automatically
- **Control available:** Users can review and edit
- **Adjustable automation:** Confidence thresholds let users control how much they review

**Example:** Users can set "only show nodes >70% confidence" to focus review effort.

### Trade-off 3: Transparency vs. Overwhelm

**Tension:** Showing all provenance and confidence is transparent but overwhelming.

**Our approach:**
- **Tiered disclosure:** Most important info visible, details on demand
- **Smart defaults:** Show confidence only when it matters (low scores, user edits)
- **Visual encoding:** Use color/size to communicate without text

**Example:** High-confidence nodes show green badge; moderate nodes show yellow + percentage.

---

## Evaluation of HAI Principles

See [evaluation_plan.md](evaluation_plan.md) for detailed evaluation methodology.

**Key questions:**
1. **G1 (Capabilities):** Do users accurately understand what the system can/can't do?
2. **G16 (Correction):** How efficiently can users fix errors?
3. **G9 (Context):** Do users feel overwhelmed or under-informed?

**Planned measures:**
- **Mental model accuracy:** Survey after use ("What can this system do?")
- **Correction efficiency:** Time to fix planted errors
- **Cognitive load:** NASA-TLX, perceived usefulness scales
- **Trust calibration:** Reliance on high vs. low confidence outputs

---

## Related Documentation

- [UI Guide](ui_guide.md) — Detailed task walkthroughs showing principles in action
- [Evaluation Plan](evaluation_plan.md) — How we'll validate these design choices
- [Architecture](architecture.md) — Technical implementation enabling HAI features
- [Intelligence Design](intelligence_design.md) — How confidence scores and explanations are generated

---

## References

- Amershi, S., et al. (2019). "Guidelines for Human-AI Interaction." *CHI 2019*.
- Google PAIR. "People + AI Guidebook." https://pair.withgoogle.com/guidebook/
- Microsoft. "Human-AI Interaction Guidelines." https://www.microsoft.com/en-us/haxtoolkit/
- Shneiderman, B. (2020). "Human-Centered AI." *Oxford University Press*.
