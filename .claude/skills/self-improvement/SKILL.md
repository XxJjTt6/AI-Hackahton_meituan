---
name: self-improvement
description: Capture project learnings, command failures, user corrections, and missing capability requests in `.learnings/` so future Claude Code sessions can reuse them. Use when a command fails, the user corrects Claude, a project assumption is disproven, a better recurring workflow is discovered, or the user asks for an automation/capability that does not exist yet.
---

# Self Improvement

This skill maintains lightweight project memory in `.learnings/`.

## Files

Use these project-root files:

- `.learnings/LEARNINGS.md` for corrections, insights, knowledge gaps, official scoring lessons, and best practices.
- `.learnings/ERRORS.md` for failed commands, broken docs, missing tools, and integration failures.
- `.learnings/FEATURE_REQUESTS.md` for requested automations or missing capabilities.

If `.learnings/` or any of the three files is missing, create the missing pieces without overwriting existing content.

## When To Log

Append to `.learnings/ERRORS.md` when:

- a command fails unexpectedly
- a documented command is missing or stale
- a tool/API/integration fails
- a generated patch or script fails and the fix is useful later

Append to `.learnings/LEARNINGS.md` when:

- the user corrects Claude
- an algorithmic assumption is disproven
- official/platform feedback teaches a reusable lesson
- a better workflow or validation gate is discovered
- a recurring pitfall should be remembered

Append to `.learnings/FEATURE_REQUESTS.md` when:

- the user asks for an automation, checker, dashboard, or workflow that does not exist
- a repeated manual process should become a tool

## Format

Use concise entries. Prefer this structure:

```markdown
## [LRN-YYYYMMDD-short-title] category

**Logged**: YYYY-MM-DDTHH:MM:SS+08:00
**Priority**: low | medium | high | critical
**Status**: pending | applied | fixed | rejected
**Area**: algorithm | tests | tooling | docs | submission

### Summary
One sentence.

### Details
Enough context to avoid repeating the mistake.

### Suggested Action
Concrete next action.

### Metadata
- Source: conversation | command | official_feedback | user_feedback
- Related Files: `path`
- Tags: tag1, tag2
```

For errors, use `ERR-YYYYMMDD-short-title`; for feature requests, use `FEAT-YYYYMMDD-short-title`.

## Promotion Rule

If a learning is repeatedly useful or changes how future agents should work, propose promoting it into `AGENTS.md` and `CLAUDE.md`.

## Safety

Do not log secrets, API keys, private tokens, full environment variables, raw browser/session cookies, full private datasets, or unredacted credentials.
