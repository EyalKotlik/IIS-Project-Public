# Final Report Outline

## Overview

This document provides a template for the final project report, aligned with course requirements and typical academic project structure. Use this outline to organize your final writeup.

**Important:** This is a template only. Sections marked with `[TODO: ...]` must be written by the team based on actual work completed.

---

## Report Specifications

**Expected Length:** 8-12 pages (excluding references, appendices)  
**Format:** IEEE or ACM conference format (double-column)  
**Sections:** As outlined below  
**Submission:** PDF + link to GitHub repository

---

## Section 1: Introduction (1 page)

### 1.1 Problem Statement

**What to write:**
- The challenge: Understanding complex argumentative texts is difficult
- Why it matters: Students, researchers, educators spend significant time parsing arguments
- Gap: Existing tools (manual highlighting, note-taking) are inefficient

**Structure:**
1. Opening paragraph: Concrete scenario/example
2. Problem scope: Who faces this issue? How common?
3. Existing approaches and their limitations
4. Transition to your solution

**[TODO: Write based on your problem framing in Milestone 1 proposal]**

### 1.2 Proposed Solution

**What to write:**
- High-level description: "The Argument Graph Builder extracts..."
- Key innovation: Combination of automated extraction + transparent, user-controllable interface
- What makes it unique: HAI principles, confidence scores, direct correction

**[TODO: Write 1-2 paragraphs summarizing your system]**

### 1.3 Contributions

**What to write:**
- Contribution 1: A hybrid extraction pipeline (heuristics + LLM)
- Contribution 2: An interactive UI implementing HAI guidelines
- Contribution 3: Evaluation methodology (human + LLM-as-user)

**[TODO: Customize to your actual contributions]**

---

## Section 2: Related Work (1-1.5 pages)

### 2.1 Argument Mining & Extraction

**What to cover:**
- Traditional NLP approaches to argument mining (surveys by Lawrence & Reed, etc.)
- Recent deep learning / LLM-based extraction (if applicable)
- How your approach compares

**Key papers to cite:**
- Lawrence & Reed (2019): "Argument Mining: A Survey"
- Stab & Gurevych (2017): "Parsing Argumentation Structures in Persuasive Essays"
- [Add others based on your research]

**[TODO: Write 2-3 paragraphs with 5-8 citations]**

### 2.2 Argument Visualization

**What to cover:**
- Existing tools: Rationale, Compendium, Argunet
- Graph visualization techniques
- What's missing: integration with extraction, user control

**[TODO: Write 1-2 paragraphs with 3-5 citations]**

### 2.3 Human-AI Interaction for Text Analysis

**What to cover:**
- HAI guidelines (PAIR, Microsoft)
- Transparency in NLP systems
- User control in AI-assisted tools

**Key papers to cite:**
- Amershi et al. (2019): "Guidelines for Human-AI Interaction"
- Shneiderman (2020): "Human-Centered AI"
- [Add domain-specific examples]

**[TODO: Write 1-2 paragraphs with 3-5 citations]**

---

## Section 3: System Design (2-3 pages)

### 3.1 Architecture Overview

**What to include:**
- High-level architecture diagram (from [architecture.md](architecture.md))
- Component breakdown: Frontend, Extraction, Q&A, Data
- Technology stack

**[TODO: Insert diagram and write 1 page describing architecture]**

### 3.2 Extraction Pipeline

**What to include:**
- Stage 1: Preprocessing and candidate detection
- Stage 2: Component classification (LLM)
- Stage 3: Relation extraction (LLM)
- Stage 4: Graph construction (deterministic)
- Prompt templates (excerpt or appendix)

**Source:** Adapt from [intelligence_design.md](intelligence_design.md)

**[TODO: Write 1 page; include pseudocode or flowchart]**

### 3.3 User Interface Design

**What to include:**
- Screenshot of main UI
- Key features: graph visualization, node details, Q&A panel
- Interaction flow for primary tasks

**Source:** Adapt from [ui_guide.md](ui_guide.md) and milestone 2 screenshots

**[TODO: Write 0.5 page with screenshots]**

