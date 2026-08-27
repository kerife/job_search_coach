# Installed synthetic smoke attestation

no_real_profile_mapping: true

case_id: `PGC-CASE-I`

origin_class: `synthetic_composite`

derivation: `counterfactual_non_mappable`

real_profile_mapping: `none_created`

attestation_state: `installed_green`

plugin_identity: `professional-growth-coach@professional-growth-coach-local`

release_version_prefix: `0.2.0+codex`

release_timestamp: `2026-08-27T12:45:15-06:00`

source_commit: `3e8c977baa2f340cf5ea64314f4c8438453be31e`

source_tree: `24f7a5a699668ae6ebd93f1ed20cc61f681cd567`

installed_cache_family: `professional-growth-coach-local/professional-growth-coach`

installed_cache_version: `0.2.0+codex.20260827124515`

installed_enabled: `true`

source_file_count: `158`

installed_file_count: `158`

normalized_source_cache_sha256: `bdcd38842af987810360ca0f9d8090749a171a9020eafc04a9b329cd0f084faf`

normalized_digest_method: `sha256(sorted relative path + NUL + file bytes; excludes __pycache__)`

normalized_excludes: `__pycache__`

active_config: `canonical_and_public_enabled`
release_smoke_plugin: `professional-growth-coach@professional-growth-coach-local`

source_cache_equivalence: `diff_qr_silent`

installed_renderer_smokes: `6/6 triage validator/renderer fixtures`

installed_reading_path_smoke: `4/4 localized fragment links; aria-current fallback; nearest-target IntersectionObserver enhancement; print/mobile offsets`

installed_dossier_v2_smoke: `4/4 EN/ES validator and renderer`

installed_market_next_research_smoke: `2/2 EN/ES unavailable-market cards expose bounded scope, sample, sources, date, and read-only boundary`

installed_dossier_validator_argument_privacy_smoke: `2/2 dossier validators return fixed opaque errors for unknown arguments`

installed_linkedin_validator_argument_privacy_smoke: `1/1 LinkedIn report validator returns a fixed opaque error for unknown arguments`

installed_market_cli_argument_privacy_smoke: `5/5 market validators and builder return fixed opaque errors for unknown arguments`

installed_market_research_smoke: `2/2 complete/limited validator`

installed_market_learning_smoke: `2/2 complete/limited builder and validator`

installed_market_renderer_smoke: `2/2 complete/limited market composition`

installed_v2_context_smoke: `2/2 EN/ES provenance, alignment coverage, vacancy context, public-source links, dates, and directional legend`
installed_vacancy_freshness_smoke: `2/2 EN/ES per-vacancy access/publication dates, 90-day status text, unknown-date boundary, and title-contextual source aria-label`
installed_learning_source_identity_smoke: `1/1 installed learning validator rejects trailing-slash and percent-decoded equivalent source URLs`
installed_release_digest_documentation_smoke: `1/1 release runner validator digests match the release documentation`

installed_replay_fingerprint_smoke: `1/1 stable identity-free receipt/checkpoint replay key`
installed_source_traceability_smoke: `2/2 EN/ES public-source links and research dates`
installed_theme_accessibility_smoke: `2/2 light tokens declared and muted text separated from border token`
installed_url_policy_smoke: `1/1 encoded LinkedIn path traversal rejected`
installed_market_json_boundary_smoke: `5/5 market validators and builder reject excessive JSON nesting`

installed_diagnostic_redaction_smoke: `6/6`

installed_descriptor_boundary_smoke: `6/6`

installed_linkedin_diagnostic_redaction_smoke: `4/4`

installed_bounded_diagnostics_smoke: `1/1`

installed_linkedin_bounded_diagnostics_smoke: `1/1 16 KiB cap with stable truncation marker`
installed_practice_readiness_smoke: `2/2 ES/EN renderer locale checks with readiness card`
installed_triage_practice_smoke: `2/2 ES/EN installed builder, validator, and renderer checks with triage route`

