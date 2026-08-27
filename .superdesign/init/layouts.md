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
  <main class="shortlist-shell">
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
    <section aria-label="{{HEADING}}">
      <div class="target-shortlist-list">{{TARGETS}}</div>
    </section>
    <footer class="shortlist-footer">
      <p class="shortlist-boundary">{{BOUNDARY}}</p>
      <p class="shortlist-no-save">{{NO_SAVE}}</p>
    </footer>
  </main>
</body>
</html>
```
