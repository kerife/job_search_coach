# Layouts

## Architecture

There is no application shell, root layout, router wrapper, navigation component, or shared footer module. Each artifact is an offline, self-contained HTML document: a Python renderer reads one template, injects dynamic HTML and that artifact's CSS, then writes the result locally.

The templates below are the complete layout sources. They are listed here once (and not duplicated in `components.md`).

## ExecutiveCareerDossierDocument

- Source: `plugins/professional-growth-coach/assets/executive-career-dossier-v1.html`
- Renders: document body with renderer-supplied header, main content, and a page-specific inline script.

When dated vacancy evidence is present, the market comparison table remains
semantic and switches to labelled cell stacks at screen widths up to 680px;
the print rendering stays tabular.

```html
<!doctype html>
<html lang="{{LANG}}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="robots" content="noindex,nofollow,noarchive">
  <meta name="referrer" content="no-referrer">
  <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; img-src 'none'; font-src 'none'; connect-src 'none'; media-src 'none'; object-src 'none'; frame-src 'none'; worker-src 'none'; manifest-src 'none'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'">
  <title>{{TITLE}}</title>
  <style>{{INLINE_CSS}}</style>
</head>
<body class="dossier-document">
  {{HEADER}}
  {{MAIN}}
  <script>{{INLINE_SCRIPT}}</script>
</body>
</html>
```

## PrivateRecruiterNextStageReviewDocument

- Source: `plugins/professional-growth-coach/assets/private-recruiter-next-stage-review-v1.html`

```html
<!doctype html>
<html lang="{{LANG}}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; img-src 'none'; font-src 'none'; connect-src 'none'; form-action 'none'; frame-ancestors 'none'">
  <title>{{TITLE}}</title>
  <style>{{INLINE_CSS}}</style>
</head>
<body class="next-stage-document">
  <a class="skip-link" href="#main-content">{{SKIP}}</a>
  <main id="main-content" tabindex="-1" class="next-stage-shell">
    <header class="next-stage-header">
      <p class="next-stage-kicker">{{KICKER}}</p>
      <h1>{{HEADING}}</h1>
      <p class="next-stage-transition"><span>{{CURRENT_STAGE_LABEL}}</span> <strong>{{CURRENT_STAGE}}</strong> <span class="next-stage-arrow" aria-hidden="true">→</span> <span>{{STAGE_LABEL}}</span> <strong>{{STAGE}}</strong></p>
      <p class="next-stage-date"><span>{{DATE_LABEL}}</span> <time datetime="{{DATE}}">{{DATE}}</time></p>
    </header>
    <section class="next-stage-card {{SUMMARY_CLASS}}" aria-labelledby="summary-title">
      <p class="next-stage-state">{{STATE}}</p>
      <h2 id="summary-title">{{NEXT_LABEL}}</h2>
      <p class="next-stage-action">{{ACTION}}</p>
      {{BLOCKED_GUIDANCE}}
    </section>
    <section class="next-stage-card" aria-labelledby="context-title">
      <h2 id="context-title">{{OWNER_LABEL}}</h2>
      <p class="next-stage-owner">{{OWNER}}</p>
    </section>
    <section class="next-stage-card" aria-labelledby="checklist-title">
      <h2 id="checklist-title">{{CHECKLIST_LABEL}}</h2>
      <ol class="next-stage-checklist">{{CHECKLIST}}</ol>
    </section>
    <footer class="next-stage-footer">
      <p>{{BOUNDARY}}</p>
      <p>{{FOOTER}}</p>
    </footer>
  </main>
</body>
</html>
```

## PrivateRecruiterScreenDebriefDocument

- Source: `plugins/professional-growth-coach/assets/private-recruiter-screen-debrief-v1.html`
- Renders: structured post-screen coverage, unknown count, and manual next-stage boundary.

