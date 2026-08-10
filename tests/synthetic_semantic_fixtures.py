"""Independently fabricated fixtures for legacy semantic validator tests."""

from __future__ import annotations


def profile_scorecard_trigger(*rows: str) -> str:
    """Return the smallest synthetic profile audit that activates the validator."""

    scorecard = (
        "- inferred: candidate_id=JSC-CASE-SEMANTIC; "
        "linkedin_profile_diagnostic_scorecard=professional_section_by_section_linkedin_page_audit; "
        "overall_profile_score=61; score_scale=0_to_100; "
        "scoring_model=synthetic_semantic_model; best_practice_source_ids=JSC_SOURCE_ALPHA; "
        "scored_evidence_coverage=1_of_1_dimensions_scored; score_confidence=medium_low; "
        "unavailable_score_policy=excluded_not_zero; primary_diagnosis=unknown; "
        "highest_leverage_fix=unknown; evidence_boundary=independently_fabricated; draft_only=true."
    )
    source_index = (
        "- inferred: candidate_id=JSC-CASE-SEMANTIC; "
        "linkedin_best_practice_source_index=dated_guidance_catalog; "
        "source_id=JSC_SOURCE_ALPHA; source_name=synthetic_source; "
        "source_type=official_platform_guidance; source_url=https://example.test/synthetic-source; "
        "access_date=2026-08-07; supports_profile_criteria=synthetic_profile_criteria; "
        "source_boundary=recommendation_support_not_outcome_or_algorithm_proof; "
        "use_in_scorecard=true; draft_only=true."
    )
    return "\n".join((scorecard, source_index, *rows))


def coach_smoke(*coach_rows: str) -> str:
    """Return a synthetic legacy smoke envelope with an isolated coach section."""

    return "\n".join(
        (
            "## Professional Jenkins profile coaching smoke",
            "coach_brief:",
            *coach_rows,
            "executive_diagnosis:",
            "- unknown: candidate_id=JSC-CASE-SEMANTIC; state=unknown.",
        )
    )


