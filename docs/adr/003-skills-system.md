# ADR-003: Anthropic-Style Skills System

## Status
Accepted

## Context
We needed a way to:
- Configure AI behavior for specific tasks
- Share reusable instructions across conversations
- Allow non-developers to customize AI capabilities
- Maintain consistency across different use cases

## Decision
We implemented an **Anthropic-style Skills system** using SKILL.md files.

## Design

### Skill Structure
```
skills/
├── code-review/
│   └── SKILL.md      # Instructions + metadata
├── python-developer/
│   └── SKILL.md
└── data-analyst/
    └── SKILL.md
```

### SKILL.md Format
```yaml
---
name: skill-name
description: What this skill does
version: 1.0.0
tags: [development, python]
tools: [execute_code, read_file]
---

# Skill Name

Instructions markdown content...

## Examples
## Guidelines
```

## Rationale

### Why Skills?
1. **Reusability** - Define once, use everywhere
2. **Versioning** - Track skill changes
3. **Composability** - Activate multiple skills
4. **Simplicity** - Markdown-based, easy to create

### Comparison to Alternatives

| Approach | Reusable | Versioned | Easy to Create |
|----------|----------|-----------|----------------|
| **Skills (SKILL.md)** | ✅ | ✅ | ✅ |
| System prompts | ❌ | ❌ | ✅ |
| Fine-tuning | ✅ | ⚠️ | ❌ |
| RAG only | ⚠️ | ❌ | ✅ |

## Implementation

```python
# Activate skill
registry.activate_skill("code-review")

# Get combined prompt
prompt = registry.get_active_skills_prompt()
messages.insert(0, {"role": "system", "content": prompt})
```

## Consequences

### Positive
- Non-technical users can create skills
- Easy to share and version control
- No model retraining required
- Dynamic activation/deactivation

### Negative
- Adds to context length
- Not as precise as fine-tuning
- Skill conflicts possible

---
*Decided: January 2026*
