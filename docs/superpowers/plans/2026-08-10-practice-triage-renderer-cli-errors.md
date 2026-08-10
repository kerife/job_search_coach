# Practice and triage renderer CLI errors Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make malformed practice and triage renderer arguments deterministic and consistent.

**Architecture:** Wrap only parse_args in the two existing `_cli` functions; preserve all loader, validator, writer, and success paths.

**Tech Stack:** Python 3 standard library, unittest, subprocess.

## Global Constraints

- Invalid/missing/unknown arguments return 3.
- `--help` returns 0.
- Semantic validation remains 2; no traceback or artifact.

### Task 1: Normalize renderer parsing

**Files:**
- Modify: `plugins/job-search-coach/scripts/render_recruiter_practice_session.py`
- Modify: `plugins/job-search-coach/scripts/render_private_recruiter_reply_triage.py`
- Modify: focused practice/triage renderer tests

- [ ] **Step 1: Add failing CLI tests**

  Invoke each renderer with an unknown argument and omitted required input/output; assert code 3, no traceback, and no output artifact. Assert help remains 0.

- [ ] **Step 2: Run tests and verify RED**

  Run both focused renderer test modules; expect current argparse code 2.

- [ ] **Step 3: Implement minimal catches**

  Catch parser `SystemExit`, returning 0 for help and 3 for other parse exits; leave validation exception handling unchanged.

- [ ] **Step 4: Verify GREEN**

  Run focused practice/triage suites, static/privacy checks, and `git diff --check`.

- [ ] **Step 5: Commit**

  Commit renderers, tests, spec, and plan as `fix: normalize practice triage renderer CLI`.
