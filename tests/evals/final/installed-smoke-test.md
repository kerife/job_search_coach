# Installed synthetic smoke attestation

no_real_profile_mapping: true

case_id: `PGC-CASE-I`

origin_class: `synthetic_composite`

derivation: `counterfactual_non_mappable`

real_profile_mapping: `none_created`

attestation_state: `installed_green`

plugin_identity: `professional-growth-coach@professional-growth-coach-local`

release_version_prefix: `0.2.0+codex`

release_timestamp: `2026-08-27T20:31:10-06:00`

source_commit: `864fe64d5d1d1a620037adce8409b578919431e0`

source_tree: `16636d9cb747e28a6877a43298efa248e825ffb5`

installed_cache_family: `professional-growth-coach-local/professional-growth-coach`

installed_cache_version: `0.2.0+codex.20260827203110`

installed_enabled: `true`

source_file_count: `172`

installed_file_count: `172`

normalized_source_cache_sha256: `bbd58f7b19210d82e1d89fb9bd0ae2ae2780d11fbe4f328ab2d20b6b85fc782b`

normalized_digest_method: `sha256(sorted relative path + NUL + file bytes; excludes __pycache__)`

normalized_excludes: `__pycache__`

active_config: `canonical_and_public_enabled`
release_smoke_plugin: `professional-growth-coach@professional-growth-coach-local`

source_cache_equivalence: `diff_qr_silent`

installed_renderer_smokes: `6/6 triage validator/renderer fixtures`

installed_reading_path_smoke: `5/5 localized fragment links; aria-current fallback; nearest-target IntersectionObserver enhancement; tablet sticky-rail offset; print/mobile offsets`

installed_dossier_v2_smoke: `4/4 EN/ES validator and renderer`

installed_market_next_research_smoke: `2/2 EN/ES unavailable-market cards expose bounded scope, sample, sources, date, and read-only boundary`

installed_dossier_validator_argument_privacy_smoke: `2/2 dossier validators return fixed opaque errors for unknown arguments`

installed_linkedin_validator_argument_privacy_smoke: `1/1 LinkedIn report validator returns a fixed opaque error for unknown arguments`

installed_market_cli_argument_privacy_smoke: `5/5 market validators and builder return fixed opaque errors for unknown arguments`

installed_market_research_smoke: `2/2 complete/limited validator`

installed_market_learning_smoke: `2/2 complete/limited builder and validator`
installed_learning_decision_aggregation_smoke: `1/1 professional-gap apply_with_boundary/pause options require review_learning_options at the aggregate coach decision`
installed_provider_freshness_smoke: `3/3 paid-learning decisions keep the inclusive 90-day boundary, demote 91-day active sources to consider with a refresh gate, and reject tampered recommended decisions`

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

installed_diagnostic_control_redaction_smoke: `3/3 zero-width, bidi, and newline field names stay opaque`

installed_dossier_unicode_control_smoke: `6/6 v1/v2 dossier prose controls are rejected without echoing`

installed_recruiter_gate_date_binding_smoke: `1/1 outer gate dates must match nested shortlist snapshots`

installed_recruiter_decision_row_binding_smoke: `7/7 copied and derived row fields remain bound to the shortlist and decision`

installed_market_print_matrix_smoke: `1/1 multi-vacancy matrix stacks labelled rows for paper readability`

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
installed_shortlist_sensitive_material_smoke: `1/1 installed shortlist rejects phone-like strings, credential markers, and generic local paths in bounded text`

installed_decision_gate_smoke: `3/3 installed EN/ES decision-gate builder, validator, and renderer; counts/snapshot reconcile, screen context remains manual-only, and HTML omits target/fact identifiers`

installed_screen_intake_smoke: `3/3 installed EN/ES target-specific intake builder, validator, and renderer; advance-only manual handoff, snapshot/locale binding, private IDs hidden, and 0600 output`
installed_screen_intake_dark_contrast_smoke: `1/1 dark-mode screen-blue token uses the accessible contrast value and stays synchronized with the Superdesign theme dump`

installed_screen_debrief_intake_smoke: `4/4 installed artifact-free EN/ES attended-screen bridge; screen_requested and interview_requested receipts carry forward, target binding is enforced, structured coverage is the only next input, malformed recovery stays bounded`

installed_debrief_locale_binding_smoke: `3/3 installed valid ES, mixed-locale recovery, interview_requested carry-forward`

installed_debrief_lineage_smoke: `4/4 installed valid binding, interview carry-forward, target mismatch, legacy recovery`
installed_debrief_sensitive_material_smoke: `1/1 installed screen debrief rejects generic local paths and credential markers before persistence`
installed_reading_path_tablet_smoke: `1/1 installed dossier reading path switches to a two-column tablet layout through 900px and one column at 640px`