```html
<!doctype html>
<html lang="{{LANG}}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; img-src 'none'; font-src 'none'; connect-src 'none'; form-action 'none'; frame-ancestors 'none'">
  <title>{{TITLE}}</title>
  <style>{{INLINE_CSS}}</style>
</head>
<body class="debrief-document">
  <a class="skip-link" href="#main-content">{{SKIP}}</a>
  <main id="main-content" tabindex="-1" class="debrief-shell">
    <header class="debrief-header">
      <p class="debrief-kicker">{{KICKER}}</p>
      <h1>{{HEADING}}</h1>
      <p class="debrief-date"><span>{{DATE_LABEL}}</span> <time datetime="{{DATE}}">{{DATE}}</time></p>
    </header>
    <section class="debrief-card debrief-summary" aria-labelledby="summary-title">
      <p class="debrief-summary__label">{{DECISION}}</p>
      <h2 id="summary-title">{{NEXT_LABEL}}</h2>
      <p class="debrief-summary__action">{{NEXT_ACTION}}</p>
    </section>
    <section class="debrief-card" aria-labelledby="context-title">
      <h2 id="context-title">{{STAGE_LABEL}}</h2>
      <dl class="debrief-context-grid">
        <div><dt>{{STAGE_LABEL}}</dt><dd>{{STAGE}}</dd></div>
        <div><dt>{{FACTS_LABEL}}</dt><dd>{{FACT_COUNT}}</dd></div>
        <div><dt>{{UNKNOWN_LABEL}}</dt><dd>{{UNKNOWN_COUNT}}</dd></div>
      </dl>
    </section>
    <section class="debrief-card" aria-labelledby="coverage-title">
      <h2 id="coverage-title">{{COVERAGE_LABEL}}</h2>
      <ol class="debrief-coverage-list">{{COVERAGE}}</ol>
      <p class="debrief-counts">{{DISCUSSED_COUNT}} · {{UNCLEAR_COUNT}}</p>
    </section>
    <footer class="debrief-footer">
      <p>{{BOUNDARY}}</p>
      <p>{{FOOTER}}</p>
    </footer>
  </main>
</body>
</html>
```

## RecruiterTargetScreenIntakeDocument

- Source: `plugins/professional-growth-coach/assets/recruiter-target-screen-intake-v1.html`
- Renders: target-specific four-check evidence brief before manual interview preparation.

```html
<!doctype html>
<html lang="{{LANG}}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; img-src 'none'; font-src 'none'; connect-src 'none'; form-action 'none'; frame-ancestors 'none'">
  <title>{{TITLE}}</title>
  <style>{{INLINE_CSS}}</style>
</head>
<body class="screen-intake-document">
  <a class="skip-link" href="#main-content">{{SKIP_LINK}}</a>
  <main id="main-content" tabindex="-1" class="screen-shell">
    <header class="screen-header">
      <p class="screen-kicker">{{KICKER}}</p>
      <h1>{{HEADING}}</h1>
      <p class="screen-date"><span>{{DATE_LABEL}}</span> <time datetime="{{AS_OF_DATE}}">{{AS_OF_DATE}}</time></p>
    </header>
    <section class="screen-card screen-decision" aria-labelledby="decision-title">
      <p class="screen-state">{{STATUS}}</p>
      <h2 id="decision-title">{{NEXT_HEADING}}</h2>
      <p>{{NEXT_COPY}}</p>
    </section>
    <section class="screen-card" aria-labelledby="context-title">
      <h2 id="context-title">{{CONTEXT_LABEL}}</h2>
      <dl class="screen-context-grid">
        <div><dt>{{STAGE_LABEL}}</dt><dd>{{STAGE}}</dd></div>
        <div><dt>{{COMPANY_LABEL}}</dt><dd>{{COMPANY_STATE}}</dd></div>
        <div><dt>{{FACTS_LABEL}}</dt><dd>{{FACT_COUNT}}</dd></div>
      </dl>
      <h3>{{REQUIREMENTS_LABEL}}</h3>
      <ul class="screen-requirements">{{REQUIREMENTS}}</ul>
    </section>
    <section class="screen-card" aria-labelledby="checks-title">
      <h2 id="checks-title">{{CHECKS_LABEL}}</h2>
      <ol class="screen-checks">{{CHECKS}}</ol>
    </section>
    <footer class="screen-footer">
      <p>{{BOUNDARY}}</p>
      <p>{{FOOTER}}</p>
    </footer>
  </main>
</body>
</html>
```

## RecruiterTargetDecisionGateDocument

- Source: `plugins/professional-growth-coach/assets/recruiter-target-decision-gate-v1.html`
- Renders: private decision brief with a dominant next-decision card, reconciled batch counts, manual screen-context boundary, and ordered target decisions.

