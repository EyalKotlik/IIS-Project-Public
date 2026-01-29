# Milestone 2 Walkthrough Script

## Video Walkthrough: Argument Graph Builder Demo

**Total Duration:** ≤3 minutes

---

## 0:00–0:20 — Problem Framing

### What to show
- Title slide: "Argument Graph Builder — Transforming Text into Interactive Argument Maps"
- Brief shot of a dense philosophical text (e.g., the death penalty sample text)

### Script
> "Understanding complex argumentative texts is challenging. Dense philosophical writing contains multiple claims, supporting premises, objections, and counter-arguments—all intertwined in ways that are hard to track.
>
> Our Argument Graph Builder solves this by automatically extracting argument components and visualizing them as an interactive graph. Let me show you how it works."

---

## 0:20–1:10 — Task 1: Generate a Graph from Text

### What to show
1. The application welcome screen with the sidebar visible
2. The "Load example text" dropdown
3. Selecting "Death Penalty Argument" example
4. Clicking "Load Example" button
5. Text appearing in the text area
6. Clicking "Run Extraction" button
7. The "Extracting..." spinner
8. The success message showing node/relation count
9. The graph appearing on screen

### Script
> "Here's our interface. On the left sidebar, users can input text in three ways: paste directly, upload a PDF, or load a sample.
>
> Let me load our death penalty argument example. [Click dropdown, select, click Load Example]
>
> The text appears in the input area. Now I'll click 'Run Extraction' to analyze it. [Click button]
>
> Notice the status feedback—the system tells us it's extracting, then shows exactly what it found: 11 nodes and 10 relations.
>
> The argument graph now appears, with nodes representing claims, premises, objections, and replies, all connected by support and attack relations."

---

## 1:10–2:00 — Task 2: Inspect a Specific Node

### What to show
1. The graph view with legend visible
2. Hovering over nodes to show tooltips
3. Clicking on a node (or using dropdown)
4. The Node Detail Panel appearing
5. Scrolling through: type badge, label, confidence
6. The "Original Text Span" section
7. The "LLM Paraphrase" section
8. The "Relations" section showing connections
9. Briefly showing the Edit tab

### Script
> "The graph uses color coding—blue for main claims, green for premises, red for objections, and yellow for replies.
>
> Let me click on this objection about deterrence. [Select node]
>
> The detail panel shows everything about this node. First, its type—objection—and the confidence score of 79%.
>
> Here's the key feature: we show the exact original text span from the source. Users can verify what the system extracted.
>
> Below that, an LLM-generated paraphrase explains the same idea in simpler terms.
>
> The relations section shows this objection attacks the main claim, and is itself attacked by a reply about lack of evidence.
>
> If something's wrong, users can click 'Edit' to correct the node type, label, or paraphrase—keeping humans in control."

---

## 2:00–2:40 — Task 3: Q&A Interaction

### What to show
1. Selecting multiple nodes using the multi-select dropdown
2. Switching to the "Q&A Panel" tab
3. The selected nodes displayed
4. Typing a question in the input field
5. Clicking "Ask Question"
6. The answer appearing with:
   - The response text
   - Confidence badge
   - Source spans used
   - Explanation section

### Script
> "Now for our Q&A feature. Users can select multiple nodes—let me choose the deterrence objection and its counter-reply. [Multi-select nodes]
>
> I'll switch to the Q&A panel and ask: 'Why doesn't the deterrence argument succeed?' [Type and click]
>
> The system generates an answer grounded in the selected nodes. Notice the confidence score and, crucially, the source spans section—it shows exactly which text was used to generate this answer.
>
> This transparency is essential. Users aren't just trusting a black-box AI; they can verify every claim against the original text."

---

## 2:40–3:00 — Recap & What's Next

### What to show
1. Full graph view
2. Export JSON button
3. Final title slide

### Script
> "To summarize: the Argument Graph Builder extracts argument structure from text, visualizes it interactively, provides detailed explanations with original sources, and lets users ask questions while maintaining full transparency.
>
> Users can export graphs as JSON for further analysis or integration with other tools.
>
> For our next milestone, we'll implement the actual extraction backend using NLP and LLMs, and conduct user studies to validate our design choices.
>
> Thank you for watching!"

---

## Notes for Recording

### Technical Setup
- Screen resolution: 1920x1080 recommended
- Browser: Chrome or Firefox
- Run with: `streamlit run app_mockup/app.py`

### Recording Tips
- Clear browser cache before recording
- Close unnecessary tabs and applications
- Use a quiet recording environment
- Consider screen zoom to 110-125% for readability
- Pause briefly between sections for editing flexibility

### Backup Plan
If the live demo has issues, pre-record each section separately and splice together.