installed_recruiter_rail_breakpoint_smoke: `5/5 installed recruiter rails expose three-column intermediate desktop and two-column print layouts with localized label wrapping`

installed_next_stage_schema_typed_closure_smoke: `2/2 installed next-stage schema rejects object-shaped network_goal and coverage note values while accepting the canonical handoff`

installed_duplicate_employer_source_url_smoke: `1/1 installed market validator rejects duplicate normalized employer official_source_url values without echoing the URL`

installed_screen_debrief_smoke: `4/4 installed EN/ES builder, validator, and renderer; target-fact ownership, requested-screen receipt, future-date, explicit-checkpoint, and 0600 boundaries remain fail-closed`

installed_feedback_sensitive_continuity_rail_smoke: `6/6 ES/EN feedback labels render one deterministic three-step rail with closed pending/blocked state copy`

installed_next_stage_review_smoke: `5/5 installed EN/ES-compatible next-stage review build, validator, and renderer; forward stage transitions, current-to-target copy, blocked guidance, private redaction, and manual-only boundary`

installed_screen_context_safety_smoke: `1/1 installed builder and validator reject contact-shaped text, URI schemes, domains, and relative or absolute paths consistently`

installed_stage_transition_smoke: `2/2 installed technical-screen to hiring-manager handoff and backward-transition rejection with localized current → target copy`

installed_stage_label_localization_smoke: `13/13 installed EN/ES intake and debrief renderers cover all supported stages without visible internal stage/check/state tokens; stop routes remain terminal`

installed_shortlist_route_e2e_smoke: `5/5 installed route runs builder → validator → renderer, returns private HTML without placeholders/IDs/action tokens, and rejects unrelated network or technical-interview phrasing`

installed_shortlist_accessibility_print_smoke: `8/8 installed shortlist renderer checks pass: skip link, focusable landmark, ordered target list, print-safe card/footer continuity, and identifier redaction`

installed_recruiter_review_design_token_smoke: `5/5 recruiter review stylesheets are covered by the installed family allowlist`

installed_recruiter_handoff_render_smoke: `16/16 installed decision-gate, screen-intake, debrief, and next-stage routes return private HTML only for validated artifacts; IDs, placeholders, and internal action tokens stay absent`

installed_recruiter_intake_hardening_smoke: `41/41 installed natural-language triggers, invalid target containers, and artifact-free downstream recovery responses stay bounded and actionable`

installed_recruiter_recovery_smoke: `5/5 installed valid recruiter chain, route-specific ES/EN recovery copy, taxonomy-derived invalid-transition recovery, terminal offer-stage recovery, and malformed-input fail-closed behavior`

installed_recruiter_schema_contract_smoke: `22/22 installed valid recruiter handoff chain accepted; unknown nested snapshot fields and impossible decision/state/forward-transition combinations rejected`

installed_recruiter_continuity_rail_smoke: `5/5 installed recruiter surfaces render the shared ES/EN five-step rail with exactly one aria-current="step", identity-free labels, responsive/print/forced-colors hooks, and no interactive controls`
installed_recruiter_focus_smoke: `5/5 recruiter surfaces expose consistent keyboard focus-visible and forced-colors focus contracts, including the compact readiness grid at 420px`

installed_recruiter_future_gate_smoke: `1/1 installed decision-gate builder rejects future-dated source shortlists before replay validation`

installed_recruiter_receipt_contract_smoke: `7/7 installed recruiter builders, validators, and renderers emit bounded JSON success receipts without paths, identifiers, or free text`

installed_dossier_reduced_motion_smoke: `1/1 installed dossier CSS suppresses card hover transforms under prefers-reduced-motion`

installed_recruiter_validator_date_smoke: `5/5 installed recruiter target/debrief validators reject an evaluation date after today while preserving bounded historical replay`

installed_recruiter_gate_freshness_smoke: `1/1 installed screen-intake bridge downgrades a 91-day-old gate to clarify_first even with structurally valid checks`

installed_shortlist_color_fallback_smoke: `1/1 installed priority card keeps a surface background fallback when color-mix is unsupported`

fresh_agent_smoke: `not_run`

fresh_agent_smoke_scope: `direct installed CLI validation/render smoke only; no new agent session; no external action`

official_release_validator: `passed`

external_action_state: `not_executed`

This record is a deterministic synthetic release attestation. It contains no
real profile mapping, recruiter identity, credential, or external action.
