# Pressure Scorer Article Count Design

## Goal

Keep ordinary English articles in candidate-facing prose from being interpreted as market-volume counts while preserving mismatch detection for actual numeric phrases.

## Root cause

`extract_market_volume_values` backtracks through number-like tokens before market nouns. The token `a` is useful in phrases such as `a couple` and `a dozen`, but an isolated `a` in ordinary prose such as `a job` is not a count. The new canonical employment boundary introduced `a job`, exposing this ambiguity and causing canonical market dossiers to fail the pressure scorer.

## Design

When a market noun is preceded by a number-like span, parse the span as today. Append a value when parsing succeeds. If parsing fails, retain the `None` marker for numeric-looking spans so malformed or out-of-range counts still fail reconciliation; skip only the exact article-only span `a`.

## Acceptance criteria

1. All canonical dossier pressure fixtures pass with zero claim violations.
2. `a job` and equivalent ordinary prose do not create a market-volume mismatch.
3. Existing mismatches for nine/forty/compound invalid counts remain rejected.
4. No schema, renderer, privacy, or external-action behavior changes.