def authorized_visual_smoke(
    *,
    photo_score: int = 70,
    banner_score: int = 40,
    first_impression_score: int = 58,
    verdict_candidate_id: str = "JSC-CASE-VISUAL",
    pillar_photo_verdict: str = "photo_clear",
    include_verdict: bool = True,
    include_subscores: bool = True,
) -> str:
    """Return a small authorized-visual fixture with hand-checkable arithmetic."""

    candidate_id = "JSC-CASE-VISUAL"
    capture_id = "cap-synthetic-visual-001"
    sources = (
        "LINKEDIN_HELP_PHOTO_GUIDELINES,LINKEDIN_BUSINESS_PHOTO,LINKEDIN_HELP_COVER"
    )
    rows = [
        "## Authorized visual evidence smoke",
        (
            f"- verified: candidate_id={candidate_id}; capture_source_snapshot={capture_id}; "
            "linkedin_visual_identity_review=photo_and_banner_coach_diagnostic; "
            "photo_review_status=visible_reviewed; banner_review_status=visible_reviewed."
        ),
        (
            f"- verified: candidate_id={candidate_id}; capture_source_snapshot={capture_id}; "
            "linkedin_visual_evidence_scorecard=authorized_photo_banner_scorecard; "
            f"visual_evidence_source=authorized_screenshot; photo_score={photo_score}; "
            f"banner_score={banner_score}; first_impression_score={first_impression_score}; "
            "aggregation_model=photo_60_banner_40; aggregation_rounding=nearest_integer; "
            "score_scale=0_to_100; confidence=medium; "
            "scoring_boundary=professional_profile_usefulness_not_identity_or_attractiveness; "
            f"best_practice_source_ids={sources}; draft_only=true."
        ),
    ]
    if include_subscores:
        for dimension in (
            "face_visibility",
            "crop",
            "lighting",
            "background",
            "image_quality",
            "recency_recognizability",
            "attire_context",
            "banner_story_alignment",
        ):
            score = 40 if dimension == "banner_story_alignment" else 70
            rows.append(
                f"- verified: candidate_id={candidate_id}; capture_source_snapshot={capture_id}; "
                "linkedin_visual_subscore_matrix=authorized_photo_banner_dimension_review; "
                f"dimension={dimension}; score={score}; score_treatment=scored_directional_estimate; "
                "evidence_observed=synthetic_visual_signal; coach_read=synthetic_coach_read; "
                "improvement_action=review_synthetic_signal; acceptance_test=synthetic_signal_reviewed; "
                "source_ids=LINKEDIN_HELP_PHOTO_GUIDELINES; "
                "protected_or_privacy_boundary=professional_usefulness_no_protected_traits_no_private_or_confidential_assets; "
                "no_external_action=true; draft_only=true."
            )
    if include_verdict:
        rows.append(
            f"- inferred: candidate_id={verdict_candidate_id}; capture_source_snapshot={capture_id}; "
            "visual_first_impression_verdict=photo_banner_recruiter_scan; "
            "visual_evidence_source=authorized_screenshot; photo_verdict=photo_clear; "
            "banner_verdict=banner_needs_review; top_card_alignment=visual_top_card_alignment; "
            "first_impression_risk=visual_signal_gap; recommended_visual_story=synthetic_visual_story; "
            "photo_next_action=review_photo_crop; banner_next_action=review_banner_story; "
            "headline_visibility_note=review_top_card_alignment; "
            "acceptance_test=visual_signals_reviewed; "
            f"source_ids={sources}; "
            "protected_traits_boundary=no_attractiveness_age_race_ethnicity_gender_disability_health_personality_or_trustworthiness_judgment; "
            "privacy_boundary=no_raw_images_no_private_identifiers_no_confidential_assets; "
            "no_external_action=true; draft_only=true."
        )
        rows.append(
            f"- inferred: candidate_id={candidate_id}; capture_source_snapshot={capture_id}; "
            "linkedin_profile_pillar_score=recruiter_scan_pillar; pillar=first_impression; "
            f"score={first_impression_score}; grade=directional; "
            "sections_used=photo,banner,headline,top_card; what_recruiter_sees=visual_signal; "
            "why_it_matters=first_screen_clarity; visual_verdict_ref=photo_banner_recruiter_scan; "
            f"photo_verdict={pillar_photo_verdict}; banner_verdict=banner_needs_review; "
            "top_card_alignment=visual_top_card_alignment; recommended_visual_story=synthetic_visual_story; "
            "specific_gap=visual_signal_gap; best_fix=review_visual_story; "
            "acceptance_test=visual_signals_reviewed; evidence_label=verified_visible; "
            "score_treatment=scored_directional_estimate; draft_only=true."
        )
    return "\n".join(rows)