```html
<!doctype html>
<html lang="{{LANG}}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; img-src 'none'; font-src 'none'; connect-src 'none'; form-action 'none'; frame-ancestors 'none'">
  <title>{{TITLE}}</title>
  <style>{{INLINE_CSS}}</style>
</head>
<body class="decision-gate-document">
  <a class="skip-link" href="#main-content">{{SKIP_LINK}}</a>
  <main id="main-content" tabindex="-1" class="gate-shell">
    <header class="gate-header">
      <p class="gate-kicker">{{KICKER}}</p>
      <h1>{{HEADING}}</h1>
      <p class="gate-date"><span>{{DATE_LABEL}}</span> <time datetime="{{AS_OF_DATE}}">{{AS_OF_DATE}}</time></p>
    </header>
    <section class="gate-card gate-next" aria-labelledby="next-title">
      <p class="gate-state">{{NEXT_STATE}}</p>
      <h2 id="next-title">{{NEXT_ACTION}}</h2>
      <p class="gate-next-copy">{{MISSING}}</p>
    </section>
    <section class="gate-card" aria-labelledby="overview-title">
      <h2 id="overview-title">{{OVERVIEW_LABEL}}</h2>
      <dl class="gate-overview-grid">
        <div><dt>{{TARGET_COUNT_LABEL}}</dt><dd>{{TARGET_COUNT}}</dd></div>
        <div><dt>{{PRIORITY_LABEL}}</dt><dd>{{PRIORITY}}</dd></div>
        <div><dt>{{WHY_LABEL}}</dt><dd>{{WHY}}</dd></div>
      </dl>
      <div class="gate-count-summary" aria-labelledby="counts-title">
        <h3 id="counts-title">{{COUNTS_LABEL}}</h3>
        <ul class="gate-counts">{{COUNTS}}</ul>
      </div>
    </section>
    <section class="gate-card gate-context" aria-labelledby="missing-title">
      <h2 id="missing-title">{{MISSING_LABEL}}</h2>
      <p>{{MISSING}}</p>
    </section>
    <section aria-labelledby="rows-title">
      <h2 id="rows-title" class="gate-section-title">{{ROWS_LABEL}}</h2>
      <ol class="gate-rows">{{ROWS}}</ol>
    </section>
    <footer class="gate-footer">
      <p>{{BOUNDARY}}</p>
      <p>{{FOOTER}}</p>
    </footer>
  </main>
</body>
</html>
```

## RecruiterPracticeSessionDocument

- Source: `plugins/professional-growth-coach/assets/recruiter-practice-session-v1.html`
- Renders: private recruiter practice document with renderer-supplied header and main content.

```html
<!doctype html>
<html lang="{{LANG}}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="robots" content="noindex,nofollow,noarchive">
  <meta name="referrer" content="no-referrer">
  <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; img-src 'none'; font-src 'none'; connect-src 'none'; media-src 'none'; object-src 'none'; frame-src 'none'; worker-src 'none'; manifest-src 'none'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'">
  <title>{{TITLE}}</title>
  <style>{{INLINE_CSS}}</style>
</head>
<body class="recruiter-practice-document">
  {{HEADER}}
  {{MAIN}}
</body>
</html>
```

## PrivateRecruiterReplyTriageDocument

- Source: `plugins/professional-growth-coach/assets/private-recruiter-reply-triage-v1.html`
- Renders: private reply-triage document with renderer-supplied header and main content.

```html
<!doctype html>
<html lang="{{LANG}}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="robots" content="noindex,nofollow,noarchive">
  <meta name="referrer" content="no-referrer">
  <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; img-src 'none'; font-src 'none'; connect-src 'none'; media-src 'none'; object-src 'none'; frame-src 'none'; worker-src 'none'; manifest-src 'none'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'">
  <title>{{TITLE}}</title>
  <style>{{INLINE_CSS}}</style>
</head>
<body class="private-recruiter-triage-document">
  {{HEADER}}
  {{MAIN}}
</body>
</html>
```

## PrivateRecruiterFollowthroughCheckpointDocument

- Source: `plugins/professional-growth-coach/assets/private-recruiter-followthrough-checkpoint-v1.html`
- Renders: compact checkpoint document with a skip link, one facts card, and a footer.

```html
<!doctype html>
<html lang="{{LANG}}">
<head>
  <meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="robots" content="noindex,nofollow,noarchive"><meta name="referrer" content="no-referrer">
  <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; img-src 'none'; font-src 'none'; connect-src 'none'; form-action 'none'; frame-ancestors 'none'">
  <title>{{TITLE}}</title><style>{{INLINE_CSS}}</style>
</head>
<body class="private-recruiter-checkpoint-document">
  <a class="skip-link" href="#main-content">{{SKIP}}</a>
  <main id="main-content" class="checkpoint-shell" tabindex="-1">
    <article class="checkpoint-card" aria-labelledby="checkpoint-heading">
      <p class="checkpoint-kicker">{{KICKER}}</p>
      <h1 id="checkpoint-heading">{{HEADING}}</h1>
      <dl class="checkpoint-facts">
        <div><dt>{{STATE_LABEL}}</dt><dd>{{STATE}}</dd></div>
        <div><dt>{{EVENT_LABEL}}</dt><dd>{{EVENT}}</dd></div>
        <div><dt>{{DATE_LABEL}}</dt><dd><time datetime="{{DATE}}">{{DATE}}</time></dd></div>
        <div><dt>{{ACTION_LABEL}}</dt><dd>{{ACTION}}</dd></div>
      </dl>
      <p class="checkpoint-boundary">{{BOUNDARY}}</p>
      {{MANUAL_NEXT_STEP}}
    </article>
  </main>
  <footer class="checkpoint-footer"><strong>{{SAVE}}</strong>{{EMPLOYMENT_BOUNDARY}}</footer>
</body>
</html>
```

