# LinkedIn source diagnostic identifier redaction Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prevent untrusted source identifiers, categories, parser labels, and duplicate reference values from leaking through LinkedIn diagnostics.

**Architecture:** Keep source validation and state resolution unchanged. Route source IDs and duplicate report references through `_safe_diagnostic_identifier()`, use an allowlisted category helper for valid source categories, and assert both API and CLI behavior.

**Tech Stack:** Python 3, `unittest`, standard-library CLI helpers.

## Global Constraints

- Preserve valid synthetic source IDs and canonical source categories.
- Return `<redacted-value>` for path-like or sensitive untrusted values.
- Redact duplicate evidence, fact, and claim values while preserving canonical IDs.
- Keep one deterministic diagnostic per CLI stderr line.
- Do not modify HTML, CSS, schemas, or source registry data.

---

### Task 1: RED regression

**Files:**
- Modify: `tests/test_linkedin_report_fixtures.py`

- [x] Add API+CLI cases for a path-like `source_id` with stale invalid fallback and a path-like `source_category` with an unregistered official URL.
- [x] Run the focused test and observe raw sentinel leakage.

### Task 2: GREEN implementation

**Files:**
- Modify: `plugins/professional-growth-coach/scripts/validate_linkedin_client_report.py`

- [x] Wrap `source_category` and `source_id` only at their diagnostic interpolation sites with `_safe_diagnostic_identifier()`.
- [x] Wrap duplicate priority/copy evidence, fact, and claim values with `_safe_diagnostic_identifier()`; preserve allowlisted `SOURCE_CATEGORIES` through `_safe_source_category()`.
- [x] Route unknown score dimensions, unexpected copy headings, and generic priority codes through `_safe_diagnostic_field_name()` so ordinary diagnostic text remains readable while paths are redacted.
- [x] Run the focused regression and LinkedIn suite.

### Task 3: Release

**Files:**
- Modify: plugin manifest and deterministic provenance/smoke artifacts.

- [ ] Run full plugin, static, privacy, official validator, and parity gates.
- [ ] Bump/install the plugin, rebind provenance, verify cache parity, and push.