def recruiter_outreach_fixture(*, stale_context: bool = False) -> str:
    """Return a two-target outreach lab with deterministic synthetic context."""

    rows = [
        "- inferred: candidate_id=JSC-CASE-OUTREACH; recruiter_outreach_lab=manual_draft_comparison; "
        "source_shortlist_id=RTS-SYNTHETIC; variant_count=2; target_scope=two_synthetic_targets; "
        "lab_goal=choose_the_lowest_risk_draft_for_manual_candidate_review; "
        "selection_rule=lowest_risk_supported_context; approval_state=not_approved; "
        "next_safe_action=draft_only_review_then_exact_authorization; draft_only=true; "
        "consent=not_granted; authorization_gate=exact_action_and_target_immediately_before_execution; "
        "no_message_action=true; causality_boundary=descriptive_only_no_guaranteed_outcome."
    ]
    observed_date = "unknown" if stale_context else "2026-08-07"
    window = "365" if stale_context else "30"
    for suffix in ("ALPHA", "BETA"):
        rows.append(
            "- inferred: candidate_id=JSC-CASE-OUTREACH; "
            "recruiter_target_context_packet=manual_target_context_before_outreach_draft; "
            f"target_id=JSC-TARGET-{suffix}; source_shortlist_id=RTS-SYNTHETIC; "
            "contact_category=recruiter; named_target_status=named; "
            "context_source=candidate_provided_role_summary; target_relevance=role_scope_summary; "
            "relationship_or_visible_signal=visible_role_signal; candidate_proof_fit=CI_CD_AUTOMATION_REPORTED; "
            "missing_context=unknown; low_friction_reason_to_reply=useful_process_summary; "
            f"context_observed_date={observed_date}; freshness_window_days={window}; "
            "context_freshness_decision=fresh_for_draft; draft_readiness=draft_ready; "
            "draft_or_block_decision=draft_variant_allowed; required_candidate_review=true; "
            f"measurement_event=LI-CONTEXT-{suffix}; privacy_boundary=no_contact_details_no_raw_profile_text; "
            "no_message_action=true; draft_only=true; consent=not_granted; "
            "authorization_gate=exact_action_and_target_immediately_before_execution; "
            "causality_boundary=descriptive_only_no_guaranteed_outcome."
        )
    for index, suffix in enumerate(("ALPHA", "BETA"), start=1):
        recommendation = "use_first" if index == 1 else "use_second"
        rows.append(
            "- inferred: candidate_id=JSC-CASE-OUTREACH; outreach_variant=manual_context_draft; "
            f"variant_id=JSC-VARIANT-{suffix}; target_id=JSC-TARGET-{suffix}; "
            "variant_type=recruiter_conversation_bridge; draft_text=synthetic_copy_placeholder_alpha; "
            "personalization_reason=visible_role_signal; low_friction_question=useful_process_question; "
            "risk_review=no_vacancy_claim; expected_signal=reply_quality; reply_likelihood_score=low; "
            "reply_likelihood_reason=limited_synthetic_context; friction_level=low; "
            f"personalization_strength=moderate; coach_recommendation={recommendation}; "
            f"measurement_event=LI-VARIANT-{suffix}; send_status=draft_only; draft_only=true; "
            "consent=not_granted; authorization_gate=exact_action_and_target_immediately_before_execution; "
            "no_message_action=true; causality_boundary=descriptive_only_no_guaranteed_outcome."
        )
    return "\n".join(rows)


def calibrated_section_rows() -> str:
    """Return one complete synthetic row for each profile-diagnosis section."""

    rows = []
    for rank, section in enumerate(
        (
            "photo_banner",
            "headline",
            "about",
            "experience",
            "skills",
            "proof_assets",
            "recommendations_activity",
            "completeness_visibility",
        ),
        start=1,
    ):
        privacy_boundary = (
            "professional_usefulness_no_protected_traits"
            if section == "photo_banner"
            else "truthful_supported_claims_only"
        )
        rows.append(
            "- inferred: candidate_id=JSC-CASE-SEMANTIC; "
            "linkedin_profile_section_diagnosis=client_ready_section_review; "
            f"section={section}; score=70; evidence_label=inferred; verdict=synthetic_verdict; "
            "what_recruiter_notices=synthetic_signal; what_good_looks_like=supported_signal; "
            "gap=synthetic_gap; fix=review_supported_signal; acceptance_test=signal_reviewed; "
            f"source_ids=JSC_SOURCE_ALPHA; privacy_or_truth_boundary={privacy_boundary}; "
            f"severity=medium; priority_rank={rank}; timebox=30_minutes; "
            "evidence_needed=JSC-EVIDENCE-ALPHA; do_not_do=do_not_publish; "
            "coach_reasoning=recruiter_scan_evidence_gap; measurement_signal=section_review; "
            "draft_only=true."
        )
    return "\n".join(rows)
