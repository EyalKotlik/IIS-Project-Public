# Data Formats

## Overview

This document defines the data structures used in the Argument Graph Builder, primarily the graph schema for nodes, edges, and metadata. These formats are used for internal representation, JSON export, and data exchange between components.

---

## Graph Schema

### Top-Level Structure

```json
{
  "nodes": [ /* array of Node objects */ ],
  "edges": [ /* array of Edge objects */ ],
  "meta": { /* Metadata object */ }
}
```

---

## Node Object

### Schema

```json
{
  "id": "string",
  "type": "string",
  "label": "string",
  "span": "string",
  "paraphrase": "string",
  "confidence": "number",
  "position": {
    "x": "number",
    "y": "number"
  },
  "edits": "array (optional)"
}
```

### Field Descriptions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Unique identifier (e.g., "n1", "n2", ...) |
| `type` | string | Yes | One of: "claim", "premise", "objection", "reply", "other" |
| `label` | string | Yes | Short summary (3-8 words) for graph visualization |
| `span` | string | Yes | Original text excerpt from source document |
| `paraphrase` | string | Yes | LLM-generated simplified explanation |
| `confidence` | number | Yes | 0.0-1.0 confidence score for this node |
| `position` | object | Optional | X/Y coordinates for graph layout |
| `edits` | array | Optional | Array of user edits (see Edit History below) |

### Valid Values

**`type`:**
- `"claim"`: Central assertion or thesis
- `"premise"`: Evidence or reasoning supporting a claim
- `"objection"`: Challenge or counterargument
- `"reply"`: Response to an objection
- `"other"`: Not a significant argument component

**`confidence`:** Float between 0.0 and 1.0
- 0.8-1.0: High confidence
- 0.6-0.8: Moderate confidence
- 0.4-0.6: Low confidence
- 0.0-0.4: Very uncertain

### Example

```json
{
  "id": "n1",
  "type": "claim",
  "label": "Death penalty should be abolished",
  "span": "The death penalty should be abolished because it fails to deter crime, is applied unfairly, and risks executing innocent people.",
  "paraphrase": "The author argues that capital punishment should be ended due to its ineffectiveness, inequitable application, and danger of wrongful executions.",
  "confidence": 0.92,
  "position": {
    "x": 400,
    "y": 100
  }
}
```

---

## Edge Object

### Schema

```json
{
  "source": "string",
  "target": "string",
  "relation": "string",
  "confidence": "number"
}
```

### Field Descriptions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `source` | string | Yes | Node ID where the relation originates |
| `target` | string | Yes | Node ID where the relation points to |
| `relation` | string | Yes | Type of relation: "support" or "attack" |
| `confidence` | number | Yes | 0.0-1.0 confidence score for this relation |

### Valid Values

**`relation`:**
- `"support"`: Source provides evidence/reasoning for target
- `"attack"`: Source challenges or refutes target

**Direction semantics:**
- Support: `source` → `target` (source supports target)
- Attack: `source` ⇢ `target` (source attacks target)

### Example

```json
{
  "source": "n2",
  "target": "n1",
  "relation": "support",
  "confidence": 0.85
}
```

This indicates: Node n2 supports Node n1 with 85% confidence.

---

## Metadata Object

### Schema

```json
{
  "source": "string",
  "created_at": "string (ISO 8601)",
  "model_version": "string",
  "extraction_params": "object (optional)",
  "note": "string (optional)"
}
```

### Field Descriptions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `source` | string | Yes | Origin of the graph: "user_input", "sample_1", etc. |
| `created_at` | string | Yes | ISO 8601 timestamp (e.g., "2025-01-15T10:30:00Z") |
| `model_version` | string | Yes | Extraction model version (e.g., "gpt-4-turbo", "mock-v1.0") |
| `extraction_params` | object | Optional | Parameters used during extraction |
| `note` | string | Optional | Human-readable note about this graph |

### Example

```json
{
  "source": "user_input",
  "created_at": "2025-01-15T14:23:00Z",
  "model_version": "gpt-4-turbo-2024-01",
  "extraction_params": {
    "confidence_threshold": 0.5,
    "max_nodes": 50,
    "include_implicit_premises": false
  },
  "note": "Extracted from article on criminal justice reform"
}
```