### 3.4 HAI Design Principles

**What to include:**
- Three key HAI guidelines implemented (from [hai_design_principles.md](hai_design_principles.md)):
  - G1: Make clear what system can do
  - G16: Support efficient correction
  - G9: Show contextually relevant information
- How each is implemented in the UI

**[TODO: Write 0.5-1 page; include UI examples]**

---

## Section 4: Implementation (1 page)

### 4.1 Technology Choices

**What to write:**
- Frontend: Streamlit (why? rapid prototyping, reactive UI)
- Visualization: PyVis (why? interactive graphs)
- LLM API: OpenAI GPT-4 / Anthropic Claude (why? state-of-art reasoning)
- Deployment: Local / Streamlit Cloud (why? ease of use)

**[TODO: Write 0.5 page justifying choices]**

### 4.2 Key Challenges & Solutions

**What to write:**
- Challenge 1: Managing LLM cost → Solution: Heuristic pre-filtering
- Challenge 2: Graph layout readability → Solution: Hierarchical algorithm
- Challenge 3: Real-time interactivity → Solution: Session state management

**[TODO: Write 0.5 page with 2-3 challenges]**

---

## Section 5: Evaluation (2-3 pages)

### 5.1 Evaluation Methodology

**What to include:**
- Overview of evaluation strategy (human users + LLM-as-user)
- Participant details: N=X, demographics, recruitment
- Tasks: Graph generation, node inspection, Q&A, error correction
- Metrics: SUS, task completion time, accuracy, think-aloud themes

**Source:** Summarize from [evaluation_plan.md](evaluation_plan.md)

**[TODO: Write 0.5 page]**

### 5.2 Usability Results

**What to report:**
- System Usability Scale (SUS) score: X ± SD
- Task completion rates: X% for each task
- Task completion times: Mean ± SD
- Qualitative themes from think-aloud and questionnaire

**Important:** Use actual evaluation data, not fabricated numbers.

**[TODO: Write 0.5-1 page with table of results]**

### 5.3 Utility Results

**What to report:**
- Did users find the graph helpful? (Likert scale responses)
- Comparison to text-only baseline (if conducted)
- Evidence that graph aided comprehension (task accuracy, user quotes)

**[TODO: Write 0.5 page]**

### 5.4 Trust Calibration Results

**What to report:**
- Did users adjust reliance based on confidence scores?
- Were low-confidence nodes reviewed more carefully?
- User quotes on transparency and trust

**[TODO: Write 0.5 page]**

### 5.5 LLM-as-User Evaluation

**What to report:**
- Graph quality scores: Accuracy, completeness, usefulness (mean ± SD)
- Q&A usefulness scores
- Common failure modes identified
- Examples of LLM critique

**Important:** Use actual LLM evaluation results.

**[TODO: Write 0.5-1 page]**

---

## Section 6: Discussion (1-2 pages)

### 6.1 Key Findings