## PrivateRecruiterConversionOutcomeDocument

- Source: `plugins/professional-growth-coach/assets/private-recruiter-conversion-outcome-v1.html`
- Renders: compact conversion receipt with a skip link, one facts card, and a footer.

```html
<!doctype html>
<html lang="{{LANG}}">
<head>
  <meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="robots" content="noindex,nofollow,noarchive"><meta name="referrer" content="no-referrer">
  <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; img-src 'none'; font-src 'none'; connect-src 'none'; form-action 'none'; frame-ancestors 'none'">
  <title>{{TITLE}}</title><style>{{INLINE_CSS}}</style>
</head>
<body class="private-recruiter-outcome-document">
  <a class="skip-link" href="#main-content">{{SKIP}}</a>
  <main id="main-content" class="outcome-shell" tabindex="-1">
    <article class="outcome-card" aria-labelledby="outcome-heading">
      <p class="outcome-kicker">{{KICKER}}</p><h1 id="outcome-heading">{{HEADING}}</h1>
      <dl class="outcome-facts">
        <div><dt>{{EVENT_LABEL}}</dt><dd>{{EVENT}}</dd></div>
        <div><dt>{{DATE_LABEL}}</dt><dd><time datetime="{{DATE}}">{{DATE}}</time></dd></div>
        <div><dt>{{ACTION_LABEL}}</dt><dd>{{ACTION}}</dd></div>
        <div><dt>{{EVIDENCE_LABEL}}</dt><dd>{{EVIDENCE}}</dd></div>
      </dl>
      <p class="outcome-boundary">{{BOUNDARY}}</p>
      {{MANUAL_NEXT_STEP}}
    </article>
  </main>
  <footer class="outcome-footer"><strong>{{SAVE}}</strong>{{EMPLOYMENT_BOUNDARY}}</footer>
</body>
</html>
```


## RecruiterTargetShortlistDocument

- Source: `plugins/professional-growth-coach/assets/recruiter-target-shortlist-v1.html`
- Renders: compact bilingual private target-review artifact with a deterministic batch gate and explicit no-contact boundary.
- Accessibility: keyboard skip link, focusable main landmark, named ordered target list, and print-safe privacy boundary.

```html
<!doctype html>
<html lang="{{LANG}}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; img-src 'none'; font-src 'none'; connect-src 'none'; form-action 'none'; frame-ancestors 'none'">
  <title>{{TITLE}}</title>
  <style>{{INLINE_CSS}}</style>
</head>
<body class="target-shortlist-document">
  <a class="skip-link" href="#main-content">{{SKIP}}</a>
  <main id="main-content" tabindex="-1" class="shortlist-shell">
    <header class="shortlist-header">
      <p class="shortlist-kicker">{{KICKER}}</p>
      <h1>{{HEADING}}</h1>
      <p class="shortlist-date">{{AS_OF_DATE}}</p>
    </header>
    <section class="shortlist-card shortlist-overview" aria-labelledby="overview-title">
      <h2 id="overview-title">{{GOAL_LABEL}}</h2>
      <p class="shortlist-goal">{{GOAL}}</p>
      <dl class="shortlist-facts">
        <div><dt>{{SEGMENTS_LABEL}}</dt><dd>{{SEGMENTS}}</dd></div>
        <div><dt>{{QUERIES_LABEL}}</dt><dd><ul>{{QUERIES}}</ul></dd></div>
        <div><dt>{{BATCH_LABEL}}</dt><dd>{{BATCH}}</dd></div>
      </dl>
      <div class="shortlist-priority-card">{{PRIORITY}}</div>
      <div class="shortlist-decision-summary">
        <h3>{{COUNT_LABEL}}</h3>
        <ul class="shortlist-decision-counts">{{DECISION_COUNTS}}</ul>
      </div>
    </section>
    <section aria-labelledby="targets-title">
      <h2 id="targets-title">{{TARGETS_LABEL}}</h2>
      <ol class="target-shortlist-list">{{TARGETS}}</ol>
    </section>
    <footer class="shortlist-footer">
      <p class="shortlist-boundary">{{BOUNDARY}}</p>
      <p class="shortlist-no-save">{{NO_SAVE}}</p>
    </footer>
  </main>
</body>
</html>
```