---

## Complete Example

### Full Graph JSON

```json
{
  "nodes": [
    {
      "id": "n1",
      "type": "claim",
      "label": "Death penalty should be abolished",
      "span": "The death penalty should be abolished because it fails to deter crime, is applied unfairly, and risks executing innocent people.",
      "paraphrase": "The author argues that capital punishment should be ended due to its ineffectiveness, inequitable application, and danger of wrongful executions.",
      "confidence": 0.92,
      "position": {"x": 400, "y": 100}
    },
    {
      "id": "n2",
      "type": "premise",
      "label": "No deterrent effect proven",
      "span": "Studies consistently show no correlation between execution rates and crime rates, suggesting the death penalty does not deter crime.",
      "paraphrase": "Research indicates that having the death penalty doesn't actually prevent crimes from happening.",
      "confidence": 0.88,
      "position": {"x": 250, "y": 250}
    },
    {
      "id": "n3",
      "type": "objection",
      "label": "Deterrence is hard to measure",
      "span": "Critics argue that deterrence is difficult to measure empirically, and absence of evidence is not evidence of absence.",
      "paraphrase": "Some people say just because we can't prove it deters crime doesn't mean it doesn't work.",
      "confidence": 0.79,
      "position": {"x": 550, "y": 250}
    },
    {
      "id": "n4",
      "type": "reply",
      "label": "Burden of proof on proponents",
      "span": "However, the burden of proof should be on those who advocate for state execution to demonstrate its necessity and effectiveness.",
      "paraphrase": "The author responds that people who support the death penalty should have to prove it works, not the other way around.",
      "confidence": 0.82,
      "position": {"x": 550, "y": 400}
    }
  ],
  "edges": [
    {
      "source": "n2",
      "target": "n1",
      "relation": "support",
      "confidence": 0.85
    },
    {
      "source": "n3",
      "target": "n2",
      "relation": "attack",
      "confidence": 0.75
    },
    {
      "source": "n4",
      "target": "n3",
      "relation": "attack",
      "confidence": 0.80
    }
  ],
  "meta": {
    "source": "sample_1",
    "created_at": "2025-01-15T10:00:00Z",
    "model_version": "mock-v1.0",
    "note": "Sample death penalty argument"
  }
}
```

---

## Edit History (Optional Extension)

### Purpose

Track user edits to nodes for analysis and model improvement.

### Schema

```json
{
  "edits": [
    {
      "timestamp": "string (ISO 8601)",
      "user_id": "string (optional)",
      "field": "string",
      "old_value": "any",
      "new_value": "any",
      "reason": "string (optional)"
    }
  ]
}
```

### Example

```json
{
  "id": "n3",
  "type": "premise",  // Changed from "objection"
  "label": "Deterrence is hard to measure",
  "span": "...",
  "paraphrase": "...",
  "confidence": 0.79,
  "edits": [
    {
      "timestamp": "2025-01-15T14:30:00Z",
      "user_id": "user_123",
      "field": "type",
      "old_value": "objection",
      "new_value": "premise",
      "reason": "This is actually supporting evidence, not an objection"
    }
  ]
}
```

---

## Validation

### JSON Schema (for validation tools)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Argument Graph",
  "type": "object",
  "required": ["nodes", "edges", "meta"],
  "properties": {
    "nodes": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["id", "type", "label", "span", "paraphrase", "confidence"],
        "properties": {
          "id": {"type": "string", "pattern": "^n[0-9]+$"},
          "type": {"type": "string", "enum": ["claim", "premise", "objection", "reply", "other"]},
          "label": {"type": "string", "minLength": 1, "maxLength": 100},
          "span": {"type": "string", "minLength": 1},
          "paraphrase": {"type": "string", "minLength": 1},
          "confidence": {"type": "number", "minimum": 0, "maximum": 1},
          "position": {
            "type": "object",
            "properties": {
              "x": {"type": "number"},
              "y": {"type": "number"}
            }
          }
        }
      }
    },
    "edges": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["source", "target", "relation", "confidence"],
        "properties": {
          "source": {"type": "string"},
          "target": {"type": "string"},
          "relation": {"type": "string", "enum": ["support", "attack"]},
          "confidence": {"type": "number", "minimum": 0, "maximum": 1}
        }
      }
    },
    "meta": {
      "type": "object",
      "required": ["source", "created_at", "model_version"],
      "properties": {
        "source": {"type": "string"},
        "created_at": {"type": "string", "format": "date-time"},
        "model_version": {"type": "string"},
        "extraction_params": {"type": "object"},
        "note": {"type": "string"}
      }
    }
  }
}
```

### Python Validation

```python
import json
import jsonschema