**What to write:**
- Finding 1: Users successfully extracted and explored graphs with minimal training
- Finding 2: Confidence scores helped calibrate trust (or didn't—report honestly)
- Finding 3: Editing feature was underutilized / well-used (report actual behavior)

**[TODO: Write 0.5 page]**

### 6.2 Limitations

**What to write:**
- Extraction accuracy: Current system makes X% errors (be specific)
- Scalability: Works for texts up to Y words; struggles with longer
- Generalizability: Tested on philosophical/op-ed texts; unclear performance on legal/scientific
- Evaluation scope: Small sample (N=X); more participants needed

**Important:** Be honest about limitations. This strengthens your work.

**[TODO: Write 0.5 page]**

### 6.3 Design Implications

**What to write:**
- Implication 1: Confidence visualization matters—users changed behavior based on it
- Implication 2: Progressive disclosure reduced overwhelm (or didn't—report findings)
- Implication 3: Correction UI needs X improvement (based on user feedback)

**[TODO: Write 0.5 page]**

---

## Section 7: Future Work (0.5 page)

**What to include:**
- **Short-term (next 6 months):**
  - Improve extraction accuracy with fine-tuned models
  - Add real-time collaboration features
  - Expand evaluation to N=30+ users

- **Long-term (beyond 1 year):**
  - Multi-language support
  - Integration with knowledge management tools (Obsidian, Notion)
  - Active learning from user corrections

**[TODO: Write 0.5 page with 3-5 concrete next steps]**

---

## Section 8: Conclusion (0.5 page)

**What to write:**
- Restate problem and your solution
- Summarize key contributions
- Emphasize what worked well
- End with broader impact: "This work demonstrates that..."

**[TODO: Write 3-4 paragraphs]**

---

## Section 9: Reflection on LLM Use (0.5-1 page)

**⚠️ IMPORTANT: This section MUST be written by humans, not LLMs.**

### 9.1 How You Used LLMs

**What to write:**
- Which tasks: Brainstorming, code generation, prompt design, documentation, debugging, etc.
- Which models: GPT-4, Claude, Copilot, etc.
- Approximate % of code/text generated by LLM vs. written by you

**Be specific:**
- "We used GPT-4 to generate initial prompt templates for classification, then manually refined them."
- "GitHub Copilot suggested ~40% of the Python code, which we reviewed and modified."

**[TODO: TEAM MUST WRITE THIS—honest reflection on LLM use]**

### 9.2 What Worked Well

**What to write:**
- Examples where LLM accelerated work (e.g., "Boilerplate UI code was generated quickly")
- Where LLM suggestions were high quality and required minimal editing

**[TODO: TEAM MUST WRITE THIS]**

### 9.3 What Didn't Work

**What to write:**
- Examples where LLM output was wrong or misleading
- Time spent debugging LLM-generated code
- Concepts LLM misunderstood

**Be honest:** "GPT-4 generated a graph layout algorithm that didn't work; we had to rewrite from scratch."

**[TODO: TEAM MUST WRITE THIS]**

### 9.4 Lessons Learned

**What to write:**
- Best practices for using LLMs in projects
- When to rely on LLMs vs. write yourself
- How this experience shaped your view of AI-assisted development

**[TODO: TEAM MUST WRITE THIS—critical reflection]**

---

## References

**Instructions:**
- Use a standard citation style (IEEE, ACM, APA)
- Cite all papers mentioned in Related Work
- Cite HAI guidelines, argumentation theory papers, technical docs
- Aim for 15-20 references

**[TODO: Compile bibliography from all sections]**

---

## Appendices (Optional)

### Appendix A: User Study Materials

- Consent form
- Task instructions
- Post-task questionnaire
- Full transcript examples (anonymized)

### Appendix B: LLM Evaluation Prompts

- Full prompt templates used for critique
- Example LLM outputs

### Appendix C: Code Repository

- Link to GitHub: `https://github.com/EyalKotlik/IIS-Project`
- Directory structure
- Key files and their purposes

### Appendix D: Additional Screenshots

- More UI screenshots not included in main text
- Annotated mockups showing design iterations

---

## Checklist Before Submission

- [ ] All sections written (no `[TODO]` markers remaining)
- [ ] Actual evaluation data included (no fabricated results)
- [ ] Section 9 (LLM Reflection) written by humans
- [ ] All figures have captions and are referenced in text
- [ ] All citations formatted correctly
- [ ] Page limit respected (8-12 pages excluding references/appendices)
- [ ] PDF generated from LaTeX / Word template
- [ ] GitHub repository link included and accessible
- [ ] Spell-checked and proofread
- [ ] Co-authors reviewed and approved

---

## Related Documentation

- [Evaluation Plan](evaluation_plan.md) — Source for Section 5 (Evaluation)
- [Architecture](architecture.md) — Source for Section 3.1 (Architecture)
- [Intelligence Design](intelligence_design.md) — Source for Section 3.2 (Extraction Pipeline)
- [HAI Design Principles](hai_design_principles.md) — Source for Section 3.4 (HAI Design)
- [UI Guide](ui_guide.md) — Source for Section 3.3 (UI Design)
- [ROADMAP](../ROADMAP.md) — Project timeline context
