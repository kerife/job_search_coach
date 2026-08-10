# Private contract-layer gate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the private schema harness execute conversion and follow-through semantic validators with deterministic dates.

**Architecture:** Keep `test_private_schema_conformance.py` as the single gate entry point. Add fixture loading and semantic checks beside the existing schema checks; use in-memory mutations for negative coverage. `run_static_checks.py` continues invoking the harness and reporting only bounded diagnostics.

**Tech Stack:** Python 3 standard library, `unittest`, existing plugin validators, dependency-free schema subset checker.

## Global Constraints

- Use fixed `date(2026, 8, 9)` values in the harness.
- Do not add dependencies, identity fields, external actions, persistence, or routing changes.
- Keep failures deterministic and free of fixture prose/raw candidate data.

### Task 1: Add semantic fixture gate tests

**Files:**
- Modify: `plugins/job-search-coach/tests/test_private_schema_conformance.py`
- Test: existing harness module

**Interfaces:**
- Consumes: `validate_private_recruiter_conversion_outcome.load_outcome`, `validate_outcome`, `validate_private_recruiter_followthrough_checkpoint.load_checkpoint`, `validate_checkpoint`.
- Produces: harness tests that fail when schema-valid mutations violate semantic contracts.

- [ ] **Step 1: Write failing tests** for all fixtures and four mutations: future date, receipt event mismatch, external action enabled, and incorrect next-safe action.
- [ ] **Step 2: Run the harness and verify the new semantic assertions fail before implementation.**
- [ ] **Step 3: Implement minimal fixture loading and fixed-date semantic assertions.**
- [ ] **Step 4: Run the harness, focused validator suites, and static checks.**
- [ ] **Step 5: Commit the implementation and spec updates.**

### Task 2: Verify publication gates

**Files:**
- Modify: provenance fixtures only when the release commit changes them.

**Interfaces:**
- Consumes: green harness from Task 1.
- Produces: published plugin version with source/cache identity evidence.

- [ ] **Step 1: Run full plugin discovery and record failures without suppressing output.**
- [ ] **Step 2: Refresh only required provenance fields and run static/privacy gates.**
- [ ] **Step 3: Invoke the cachebuster exactly once and commit the manifest/provenance.**
- [ ] **Step 4: Install the exact cache version, compare source/cache trees, run focused smoke, and remove generated caches.**
