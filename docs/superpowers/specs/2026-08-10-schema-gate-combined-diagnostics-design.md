# Combine bounded nonzero harness diagnostics

## Goal

Retain useful error context from both subprocess channels when stderr has an
error and stdout has only the unittest summary.

## Design

For nonzero harness results, collect non-empty first/last lines from each channel,
deduplicate in stable order, and cap the diagnostic at four lines. Keep the
harness path, existing one-error contract, and no raw middle logs. Summary
selection for successful results remains unchanged.

## Verification

Test error+summary across channels, warning+error, empty channels, and truncation.
Pass, timeout, invalid-summary, and static behavior remain green.
