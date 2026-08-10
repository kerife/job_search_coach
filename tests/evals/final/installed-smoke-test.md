# Interim synthetic release attestation

no_real_profile_mapping: true

case_id: `JSC-CASE-I`

origin_class: `synthetic_composite`

derivation: `counterfactual_non_mappable`

real_profile_mapping: `none_created`

attestation_state: `interim_not_installed`

This record is a deterministic source-tree fixture, not a live agent transcript
and not evidence of a fresh plugin installation. Increment 5 performs no
cachebuster update, marketplace edit, Codex configuration change, or plugin
install. Increment 6 must replace this file after exact installation
authorization, source-to-cache equivalence checks, official validator passes,
and a fresh installed synthetic smoke run.

Aggregate source-tree evidence available at this increment:

- Repository privacy gate: passed on controlled synthetic artifacts.
- Static checker: passed on the source tree.
- Full unit suite: passed on the source tree.
- Official validators: passed through the checksum-gated pinned runner.
- External action state: `not_executed`.
