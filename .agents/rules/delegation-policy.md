---
trigger: always_on
glob:
description: Model delegation roles for this repo
---

# Delegation Policy

## Claude

- Planning only
- No file edits
- No terminal commands
- No web fetches
- Produces task breakdowns, architecture notes, and delegation prompts

## Gemini 3.1 Pro

- Primary executor
- Handles file edits
- Runs lint, tests, report generation, and fix loops
- Applies repo rules after every edit
- Follows `loop-until-done.md` and `lint-and-fix.md`

## DeepSeek

- Research only
- Validates citations
- Checks external technical claims
- Helps confirm rationale and documentation accuracy

## Coordination Rule

- Claude plans the work
- DeepSeek verifies external facts
- Gemini implements and fixes
- Stop after each pass and request human review before repeating loops