def validate_graph(graph_data: dict) -> bool:
    """Validate graph data against schema."""
    schema = { ... }  # JSON Schema from above
    try:
        jsonschema.validate(instance=graph_data, schema=schema)
        return True
    except jsonschema.ValidationError as e:
        print(f"Validation error: {e.message}")
        return False
```

---

## Export Formats

### JSON (Native)

**Use case:** Data exchange, archiving, programmatic analysis

**File extension:** `.json`

**Example:** See "Complete Example" above

### Markdown (Human-Readable)

**Use case:** Sharing with non-technical users, inclusion in documents

**File extension:** `.md`

**Example:**

```markdown
# Argument Graph: Death Penalty Argument

## Nodes

### n1: Death penalty should be abolished (Claim, 92% confidence)

**Original Text:**
> The death penalty should be abolished because it fails to deter crime...

**Paraphrase:**
The author argues that capital punishment should be ended...

---

### n2: No deterrent effect proven (Premise, 88% confidence)

**Original Text:**
> Studies consistently show no correlation between execution rates...

**Paraphrase:**
Research indicates that having the death penalty doesn't actually prevent crimes...

---

## Relations

- **n2** supports **n1** (85% confidence)
- **n3** attacks **n2** (75% confidence)
- **n4** attacks **n3** (80% confidence)
```

### CSV (Tabular, for spreadsheet analysis)

**Use case:** Quantitative analysis in Excel/R/Python

**File extension:** `.csv`

**Nodes CSV:**
```csv
id,type,label,span,paraphrase,confidence
n1,claim,"Death penalty should be abolished","The death penalty should be...","The author argues that...",0.92
n2,premise,"No deterrent effect proven","Studies consistently show...","Research indicates...",0.88
```

**Edges CSV:**
```csv
source,target,relation,confidence
n2,n1,support,0.85
n3,n2,attack,0.75
```

### GraphML (For graph analysis tools)

**Use case:** Import into Gephi, Cytoscape, NetworkX

**File extension:** `.graphml`

**Example:**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<graphml xmlns="http://graphml.graphdrawing.org/xmlns">
  <graph id="G" edgedefault="directed">
    <node id="n1">
      <data key="type">claim</data>
      <data key="label">Death penalty should be abolished</data>
      <data key="confidence">0.92</data>
    </node>
    <node id="n2">
      <data key="type">premise</data>
      <data key="label">No deterrent effect proven</data>
      <data key="confidence">0.88</data>
    </node>
    <edge source="n2" target="n1">
      <data key="relation">support</data>
      <data key="confidence">0.85</data>
    </edge>
  </graph>
</graphml>
```

---

## Future Extensions

### Version 2.0 (Potential)

**Additional node fields:**
- `implicit`: Boolean indicating if premise is unstated in original text
- `rhetorical_device`: Array of rhetorical strategies used (e.g., "ethos", "pathos")
- `entities`: Array of named entities mentioned in span

**Additional edge fields:**
- `strength`: Qualitative strength ("weak", "moderate", "strong")
- `type_detail`: More granular relation types ("causal_support", "analogical_support", etc.)

**Additional metadata:**
- `text_source`: Full bibliographic citation
- `user_annotations`: Free-form user notes on the graph

---

## Related Documentation

- [Architecture](architecture.md) — How data flows through the system
- [Intelligence Design](intelligence_design.md) — How graphs are generated
- [Developer Guide](dev_guide.md) — How to work with graph data in code
- [UI Guide](ui_guide.md) — How users interact with graph data
