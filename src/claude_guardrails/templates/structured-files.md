# Structured File Handling

JSON and YAML files are **queryable**, not just readable. Before consuming a whole file, pause and consider the surgical approach.

## The Principle

Reading an entire structured file into context is often wasteful:
- You may only need a few keys
- The structure itself reveals what's interesting
- Large files pollute context with irrelevant data

**Prefer progressive disclosure:** probe structure first, extract selectively, read whole only when necessary.

## The Workflow

For JSON files:
```bash
jq 'type' file.json          # What is this? object/array?
jq 'keys' file.json          # What keys exist?
jq 'length' file.json        # How many elements?
jq '.[0]' file.json          # What does one element look like?
jq '.specific.path' file.json # Extract what you need
```

For YAML files:
```bash
yq 'type' file.yaml          # What is this?
yq 'keys' file.yaml          # What keys exist?
yq '.specific.path' file.yaml # Extract what you need
```

## When to Read Whole File

- File is small (< 100 lines)
- You genuinely need all content (e.g., rewriting entire config)
- Structure is already known and you need full data
- You've explored and determined full read is necessary

## Available Tools

- `jq` — JSON query tool
- `yq` — YAML query tool

When in doubt, probe first.