installed_answer_boundary_smoke: `2/2 ES/EN installed builder, validator, and renderer checks with answer boundary`

installed_handoff_prose_smoke: `2/2 ES/EN installed valid renderer; validator-hostile and URL-hostile prose rejected before output`

installed_handoff_wrapper_renderer_smoke: `2/2 ES/EN installed builder, wrapper validator, and wrapper-to-HTML receipts with 0600 outputs`

installed_triage_first_answer_outline_smoke: `2/2 ES/EN installed builder, validator, and renderer checks with localized triage-first answer outline`

installed_private_cli_receipt_smoke: `2/2 ES/EN installed builder, validator, and renderer receipts; renderer outputs 0600; malformed direct CLI arguments return fixed opaque errors`

installed_cli_receipt_privacy_smoke: `5/5 default receipts omit absolute artifact path; explicit opt-in restores path`

installed_private_validator_argument_privacy_smoke: `3/3 private validators return fixed opaque errors for unknown arguments`

installed_private_json_loader_hardening_smoke: `7/7 installed private loaders and dossier/practice renderers reject oversized-integer JSON with fixed opaque errors; no traceback, raw-content echo, or output artifact`

installed_action_aligned_rail_smoke: `11/11 installed EN/ES outcome/checkpoint rails select closed action copy, stop renders a terminal recorded rail, dark surface and forced-colors hooks are present, and non-finite schema numbers are rejected`

installed_continuity_rail_semantics_smoke: `2/2 installed EN/ES outcome/checkpoint rails expose recorded -> pending -> blocked states with exactly one aria-current="step" pending safe step; terminal stop remains recorded`

installed_duplicate_vacancy_source_url_smoke: `1/1 installed market validator rejects duplicate normalized vacancy source URLs even when vacancy IDs and fingerprints differ`

installed_practice_continuity_accessibility_smoke: `2/2 installed EN/ES practice rails expose recorded evidence/decision states and exactly one pending-or-blocked aria-current="step" without private identifiers or interactive controls`

installed_triage_handoff_continuity_smoke: `2/2 installed EN/ES triage handoffs expose recorded -> recorded -> pending states with one aria-current="step" re-entry stage and preserve manual-only boundaries`

installed_shortlist_artifact_smoke: `1/1 installed EN/ES shortlist builder, validator, and offline renderer; rows retain draft-only/no-message/no-calendar controls and HTML omits target/fact identifiers`
installed_shortlist_boundary_smoke: `4/4 installed shortlist rejects asset symlinks, output-parent symlinks, non-HTTP URI prose, and future-dated direct renders`

installed_decision_gate_smoke: `3/3 installed EN/ES decision-gate builder, validator, and renderer; counts/snapshot reconcile, screen context remains manual-only, and HTML omits target/fact identifiers`

installed_screen_intake_smoke: `3/3 installed EN/ES target-specific intake builder, validator, and renderer; advance-only manual handoff, snapshot/locale binding, private IDs hidden, and 0600 output`

installed_duplicate_employer_source_url_smoke: `1/1 installed market validator rejects duplicate normalized employer official_source_url values without echoing the URL`

installed_screen_debrief_smoke: `2/2 installed EN/ES completed screen_attended checkpoints render the closed debrief_after_screen action, preserve manual-only follow-up boundaries, and reject preparation routing`

installed_feedback_sensitive_continuity_rail_smoke: `6/6 ES/EN feedback labels render one deterministic three-step rail with closed pending/blocked state copy`

fresh_agent_smoke: `not_run`

fresh_agent_smoke_scope: `direct installed CLI validation/render smoke only; no new agent session; no external action`

official_release_validator: `passed`

external_action_state: `not_executed`

This record is a deterministic synthetic release attestation. It contains no
real profile mapping, recruiter identity, credential, or external action.
