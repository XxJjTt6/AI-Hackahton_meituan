# Claude Code Instructions

@AGENTS.md

This project is an AutoSolver competition repository. Treat `solver.py` as the only official submission artifact and follow the constraints in `AGENTS.md`.

## Self-Improvement Workflow

Use the local `self-improvement` skill for this project.

Before substantial work, read:

- `.learnings/LEARNINGS.md`
- `.learnings/ERRORS.md`
- `.learnings/FEATURE_REQUESTS.md`

Log new project memory as follows:

- Command failures, missing tools, broken docs, failed integrations -> append to `.learnings/ERRORS.md`.
- User corrections, disproven assumptions, better recurring workflows, official scoring lessons -> append to `.learnings/LEARNINGS.md`.
- Requested automation or missing capabilities -> append to `.learnings/FEATURE_REQUESTS.md`.
- Repeatedly useful lessons -> propose promoting them into `AGENTS.md` and this file.

Do not log secrets, API keys, private tokens, full environment variables, full private datasets, or raw login/session material.

## AutoSolver Validation

Use these as the default local gates after solver changes:

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
python3 _bench.py solver.py 1
```

Do not call `python3 -m autosolver.submission_audit` unless the missing module has been restored.

## Submission Discipline

Official submissions are scarce. Do not submit or recommend submitting a candidate unless it has credible evidence for roughly `>= 1.0` average-score improvement or high information value approved by the user.

Never resubmit a known official SHA recorded in `AGENTS.md`, `.learnings/LEARNINGS.md`, or `runs/official_submit_*.json`.
