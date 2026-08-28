# Theme

## Compact token summary

Receipt surfaces are intentionally path-minimal: successful CLI output carries only opaque artifact metadata unless the trusted caller explicitly opts into `--include-artifact-path`. This is a delivery/privacy contract, not a visual control; offline HTML layout and the in-process rich receipt remain unchanged.

The career-market matrix stacks rows on narrow and print surfaces; its generated
`td::before` labels use `CanvasText` in forced-colors mode so the only visible
column context remains explicit and readable.

Triage-to-practice wrappers carry a deterministic projection snapshot over the
unanswered session; it is a structural integrity signal, not visible candidate
content. Compact outcome/checkpoint rails use 2px rail, step, and marker borders
under `prefers-contrast: more`, keeping their recorded/pending/blocked states
readable in the same visual language as the five recruiter review rails.

The v2 `reading-path` uses the existing forest, line, surface, and focus tokens;
it stays editorial rather than floating, is sticky only on screen, and marks
the visible destination with `aria-current="location"`. It keeps a static
no-script/print fallback and stacks as full-width 44px links at 640px and
below. The fourth destination, first-conversation preparation, closes the
dossier-to-coaching handoff without adding an action control.

This plugin has **no shared Tailwind config, CSS module system, theme provider, or global stylesheet**. Each rendered offline artifact inlines its co-located CSS; the v2 dossier composes the base dossier stylesheet with its v2 and optional market extensions. There is no `.dark` selector; every surface now declares a screen-scoped `prefers-color-scheme: dark` contract while print remains light.

### Palette

| Family | Tokens / values |
| --- | --- |
| Dossier | light `--paper #f6f4ee`, `--forest #173e30`, `--ink #1a1a1a`, `--muted #e2ddd6`, `--muted-text #5d5a55`, `--line #c8c0b5`, `--coral #d96c52`, `--gold #be9338`, `--surface #ffffff`; dark `--paper #101521`, `--surface #182235`, `--ink #f3f6ff`, `--muted #b8c4d8`, `--muted-text #b8c4d8`, `--forest #8fc9b0`, `--coral #ff9f8d`, `--gold #f2c970`, `--line #5f718e` |
| Practice / triage | light `--paper #f6f4ee`, `--surface #ffffff`, `--ink #1b1c1a`, `--forest #173e30`, `--forest-soft #dce5e0`, `--coral #b9513a`, `--line #b8c7c0`, `--decision-term #dfbf70`; dark `--paper #101521`, `--surface #182235`, `--ink #f3f6ff`, `--forest #8fc9b0`, `--coral #ff9f8d`, `--line #5f718e`, `--decision-term #f5d68a` |
| Checkpoint / outcome | `--ink #172033`, `--muted #536174`, `--surface #fff`, `--accent #315bd6`, `--line #d9dfeb`; document background `#f4f6fa` |
| Recruiter review | Five registered surfaces: shortlist, decision gate, screen intake, screen debrief, and next-stage review. Their shared identity-free continuity rail uses each surface's existing text, muted, border, and accent tokens; shortlist and decision-gate dark markers use `--continuity-marker-ink` for WCAG-safe text on bright accents. It is checked as one family by `validate_design_tokens.py`, and no new color is valid without an allowlist update and parity review. |

### Typography and dimensions

- **Serif display:** `Georgia, "Times New Roman", Times, serif`.
- **Sans body:** `-apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif`; compact receipts use `system-ui, sans-serif`.
- **Base:** 16px / 1.55 on dossier, practice, and triage; compact receipts use 100% / 1.5.
- **Display scale:** dossier title `clamp(2rem, 5vw, 3.45rem)`; practice/triage H1 `clamp(2rem, 6vw, 3.25rem)`; compact H1 `clamp(1.6rem, 4vw, 2.35rem)`; H2 usually `clamp(1.35rem, 3vw, 2rem/1.85rem)`.
- **Content measure:** `--measure: 72ch`; main document widths: 1160px dossier, 920px practice/triage, 48rem compact receipts.
- **Spacing:** no named scale; repeated steps range from `.25rem` to `3rem`, with `.5rem`, `.75rem`, `1rem`, `1.5rem`, and `2rem` most common.
- **Radius:** dossier/practice/triage remain square; compact receipt cards use `1rem`.
- **Shadows:** dossier none; practice/triage `0 1px 0 rgb(23 62 48 / 10%)`; compact cards `0 .5rem 2rem rgb(23 32 51 / .08)`.
- Learning cards lead with readable decision and option-type labels; decision basis and opportunity cost remain visible without new shadows or decorative effects.
- Learning decision cards are independently named regions: each `<article>` uses `aria-labelledby` to reference its unique `<h4>` decision heading, preserving the editorial hierarchy for screen readers without changing the visual treatment.
- Private recruiter receipts and practice sessions use static continuity rails with textual states; compact outcome/checkpoint rails select closed copy from `next_safe_action`, use the semantic sequence Recorded/Registrado -> Pending/Pendiente -> Blocked/Bloqueada, and mark the pending safe step with `aria-current="step"`; terminal Recorded/Registrado rails mark their recorded step current as well. The five recruiter target artifacts additionally share a localized five-surface orientation rail rendered by `recruiter_continuity_rail.py`; it is a static `section` rather than a navigation landmark, labels the current item as the current review surface (not a completed milestone), marks only that surface with `aria-current="step"`, collapses to one column below 420px, never infers completed stages, and remains non-interactive, identity-free, responsive, print-safe, forced-colors-safe, and offline. `record_stop_decision` renders a terminal Recorded/Registrado state with no continuation language. Rails reuse each family’s accent tokens, use surface tokens in dark mode, and preserve higher-contrast readability.
- Practice and triage handoff sequences reuse the same visual state language: recorded evidence/focus, one pending or blocked private next step, and a single `aria-current="step"` marker. State remains textual and non-interactive so color is never the only signal.
- Practice sessions also use a four-cell first-conversation readiness card with textual current/pending states; it is derived from validated state, remains private, and never becomes an action control.
- **Breakpoints:** dossier: 900px, 680px, 480px; practice/triage: 640px; compact receipts: `min-width: 641px` (one column through 640px). All families include print, reduced-motion, forced-color, and high-contrast handling.
- Compact receipt skip links expose an explicit 3px `--accent` focus ring in normal mode and a 2px `Highlight` ring in forced-colors mode, so keyboard users can locate the jump target before entering the card.

## Raw source dumps

### `plugins/professional-growth-coach/assets/executive-career-dossier-v1.css`

```css
:root {
  --paper: #f6f4ee;
  --forest: #173e30;
  --ink: #1a1a1a;
  --muted: #e2ddd6;
  --muted-text: #5d5a55;
  --line: #c8c0b5;
  --coral: #d96c52;
  --gold: #be9338;
  --surface: #ffffff;
  --forest-soft: #dce5e0;
  --coral-soft: #f7e4df;
  --gold-soft: #f5ecd8;
  --measure: 72ch;
  --serif: Georgia, "Times New Roman", Times, serif;
  --sans: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
}

* { box-sizing: border-box; }

html { color-scheme: light; background: var(--paper); }

body {
  margin: 0;
  min-width: 0;
  background: var(--paper);
  color: var(--ink);
  font-family: var(--sans);
  font-size: 16px;
  line-height: 1.55;
  overflow-wrap: anywhere;
}

a { color: var(--forest); text-underline-offset: 0.18em; }

a:focus-visible,
button:focus-visible,
summary:focus-visible {
  outline: 3px solid var(--coral);
  outline-offset: 3px;
}

.skip-link {
  position: fixed;
  z-index: 10;
  top: 0.5rem;
  left: 0.5rem;
  padding: 0.75rem 1rem;
  background: var(--surface);
  border: 1px solid var(--forest);
  transform: translateY(-200%);
}

.skip-link:focus { transform: none; }

main:focus-visible {
  outline: 3px solid var(--coral);
  outline-offset: 4px;
}

.shell {
  width: min(1160px, calc(100% - 2rem));
  margin-inline: auto;
}

.utility-header {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 1.5rem;
  padding-block: 2rem 1rem;
  border-bottom: 1px solid var(--forest);
}

.eyebrow,
.meta,
.status-label,
.section-kicker {
  margin: 0;
  color: var(--forest);
  font-size: 0.8125rem;
  font-weight: 700;
  letter-spacing: 0.11em;
  line-height: 1.5;
  text-transform: uppercase;
}

.report-title,
h2,
h3,
.score-value,
.priority-rank {
  font-family: var(--serif);
}

.report-title {
  margin: 0.15rem 0 0;
  font-size: clamp(2rem, 5vw, 3.45rem);
  font-style: italic;
  font-weight: 600;
  letter-spacing: -0.035em;
  line-height: 1;
}

.utility-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  flex-wrap: wrap;
  gap: 0.65rem;
}

.privacy-chip,
.state-chip,
.confidence-chip {
  display: inline-flex;
  align-items: center;
  min-height: 2.25rem;
  padding: 0.4rem 0.75rem;
  border: 1px solid currentColor;
  color: var(--forest);
  font-size: 0.8125rem;
  font-weight: 700;
  line-height: 1.2;
}

button {
  min-width: 44px;
  min-height: 44px;
  padding: 0.6rem 0.9rem;
  border: 1px solid var(--forest);
  border-radius: 0;
  background: var(--forest);
  color: var(--surface);
  font: inherit;
  font-weight: 700;
  cursor: pointer;
}

button:hover { background: var(--ink); }

main { padding-block: 1.25rem 3rem; }

.dossier-grid {
  display: grid;
  grid-template-columns: repeat(12, minmax(0, 1fr));
  gap: 1rem;
}

.section-block {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px dotted var(--muted);
}
.span-12 { grid-column: span 12; }
.span-8 { grid-column: span 8; }
.span-7 { grid-column: span 7; }
.span-6 { grid-column: span 6; }
.span-5 { grid-column: span 5; }
.span-4 { grid-column: span 4; }

.card {
  min-width: 0;
  background: var(--surface);
  border: 1px solid var(--forest-soft);
  box-shadow: none;
  padding: clamp(1.15rem, 2.5vw, 1.75rem);
  animation: dossier-enter 0.6s ease both;
  transition: transform 0.2s ease;
}

.card:hover { transform: translateY(-2px); }
.card:nth-child(2n) { animation-delay: 0.08s; }
.card:nth-child(3n) { animation-delay: 0.16s; }

.card h2,
.card h3 { margin-top: 0; }

h2 {
  margin-bottom: 1rem;
  color: var(--forest);
  font-size: clamp(1.35rem, 3vw, 2rem);
  line-height: 1.15;
}

h3 {
  margin-bottom: 0.75rem;
  font-size: 1.25rem;
  line-height: 1.2;
}

p { max-width: var(--measure); }

.verdict-card {
  display: flex;
  min-height: 19rem;
  flex-direction: column;
  justify-content: space-between;
  border-top: 4px solid var(--forest);
}

.verdict-statement {
  margin: 0.3rem 0 0.85rem;
  max-width: 48ch;
  font-family: var(--serif);
  font-size: clamp(1.45rem, 3vw, 2.35rem);
  line-height: 1.16;
}

.start-here {
  margin-top: 1rem;
  padding: 1rem;
  background: var(--forest-soft);
  border-left: 4px solid var(--forest);
}

.start-here strong { display: block; color: var(--forest); }

.coverage-row,
.score-line,
.priority-header,
.copy-heading,
.metric-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
}

.coverage-row { flex-wrap: wrap; margin-top: 1rem; }
.score-value { color: var(--forest); font-size: 2.5rem; font-weight: 600; line-height: 1; }
.score-note { color: #4f5955; font-size: 0.875rem; }

.scan-list,
.clean-list,
.priority-list,
.plan-list,
.question-list {
  margin: 0;
  padding: 0;
  list-style: none;
}

.scan-list li,
.clean-list li {
  padding: 0.8rem 0 0.8rem 1rem;
  border-left: 2px solid var(--muted);
}

.scan-list li + li,
.clean-list li + li { margin-top: 0.5rem; }

.label {
  display: block;
  margin-bottom: 0.15rem;
  color: #53605a;
  font-size: 0.8125rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  line-height: 1.5;
  text-transform: uppercase;
}

.priorities-grid .card { border-top: 4px solid var(--coral); }
.priority-rank { color: var(--coral); font-size: 2.25rem; line-height: 1; }
.priority-body dt { margin-top: 0.75rem; color: #53605a; font-size: 0.8125rem; font-weight: 700; text-transform: uppercase; }
.priority-body dd { margin: 0.15rem 0 0; }

.timebox {
  display: inline-block;
  margin-top: 1rem;
  padding: 0.25rem 0.55rem;
  background: var(--gold-soft);
  border: 1px solid var(--gold);
  font-weight: 700;
}

.analytics-card { border-top: 4px solid var(--gold); }
.metric-value { color: var(--forest); font-family: var(--serif); font-size: 2rem; font-weight: 600; }
.metric-row + .metric-row { margin-top: 0.75rem; padding-top: 0.75rem; border-top: 1px solid var(--muted); }

.dimension-grid { align-items: stretch; }
.dimension-card { grid-column: span 4; }
.dimension-card:last-child { grid-column: span 12; }
.not-evaluated { border-style: dashed; }

progress {
  display: block;
  width: 100%;
  height: 0.65rem;
  margin-top: 0.75rem;
  border: 0;
  border-radius: 0;
  background: var(--muted);
  color: var(--forest);
}

progress::-webkit-progress-bar { background: var(--muted); }
progress::-webkit-progress-value { background: var(--forest); }
progress::-moz-progress-bar { background: var(--forest); }

.visual-card { border-top: 4px solid var(--forest); }
.market-card { border-top: 4px solid var(--gold); }

.comparison-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 1rem;
  table-layout: fixed;
}

.comparison-table caption {
  padding-bottom: 0.75rem;
  text-align: left;
  font-weight: 700;
}

.comparison-table th,
.comparison-table td {
  padding: 0.8rem;
  border-bottom: 1px solid var(--muted);
  hyphens: auto;
  overflow-wrap: anywhere;
  text-align: left;
  vertical-align: top;
}

.comparison-table th { color: var(--forest); }

.copy-card { position: relative; }
.copy-text { margin: 1rem 0; padding: 1rem; background: var(--paper); border-left: 4px solid var(--forest); font-family: var(--serif); font-size: 1.15rem; }
.copy-status { display: block; min-height: 1.4em; margin-top: .5rem; color: #4f5955; font-size: .875rem; }
.boundary { color: #4f5955; font-size: 0.875rem; }
.screen-preparation-card {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 1rem;
  border-top: 4px solid var(--gold);
  font-size: 1rem;
}
.screen-preparation-card > h2 { grid-column: 1; grid-row: 1; margin-bottom: 0; }
.screen-preparation-card > .label,
.screen-preparation-card > .copy-text,
.screen-preparation-evidence,
.screen-preparation-boundary,
.screen-preparation-rehearsal { grid-column: 1 / -1; }
.readiness-chip {
  grid-column: 2;
  grid-row: 1;
  align-self: start;
  min-height: 44px;
  padding: 0.45rem 0.75rem;
  border: 1px solid currentColor;
  font-size: 0.875rem;
  font-weight: 700;
  line-height: 1.2;
}
.screen-preparation-state--ready { background: var(--forest-soft); color: var(--forest); }
.screen-preparation-state--requires-confirmation { background: var(--gold-soft); color: #654c10; }
.screen-preparation-state--omit { background: var(--coral-soft); color: #7c2f1e; }
.screen-preparation-state--paused { background: var(--muted); color: #39443f; }
.screen-preparation-evidence { padding: 1rem; background: var(--paper); }
.screen-preparation-question {
  grid-column: 1 / -1;
  padding: 1rem;
  border: 1px solid var(--forest);
  border-left: 4px solid var(--forest);
  background: var(--forest-soft);
}
.screen-preparation-question h3 { margin: 0; color: var(--forest); font-size: 1.2rem; }
.screen-preparation-question p { max-width: var(--measure); margin: 0.45rem 0 0; }
.screen-preparation-handoff {
  grid-column: 1 / -1;
  padding: 1rem;
  border: 1px dashed var(--forest);
  background: var(--paper);
}
.screen-preparation-handoff h3 { margin: 0; color: var(--forest); font-size: 1.1rem; }
.screen-preparation-handoff p { max-width: var(--measure); margin: 0.4rem 0 0; }
.screen-preparation-manual-note {
  grid-column: 1 / -1;
  margin: 0;
  padding: 0.75rem 1rem;
  border: 1px solid var(--gold);
  border-left: 4px solid var(--gold);
  background: var(--gold-soft);
}
.screen-preparation-manual-note h3 { margin: 0; color: #654c10; font-size: 1.1rem; }
.screen-preparation-manual-note p { max-width: var(--measure); margin: 0.4rem 0 0; }
.screen-preparation-boundary,
.screen-preparation-rehearsal { margin: 0; font-size: 1rem; }
.hold-card { border-left: 4px solid var(--coral); }
.question-card:first-child { border-top: 4px solid var(--coral); }

.plan-day {
  display: grid;
  grid-template-columns: minmax(3.5rem, auto) 1fr;
  gap: 1rem;
  padding: 1rem 0;
  border-bottom: 1px solid var(--muted);
}

.day-badge { color: var(--forest); font-family: var(--serif); font-size: 1.25rem; font-weight: 700; }

details summary {
  min-height: 44px;
  padding-block: 0.6rem;
  color: var(--forest);
  font-weight: 700;
  cursor: pointer;
}

.method-list { padding-left: 1.25rem; }
.method-list li + li { margin-top: 0.6rem; }
.method-list a {
  display: inline-flex;
  min-width: 44px;
  min-height: 44px;
  align-items: center;
  word-break: break-word;
}

.footer {
  padding-block: 1.5rem 2.5rem;
  border-top: 1px solid var(--forest);
  color: #39443f;
  font-size: 0.875rem;
}

@media screen and (prefers-color-scheme: dark) {
  :root {
    color-scheme: dark;
    --paper: #101521;
    --surface: #182235;
    --ink: #f3f6ff;
    --muted: #b8c4d8;
    --muted-text: #b8c4d8;
    --line: #5f718e;
    --forest: #8fc9b0;
    --forest-soft: #223b35;
    --coral: #ff9f8d;
    --coral-soft: #3f282d;
    --gold: #f2c970;
    --gold-soft: #3b301f;
  }
  html,
  .dossier-document { background: var(--paper); color: var(--ink); }
  .dossier-document progress { background: var(--forest-soft); }
  .dossier-document progress::-webkit-progress-bar { background: var(--forest-soft); }
  .dossier-document progress::-moz-progress-bar { background: var(--forest); }
  .dossier-document .score-note,
  .dossier-document .label,
  .dossier-document .priority-body dt,
  .dossier-document .copy-status,
  .dossier-document .boundary,
  .dossier-document .footer { color: var(--muted); }
  .dossier-document .section-block,
  .dossier-document .metric-row + .metric-row,
  .dossier-document .comparison-table { border-color: var(--line); }
  .dossier-document .screen-preparation-state--requires-confirmation { color: var(--gold); background: var(--gold-soft); }
  .dossier-document .screen-preparation-state--omit { color: var(--coral); background: var(--coral-soft); }
  .dossier-document .screen-preparation-state--paused { color: var(--ink); background: var(--forest-soft); }
  .dossier-document .screen-preparation-evidence,
  .dossier-document .copy-text { background: var(--paper); }
  .dossier-document .screen-preparation-manual-note { background: var(--gold-soft); }
  .dossier-document .screen-preparation-manual-note h3 { color: var(--gold); }
}

@keyframes dossier-enter {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: none; }
}

@media (max-width: 900px) {
  .span-8,
  .span-7,
  .span-6,
  .span-5,
  .span-4,
  .dimension-card,
  .dimension-card:last-child { grid-column: span 12; }
  .utility-header { align-items: flex-start; flex-direction: column; }
  .utility-actions { justify-content: flex-start; }
  .verdict-card { min-height: auto; }
}

@media (max-width: 680px) {
  .screen-preparation-card { grid-template-columns: 1fr; }
  .screen-preparation-card > h2,
  .readiness-chip { grid-column: 1; grid-row: auto; }
}

@media (max-width: 480px) {
  .shell { width: min(100% - 1rem, 1160px); }
  .card { padding: 1rem; }
  .coverage-row,
  .score-line,
  .priority-header,
  .copy-heading,
  .metric-row { align-items: flex-start; flex-direction: column; }
  .comparison-table th,
  .comparison-table td { padding: 0.5rem 0.25rem; }
  .plan-day { grid-template-columns: 1fr; gap: 0.25rem; }
}

@media screen and (max-width: 680px) {
  .comparison-table,
  .comparison-table tbody,
  .comparison-table tr,
  .comparison-table th,
  .comparison-table td {
    display: block;
    width: 100%;
  }

  .comparison-table thead {
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
    white-space: nowrap;
    border: 0;
  }

  .comparison-table tr {
    padding: 0.75rem 0;
    border-bottom: 1px solid var(--muted);
  }

  .comparison-table tbody th {
    padding: 0 0 0.5rem;
    border-bottom: 0;
  }

  .comparison-table td {
    display: grid;
    grid-template-columns: minmax(8.5rem, 0.38fr) minmax(0, 1fr);
    gap: 0.75rem;
    padding: 0.45rem 0;
    border-bottom: 0;
  }

  .comparison-table td::before {
    content: attr(data-label);
    color: var(--muted);
    font-size: 0.8125rem;
    font-weight: 700;
  }
}

@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation: none !important;
    scroll-behavior: auto !important;
    transition: none !important;
  }

  .card:hover { transform: none !important; }
}

@page { size: auto; margin: 14mm; }

@media print {
  html,
  .dossier-document { background: #ffffff; }
  .dossier-document {
    font-size: 12pt;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }
  .shell { width: 100%; }
  .no-print,
  .skip-link { display: none !important; }
  .card,
  tr,
  .plan-day {
    break-inside: avoid;
    page-break-inside: avoid;
  }
  .screen-preparation-card {
    break-inside: avoid;
    break-after: avoid;
    page-break-inside: avoid;
    page-break-after: avoid;
  }
  .screen-preparation-question { break-inside: avoid; page-break-inside: avoid; }
  .screen-preparation-handoff { break-inside: avoid; page-break-inside: avoid; }
  .screen-preparation-manual-note { break-inside: avoid; page-break-inside: avoid; }
  h1,
  h2,
  h3 {
    break-after: avoid;
    page-break-after: avoid;
  }
  p,
  li { orphans: 3; widows: 3; }
  details { display: block; }
  details > * { display: block !important; }
  .card { animation: none; transition: none; }
  .footer {
    padding-bottom: 0;
    break-inside: avoid;
    page-break-inside: avoid;
  }
}

@media (forced-colors: active) {
  button { background: ButtonFace; color: ButtonText; border-color: ButtonText; }
  button:hover { background: Highlight; color: HighlightText; }
  a:focus-visible,
  button:focus-visible,
  summary:focus-visible,
  main:focus-visible { outline-color: Highlight; }
  .dossier-document progress {
    border: 1px solid CanvasText;
    background: Canvas;
    color: CanvasText;
  }
  .dossier-document progress::-webkit-progress-bar { background: Canvas; }
  .dossier-document progress::-webkit-progress-value { background: Highlight; }
  .dossier-document progress::-moz-progress-bar { background: Highlight; }
  .screen-preparation-question {
    border: 1px solid CanvasText;
    border-left: 4px solid Highlight;
    background: Canvas;
    color: CanvasText;
  }
  .screen-preparation-question h3 { color: CanvasText; }
  .screen-preparation-handoff { border: 1px dashed CanvasText; background: Canvas; color: CanvasText; }
  .screen-preparation-handoff h3 { color: CanvasText; }
  .screen-preparation-manual-note { border: 1px solid CanvasText; border-left: 4px solid Highlight; background: Canvas; color: CanvasText; }
  .screen-preparation-manual-note h3 { color: CanvasText; }
  .comparison-table td::before { color: CanvasText; }
  .footer { color: CanvasText; border-color: CanvasText; }
}

@media (prefers-contrast: more) {
  .screen-preparation-question,
  .screen-preparation-handoff,
  .screen-preparation-manual-note { border-width: 2px; }
  .screen-preparation-question h3,
  .screen-preparation-handoff h3,
  .screen-preparation-manual-note h3 { text-decoration: underline; text-decoration-thickness: 0.12em; }
}
```

### `plugins/professional-growth-coach/assets/private-recruiter-next-stage-review-v1.css`

```css
:root { color-scheme: light dark; --next-bg: #f5f7fa; --next-surface: #fff; --next-text: #16202a; --next-muted: #52606d; --next-accent: #126782; --next-border: #c8d2dc; --next-blocked: #8a4b08; }
* { box-sizing: border-box; }
body { margin: 0; background: var(--next-bg); color: var(--next-text); font: 16px/1.55 system-ui, -apple-system, sans-serif; overflow-wrap: anywhere; }
.skip-link { position: absolute; left: 1rem; top: -4rem; background: var(--next-text); color: var(--next-surface); padding: .5rem .75rem; border-radius: .25rem; }
.skip-link:focus { top: 1rem; }
.skip-link:focus-visible, main:focus-visible { outline: 3px solid var(--next-accent); outline-offset: 3px; }
.next-stage-shell { max-width: 52rem; margin: 0 auto; padding: 2rem 1rem 3rem; }
.next-stage-header { margin-bottom: 1.5rem; }
.next-stage-kicker, .next-stage-state { color: var(--next-accent); font-weight: 700; letter-spacing: .04em; text-transform: uppercase; }
h1, h2 { line-height: 1.2; }
h1 { margin: .35rem 0; font-size: clamp(1.8rem, 5vw, 3rem); }
h2 { margin-top: 0; font-size: 1.2rem; }
.next-stage-date { color: var(--next-muted); }
.next-stage-transition { display: inline-flex; flex-wrap: wrap; gap: .45rem; align-items: baseline; margin: .75rem 0 .25rem; padding: .45rem .65rem; border: 1px solid var(--next-border); border-radius: .4rem; }
.next-stage-transition span { color: var(--next-muted); font-size: .9rem; }
.next-stage-transition strong { color: var(--next-text); }
.next-stage-arrow { color: var(--next-accent) !important; font-size: 1.15rem !important; font-weight: 700; }
.next-stage-card { background: var(--next-surface); border: 1px solid var(--next-border); border-radius: .8rem; padding: 1.25rem; margin: 1rem 0; }
.next-stage-summary { border-left: .35rem solid var(--next-accent); }
.next-stage-summary:has(.next-stage-state) { border-left-color: var(--next-accent); }
.next-stage-summary--blocked { border-left-style: dashed; border-left-color: var(--next-blocked); }
.next-stage-action { font-weight: 650; }
.next-stage-guidance { margin-top: 1rem; padding: .75rem 1rem; border: 1px dashed var(--next-blocked); color: var(--next-text); }
.next-stage-guidance strong { display: block; color: var(--next-blocked); }
.next-stage-guidance ul { margin: .45rem 0 0; padding-left: 1.25rem; }
.next-stage-checklist { display: grid; gap: .7rem; margin: 0; padding-left: 1.3rem; }
.next-stage-check { display: flex; justify-content: space-between; gap: 1rem; border-bottom: 1px solid var(--next-border); padding: .55rem 0; }
.next-stage-check--needs_clarification { color: var(--next-blocked); }
.next-stage-footer { color: var(--next-muted); font-size: .92rem; margin-top: 1.5rem; }
@media (prefers-reduced-motion: reduce) { * { scroll-behavior: auto !important; transition: none !important; } }
@media (forced-colors: active) { .next-stage-card { border: 2px solid CanvasText; } .next-stage-summary { border-left: .35rem solid Highlight; } .next-stage-summary--blocked { border-left-style: dashed; border-left-color: CanvasText; } .next-stage-guidance { border-color: CanvasText; } .next-stage-guidance strong { color: CanvasText; } .skip-link:focus-visible, main:focus-visible { outline: 3px solid Highlight; outline-offset: 3px; } }
@media (max-width: 640px) { .next-stage-shell { padding: 1.25rem .75rem 2rem; } .next-stage-check { align-items: flex-start; flex-direction: column; gap: .1rem; } }
@media (prefers-contrast: more) { .next-stage-card, .next-stage-guidance { border-width: 2px; box-shadow: none; } .continuity-rail { border-width: 2px; } .continuity-rail__marker { border-width: 2px; } }
@media print { html { color-scheme: light; } body { background: #fff; color: #000; } .next-stage-card { break-inside: avoid; page-break-inside: avoid; box-shadow: none; } .skip-link { display: none; } }
@media screen and (prefers-color-scheme: dark) { :root { color-scheme: dark; --next-bg: #101820; --next-surface: #18232d; --next-text: #eef3f7; --next-muted: #b4c0ca; --next-accent: #76c7dc; --next-border: #40515e; --next-blocked: #ffc078; } }
@media screen and (prefers-color-scheme: dark) and (prefers-contrast: more) { :root { --next-border: #b4c0ca; } }

.continuity-rail { margin: 1rem 0 1.5rem; padding: .85rem 1rem 1rem; border: 1px solid currentColor; border-radius: .8rem; color: var(--next-text); }
.continuity-rail__label { margin: 0 0 .65rem; color: var(--next-muted); font-size: .76rem; font-weight: 800; letter-spacing: .08em; text-transform: uppercase; }
.continuity-rail ol { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: .4rem; margin: 0; padding: 0; list-style: none; }
.continuity-rail li { display: flex; min-width: 0; gap: .45rem; align-items: flex-start; padding: .55rem .45rem; border-top: .2rem solid transparent; color: var(--next-muted); }
.continuity-rail li[data-state="current"] { border-top-color: var(--next-accent); background: var(--next-bg); color: var(--next-text); }
.continuity-rail__marker { display: grid; flex: 0 0 1.45rem; width: 1.45rem; height: 1.45rem; place-items: center; border: 1px solid currentColor; border-radius: 50%; font-size: .75rem; font-weight: 800; }
.continuity-rail li[data-state="current"] .continuity-rail__marker { background: var(--next-accent); border-color: var(--next-accent); color: var(--next-bg); }
.continuity-rail__copy { display: grid; gap: .15rem; min-width: 0; font-size: .8rem; line-height: 1.25; }
.continuity-rail__copy strong { overflow-wrap: anywhere; }
.continuity-rail__status { color: var(--next-accent); font-size: .7rem; font-weight: 800; text-transform: uppercase; }
@media (max-width: 720px) { .continuity-rail ol { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
@media screen and (max-width: 420px) { .continuity-rail ol { grid-template-columns: 1fr; } }
@media (min-width: 721px) and (max-width: 900px) { .continuity-rail ol { grid-template-columns: repeat(3, minmax(0, 1fr)); } }
@media (forced-colors: active) { .continuity-rail, .continuity-rail li { border-color: CanvasText; } .continuity-rail li[data-state="current"] { background: Canvas; } .continuity-rail li[data-state="current"] .continuity-rail__marker { background: Highlight; border-color: CanvasText; color: HighlightText; } }
@media print { .continuity-rail { break-inside: avoid; page-break-inside: avoid; } .continuity-rail ol { grid-template-columns: repeat(2, minmax(0, 1fr)); } .continuity-rail__copy strong { overflow-wrap: normal; hyphens: auto; } }
```

### `plugins/professional-growth-coach/assets/private-recruiter-screen-debrief-v1.css`

```css
:root { color-scheme: light; --debrief-ink:#172033; --debrief-muted:#536176; --debrief-surface:#fff; --debrief-soft:#f3f6fb; --debrief-border:#c7d2e5; --debrief-blue:#315bd6; --debrief-marker-ink:#fff; --debrief-green:#176b4d; --debrief-amber:#8a5a00; }
* { box-sizing: border-box; }
html { background: var(--debrief-soft); }
body { margin:0; color:var(--debrief-ink); background:var(--debrief-soft); font:16px/1.55 ui-sans-serif,system-ui,-apple-system,sans-serif; overflow-wrap:anywhere; }
.skip-link { position:absolute; left:1rem; top:-4rem; padding:.6rem .8rem; color:var(--debrief-surface); background:var(--debrief-ink); border-radius:.4rem; z-index:2; }
.skip-link:focus { top:1rem; }
.skip-link:focus-visible, main:focus-visible { outline:3px solid var(--debrief-blue); outline-offset:3px; }
.debrief-shell { width:min(960px,calc(100% - 2rem)); margin:0 auto; padding:3rem 0; }
.debrief-header { margin-bottom:1.25rem; }
.debrief-kicker { margin:0 0 .35rem; color:var(--debrief-blue); font-size:.78rem; font-weight:800; letter-spacing:.12em; text-transform:uppercase; }
h1,h2 { line-height:1.2; } h1 { max-width:40rem; margin:0; font-size:clamp(1.75rem,4vw,2.8rem); } h2 { margin-top:0; }
.debrief-date { color:var(--debrief-muted); margin:.7rem 0 0; } .debrief-date span { font-weight:700; }
.debrief-card { margin:1rem 0; padding:clamp(1rem,3vw,1.5rem); background:var(--debrief-surface); border:1px solid var(--debrief-border); border-radius:.8rem; box-shadow:0 8px 20px rgb(23 32 51 / 6%); }
.debrief-summary { border-left:.35rem solid var(--debrief-blue); } .debrief-summary__label { margin:0 0 .35rem; color:var(--debrief-blue); font-weight:800; } .debrief-summary__action { font-size:1.08rem; font-weight:700; }
.debrief-context-grid { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:.8rem; margin:0; } .debrief-context-grid div { padding:.75rem; background:var(--debrief-soft); border-radius:.5rem; }
dt { color:var(--debrief-muted); font-size:.78rem; font-weight:800; letter-spacing:.06em; text-transform:uppercase; } dd { margin:.25rem 0 0; font-weight:700; }
.debrief-coverage-list { display:grid; gap:.7rem; padding-left:1.4rem; } .debrief-coverage { padding:.75rem 1rem; border:1px solid var(--debrief-border); border-left-width:.3rem; border-radius:.5rem; }
.debrief-coverage--discussed { border-left-color:var(--debrief-green); } .debrief-coverage--unclear { border-left-color:var(--debrief-amber); } .debrief-coverage strong { margin-right:.6rem; } .debrief-coverage span { color:var(--debrief-muted); font-weight:800; }
.debrief-counts { color:var(--debrief-muted); font-size:.9rem; }
.debrief-footer { margin-top:1.5rem; color:var(--debrief-muted); font-size:.92rem; }
@media (max-width:640px) { .debrief-shell { width:min(100% - 1rem,960px); padding-top:2rem; } .debrief-context-grid { grid-template-columns:1fr; } }
@media (prefers-contrast:more) { :root { --debrief-border:#536176; } .debrief-card,.debrief-coverage { border-width:2px; box-shadow:none; } .debrief-summary,.debrief-coverage { border-left-width:.5rem; } }
@media (prefers-reduced-motion:reduce) { *,*::before,*::after { scroll-behavior:auto !important; transition:none !important; } }
@media (forced-colors:active) { .debrief-card,.debrief-coverage { border:2px solid CanvasText; box-shadow:none; } .debrief-summary,.debrief-coverage { border-left-color:CanvasText; } .skip-link { background:CanvasText; color:Canvas; } .skip-link:focus-visible, main:focus-visible { outline:3px solid Highlight; outline-offset:3px; } }
@media screen and (prefers-color-scheme: dark) { :root { color-scheme: dark; --debrief-ink:#edf2fa; --debrief-muted:#b9c5d8; --debrief-surface:#1c2738; --debrief-soft:#111927; --debrief-border:#536176; --debrief-marker-ink:#101a35; } }
@media screen and (prefers-color-scheme: dark) and (prefers-contrast: more) { :root { --debrief-border: #b9c5d8; } }
@media (prefers-contrast: more) { .continuity-rail { border-width: 2px; } .continuity-rail__marker { border-width: 2px; } }
@media print { html,body { color-scheme:light; background:#fff; } .debrief-shell { width:100%; padding:0; } .debrief-card { box-shadow:none; break-inside:avoid; page-break-inside:avoid; } .skip-link { display:none; } }

.continuity-rail { margin: 1rem 0 1.5rem; padding: .85rem 1rem 1rem; border: 1px solid currentColor; border-radius: .8rem; color: var(--debrief-ink); }
.continuity-rail__label { margin: 0 0 .65rem; color: var(--debrief-muted); font-size: .76rem; font-weight: 800; letter-spacing: .08em; text-transform: uppercase; }
.continuity-rail ol { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: .4rem; margin: 0; padding: 0; list-style: none; }
.continuity-rail li { display: flex; min-width: 0; gap: .45rem; align-items: flex-start; padding: .55rem .45rem; border-top: .2rem solid transparent; color: var(--debrief-muted); }
.continuity-rail li[data-state="current"] { border-top-color: var(--debrief-blue); background: var(--debrief-soft); color: var(--debrief-ink); }
.continuity-rail__marker { display: grid; flex: 0 0 1.45rem; width: 1.45rem; height: 1.45rem; place-items: center; border: 1px solid currentColor; border-radius: 50%; font-size: .75rem; font-weight: 800; }
.continuity-rail li[data-state="current"] .continuity-rail__marker { background: var(--debrief-blue); border-color: var(--debrief-blue); color: var(--debrief-marker-ink); }
.continuity-rail__copy { display: grid; gap: .15rem; min-width: 0; font-size: .8rem; line-height: 1.25; }
.continuity-rail__copy strong { overflow-wrap: anywhere; }
.continuity-rail__status { color: var(--debrief-blue); font-size: .7rem; font-weight: 800; text-transform: uppercase; }
@media (max-width: 720px) { .continuity-rail ol { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
@media screen and (max-width: 420px) { .continuity-rail ol { grid-template-columns: 1fr; } }
@media (min-width: 721px) and (max-width: 900px) { .continuity-rail ol { grid-template-columns: repeat(3, minmax(0, 1fr)); } }
@media (forced-colors: active) { .continuity-rail, .continuity-rail li { border-color: CanvasText; } .continuity-rail li[data-state="current"] { background: Canvas; } .continuity-rail li[data-state="current"] .continuity-rail__marker { background: Highlight; border-color: CanvasText; color: HighlightText; } }
@media print { .continuity-rail { break-inside: avoid; page-break-inside: avoid; } .continuity-rail ol { grid-template-columns: repeat(2, minmax(0, 1fr)); } .continuity-rail__copy strong { overflow-wrap: normal; hyphens: auto; } }
```

### `plugins/professional-growth-coach/assets/recruiter-target-screen-intake-v1.css`

```css
:root {
  color-scheme: light;
  --screen-ink: #172033;
  --screen-muted: #536176;
  --screen-surface: #ffffff;
  --screen-soft: #f3f6fb;
  --screen-border: #c7d2e5;
  --screen-blue: #315bd6;
  --screen-marker-ink: #fff;
  --screen-green: #176b4d;
  --screen-amber: #8a5a00;
  --screen-red: #a43d3d;
}

* { box-sizing: border-box; }
html { background: var(--screen-soft); }
body { margin: 0; color: var(--screen-ink); background: var(--screen-soft); font: 16px/1.55 ui-sans-serif, system-ui, -apple-system, sans-serif; overflow-wrap: anywhere; }
.skip-link { position: absolute; left: 1rem; top: -4rem; padding: .6rem .8rem; color: var(--screen-surface); background: var(--screen-ink); border-radius: .4rem; z-index: 2; }
.skip-link:focus { top: 1rem; }
.skip-link:focus-visible, main:focus-visible { outline: 3px solid var(--screen-blue); outline-offset: 3px; }
.screen-shell { width: min(960px, calc(100% - 2rem)); margin: 0 auto; padding: 3rem 0; }
.screen-header { margin-bottom: 1.25rem; }
.screen-kicker { margin: 0 0 .35rem; color: var(--screen-blue); font-size: .78rem; font-weight: 800; letter-spacing: .12em; text-transform: uppercase; }
h1, h2, h3 { line-height: 1.2; }
h1 { max-width: 36rem; margin: 0; font-size: clamp(1.75rem, 4vw, 2.8rem); }
h2 { margin-top: 0; }
.screen-date { color: var(--screen-muted); margin: .7rem 0 0; }
.screen-date span { font-weight: 700; }
.screen-card { margin: 1rem 0; padding: clamp(1rem, 3vw, 1.5rem); background: var(--screen-surface); border: 1px solid var(--screen-border); border-radius: .8rem; box-shadow: 0 8px 20px rgb(23 32 51 / 6%); }
.screen-decision { border-left: .35rem solid var(--screen-blue); }
.screen-state { margin: 0 0 .35rem; color: var(--screen-blue); font-weight: 800; }
.screen-context-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: .8rem; margin: 0 0 1.1rem; }
.screen-context-grid div { padding: .75rem; background: var(--screen-soft); border-radius: .5rem; }
dt { color: var(--screen-muted); font-size: .78rem; font-weight: 800; text-transform: uppercase; letter-spacing: .06em; }
dd { margin: .25rem 0 0; font-weight: 700; }
.screen-requirements { margin-bottom: 0; }
.screen-checks { display: grid; gap: .75rem; padding-left: 1.4rem; }
.screen-check { padding: .8rem 1rem; border: 1px solid var(--screen-border); border-left-width: .3rem; border-radius: .5rem; }
.screen-check--pass { border-left-color: var(--screen-green); }
.screen-check--clarify { border-left-color: var(--screen-amber); }
.screen-check--stop { border-left-color: var(--screen-red); }
.screen-check strong { margin-right: .6rem; }
.screen-check span { color: var(--screen-muted); font-weight: 800; }
.screen-check p { margin: .25rem 0 0; }
.screen-footer { margin-top: 1.5rem; color: var(--screen-muted); font-size: .92rem; }
@media (max-width: 640px) { .screen-shell { width: min(100% - 1rem, 960px); padding-top: 2rem; } .screen-context-grid { grid-template-columns: 1fr; } }
@media (prefers-contrast: more) { :root { --screen-border: #536176; } .screen-card, .screen-check { border-width: 2px; box-shadow: none; } .screen-decision, .screen-check { border-left-width: .5rem; } .continuity-rail { border-width: 2px; } .continuity-rail__marker { border-width: 2px; } }
@media (prefers-reduced-motion: reduce) { *, *::before, *::after { scroll-behavior: auto !important; transition: none !important; } }
@media (forced-colors: active) { .screen-card, .screen-check { border: 2px solid CanvasText; box-shadow: none; } .screen-decision, .screen-check { border-left-color: CanvasText; } .skip-link { background: CanvasText; color: Canvas; } .skip-link:focus-visible, main:focus-visible { outline: 3px solid Highlight; outline-offset: 3px; } }
@media screen and (prefers-color-scheme: dark) { :root { color-scheme: dark; --screen-ink: #edf2fa; --screen-muted: #b9c5d8; --screen-blue: #8eb2ff; --screen-marker-ink: #101a35; --screen-surface: #1c2738; --screen-soft: #111927; --screen-border: #536176; } }
@media screen and (prefers-color-scheme: dark) and (prefers-contrast: more) { :root { --screen-border: #b9c5d8; } }
@media print { html, body { color-scheme: light; background: #fff; } .screen-shell { width: 100%; padding: 0; } .screen-card { box-shadow: none; break-inside: avoid; page-break-inside: avoid; } .skip-link { display: none; } }

.continuity-rail { margin: 1rem 0 1.5rem; padding: .85rem 1rem 1rem; border: 1px solid currentColor; border-radius: .8rem; color: var(--screen-ink); }
.continuity-rail__label { margin: 0 0 .65rem; color: var(--screen-muted); font-size: .76rem; font-weight: 800; letter-spacing: .08em; text-transform: uppercase; }
.continuity-rail ol { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: .4rem; margin: 0; padding: 0; list-style: none; }
.continuity-rail li { display: flex; min-width: 0; gap: .45rem; align-items: flex-start; padding: .55rem .45rem; border-top: .2rem solid transparent; color: var(--screen-muted); }
.continuity-rail li[data-state="current"] { border-top-color: var(--screen-blue); background: var(--screen-soft); color: var(--screen-ink); }
.continuity-rail__marker { display: grid; flex: 0 0 1.45rem; width: 1.45rem; height: 1.45rem; place-items: center; border: 1px solid currentColor; border-radius: 50%; font-size: .75rem; font-weight: 800; }
.continuity-rail li[data-state="current"] .continuity-rail__marker { background: var(--screen-blue); border-color: var(--screen-blue); color: var(--screen-marker-ink); }
.continuity-rail__copy { display: grid; gap: .15rem; min-width: 0; font-size: .8rem; line-height: 1.25; }
.continuity-rail__copy strong { overflow-wrap: anywhere; }
.continuity-rail__status { color: var(--screen-blue); font-size: .7rem; font-weight: 800; text-transform: uppercase; }
@media (max-width: 720px) { .continuity-rail ol { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
@media screen and (max-width: 420px) { .continuity-rail ol { grid-template-columns: 1fr; } }
@media (min-width: 721px) and (max-width: 900px) { .continuity-rail ol { grid-template-columns: repeat(3, minmax(0, 1fr)); } }
@media (forced-colors: active) { .continuity-rail, .continuity-rail li { border-color: CanvasText; } .continuity-rail li[data-state="current"] { background: Canvas; } .continuity-rail li[data-state="current"] .continuity-rail__marker { background: Highlight; border-color: CanvasText; color: HighlightText; } }
@media print { .continuity-rail { break-inside: avoid; page-break-inside: avoid; } .continuity-rail ol { grid-template-columns: repeat(2, minmax(0, 1fr)); } .continuity-rail__copy strong { overflow-wrap: normal; hyphens: auto; } }
```

### `plugins/professional-growth-coach/assets/career-market-learning-dossier-v1.css`

```css
.market-summary { min-width: 0; padding: 1.25rem; border: 1px solid var(--line); border-top: 4px solid var(--gold); background: var(--surface); }
.market-summary h2, .market-summary h3 { color: var(--forest); }
.market-scan-summary { margin: .85rem 0 1rem; padding: .8rem 1rem; border-left: 4px solid var(--forest); background: var(--forest-soft); break-inside: avoid; page-break-inside: avoid; }
.market-scan-summary h3 { margin: 0 0 .5rem; font-size: 1rem; }
.market-scan-summary dl { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: .6rem; margin: 0; }
.market-scan-summary dl > div:last-child { grid-column: 1 / -1; padding-top: .6rem; border-top: 1px solid var(--line); }
.market-scan-summary dt { color: var(--muted-text); font-size: .75rem; font-weight: 700; }
.market-scan-summary dd { margin: .15rem 0 0; overflow-wrap: anywhere; }
.vacancy-alignment-list { display: grid; grid-template-columns: repeat(auto-fit, minmax(12rem, 1fr)); gap: .75rem; }
.vacancy-alignment-card { min-width: 0; padding: 1rem; border: 1px solid var(--forest-soft); background: var(--paper); break-inside: avoid; page-break-inside: avoid; }
.vacancy-alignment-card h3 { margin: .25rem 0 .75rem; overflow-wrap: anywhere; }
.market-vacancy-key { margin: 0; color: var(--muted-text); font-weight: 700; }
.market-alignment-line { display: flex; align-items: baseline; justify-content: space-between; gap: .75rem; margin: .75rem 0 0; }
.market-alignment-score, .market-recurrence-count { color: var(--forest); font-variant-numeric: tabular-nums; }
.market-alignment-facts { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: .3rem .75rem; margin: .75rem 0 0; }
.market-alignment-facts dt { color: var(--muted-text); font-size: .875rem; font-weight: 700; }
.market-alignment-facts dd { margin: 0; overflow-wrap: anywhere; }
.market-vacancy-context { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: .25rem .75rem; margin: .75rem 0 0; padding-top: .65rem; border-top: 1px solid var(--muted); }
.market-vacancy-context dt { color: var(--muted-text); font-size: .875rem; font-weight: 700; }
.market-vacancy-context dd { margin: 0; overflow-wrap: anywhere; }
.market-source-meta { display: flex; flex-wrap: wrap; justify-content: space-between; gap: .5rem .75rem; margin: .75rem 0 0; padding-top: .65rem; border-top: 1px solid var(--line); color: var(--muted-text); font-size: .875rem; }
.market-freshness { flex-basis: 100%; font-variant-numeric: tabular-nums; }
.market-source-link { display: inline-flex; align-items: center; min-height: 44px; padding: .35rem .5rem; color: var(--forest); font-weight: 700; }
.market-source-link:focus-visible { outline: 2px solid var(--coral); outline-offset: 2px; }
.market-directional-legend { margin-top: .5rem; }
.market-key, .market-matrix-wrap, .gap-closure-route { margin-top: 1.25rem; min-width: 0; }
.market-key ol, .gap-closure-route ol { margin: .5rem 0 0; padding-left: 1.25rem; }
.market-matrix { width: 100%; border-collapse: collapse; table-layout: fixed; }
.market-matrix th, .market-matrix td { padding: .6rem; border: 1px solid var(--muted); overflow-wrap: anywhere; text-align: left; vertical-align: top; }
.market-matrix th { color: var(--forest); }
.market-state { display: block; margin-top: .25rem; color: var(--muted-text); font-size: .875rem; font-weight: 400; }
.recurrence-list { display: grid; gap: .6rem; margin: .5rem 0 0; padding: 0; list-style: none; }
.recurrence-row { display: grid; grid-template-columns: minmax(0, 1fr) minmax(6rem, 2fr) auto; gap: .75rem; align-items: center; padding: .5rem; border: 1px solid var(--muted); break-inside: avoid; page-break-inside: avoid; }
.market-boundary, .market-limitation { margin: .75rem 0 0; padding-left: .75rem; border-left: 4px solid var(--gold); }
.gap-closure-route { padding: 1rem; border-left: 4px solid var(--forest); background: var(--paper); }
.market-learning-roi { margin-top: 1.25rem; padding: 1rem; border: 1px solid var(--line); border-left: 4px solid var(--gold); background: var(--surface); break-inside: avoid; page-break-inside: avoid; }
.market-learning-roi h3, .market-learning-roi h4 { color: var(--forest); }
.learning-coach-decision, .learning-proof-sprint, .learning-reuse { margin-top: 1rem; padding: .75rem; border: 1px solid var(--muted); background: var(--paper); }
.learning-decision-list { display: grid; grid-template-columns: repeat(auto-fit, minmax(14rem, 1fr)); gap: .75rem; }
.learning-decision-row { min-width: 0; padding: .75rem; border: 1px solid var(--muted); background: var(--paper); break-inside: avoid; page-break-inside: avoid; }
.learning-decision-row--project-first { border-left: 4px solid var(--forest); }
.learning-decision-row--consider { border-left: 4px solid var(--gold); }
.learning-decision-row--not-needed { border-left: 4px solid var(--muted); }
.learning-decision-row--recommended { border-left: 4px solid var(--forest); }
.learning-decision-row--pause, .learning-decision-row--apply-with-boundary { border-left: 4px solid var(--coral); }
.learning-decision-heading { display: flex; align-items: flex-start; justify-content: space-between; gap: .75rem; margin-bottom: .75rem; }
.learning-decision-heading h4 { margin: .15rem 0 0; }
.learning-decision-kicker { display: block; color: var(--muted-text); font-size: .75rem; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; }
.learning-option-type { flex: 0 1 auto; padding: .3rem .5rem; border: 1px solid var(--forest); color: var(--forest); font-size: .75rem; font-weight: 700; line-height: 1.2; text-align: right; }
.learning-decision-row--consider .learning-option-type, .learning-decision-row--recommended .learning-option-type { border-color: var(--gold); color: #654c10; }
.learning-decision-row--pause .learning-option-type, .learning-decision-row--apply-with-boundary .learning-option-type { border-color: var(--coral); color: #7c2f1e; }
.market-provider-evidence-boundary { margin-top: .75rem; }
.learning-decision-facts { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: .35rem .75rem; }
.learning-decision-facts dt { color: var(--muted-text); font-weight: 700; }
.learning-decision-facts dd { margin: 0; overflow-wrap: anywhere; }
.learning-provenance { margin: 0 0 .85rem; padding: .65rem; border: 1px dashed var(--forest-soft); background: var(--surface); }
.learning-provenance h5 { margin: 0 0 .4rem; color: var(--forest); font-size: .9rem; }
.learning-provenance-facts { display: grid; grid-template-columns: minmax(0, .8fr) minmax(0, 1.2fr); gap: .25rem .65rem; margin: 0; }
.learning-provenance-facts dt { color: var(--muted-text); font-size: .875rem; font-weight: 700; }
.learning-provenance-facts dd { margin: 0; overflow-wrap: anywhere; }
.learning-reuse ul { display: grid; gap: .35rem; margin: .5rem 0 0; padding-left: 1.25rem; }

@media screen and (prefers-color-scheme: dark) {
  .market-source-link { color: var(--gold); }
  .learning-decision-row--consider .learning-option-type,
  .learning-decision-row--recommended .learning-option-type { color: var(--gold); }
  .learning-decision-row--pause .learning-option-type,
  .learning-decision-row--apply-with-boundary .learning-option-type { color: var(--coral); }
}

@media screen and (max-width: 680px) {
  .vacancy-alignment-list { grid-template-columns: 1fr; }
  .market-matrix, .market-matrix tbody, .market-matrix tr, .market-matrix th, .market-matrix td { display: block; width: 100%; }
  .market-matrix thead { position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px; overflow: hidden; clip: rect(0, 0, 0, 0); border: 0; }
  .market-matrix tr { padding: .75rem 0; border-bottom: 1px solid var(--muted); }
  .market-matrix td { display: grid; grid-template-columns: minmax(7rem, .4fr) minmax(0, 1fr); gap: .75rem; border: 0; }
  .market-matrix td::before { content: attr(data-label); color: var(--muted-text); font-size: .8125rem; font-weight: 700; }
  .market-alignment-line { align-items: flex-start; flex-direction: column; gap: .2rem; }
  .market-alignment-facts, .market-vacancy-context, .market-scan-summary dl, .learning-provenance-facts { grid-template-columns: 1fr; gap: .2rem; }
  .recurrence-row { grid-template-columns: 1fr; gap: .35rem; }
  .learning-decision-list { grid-template-columns: 1fr; }
  .learning-decision-facts { grid-template-columns: 1fr; gap: .2rem; }
  .learning-decision-heading { display: block; }
  .learning-option-type { display: inline-block; margin-top: .5rem; text-align: left; }
}

@media (prefers-reduced-motion: reduce) { .vacancy-alignment-card, .recurrence-row { animation: none !important; transition: none !important; transform: none !important; } }

@media print {
  .market-summary, .market-scan-summary, .market-key, .market-matrix-wrap, .gap-closure-route, .market-learning-roi, .learning-decision-row, .vacancy-alignment-card, .recurrence-row, .market-source-meta { break-inside: avoid; page-break-inside: avoid; }
  .market-matrix, .market-matrix tbody, .market-matrix tr, .market-matrix th, .market-matrix td { display: block; width: 100%; }
  .market-matrix thead { position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px; overflow: hidden; clip: rect(0, 0, 0, 0); border: 0; }
  .market-matrix tr { padding: .75rem 0; border-bottom: 1px solid var(--muted); }
  .market-matrix td { display: grid; grid-template-columns: minmax(7rem, .4fr) minmax(0, 1fr); gap: .75rem; border: 0; }
  .market-matrix td::before { content: attr(data-label); color: var(--muted-text); font-size: .8125rem; font-weight: 700; }
  .market-scan-summary dl > div:last-child { grid-column: 1 / -1; }
}

@media (forced-colors: active) {
  .market-summary, .market-scan-summary, .vacancy-alignment-card, .recurrence-row, .gap-closure-route, .market-learning-roi, .learning-coach-decision, .learning-proof-sprint, .learning-reuse, .learning-decision-row, .learning-provenance, .market-matrix th, .market-matrix td, .market-alignment-score, .market-recurrence-count, .market-vacancy-context, .market-source-meta { background: Canvas; color: CanvasText; border-color: CanvasText; }
  .market-source-link { color: LinkText; }
  .market-boundary, .market-limitation, .gap-closure-route { border-left-color: Highlight; }
  .market-scan-summary dl > div:last-child { border-top-color: CanvasText; }
  .market-matrix td::before { color: CanvasText; }
  .learning-decision-row .learning-option-type { color: CanvasText; border-color: CanvasText; }
}

@media (prefers-contrast: more) { .market-summary, .vacancy-alignment-card, .recurrence-row, .market-learning-roi, .learning-coach-decision, .learning-proof-sprint, .learning-reuse, .learning-decision-row, .market-matrix th, .market-matrix td { border-width: 2px; } }
```

### `plugins/professional-growth-coach/assets/recruiter-practice-session-v1.css`

```css
:root {
  --paper: #f6f4ee;
  --surface: #ffffff;
  --ink: #1b1c1a;
  --forest: #173e30;
  --forest-soft: #dce5e0;
  --coral: #b9513a;
  --coral-soft: #f6e0da;
  --decision-term: #dfbf70;
  --muted: #46534d;
  --line: #b8c7c0;
  --measure: 72ch;
  --serif: Georgia, "Times New Roman", Times, serif;
  --sans: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
}

* { box-sizing: border-box; }

html { color-scheme: light; background: var(--paper); }

.recruiter-practice-document {
  margin: 0;
  background: var(--paper);
  color: var(--ink);
  font-family: var(--sans);
  font-size: 16px;
  line-height: 1.55;
  overflow-wrap: anywhere;
}

.recruiter-practice-document :focus-visible {
  outline: 3px solid var(--coral);
  outline-offset: 3px;
}

.recruiter-practice-document .skip-link {
  position: fixed;
  z-index: 10;
  top: 0.5rem;
  left: 0.5rem;
  transform: translateY(-200%);
  padding: 0.75rem 1rem;
  background: var(--surface);
  border: 1px solid var(--forest);
  color: var(--forest);
  font-weight: 700;
}

.recruiter-practice-document .skip-link:focus { transform: none; }

.recruiter-practice-document .practice-shell {
  width: min(920px, calc(100% - 2rem));
  margin-inline: auto;
}

.recruiter-practice-document .practice-header {
  display: flex;
  align-items: end;
  justify-content: space-between;
  gap: 1rem;
  padding-block: 2rem 1rem;
  border-bottom: 1px solid var(--forest);
}

.recruiter-practice-document .practice-kicker,
.recruiter-practice-document .practice-label {
  margin: 0;
  color: var(--forest);
  font-size: 0.8125rem;
  font-weight: 700;
  letter-spacing: 0.09em;
  text-transform: uppercase;
}

.recruiter-practice-document h1,
.recruiter-practice-document h2 {
  font-family: var(--serif);
}

.recruiter-practice-document h1 {
  margin: 0.2rem 0 0;
  font-size: clamp(2rem, 6vw, 3.25rem);
  font-style: italic;
  line-height: 1.04;
}

.recruiter-practice-document h2 {
  margin: 0;
  color: var(--forest);
  font-size: clamp(1.35rem, 3vw, 1.85rem);
  line-height: 1.16;
}

.recruiter-practice-document .state-chip {
  display: inline-flex;
  align-items: center;
  min-height: 2.25rem;
  padding: 0.4rem 0.75rem;
  border: 1px solid currentColor;
  color: var(--forest);
  font-size: 0.875rem;
  font-weight: 700;
  line-height: 1.2;
  text-align: center;
}

.recruiter-practice-document .state-chip--feedback_available { color: #854117; background: #f7ecd5; }
.recruiter-practice-document .state-chip--ready_to_practice { color: var(--forest); background: var(--forest-soft); }
.recruiter-practice-document .state-chip--awaiting_answer { color: #5c4a12; background: #f5ecd8; }
.recruiter-practice-document main { padding-block: 1.5rem 3rem; }

.recruiter-practice-document .practice-session {
  min-width: 0;
  padding: clamp(1.15rem, 3vw, 2rem);
  background: var(--surface);
  border-top: 4px solid var(--forest);
  box-shadow: 0 1px 0 rgb(23 62 48 / 10%);
  animation: practice-enter 0.35s ease both;
}

.recruiter-practice-document .practice-session > * + * { margin-top: 1.5rem; }
.recruiter-practice-document .practice-summary { max-width: var(--measure); margin: 0.5rem 0 0; }

.recruiter-practice-document .practice-context,
.recruiter-practice-document .practice-prompt,
.recruiter-practice-document .practice-rehearsal,
.recruiter-practice-document .practice-evidence,
.recruiter-practice-document .practice-boundary,
.recruiter-practice-document .practice-feedback,
.recruiter-practice-document .practice-decision,
.recruiter-practice-document .practice-next-version {
  padding: 1rem;
  border: 1px solid var(--line);
}

.recruiter-practice-document .practice-prompt { background: var(--forest-soft); border-left: 4px solid var(--forest); }
.recruiter-practice-document .practice-prompt p { margin: 0.55rem 0 0; max-width: var(--measure); font-family: var(--serif); font-size: clamp(1.2rem, 2.5vw, 1.55rem); line-height: 1.25; }
.recruiter-practice-document .practice-rehearsal { background: #f8f7f2; }
.recruiter-practice-document .practice-rehearsal--triage-first-answer { max-width: var(--measure); border-left: 4px solid var(--forest); background: var(--forest-soft); }
.recruiter-practice-document .practice-rehearsal--triage-first-answer ol { grid-template-columns: repeat(3, minmax(0, 1fr)); gap: .65rem; padding: 0; list-style: none; counter-reset: triage-first-answer-step; }
.recruiter-practice-document .practice-rehearsal--triage-first-answer li { counter-increment: triage-first-answer-step; position: relative; min-width: 0; padding: .7rem .7rem .7rem 2.5rem; border: 1px solid var(--line); background: var(--surface); }
.recruiter-practice-document .practice-rehearsal--triage-first-answer li::before { content: counter(triage-first-answer-step); display: inline-grid; position: absolute; top: .65rem; left: .65rem; width: 1.35rem; height: 1.35rem; place-items: center; border: 1px solid var(--forest); border-radius: 50%; color: var(--forest); font-size: .8rem; font-weight: 800; line-height: 1; }
.recruiter-practice-document .practice-next-version { max-width: var(--measure); border-left: 4px solid var(--forest); background: var(--forest-soft); }
.recruiter-practice-document .practice-next-version-kicker { margin: 0; color: var(--forest); font-size: .8rem; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; }
.recruiter-practice-document .practice-next-version h2 { margin: .25rem 0 0; font-size: 1.25rem; }
.recruiter-practice-document .practice-next-version-intro { max-width: var(--measure); margin: .45rem 0 0; color: #46534d; }
.recruiter-practice-document .practice-next-version ol { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: .65rem; margin: .75rem 0 0; padding: 0; list-style: none; counter-reset: next-version-step; }
.recruiter-practice-document .practice-next-version li { counter-increment: next-version-step; position: relative; min-width: 0; padding: .7rem .7rem .7rem 2.5rem; border: 1px solid var(--line); background: var(--surface); }
.recruiter-practice-document .practice-next-version li::before { content: counter(next-version-step); display: inline-grid; position: absolute; top: .65rem; left: .65rem; width: 1.35rem; height: 1.35rem; place-items: center; border: 1px solid var(--forest); border-radius: 50%; color: var(--forest); font-size: .8rem; font-weight: 800; line-height: 1; }
.recruiter-practice-document .practice-next-version li p { margin: .35rem 0 0; color: #46534d; }
.recruiter-practice-document .screen-readiness { padding: 1rem; border: 1px solid var(--line); border-left: 4px solid var(--decision-term); background: var(--paper); }
.recruiter-practice-document .screen-readiness-kicker { margin: 0; color: var(--forest); font-size: .8rem; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; }
.recruiter-practice-document .screen-readiness h2 { margin: .25rem 0 0; font-size: 1.3rem; }
.recruiter-practice-document .screen-readiness-intro { max-width: var(--measure); margin: .45rem 0 0; color: var(--muted); }
.recruiter-practice-document .screen-readiness-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: .65rem; margin: .8rem 0 0; }
.recruiter-practice-document .screen-readiness-item { position: relative; min-width: 0; padding: .7rem; border: 1px solid var(--line); background: var(--surface); }
.recruiter-practice-document .screen-readiness-item--current { border-top: 3px solid var(--forest); }
.recruiter-practice-document .screen-readiness-item--pending { border-top: 3px solid var(--decision-term); }
.recruiter-practice-document .screen-readiness-label { display: block; color: var(--forest); font-size: .78rem; font-weight: 700; letter-spacing: .05em; text-transform: uppercase; }
.recruiter-practice-document .screen-readiness-item strong { display: block; margin-top: .25rem; }
.recruiter-practice-document .screen-readiness-state { display: block; margin-top: .35rem; color: var(--muted); font-size: .75rem; font-weight: 700; text-transform: uppercase; }
.recruiter-practice-document .practice-next-action { background: var(--forest); color: #fff; border: 1px solid var(--forest); padding: 1rem; }
.recruiter-practice-document .practice-next-action h2 { color: #fff; }
.recruiter-practice-document .practice-next-action p { max-width: var(--measure); margin: 0.45rem 0 0; }
.recruiter-practice-document .practice-next-action--ready_to_practice { border-left: 4px solid #9fc4b4; }
.recruiter-practice-document .practice-next-action--awaiting_answer { border-left: 4px solid #dfbf70; }
.recruiter-practice-document .practice-handoff { padding: 1rem; border: 1px dashed var(--forest); background: #f8f7f2; }
.recruiter-practice-document .practice-handoff h2 { font-size: 1.25rem; }
.recruiter-practice-document .practice-handoff p { max-width: var(--measure); margin: 0.45rem 0 0; }
.recruiter-practice-document .practice-handoff--dossier { border-left: 4px solid var(--forest); }
.recruiter-practice-document .practice-handoff--reply { border-left: 4px solid var(--coral); }
.recruiter-practice-document .triage-practice-route { padding: 1rem; border: 1px solid var(--line); border-left: 4px solid var(--coral); background: var(--coral-soft); }
.recruiter-practice-document .triage-practice-route-kicker { margin: 0; color: var(--forest); font-size: .8rem; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; }
.recruiter-practice-document .triage-practice-route h2 { margin: .25rem 0 0; font-size: 1.25rem; }
.recruiter-practice-document .triage-practice-route-list { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: .65rem; margin: .75rem 0 0; padding: 0; list-style: none; counter-reset: triage-practice-route-step; }
.recruiter-practice-document .triage-practice-route-step { counter-increment: triage-practice-route-step; min-width: 0; padding: .7rem .7rem .7rem 2.5rem; border: 1px solid var(--line); background: var(--surface); position: relative; }
.recruiter-practice-document .triage-practice-route-step::before { content: counter(triage-practice-route-step); display: inline-grid; position: absolute; top: .65rem; left: .65rem; width: 1.35rem; height: 1.35rem; place-items: center; border: 1px solid var(--forest); border-radius: 50%; color: var(--forest); font-size: .8rem; font-weight: 800; line-height: 1; }
.recruiter-practice-document .continuity-rail { margin-top: 1rem; padding: 1rem; border: 1px solid var(--line); border-left: 4px solid var(--forest); background: var(--surface); }
.recruiter-practice-document .continuity-rail-kicker { margin: 0; color: var(--forest); font-size: .8rem; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; }
.recruiter-practice-document .continuity-rail h2 { margin: .25rem 0 0; font-size: 1.2rem; }
.recruiter-practice-document .continuity-rail-list { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: .75rem; margin: .75rem 0 0; padding: 0; list-style: none; counter-reset: continuity-step; }
.recruiter-practice-document .continuity-step { counter-increment: continuity-step; position: relative; min-width: 0; padding: .75rem .75rem .75rem 2.75rem; border: 1px solid var(--line); background: var(--paper); }
.recruiter-practice-document .continuity-step::before { content: counter(continuity-step); display: inline-grid; position: absolute; top: .75rem; left: .75rem; width: 1.5rem; height: 1.5rem; place-items: center; border: 1px solid var(--forest); border-radius: 50%; color: var(--forest); font-weight: 800; line-height: 1; }
.recruiter-practice-document .continuity-step--current { border-left: 4px solid var(--forest); }
.recruiter-practice-document .continuity-step--pending { border-left: 4px solid var(--decision-term); }
.recruiter-practice-document .continuity-step--blocked { border-left: 4px solid var(--coral); }
.recruiter-practice-document .continuity-rail--feedback-available { border-left-color: var(--coral); }
.recruiter-practice-document .continuity-rail--feedback-available .continuity-step--pending { background: var(--forest-soft); }
.recruiter-practice-document .continuity-rail--feedback-available .continuity-step--blocked { background: var(--coral-soft); }
.recruiter-practice-document .continuity-step-state { display: block; color: var(--muted, #46534d); font-size: .75rem; font-weight: 700; letter-spacing: .06em; text-transform: uppercase; }
.recruiter-practice-document .continuity-step strong { display: block; margin-top: .2rem; }
.recruiter-practice-document .continuity-step p { margin: .35rem 0 0; color: var(--muted, #46534d); font-size: .9rem; }
.recruiter-practice-document .practice-rehearsal-hint { max-width: var(--measure); margin: 0.45rem 0 0; color: #46534d; }
.recruiter-practice-document .practice-rehearsal ol { display: grid; gap: 0.5rem; margin: 0.65rem 0 0; padding-left: 1.5rem; }
.recruiter-practice-document .practice-rehearsal li::marker { color: var(--forest); font-weight: 700; }
.recruiter-practice-document .practice-evidence ul { margin: 0.65rem 0 0; padding-left: 1.25rem; }
.recruiter-practice-document .practice-evidence li + li { margin-top: 0.5rem; }
.recruiter-practice-document .practice-boundary { background: var(--coral-soft); border-color: var(--coral); }
.recruiter-practice-document .practice-boundary p { margin: 0.45rem 0 0; }
.recruiter-practice-document .practice-claim-guardrail {
  max-width: var(--measure);
  padding: 1rem;
  border: 1px solid var(--coral);
  border-left: 4px solid var(--coral);
  background: var(--coral-soft);
}
.recruiter-practice-document .practice-claim-guardrail h2 { font-size: 1.2rem; }
.recruiter-practice-document .practice-claim-guardrail p { margin: .45rem 0 0; }
.recruiter-practice-document .practice-feedback { border-left: 4px solid var(--coral); }
.recruiter-practice-document .practice-decision {
  padding: 1rem;
  border: 1px solid var(--forest);
  border-left: 4px solid var(--decision-term);
  background: var(--forest);
  color: #fff;
}
.recruiter-practice-document .practice-decision h2 { color: #fff; }
.recruiter-practice-document .practice-decision-explanation {
  max-width: var(--measure);
  margin: 0.45rem 0 0;
}
.recruiter-practice-document .practice-decision dl {
  display: grid;
  grid-template-columns: minmax(9rem, 0.35fr) minmax(0, 1fr);
  gap: 0.5rem 1rem;
  min-width: 0;
  margin: 1rem 0 0;
}
.recruiter-practice-document .practice-decision dt {
  min-width: 0;
  color: var(--decision-term);
  font-weight: 700;
}
.recruiter-practice-document .practice-decision dd {
  min-width: 0;
  margin: 0;
  color: #fff;
}
.recruiter-practice-document .visually-hidden {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}
.recruiter-practice-document .practice-feedback ul { margin: 0.65rem 0 0; padding-left: 1.25rem; }
.recruiter-practice-document .practice-feedback li + li { margin-top: 0.5rem; }
.recruiter-practice-document .feedback-label { font-weight: 700; color: var(--ink); }
.recruiter-practice-document .feedback-label--solid { color: var(--ink); }
.recruiter-practice-document .feedback-label--confirm { color: var(--ink); }
.recruiter-practice-document .feedback-label--do_not_assert { color: var(--ink); }
.recruiter-practice-document .feedback-item { padding: 0.55rem 0.65rem; border-left: 3px solid var(--line); }
.recruiter-practice-document .feedback-item--solid { border-left-color: var(--forest); background: var(--forest-soft); }
.recruiter-practice-document .feedback-item--confirm { border-left-color: #854117; background: #f7ecd5; }
.recruiter-practice-document .feedback-item--do_not_assert { border-left-color: var(--coral); background: var(--coral-soft); }

.recruiter-practice-document .practice-footer {
  padding-block: 1rem 2rem;
  border-top: 1px solid var(--forest);
  color: var(--forest);
}

@media screen and (prefers-color-scheme: dark) {
  :root {
    color-scheme: dark;
    --paper: #101521;
    --surface: #182235;
    --ink: #f3f6ff;
    --muted: #b8c4d8;
    --line: #5f718e;
    --forest: #8fc9b0;
    --forest-soft: #223b35;
    --coral: #ff9f8d;
    --coral-soft: #3f282d;
    --gold-soft: #3b301f;
    --decision-term: #f5d68a;
  }
  html,
  .recruiter-practice-document { background: var(--paper); color: var(--ink); }
  .recruiter-practice-document .state-chip--feedback_available { color: var(--coral); background: var(--coral-soft); }
  .recruiter-practice-document .state-chip--awaiting_answer { color: var(--decision-term); background: var(--forest-soft); }
  .recruiter-practice-document .practice-rehearsal,
  .recruiter-practice-document .practice-handoff,
  .recruiter-practice-document .triage-practice-route { background: var(--surface); }
  .recruiter-practice-document .practice-rehearsal--triage-first-answer { background: var(--forest-soft); color: var(--ink); }
  .recruiter-practice-document .practice-rehearsal--triage-first-answer li { background: var(--surface); color: var(--ink); }
  .recruiter-practice-document .practice-next-version { background: var(--forest-soft); color: var(--ink); }
  .recruiter-practice-document .practice-next-version li { background: var(--surface); color: var(--ink); }
  .recruiter-practice-document .practice-next-version-intro,
  .recruiter-practice-document .practice-next-version li p { color: var(--muted); }
  .recruiter-practice-document .screen-readiness { background: var(--surface); }
  .recruiter-practice-document .practice-rehearsal-hint { color: var(--muted); }
  .recruiter-practice-document .practice-next-action,
  .recruiter-practice-document .practice-decision { background: var(--forest-soft); color: var(--ink); }
  .recruiter-practice-document .practice-next-action h2,
  .recruiter-practice-document .practice-decision h2,
  .recruiter-practice-document .practice-decision dd { color: var(--ink); }
  .recruiter-practice-document .feedback-item--confirm {
    background: var(--gold-soft);
    border-left-color: var(--decision-term);
    color: var(--ink);
  }
  .recruiter-practice-document .feedback-label--confirm { color: var(--ink); }
  .recruiter-practice-document .practice-boundary { background: var(--coral-soft); }
  .recruiter-practice-document .practice-claim-guardrail { background: var(--coral-soft); color: var(--ink); }
  .recruiter-practice-document .practice-footer { color: var(--muted); border-color: var(--forest); }
  .recruiter-practice-document .continuity-rail--feedback-available { border-left-color: var(--coral); }
  .recruiter-practice-document .continuity-rail--feedback-available .continuity-step--pending { background: var(--forest-soft); }
  .recruiter-practice-document .continuity-rail--feedback-available .continuity-step--blocked { background: var(--coral-soft); }
}

@keyframes practice-enter {
  from { opacity: 0; transform: translateY(4px); }
  to { opacity: 1; transform: translateY(0); }
}

@media (max-width: 640px) {
  .recruiter-practice-document .practice-shell { width: min(100% - 1rem, 920px); }
  .recruiter-practice-document .practice-header { align-items: start; flex-direction: column; }
  .recruiter-practice-document .state-chip { text-align: left; }
  .recruiter-practice-document .practice-decision dl { grid-template-columns: 1fr; }
  .recruiter-practice-document .screen-readiness-grid { grid-template-columns: 1fr 1fr; }
  .recruiter-practice-document .triage-practice-route-list { grid-template-columns: 1fr; }
  .recruiter-practice-document .continuity-rail-list { grid-template-columns: 1fr; }
  .recruiter-practice-document .practice-claim-guardrail { padding: .875rem; }
  .recruiter-practice-document .practice-rehearsal--triage-first-answer ol { grid-template-columns: 1fr; }
  .recruiter-practice-document .practice-next-version ol { grid-template-columns: 1fr; }
}

@media screen and (max-width: 420px) {
  .recruiter-practice-document .screen-readiness-grid { grid-template-columns: 1fr; }
}

@media (prefers-reduced-motion: reduce) {
  .recruiter-practice-document *,
  .recruiter-practice-document *::before,
  .recruiter-practice-document *::after {
    animation: none !important;
    transition: none !important;
    scroll-behavior: auto !important;
  }
  .recruiter-practice-document .practice-claim-guardrail { transition: none !important; }
  .recruiter-practice-document .practice-rehearsal--triage-first-answer { transition: none !important; }
  .recruiter-practice-document .practice-next-version { transition: none !important; }
}

@media (forced-colors: active) {
  .recruiter-practice-document main:focus-visible { outline-color: Highlight; }
  .recruiter-practice-document .practice-handoff { border: 1px dashed CanvasText; background: Canvas; color: CanvasText; }
  .recruiter-practice-document .practice-handoff h2 { color: CanvasText; }
  .recruiter-practice-document .triage-practice-route { border-color: CanvasText; background: Canvas; color: CanvasText; }
  .recruiter-practice-document .triage-practice-route h2,
  .recruiter-practice-document .triage-practice-route-kicker { color: CanvasText; }
  .recruiter-practice-document .triage-practice-route-step { border-color: CanvasText; background: Canvas; color: CanvasText; }
  .recruiter-practice-document .triage-practice-route-step::before { border-color: CanvasText; color: CanvasText; }
  .recruiter-practice-document .practice-next-action { background: Canvas; color: CanvasText; border-color: CanvasText; }
  .recruiter-practice-document .practice-next-action h2 { color: CanvasText; }
  .recruiter-practice-document .practice-next-action--ready_to_practice,
  .recruiter-practice-document .practice-next-action--awaiting_answer { border-left-color: CanvasText; }
  .recruiter-practice-document .practice-feedback { border: 1px solid CanvasText; background: Canvas; color: CanvasText; }
  .recruiter-practice-document .feedback-item { border: 1px solid CanvasText; background: Canvas; color: CanvasText; }
  .recruiter-practice-document .practice-decision { border: 1px solid CanvasText; background: Canvas; color: CanvasText; }
  .recruiter-practice-document .practice-decision h2,
  .recruiter-practice-document .practice-decision dt,
  .recruiter-practice-document .practice-decision dd { color: CanvasText; }
  .recruiter-practice-document .screen-readiness,
  .recruiter-practice-document .screen-readiness-item { background: Canvas; color: CanvasText; border-color: CanvasText; }
  .recruiter-practice-document .screen-readiness-kicker,
  .recruiter-practice-document .screen-readiness-label,
  .recruiter-practice-document .screen-readiness-state { color: CanvasText; }
  .recruiter-practice-document .continuity-rail,
  .recruiter-practice-document .continuity-step { background: Canvas; color: CanvasText; border-color: CanvasText; }
  .recruiter-practice-document .continuity-rail--feedback-available { border-left-color: CanvasText; }
  .recruiter-practice-document .continuity-rail--feedback-available .continuity-step--pending,
  .recruiter-practice-document .continuity-rail--feedback-available .continuity-step--blocked { background: Canvas; border-left-color: CanvasText; }
  .recruiter-practice-document .continuity-rail-kicker,
  .recruiter-practice-document .continuity-step-state { color: CanvasText; }
  .recruiter-practice-document .continuity-step::before { border-color: CanvasText; color: CanvasText; }
  .recruiter-practice-document .feedback-label--solid,
  .recruiter-practice-document .feedback-label--confirm,
  .recruiter-practice-document .feedback-label--do_not_assert { color: CanvasText; }
  .recruiter-practice-document .practice-claim-guardrail { border-color: CanvasText; background: Canvas; color: CanvasText; }
  .recruiter-practice-document .practice-claim-guardrail h2 { color: CanvasText; }
  .recruiter-practice-document .practice-rehearsal--triage-first-answer { border-color: CanvasText; background: Canvas; color: CanvasText; }
  .recruiter-practice-document .practice-rehearsal--triage-first-answer h2,
  .recruiter-practice-document .practice-rehearsal--triage-first-answer .practice-rehearsal-kicker { color: CanvasText; }
  .recruiter-practice-document .practice-rehearsal--triage-first-answer li { border-color: CanvasText; background: Canvas; color: CanvasText; }
  .recruiter-practice-document .practice-rehearsal--triage-first-answer li::before { border-color: CanvasText; color: CanvasText; }
  .recruiter-practice-document .practice-next-version { border-color: CanvasText; background: Canvas; color: CanvasText; }
  .recruiter-practice-document .practice-next-version h2,
  .recruiter-practice-document .practice-next-version-kicker,
  .recruiter-practice-document .practice-next-version-intro { color: CanvasText; }
  .recruiter-practice-document .practice-next-version li { border-color: CanvasText; background: Canvas; color: CanvasText; }
  .recruiter-practice-document .practice-next-version li::before { border-color: CanvasText; color: CanvasText; }
  .recruiter-practice-document .practice-next-version li p { color: CanvasText; }
  .recruiter-practice-document .practice-footer { color: CanvasText; border-color: CanvasText; }
}

@media (prefers-contrast: more) {
  .recruiter-practice-document .state-chip,
  .recruiter-practice-document .practice-next-action,
  .recruiter-practice-document .practice-handoff,
  .recruiter-practice-document .triage-practice-route,
  .recruiter-practice-document .triage-practice-route-step,
  .recruiter-practice-document .practice-feedback,
  .recruiter-practice-document .feedback-item,
  .recruiter-practice-document .practice-decision { border-width: 2px; }
  .recruiter-practice-document .screen-readiness,
  .recruiter-practice-document .screen-readiness-item,
  .recruiter-practice-document .triage-practice-route,
  .recruiter-practice-document .triage-practice-route-step { border-width: 2px; }
  .recruiter-practice-document .practice-claim-guardrail { border-width: 2px; border-left-width: .5rem; }
  .recruiter-practice-document .practice-rehearsal--triage-first-answer { border-width: 2px; border-left-width: .5rem; }
  .recruiter-practice-document .practice-rehearsal--triage-first-answer li { border-width: 2px; }
  .recruiter-practice-document .practice-next-version { border-width: 2px; border-left-width: .5rem; }
  .recruiter-practice-document .practice-next-version li { border-width: 2px; }
  .recruiter-practice-document .continuity-rail,
  .recruiter-practice-document .continuity-step { border-width: 2px; }
  .recruiter-practice-document .continuity-step::before,
  .recruiter-practice-document .triage-practice-route-step::before { border-width: 2px; }
  .recruiter-practice-document .continuity-rail--feedback-available .continuity-step--pending,
  .recruiter-practice-document .continuity-rail--feedback-available .continuity-step--blocked { border-left-width: .5rem; }
  .recruiter-practice-document .feedback-label { text-decoration: underline; text-decoration-thickness: 0.12em; }
}

@page { size: auto; margin: 14mm; }

@media print {
  .recruiter-practice-document { background: #fff; font-size: 12pt; }
  .recruiter-practice-document .skip-link { display: none !important; }
  .recruiter-practice-document .practice-shell { width: auto; }
  .recruiter-practice-document .practice-session,
  .recruiter-practice-document .practice-context,
  .recruiter-practice-document .practice-prompt,
  .recruiter-practice-document .practice-rehearsal,
  .recruiter-practice-document .screen-readiness,
  .recruiter-practice-document .triage-practice-route,
  .recruiter-practice-document .triage-practice-route-step,
  .recruiter-practice-document .practice-next-action,
  .recruiter-practice-document .practice-evidence,
  .recruiter-practice-document .practice-boundary,
  .recruiter-practice-document .practice-feedback {
    break-inside: avoid;
    page-break-inside: avoid;
  }
  .recruiter-practice-document .practice-handoff,
  .recruiter-practice-document .triage-practice-route,
  .recruiter-practice-document .triage-practice-route-step,
  .recruiter-practice-document .continuity-rail,
  .recruiter-practice-document .continuity-step {
    break-inside: avoid;
    page-break-inside: avoid;
  }
  .recruiter-practice-document .continuity-rail--feedback-available .continuity-step--pending,
  .recruiter-practice-document .continuity-rail--feedback-available .continuity-step--blocked {
    background: transparent;
    border-left-color: var(--ink);
  }
  .recruiter-practice-document .practice-feedback {
    break-after: avoid-page;
  }
  .recruiter-practice-document .practice-decision {
    break-inside: avoid;
    page-break-inside: avoid;
    break-before: avoid-page;
    background: transparent;
    color: var(--ink);
    border: 1px solid var(--ink);
  }
  .recruiter-practice-document .practice-decision h2,
  .recruiter-practice-document .practice-decision dt,
  .recruiter-practice-document .practice-decision dd {
    color: var(--ink);
  }
  .recruiter-practice-document .practice-next-action {
    background: transparent;
    color: var(--ink);
    border: 1px solid var(--ink);
    border-left-width: 4px;
  }
  .recruiter-practice-document .practice-next-action h2 { color: var(--ink); }
  .recruiter-practice-document .practice-session {
    animation: none !important;
    transition: none !important;
    transform: none !important;
  }
  .recruiter-practice-document .practice-session { box-shadow: none; }
  .recruiter-practice-document .practice-footer {
    break-inside: avoid;
    page-break-inside: avoid;
  }
  .recruiter-practice-document .practice-claim-guardrail {
    break-inside: avoid;
    page-break-inside: avoid;
  }
  .recruiter-practice-document .practice-rehearsal--triage-first-answer {
    break-inside: avoid;
    page-break-inside: avoid;
  }
  .recruiter-practice-document .practice-next-version {
    break-inside: avoid;
    page-break-inside: avoid;
  }
}
```

### `plugins/professional-growth-coach/assets/private-recruiter-reply-triage-v1.css`

```css
:root {
  --paper: #f6f4ee;
  --surface: #ffffff;
  --ink: #1b1c1a;
  --forest: #173e30;
  --forest-soft: #dce5e0;
  --coral: #b9513a;
  --coral-soft: #f6e0da;
  --line: #b8c7c0;
  --measure: 72ch;
  --serif: Georgia, "Times New Roman", Times, serif;
  --sans: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
}

.private-recruiter-triage-document { margin: 0; background: var(--paper); color: var(--ink); font-family: var(--sans); font-size: 16px; line-height: 1.55; overflow-wrap: anywhere; }
.private-recruiter-triage-document * { box-sizing: border-box; }
.private-recruiter-triage-document :focus-visible { outline: 3px solid var(--coral); outline-offset: 3px; }
.private-recruiter-triage-document .triage-shell { width: min(920px, calc(100% - 2rem)); margin-inline: auto; }
.private-recruiter-triage-document .skip-link { position: fixed; z-index: 10; top: 0.5rem; left: 0.5rem; transform: translateY(-200%); padding: 0.75rem 1rem; background: var(--surface); border: 1px solid var(--forest); color: var(--forest); font-weight: 700; }
.private-recruiter-triage-document .skip-link:focus { transform: none; }
.private-recruiter-triage-document .triage-header { padding-block: 2rem 1rem; border-bottom: 1px solid var(--forest); }
.private-recruiter-triage-document .triage-kicker { margin: 0; color: var(--forest); font-size: 0.8125rem; font-weight: 700; letter-spacing: 0.09em; text-transform: uppercase; }
.private-recruiter-triage-document h1, .private-recruiter-triage-document h2 { font-family: var(--serif); }
.private-recruiter-triage-document h1 { margin: 0.2rem 0 0; font-size: clamp(2rem, 6vw, 3.25rem); font-style: italic; line-height: 1.04; }
.private-recruiter-triage-document h2 { margin: 0; color: var(--forest); font-size: clamp(1.35rem, 3vw, 1.85rem); line-height: 1.16; }
.private-recruiter-triage-document main { padding-block: 1.5rem 3rem; }
.private-recruiter-triage-document .triage-card { min-width: 0; padding: clamp(1.15rem, 3vw, 2rem); background: var(--surface); border-top: 4px solid var(--forest); box-shadow: 0 1px 0 rgb(23 62 48 / 10%); animation: triage-enter 0.35s ease both; }
.private-recruiter-triage-document .triage-card > * + * { margin-top: 1.5rem; }
.private-recruiter-triage-document .triage-state { display: inline-flex; align-items: center; min-height: 2.25rem; padding: 0.4rem 0.75rem; border: 1px solid currentColor; color: var(--forest); font-size: 0.875rem; font-weight: 700; line-height: 1.2; }
.private-recruiter-triage-document .triage-state--stop { color: #854117; background: #f7ecd5; }
.private-recruiter-triage-document .triage-section { padding: 1rem; border: 1px solid var(--line); }
.private-recruiter-triage-document .triage-section p, .private-recruiter-triage-document .triage-section ul { max-width: var(--measure); }
.private-recruiter-triage-document .triage-section p { margin: 0.55rem 0 0; }
.private-recruiter-triage-document .triage-section ul { margin: 0.65rem 0 0; padding-left: 1.25rem; }
.private-recruiter-triage-document .triage-section li + li { margin-top: 0.5rem; }
.private-recruiter-triage-document .triage-decision, .private-recruiter-triage-document .triage-missing { background: var(--forest-soft); border-left: 4px solid var(--forest); }
.private-recruiter-triage-document .triage-next-safe-action { background: var(--paper); border-left: 4px solid var(--coral); }
.private-recruiter-triage-document .triage-blocked { background: var(--coral-soft); border-color: var(--coral); }
.private-recruiter-triage-document .triage-handoff { border-left: 4px solid var(--forest); }
.private-recruiter-triage-document .triage-handoff-sequence { display: grid; gap: 1rem; margin: 1rem 0 0; padding: 0; list-style: none; counter-reset: handoff-step; }
.private-recruiter-triage-document .triage-handoff-sequence > li { position: relative; counter-increment: handoff-step; min-width: 0; padding-left: 3.25rem; }
.private-recruiter-triage-document .triage-handoff-sequence > li::before { content: counter(handoff-step); display: inline-grid; position: absolute; top: 0; left: 0; width: 2.25rem; height: 2.25rem; place-items: center; border: 1px solid var(--forest); border-radius: 50%; background: var(--forest-soft); color: var(--forest); font-weight: 800; line-height: 1; }
.private-recruiter-triage-document .triage-handoff-step-label { display: block; margin-bottom: 0.45rem; color: var(--forest); font-size: 0.8125rem; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; }
.private-recruiter-triage-document .triage-handoff-readiness { margin-top: 1rem; padding: 0.85rem 1rem; background: var(--paper); border: 1px solid var(--line); }
.private-recruiter-triage-document .triage-handoff-readiness h3 { margin: 0; color: var(--forest); font-family: var(--serif); font-size: 1.1rem; line-height: 1.2; }
.private-recruiter-triage-document .triage-handoff-readiness dl { display: grid; gap: 0.55rem; margin: 0.75rem 0 0; max-width: var(--measure); }
.private-recruiter-triage-document .triage-handoff-readiness-row { display: grid; grid-template-columns: minmax(14rem, 1fr) auto; gap: 0.75rem 1rem; align-items: baseline; }
.private-recruiter-triage-document .triage-handoff-readiness dt { color: var(--forest); font-weight: 700; }
.private-recruiter-triage-document .triage-handoff-readiness dd { margin: 0; font-weight: 700; }
.private-recruiter-triage-document .triage-handoff-focus { margin-top: 1rem; padding: 0.85rem 1rem; background: var(--forest-soft); border-left: 4px solid var(--forest); }
.private-recruiter-triage-document .triage-handoff-focus h3 { margin: 0; color: var(--forest); font-family: var(--serif); font-size: 1.1rem; line-height: 1.2; }
.private-recruiter-triage-document .triage-handoff-focus p { margin: 0.55rem 0 0; max-width: var(--measure); }
.private-recruiter-triage-document .triage-handoff-next-step { margin-top: 1rem; padding: 0.85rem 1rem; background: var(--paper); border-left: 4px solid var(--coral); }
.private-recruiter-triage-document .triage-handoff-next-step h3 { margin: 0; color: var(--forest); font-family: var(--serif); font-size: 1.1rem; line-height: 1.2; }
.private-recruiter-triage-document .triage-handoff-next-step p { margin: 0.55rem 0 0; max-width: var(--measure); }
.private-recruiter-triage-document .triage-handoff-reentry-cue { padding-top: 0.55rem; border-top: 1px solid var(--line); color: var(--forest); }
.private-recruiter-triage-document .triage-handoff-receipt { margin-top: 1rem; padding: 0.85rem 1rem; background: var(--paper); border: 1px solid var(--line); }
.private-recruiter-triage-document .triage-handoff-receipt h3 { margin: 0; color: var(--forest); font-family: var(--serif); font-size: 1.1rem; line-height: 1.2; }
.private-recruiter-triage-document .triage-handoff-receipt h4 { margin: 0.75rem 0 0; color: var(--forest); font-size: 0.8125rem; letter-spacing: 0.08em; text-transform: uppercase; }
.private-recruiter-triage-document .triage-handoff-receipt-group + .triage-handoff-receipt-group { margin-top: 0.8rem; padding-top: 0.8rem; border-top: 1px solid var(--line); }
.private-recruiter-triage-document .triage-handoff-receipt-list { display: grid; gap: 0.45rem; margin: 0.45rem 0 0; max-width: var(--measure); padding: 0; list-style: none; }
.private-recruiter-triage-document .triage-handoff-receipt-list li { padding-left: 1rem; border-left: 2px solid var(--line); }
.private-recruiter-triage-document .triage-handoff-receipt p { margin: 0.75rem 0 0; max-width: var(--measure); }
.private-recruiter-triage-document .triage-handoff-preview { margin-top: 1rem; padding: 1rem; background: var(--forest-soft); border-top: 1px solid var(--line); }
.private-recruiter-triage-document .triage-handoff-preview h3 { margin: 0; color: var(--forest); font-family: var(--serif); font-size: 1.2rem; line-height: 1.2; }
.private-recruiter-triage-document .triage-handoff-preview dl { display: grid; grid-template-columns: minmax(9rem, 0.35fr) minmax(0, 1fr); gap: 0.6rem 1rem; margin: 0.75rem 0 0; max-width: var(--measure); }
.private-recruiter-triage-document .triage-handoff-preview dt { color: var(--forest); font-weight: 700; }
.private-recruiter-triage-document .triage-handoff-preview dd { margin: 0; }
.private-recruiter-triage-document .triage-handoff-answer-path { margin-top: 1rem; padding: 0.85rem 1rem; background: var(--surface); border: 1px solid var(--line); }
.private-recruiter-triage-document .triage-handoff-answer-path h3 { margin: 0; color: var(--forest); font-family: var(--serif); font-size: 1.1rem; line-height: 1.2; }
.private-recruiter-triage-document .triage-handoff-answer-path ol { display: grid; gap: 0.45rem; margin: 0.65rem 0 0; max-width: var(--measure); padding-left: 1.35rem; }
.private-recruiter-triage-document .triage-handoff-answer-path li + li { margin-top: 0.25rem; }
.private-recruiter-triage-document .triage-footer { padding-block: 1rem 2rem; border-top: 1px solid var(--forest); color: var(--forest); }

@media screen and (prefers-color-scheme: dark) {
  :root {
    color-scheme: dark;
    --paper: #101521;
    --surface: #182235;
    --ink: #f3f6ff;
    --muted: #b8c4d8;
    --line: #5f718e;
    --forest: #8fc9b0;
    --forest-soft: #223b35;
    --coral: #ff9f8d;
    --coral-soft: #3f282d;
    --decision-term: #f5d68a;
  }
  html,
  .private-recruiter-triage-document { background: var(--paper); color: var(--ink); }
  .private-recruiter-triage-document .triage-state--stop { color: var(--decision-term); background: var(--forest-soft); }
  .private-recruiter-triage-document .triage-next-safe-action { background: var(--surface); }
  .private-recruiter-triage-document .triage-blocked { background: var(--coral-soft); }
  .private-recruiter-triage-document .triage-handoff-readiness,
  .private-recruiter-triage-document .triage-handoff-next-step,
  .private-recruiter-triage-document .triage-handoff-receipt { background: var(--surface); }
  .private-recruiter-triage-document .triage-footer { color: var(--muted); border-color: var(--forest); }
}

@keyframes triage-enter { from { opacity: 0; transform: translateY(4px); } to { opacity: 1; transform: translateY(0); } }

@media (max-width: 640px) {
  .private-recruiter-triage-document .triage-shell { width: min(100% - 1rem, 920px); }
  .private-recruiter-triage-document .triage-state { align-items: flex-start; }
}

@media (prefers-reduced-motion: reduce) {
  .private-recruiter-triage-document *, .private-recruiter-triage-document *::before, .private-recruiter-triage-document *::after { animation: none !important; transition: none !important; scroll-behavior: auto !important; }
}

@page { size: auto; margin: 14mm; }

@media print {
  .private-recruiter-triage-document { background: #fff; font-size: 12pt; }
  .private-recruiter-triage-document .skip-link { display: none !important; }
  .private-recruiter-triage-document .triage-shell { width: auto; }
  .private-recruiter-triage-document .triage-card, .private-recruiter-triage-document .triage-section { break-inside: avoid; page-break-inside: avoid; }
  .private-recruiter-triage-document .triage-handoff-preview { break-inside: avoid; page-break-inside: avoid; }
  .private-recruiter-triage-document .triage-handoff-answer-path { break-inside: avoid; page-break-inside: avoid; }
  .private-recruiter-triage-document .triage-next-safe-action { break-inside: avoid; page-break-inside: avoid; }
  .private-recruiter-triage-document .triage-handoff-focus { break-inside: avoid; page-break-inside: avoid; }
  .private-recruiter-triage-document .triage-handoff-next-step { break-inside: avoid; page-break-inside: avoid; }
  .private-recruiter-triage-document .triage-handoff-reentry-cue { break-inside: avoid; page-break-inside: avoid; }
  .private-recruiter-triage-document .triage-handoff-receipt { break-inside: avoid; page-break-inside: avoid; }
  .private-recruiter-triage-document .triage-handoff-sequence > li { break-inside: avoid; page-break-inside: avoid; }
  .private-recruiter-triage-document .triage-card {
    box-shadow: none;
    animation: none !important;
    transition: none !important;
    transform: none !important;
  }
  .private-recruiter-triage-document .triage-footer {
    break-inside: avoid;
    page-break-inside: avoid;
  }
}

@media (forced-colors: active) {
  .private-recruiter-triage-document main:focus-visible { outline-color: Highlight; }
  .private-recruiter-triage-document .triage-handoff-sequence > li,
  .private-recruiter-triage-document .triage-handoff-step-label,
  .private-recruiter-triage-document .triage-handoff-readiness,
  .private-recruiter-triage-document .triage-handoff-focus,
  .private-recruiter-triage-document .triage-handoff-next-step,
  .private-recruiter-triage-document .triage-handoff-reentry-cue,
  .private-recruiter-triage-document .triage-next-safe-action,
  .private-recruiter-triage-document .triage-handoff-preview { border-color: CanvasText; }
  .private-recruiter-triage-document .triage-handoff-receipt { border-color: CanvasText; }
  .private-recruiter-triage-document .triage-handoff-answer-path { border-color: CanvasText; background: Canvas; color: CanvasText; }
  .private-recruiter-triage-document .triage-handoff-answer-path h3 { color: CanvasText; }
  .private-recruiter-triage-document .triage-handoff-step-label { color: CanvasText; }
  .private-recruiter-triage-document .triage-handoff-sequence > li::before { border-color: CanvasText; background: Canvas; color: CanvasText; }
  .private-recruiter-triage-document .triage-footer { color: CanvasText; border-color: CanvasText; }
}

@media (prefers-contrast: more) {
  .private-recruiter-triage-document .triage-state {
    border: 2px solid currentColor;
    text-decoration: underline;
    text-decoration-thickness: 0.12em;
    text-underline-offset: 0.15em;
  }
  .private-recruiter-triage-document .triage-next-safe-action,
  .private-recruiter-triage-document .triage-blocked {
    border: 2px solid currentColor;
    border-left-width: 5px;
  }
  .private-recruiter-triage-document .triage-next-safe-action h2,
  .private-recruiter-triage-document .triage-blocked h2 {
    text-decoration: underline;
    text-decoration-thickness: 0.12em;
    text-underline-offset: 0.15em;
  }
}

@media (max-width: 640px) {
  .private-recruiter-triage-document .triage-handoff-preview dl { grid-template-columns: 1fr; gap: 0.25rem; }
  .private-recruiter-triage-document .triage-handoff-preview dd + dt { margin-top: 0.75rem; }
  .private-recruiter-triage-document .triage-handoff-readiness-row { grid-template-columns: 1fr; gap: 0.1rem; }
  .private-recruiter-triage-document .triage-handoff-readiness-row + .triage-handoff-readiness-row { margin-top: 0.55rem; }
}
```

### `plugins/professional-growth-coach/assets/private-recruiter-followthrough-checkpoint-v1.css`

```css
:root { color-scheme: light dark; --ink: #172033; --muted: #536174; --surface: #fff; --accent: #315bd6; --line: #d9dfeb; }
* { box-sizing: border-box; }
html { font: 100%/1.5 system-ui, sans-serif; background: #f4f6fa; color: var(--ink); }
body { margin: 0; }
.skip-link { position: absolute; left: -10000px; top: auto; }
.skip-link:focus { left: 1rem; top: 1rem; padding: .5rem; background: var(--surface); color: var(--ink); }
.skip-link:focus-visible { outline: 3px solid var(--accent); outline-offset: 3px; }
main:focus-visible { outline: 3px solid var(--accent); outline-offset: 4px; }
.checkpoint-shell { max-width: 48rem; margin: 0 auto; padding: clamp(1rem, 4vw, 3rem); }
.checkpoint-card { background: var(--surface); border: 1px solid var(--line); border-radius: 1rem; padding: clamp(1.25rem, 4vw, 2.5rem); box-shadow: 0 .5rem 2rem rgb(23 32 51 / .08); }
.checkpoint-kicker { color: var(--accent); font-size: .8rem; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; }
h1 { margin-top: .25rem; font-size: clamp(1.6rem, 4vw, 2.35rem); }
.checkpoint-facts { display: grid; gap: 1rem; margin: 2rem 0; }
.checkpoint-facts div { border-top: 1px solid var(--line); padding-top: .75rem; }
dt { color: var(--muted); font-size: .85rem; font-weight: 700; }
dd { margin: .15rem 0 0; font-weight: 600; }
.checkpoint-boundary { border-left: .25rem solid var(--accent); margin: 0; padding: .75rem 1rem; color: var(--muted); }
.checkpoint-manual-next-step { min-width: 0; overflow-wrap: anywhere; border-left: .25rem solid var(--accent); margin: 1rem 0 0; padding: .75rem 1rem; color: var(--muted); }
.checkpoint-manual-next-step h2 { margin: 0; font-size: 1rem; }
.checkpoint-manual-next-step p { margin: .35rem 0 0; }
.continuity-rail { margin-top: 1rem; padding: 1rem; border: 1px solid var(--line); border-left: .25rem solid var(--accent); background: var(--surface); }
.continuity-rail-kicker { margin: 0; color: var(--accent); font-size: .8rem; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; }
.continuity-rail h2 { margin: .25rem 0 0; font-size: 1.2rem; }
.continuity-rail-list { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: .75rem; margin: .75rem 0 0; padding: 0; list-style: none; counter-reset: continuity-step; }
.continuity-step { counter-increment: continuity-step; position: relative; min-width: 0; padding: .75rem .75rem .75rem 2.75rem; border: 1px solid var(--line); background: var(--surface); }
.continuity-step::before { content: counter(continuity-step); display: inline-grid; position: absolute; top: .75rem; left: .75rem; width: 1.5rem; height: 1.5rem; place-items: center; border: 1px solid var(--accent); border-radius: 50%; color: var(--accent); font-weight: 800; line-height: 1; }
.continuity-step--current { border-left: .25rem solid var(--accent); }
.continuity-step--pending { border-left: .25rem solid var(--accent); }
.continuity-step--pending::before { background: var(--accent); border-color: var(--accent); color: var(--surface); }
.continuity-step--blocked { border-left: .25rem dashed var(--accent); }
.continuity-step--recorded { border-style: double; border-width: 3px; }
.continuity-step--recorded .continuity-step-state { text-decoration: underline; text-decoration-thickness: .15em; text-underline-offset: .15em; }
.continuity-step-state { display: block; color: var(--muted); font-size: .75rem; font-weight: 700; letter-spacing: .06em; text-transform: uppercase; }
.continuity-step strong { display: block; margin-top: .2rem; }
.continuity-step p { margin: .35rem 0 0; color: var(--muted); font-size: .9rem; }
.checkpoint-footer { max-width: 48rem; margin: 0 auto; padding: 0 clamp(1rem, 4vw, 3rem) 2rem; color: var(--muted); font-size: .85rem; }
.checkpoint-employment-boundary { margin: .5rem 0 0; color: var(--ink); font-weight: 600; }
@media (min-width: 641px) { .checkpoint-facts { grid-template-columns: 1fr 1fr; } }
@media (max-width: 640px) { .continuity-rail-list { grid-template-columns: 1fr; } }
@media screen and (prefers-color-scheme: dark) {
  :root { color-scheme: dark; --ink: #f3f6ff; --muted: #b8c4d8; --surface: #182235; --accent: #8eb2ff; --line: #5f718e; }
  html { background: #101521; }
  .checkpoint-card { box-shadow: 0 .5rem 2rem rgb(0 0 0 / .35); }
  .continuity-step--blocked { border-left-color: var(--accent); border-left-style: dashed; }
}
@page { size: auto; margin: 14mm; }
@media print { html { background: #fff; } .checkpoint-card { box-shadow: none; break-inside: avoid; page-break-inside: avoid; } .checkpoint-manual-next-step { break-inside: avoid; page-break-inside: avoid; } .continuity-rail, .continuity-step { break-inside: avoid; page-break-inside: avoid; } .checkpoint-footer { break-inside: avoid; page-break-inside: avoid; } .skip-link { display: none; } }
@media (prefers-reduced-motion: reduce) { *, *::before, *::after { animation-duration: .01ms !important; transition-duration: .01ms !important; scroll-behavior: auto !important; } }
@media (prefers-contrast: more) { .checkpoint-card { border: 2px solid var(--ink); box-shadow: none; } .checkpoint-facts div { border-top: 2px solid var(--ink); } .checkpoint-boundary { border-left-width: .5rem; color: var(--ink); } .checkpoint-manual-next-step { border-left-width: .5rem; color: var(--ink); } .continuity-rail { border-color: var(--ink); border-width: 2px; color: var(--ink); } .continuity-step, .continuity-step--recorded { border-color: var(--ink); border-width: 2px; color: var(--ink); } .continuity-step--blocked { border-left: .5rem dashed var(--ink); } .continuity-step--recorded { border-style: double; border-width: 3px; } .continuity-step::before { border-width: 2px; } .continuity-step-state, .continuity-step p { color: var(--ink); } }
@media (forced-colors: active) { .checkpoint-card { background: Canvas; color: CanvasText; border: 1px solid CanvasText; } .checkpoint-boundary { color: CanvasText; border: 1px solid CanvasText; border-left-width: .25rem; } .checkpoint-manual-next-step { border: 1px solid CanvasText; border-left-width: .25rem; color: CanvasText; } .continuity-rail, .continuity-step { border: 1px solid CanvasText; color: CanvasText; background: Canvas; } .continuity-step--blocked { border-left: .25rem dashed CanvasText; } .continuity-step--recorded { border-color: CanvasText; color: CanvasText; border-style: double; border-width: 3px; } .continuity-step-state, .continuity-step p { color: CanvasText; } .continuity-step::before { border-color: CanvasText; color: CanvasText; } .continuity-step--pending::before { background: Highlight; border-color: CanvasText; color: HighlightText; } .checkpoint-kicker, .continuity-rail-kicker { color: LinkText; } main:focus-visible { outline-color: Highlight; } .skip-link { background: Canvas; border-color: CanvasText; color: CanvasText; } .skip-link:focus-visible { outline: 2px solid Highlight; outline-offset: 2px; } }
```

### `plugins/professional-growth-coach/assets/private-recruiter-conversion-outcome-v1.css`

```css
:root { color-scheme: light dark; --ink: #172033; --muted: #536174; --surface: #fff; --accent: #315bd6; --line: #d9dfeb; }
* { box-sizing: border-box; }
html { font: 100%/1.5 system-ui, sans-serif; background: #f4f6fa; color: var(--ink); }
body { margin: 0; }
.skip-link { position: absolute; left: -10000px; top: auto; }
.skip-link:focus { left: 1rem; top: 1rem; padding: .5rem; background: var(--surface); color: var(--ink); }
.skip-link:focus-visible { outline: 3px solid var(--accent); outline-offset: 3px; }
main:focus-visible { outline: 3px solid var(--accent); outline-offset: 4px; }
.outcome-shell { max-width: 48rem; margin: 0 auto; padding: clamp(1rem, 4vw, 3rem); }
.outcome-card { background: var(--surface); border: 1px solid var(--line); border-radius: 1rem; padding: clamp(1.25rem, 4vw, 2.5rem); box-shadow: 0 .5rem 2rem rgb(23 32 51 / .08); }
.outcome-kicker { color: var(--accent); font-size: .8rem; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; }
h1 { margin-top: .25rem; font-size: clamp(1.6rem, 4vw, 2.35rem); }
.outcome-facts { display: grid; gap: 1rem; margin: 2rem 0; }
.outcome-facts div { border-top: 1px solid var(--line); padding-top: .75rem; }
dt { color: var(--muted); font-size: .85rem; font-weight: 700; }
dd { margin: .15rem 0 0; font-weight: 600; }
.outcome-boundary { border-left: .25rem solid var(--accent); margin: 0; padding: .75rem 1rem; color: var(--muted); }
.outcome-manual-next-step { min-width: 0; overflow-wrap: anywhere; border-left: .25rem solid var(--accent); margin: 1rem 0 0; padding: .75rem 1rem; color: var(--muted); }
.outcome-manual-next-step h2 { margin: 0; font-size: 1rem; }
.outcome-manual-next-step p { margin: .35rem 0 0; }
.continuity-rail { margin-top: 1rem; padding: 1rem; border: 1px solid var(--line); border-left: .25rem solid var(--accent); background: var(--surface); }
.continuity-rail-kicker { margin: 0; color: var(--accent); font-size: .8rem; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; }
.continuity-rail h2 { margin: .25rem 0 0; font-size: 1.2rem; }
.continuity-rail-list { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: .75rem; margin: .75rem 0 0; padding: 0; list-style: none; counter-reset: continuity-step; }
.continuity-step { counter-increment: continuity-step; position: relative; min-width: 0; padding: .75rem .75rem .75rem 2.75rem; border: 1px solid var(--line); background: var(--surface); }
.continuity-step::before { content: counter(continuity-step); display: inline-grid; position: absolute; top: .75rem; left: .75rem; width: 1.5rem; height: 1.5rem; place-items: center; border: 1px solid var(--accent); border-radius: 50%; color: var(--accent); font-weight: 800; line-height: 1; }
.continuity-step--current { border-left: .25rem solid var(--accent); }
.continuity-step--pending { border-left: .25rem solid var(--accent); }
.continuity-step--pending::before { background: var(--accent); border-color: var(--accent); color: var(--surface); }
.continuity-step--blocked { border-left: .25rem dashed var(--accent); }
.continuity-step--recorded { border-style: double; border-width: 3px; }
.continuity-step--recorded .continuity-step-state { text-decoration: underline; text-decoration-thickness: .15em; text-underline-offset: .15em; }
.continuity-step-state { display: block; color: var(--muted); font-size: .75rem; font-weight: 700; letter-spacing: .06em; text-transform: uppercase; }
.continuity-step strong { display: block; margin-top: .2rem; }
.continuity-step p { margin: .35rem 0 0; color: var(--muted); font-size: .9rem; }
.outcome-footer { max-width: 48rem; margin: 0 auto; padding: 0 clamp(1rem, 4vw, 3rem) 2rem; color: var(--muted); font-size: .85rem; }
.outcome-employment-boundary { margin: .5rem 0 0; color: var(--ink); font-weight: 600; }
@media (min-width: 641px) { .outcome-facts { grid-template-columns: 1fr 1fr; } }
@media (max-width: 640px) { .continuity-rail-list { grid-template-columns: 1fr; } }
@media screen and (prefers-color-scheme: dark) {
  :root { color-scheme: dark; --ink: #f3f6ff; --muted: #b8c4d8; --surface: #182235; --accent: #8eb2ff; --line: #5f718e; }
  html { background: #101521; }
  .outcome-card { box-shadow: 0 .5rem 2rem rgb(0 0 0 / .35); }
  .continuity-step--blocked { border-left-color: var(--accent); border-left-style: dashed; }
}
@page { size: auto; margin: 14mm; }
@media print { html { background: #fff; } .outcome-card { box-shadow: none; break-inside: avoid; page-break-inside: avoid; } .outcome-manual-next-step { break-inside: avoid; page-break-inside: avoid; } .continuity-rail, .continuity-step { break-inside: avoid; page-break-inside: avoid; } .outcome-footer { break-inside: avoid; page-break-inside: avoid; } .skip-link { display: none; } }
@media (prefers-reduced-motion: reduce) { *, *::before, *::after { animation-duration: .01ms !important; transition-duration: .01ms !important; scroll-behavior: auto !important; } }
@media (prefers-contrast: more) { .outcome-card { border: 2px solid var(--ink); box-shadow: none; } .outcome-facts div { border-top: 2px solid var(--ink); } .outcome-boundary { border-left-width: .5rem; color: var(--ink); } .outcome-manual-next-step { border-left-width: .5rem; color: var(--ink); } .continuity-rail { border-color: var(--ink); border-width: 2px; color: var(--ink); } .continuity-step, .continuity-step--recorded { border-color: var(--ink); border-width: 2px; color: var(--ink); } .continuity-step--blocked { border-left: .5rem dashed var(--ink); } .continuity-step--recorded { border-style: double; border-width: 3px; } .continuity-step::before { border-width: 2px; } .continuity-step-state, .continuity-step p { color: var(--ink); } }
@media (forced-colors: active) { .outcome-card { background: Canvas; color: CanvasText; border: 1px solid CanvasText; } .outcome-boundary { color: CanvasText; border: 1px solid CanvasText; border-left-width: .25rem; } .outcome-manual-next-step { border: 1px solid CanvasText; border-left-width: .25rem; color: CanvasText; } .continuity-rail, .continuity-step { border: 1px solid CanvasText; color: CanvasText; background: Canvas; } .continuity-step--blocked { border-left: .25rem dashed CanvasText; } .continuity-step--recorded { border-color: CanvasText; color: CanvasText; border-style: double; border-width: 3px; } .continuity-step-state, .continuity-step p { color: CanvasText; } .continuity-step::before { border-color: CanvasText; color: CanvasText; } .continuity-step--pending::before { background: Highlight; border-color: CanvasText; color: HighlightText; } .outcome-kicker, .continuity-rail-kicker { color: LinkText; } main:focus-visible { outline-color: Highlight; } .skip-link { background: Canvas; border-color: CanvasText; color: CanvasText; } .skip-link:focus-visible { outline: 2px solid Highlight; outline-offset: 2px; } }
```


### `plugins/professional-growth-coach/assets/executive-career-dossier-v2.css`

```css
.reading-path {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  margin-top: 1rem;
  padding: .75rem 1rem;
  border: 1px solid var(--forest-soft);
  background: var(--surface);
}
.reading-path-title {
  color: var(--forest);
  font-family: var(--serif);
  font-size: 1.1rem;
  font-weight: 700;
}
.reading-path ol {
  display: flex;
  flex: 1;
  justify-content: flex-end;
  gap: .5rem;
  margin: 0;
  padding: 0;
  list-style: none;
}
.reading-path a {
  display: inline-flex;
  min-height: 44px;
  align-items: center;
  padding: .55rem .8rem;
  border: 1px solid var(--line);
  color: var(--forest);
  font-weight: 700;
  text-decoration: none;
}
.reading-path a:hover { background: var(--forest-soft); }
.reading-path a[aria-current="location"] { border-color: var(--coral); background: var(--coral-soft); }
.reading-path-active { outline: 2px solid transparent; }
.reading-path-scope { min-width: 0; }

@media screen {
  .reading-path { position: sticky; top: .75rem; z-index: 2; }
}

#section-coverage, #coach-priorities, #market-evidence, #screen-preparation { scroll-margin-top: 5rem; }

.section-coverage-list { display: grid; gap: .75rem; margin: 0; padding: 0; list-style: none; }
.section-coverage-ledger, .coach-priorities, .reading-path { min-width: 0; }
.section-coverage-row { min-width: 0; overflow-wrap: anywhere; }
.section-coverage-row article { padding: 1rem; border: 1px solid var(--forest-soft); background: var(--surface); }
.section-coverage-facts { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: .75rem 1rem; }
.section-coverage-facts dt, .section-coverage-facts dd { min-width: 0; }
.section-coverage-facts dd { margin: 0; }
.section-coverage-row h3 { margin: 0; }
.section-coverage-request { margin: 0; padding-left: .75rem; border-left: 4px solid var(--gold); }
.coach-priority-card { border-top: 4px solid var(--coral); }
.coach-template { margin: 1rem 0 0; padding: 1rem; border-left: 4px solid var(--forest); background: var(--paper); }
.coach-template h4 { margin: 0; }
.coach-template-list { margin: .5rem 0 0; padding-left: 1.25rem; }
.coach-template-field { display: block; font-weight: 700; }
.coach-template-blank { display: block; min-height: 1.5rem; border-bottom: 1px solid var(--line); }
.market-next-investigation { margin-top: 1.25rem; padding: 1rem; border-left: 4px solid var(--gold); background: var(--gold-soft); }
.market-next-investigation h3 { margin: 0; }
.market-next-investigation-facts { display: grid; grid-template-columns: minmax(10rem, .35fr) minmax(0, 1fr); gap: .5rem 1rem; margin: .75rem 0 0; }
.market-next-investigation-facts dt { min-width: 0; font-weight: 700; }
.market-next-investigation-facts dd { min-width: 0; margin: 0; overflow-wrap: anywhere; }
.market-next-investigation-boundary { margin: .9rem 0 0; }

@media screen and (prefers-color-scheme: dark) {
  .section-coverage-row article { border-color: var(--forest); background: var(--surface); color: var(--ink); }
  .coach-template { background: var(--paper); color: var(--ink); }
  .market-next-investigation { background: var(--gold-soft); color: var(--ink); }
}

@media screen and (max-width: 900px) {
  .reading-path { align-items: stretch; flex-direction: column; }
  .reading-path ol { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); justify-content: stretch; }
  .reading-path a { justify-content: center; }
  #section-coverage, #coach-priorities, #market-evidence, #screen-preparation { scroll-margin-top: 11rem; }
}

@media (max-width: 480px) {
  .section-coverage-facts { grid-template-columns: 1fr; }
  .section-coverage-ledger, .section-coverage-list, .section-coverage-row, .section-coverage-row article, .coach-priorities, .coach-priority-card, .coach-template, .reading-path { min-width: 0; }
}

@media screen and (max-width: 640px) {
  .reading-path { align-items: stretch; flex-direction: column; }
  .reading-path ol { display: grid; grid-template-columns: 1fr; justify-content: stretch; }
  .reading-path a { justify-content: center; }
  .section-coverage-facts { grid-template-columns: 1fr; }
  .market-next-investigation-facts { grid-template-columns: 1fr; }
  #section-coverage, #coach-priorities, #market-evidence, #screen-preparation { scroll-margin-top: 18rem; }
}

@media (prefers-reduced-motion: reduce) {
  .section-coverage-row article, .coach-priority-card, .coach-template, .reading-path { animation: none !important; transition: none !important; transform: none !important; scroll-behavior: auto; }
}

@media print {
  .reading-path { position: static; }
  .reading-path, .section-coverage-row, .section-coverage-row article, .coach-priority-card, .coach-template, .market-unavailable-card, .market-next-investigation { break-inside: avoid; page-break-inside: avoid; }
}

@media (forced-colors: active) {
  .reading-path, .section-coverage-row article, .coach-priority-card, .coach-template, .market-unavailable-card, .market-next-investigation { background: Canvas; color: CanvasText; border-color: CanvasText; }
  .reading-path a { color: LinkText; border-color: CanvasText; }
  .reading-path a[aria-current="location"] { background: Canvas; outline: 2px solid Highlight; }
  .section-coverage-request, .coach-template, .market-next-investigation { border-left-color: Highlight; }
  .coach-priority-card { border-top-color: Highlight; }
  main:focus-visible { outline-color: Highlight; }
}

@media (prefers-contrast: more) {
  .reading-path, .section-coverage-row article, .coach-priority-card, .coach-template, .market-unavailable-card, .market-next-investigation { border-width: 2px; }
  .reading-path a { border-width: 2px; border-color: var(--forest); }
  .section-coverage-request, .coach-template, .market-next-investigation { border-left-width: 5px; }
  .coach-priority-card { border-top-width: 5px; }
}
```


### `plugins/professional-growth-coach/assets/recruiter-target-shortlist-v1.css`

```css
:root {
  color-scheme: light dark;
  --canvas: #f5f7f8;
  --surface: #ffffff;
  --ink: #17212b;
  --muted: #5c6975;
  --line: #cbd5dc;
  --accent: #0b6477;
  --continuity-marker-ink: #fff;
  --advance: #157347;
  --clarify: #9a6700;
  --pause: #7057a2;
  --stop: #b42318;
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--canvas); color: var(--ink); font: 16px/1.5 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; overflow-wrap: anywhere; }
.skip-link { position: absolute; left: 1rem; top: -4rem; z-index: 2; padding: .6rem .8rem; color: var(--surface); background: var(--ink); }
.skip-link:focus { top: 1rem; }
:focus-visible { outline: 3px solid var(--accent); outline-offset: 3px; }
main:focus-visible { outline-color: var(--accent); }
.shortlist-shell { width: min(100% - 2rem, 58rem); margin: 0 auto; padding: 3rem 0; }
.shortlist-header { display: grid; grid-template-columns: 1fr auto; gap: .3rem 1rem; align-items: end; margin-bottom: 1.5rem; }
.shortlist-kicker { grid-column: 1 / -1; margin: 0; color: var(--accent); font-size: .75rem; font-weight: 750; letter-spacing: .12em; text-transform: uppercase; }
h1, h2, p { margin-top: 0; }
h1 { margin-bottom: 0; font-size: clamp(2rem, 5vw, 3.25rem); letter-spacing: -.04em; line-height: 1.05; }
.shortlist-date { margin: 0; color: var(--muted); font-variant-numeric: tabular-nums; }
.shortlist-date-label { margin-right: .25rem; font-size: .75rem; font-weight: 750; letter-spacing: .05em; text-transform: uppercase; }
.shortlist-card { background: var(--surface); border: 1px solid var(--line); border-radius: 1rem; box-shadow: 0 .5rem 1.5rem rgb(23 33 43 / 8%); padding: 1.25rem; }
.shortlist-overview { border-top: .35rem solid var(--accent); margin-bottom: 1rem; }
.shortlist-overview h2 { margin-bottom: .4rem; font-size: 1rem; }
.shortlist-goal { max-width: 48rem; font-size: 1.12rem; }
.shortlist-priority-card { margin-top: 1rem; padding: .8rem 1rem; border-left: .35rem solid var(--accent); background: var(--surface); background: color-mix(in srgb, var(--accent) 10%, var(--surface)); }
.shortlist-priority-label { margin: 0; color: var(--muted); font-size: .72rem; font-weight: 750; letter-spacing: .08em; text-transform: uppercase; }
.shortlist-priority-value { margin: .15rem 0 0; font-weight: 750; }
.shortlist-decision-summary { margin-top: 1rem; }
.shortlist-decision-summary h3 { margin: 0 0 .45rem; font-size: .82rem; text-transform: uppercase; letter-spacing: .08em; }
.shortlist-decision-counts { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: .5rem; list-style: none; margin: 0; padding: 0; }
.shortlist-decision-count { display: flex; justify-content: space-between; gap: .5rem; border: 1px solid var(--line); border-top-width: .25rem; padding: .55rem .65rem; }
.shortlist-decision-count span { font-variant-numeric: tabular-nums; font-weight: 750; }
.shortlist-decision-count--advance { border-top-color: var(--advance); }
.shortlist-decision-count--clarify { border-top-color: var(--clarify); }
.shortlist-decision-count--pause { border-top-color: var(--pause); }
.shortlist-decision-count--stop { border-top-color: var(--stop); }
.shortlist-next-step { margin: 1rem 0 1.5rem; padding: 1rem 1.2rem; border-left: .45rem solid var(--accent); background: var(--surface); background: color-mix(in srgb, var(--accent) 10%, var(--surface)); }
.shortlist-next-step--advance { border-left-color: var(--advance); }
.shortlist-next-step--clarify { border-left-color: var(--clarify); }
.shortlist-next-step--pause { border-left-color: var(--pause); }
.shortlist-next-step--stop { border-left-color: var(--stop); }
.shortlist-next-step-kicker { margin: 0 0 .25rem; color: var(--muted); font-size: .75rem; font-weight: 800; letter-spacing: .08em; text-transform: uppercase; }
.shortlist-next-step h2 { margin: 0; font-size: 1.1rem; }
.shortlist-facts { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 1rem; margin: 1rem 0 0; }
.shortlist-facts div, .target-shortlist-facts div { min-width: 0; }
dt { color: var(--muted); font-size: .75rem; font-weight: 750; letter-spacing: .08em; text-transform: uppercase; }
dd { margin: .2rem 0 0; }
ul { margin: .2rem 0 0; padding-left: 1.15rem; }
.target-shortlist-list { display: grid; gap: 1rem; list-style: none; margin: 0; padding: 0; }
.target-shortlist-item { margin: 0; padding: 0; }
.target-shortlist-card { position: relative; border-left: .45rem solid var(--line); }
.target-shortlist-card--advance { border-left-color: var(--advance); }
.target-shortlist-card--clarify { border-left-color: var(--clarify); border-style: solid dashed solid solid; }
.target-shortlist-card--pause { border-left-color: var(--pause); border-style: double solid solid solid; }
.target-shortlist-card--stop { border-left-color: var(--stop); border-style: dotted solid solid solid; }
.target-shortlist-index { margin-bottom: .2rem; color: var(--muted); font-size: .75rem; font-weight: 750; }
.target-shortlist-card h2 { margin-bottom: .35rem; font-size: 1.35rem; }
.target-shortlist-status { margin-bottom: 1rem; color: var(--muted); }
.target-shortlist-status strong { color: var(--ink); }
.target-shortlist-facts { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: .85rem 1.2rem; margin: 0; }
.shortlist-footer { margin-top: 1.5rem; border-top: 1px solid var(--line); color: var(--muted); font-size: .9rem; padding-top: 1rem; }
.shortlist-boundary { margin-bottom: .35rem; }
.shortlist-no-save { margin-bottom: 0; font-weight: 700; }
@media (max-width: 640px) {
  .shortlist-shell { width: min(100% - 1rem, 58rem); padding: 1.5rem 0; }
  .shortlist-header { display: block; }
  .shortlist-date { margin-top: .5rem; }
  .shortlist-facts, .target-shortlist-facts, .shortlist-decision-counts { grid-template-columns: 1fr; }
}
@media (prefers-reduced-motion: reduce) { *, *::before, *::after { scroll-behavior: auto !important; transition: none !important; } }
@media (prefers-contrast: more) {
  :root { --line: #17212b; --muted: #17212b; }
  .shortlist-card, .shortlist-decision-count, .target-shortlist-card { box-shadow: none; border-width: 2px; }
  .continuity-rail { border-width: 2px; }
  .continuity-rail__marker { border-width: 2px; }
}
@media screen and (prefers-color-scheme: dark) {
  :root { --canvas: #10171d; --surface: #17212b; --ink: #ecf2f6; --muted: #adbac4; --line: #3b4a55; --accent: #75d2e4; --continuity-marker-ink: #10232a; --advance: #69d39a; --clarify: #e7bd65; --pause: #c5a7f4; --stop: #ff938a; }
  .shortlist-card { box-shadow: none; }
  .shortlist-priority-card { background: #20313b; }
}
@media screen and (prefers-color-scheme: dark) and (prefers-contrast: more) { :root { --line: #adbac4; } }
@media (forced-colors: active) {
  .skip-link { forced-color-adjust: none; color: Canvas; background: CanvasText; }
  .shortlist-card, .shortlist-next-step { forced-color-adjust: none; border: 2px solid CanvasText; box-shadow: none; }
  .shortlist-priority-card { background: Canvas; color: CanvasText; border-color: CanvasText; }
  .target-shortlist-card--advance, .target-shortlist-card--clarify, .target-shortlist-card--pause, .target-shortlist-card--stop { border-left: .6rem solid CanvasText; }
}
@media print {
  html { color-scheme: light; }
  @page { margin: 1.4cm; }
  body { background: #fff; color: #000; }
  .shortlist-shell { width: 100%; padding: 0; }
  .shortlist-card, .shortlist-next-step { box-shadow: none; break-inside: avoid; page-break-inside: avoid; }
  .target-shortlist-card { break-inside: avoid; page-break-inside: avoid; }
  .shortlist-footer { break-inside: avoid; page-break-inside: avoid; }
  .skip-link { display: none; }
}

.continuity-rail { margin: 1rem 0 1.5rem; padding: .85rem 1rem 1rem; border: 1px solid currentColor; border-radius: .8rem; color: var(--ink); }
.continuity-rail__label { margin: 0 0 .65rem; color: var(--muted); font-size: .76rem; font-weight: 800; letter-spacing: .08em; text-transform: uppercase; }
.continuity-rail ol { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: .4rem; margin: 0; padding: 0; list-style: none; }
.continuity-rail li { display: flex; min-width: 0; gap: .45rem; align-items: flex-start; padding: .55rem .45rem; border-top: .2rem solid transparent; color: var(--muted); }
.continuity-rail li[data-state="current"] { border-top-color: var(--accent); background: var(--canvas); color: var(--ink); }
.continuity-rail__marker { display: grid; flex: 0 0 1.45rem; width: 1.45rem; height: 1.45rem; place-items: center; border: 1px solid currentColor; border-radius: 50%; font-size: .75rem; font-weight: 800; }
.continuity-rail li[data-state="current"] .continuity-rail__marker { background: var(--accent); border-color: var(--accent); color: var(--continuity-marker-ink); }
.continuity-rail__copy { display: grid; gap: .15rem; min-width: 0; font-size: .8rem; line-height: 1.25; }
.continuity-rail__copy strong { overflow-wrap: anywhere; }
.continuity-rail__status { color: var(--accent); font-size: .7rem; font-weight: 800; text-transform: uppercase; }
@media (max-width: 720px) { .continuity-rail ol { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
@media screen and (max-width: 420px) { .continuity-rail ol { grid-template-columns: 1fr; } }
@media (min-width: 721px) and (max-width: 900px) { .continuity-rail ol { grid-template-columns: repeat(3, minmax(0, 1fr)); } }
@media (forced-colors: active) { .continuity-rail, .continuity-rail li { border-color: CanvasText; } .continuity-rail li[data-state="current"] { background: Canvas; } .continuity-rail li[data-state="current"] .continuity-rail__marker { background: Highlight; border-color: CanvasText; color: HighlightText; } }
@media print { .continuity-rail { break-inside: avoid; page-break-inside: avoid; } .continuity-rail ol { grid-template-columns: repeat(2, minmax(0, 1fr)); } .continuity-rail__copy strong { overflow-wrap: normal; hyphens: auto; } }
```

### `plugins/professional-growth-coach/assets/recruiter-target-decision-gate-v1.css`

```css
:root {
  color-scheme: light dark;
  --canvas: #f4f6fa;
  --surface: #ffffff;
  --ink: #172033;
  --muted: #536174;
  --line: #d9dfeb;
  --accent: #315bd6;
  --continuity-marker-ink: #fff;
  --accent-soft: #b8c4d8;
  --dark-canvas: #101521;
  --dark-surface: #182235;
  --dark-ink: #f3f6ff;
  --dark-muted: #b8c4d8;
}
* { box-sizing: border-box; }
html { scroll-behavior: smooth; }
body { margin: 0; background: var(--canvas); color: var(--ink); font: 16px/1.5 -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; overflow-wrap: anywhere; }
.gate-shell { width: min(100% - 2rem, 58rem); margin: 0 auto; padding: 2rem 0 3rem; }
.skip-link { position: absolute; left: .75rem; top: .75rem; transform: translateY(-180%); background: var(--ink); color: var(--surface); padding: .65rem .8rem; font-weight: 700; }
.skip-link:focus { transform: translateY(0); }
.skip-link:focus-visible, main:focus-visible { outline: 3px solid var(--accent); outline-offset: 3px; }
.gate-header { display: grid; grid-template-columns: 1fr auto; gap: .35rem 1rem; align-items: end; margin-bottom: 1.25rem; }
.gate-kicker { grid-column: 1 / -1; margin: 0; color: var(--accent); font-size: .75rem; font-weight: 800; letter-spacing: .12em; text-transform: uppercase; }
h1, h2, h3, p { margin-top: 0; }
h1 { margin-bottom: 0; font-size: clamp(2rem, 5vw, 3.2rem); letter-spacing: -.04em; line-height: 1.05; }
.gate-date { margin: 0; color: var(--muted); font-size: .9rem; }
.gate-date span { font-weight: 700; }
.gate-card { margin-bottom: 1rem; padding: 1.15rem; background: var(--surface); border: 1px solid var(--line); border-radius: 1rem; box-shadow: 0 .5rem 2rem rgb(23 32 51 / .08); }
.gate-next { border-left: .5rem solid var(--accent); }
.gate-state { margin-bottom: .35rem; color: var(--muted); font-size: .75rem; font-weight: 800; letter-spacing: .08em; text-transform: uppercase; }
.gate-next h2 { margin-bottom: .45rem; font-size: clamp(1.5rem, 3vw, 2.1rem); }
.gate-next-copy { max-width: 62ch; margin-bottom: 0; }
.gate-overview-grid { display: grid; grid-template-columns: .6fr 1fr 1.5fr; gap: 1rem; }
dt { color: var(--muted); font-size: .72rem; font-weight: 800; letter-spacing: .08em; text-transform: uppercase; }
dd { margin: .2rem 0 0; }
.gate-overview-grid dd { font-weight: 700; }
.gate-count-summary { margin-top: 1rem; padding-top: 1rem; border-top: 1px solid var(--line); }
.gate-count-summary h3 { margin-bottom: .5rem; font-size: .8rem; letter-spacing: .08em; text-transform: uppercase; }
.gate-counts { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: .5rem; list-style: none; margin: 0; padding: 0; }
.gate-count { display: flex; justify-content: space-between; gap: .5rem; border: 1px solid var(--line); border-top: .3rem solid var(--accent); padding: .55rem .65rem; }
.gate-count span { font-variant-numeric: tabular-nums; font-weight: 800; }
.gate-section-title { margin: 1.75rem 0 .65rem; font-size: 1rem; letter-spacing: .08em; text-transform: uppercase; }
.gate-rows { display: grid; gap: .85rem; margin: 0; padding: 0; list-style: none; counter-reset: gate-row; }
.gate-row { counter-increment: gate-row; position: relative; margin: 0; padding: 1rem 1rem 1rem 3.2rem; background: var(--surface); border: 1px solid var(--line); border-left: .45rem solid var(--accent); border-radius: .85rem; }
.gate-row--clarify { border-left-style: dashed; }
.gate-row--pause { border-left-style: double; }
.gate-row--stop { border-left-style: dotted; }
.gate-row-heading { display: flex; align-items: flex-start; justify-content: space-between; gap: .75rem; }
.gate-row-index { position: absolute; left: 1rem; top: 1rem; color: var(--muted); font-variant-numeric: tabular-nums; font-weight: 800; }
.gate-row-heading-copy { min-width: 0; }
.gate-row-kicker { display: block; margin-bottom: .15rem; color: var(--muted); font-size: .72rem; font-weight: 800; letter-spacing: .08em; text-transform: uppercase; }
.gate-row-target { margin-bottom: .35rem; font-size: 1.15rem; overflow-wrap: anywhere; }
.gate-row-decision { flex: 0 1 auto; max-width: 12rem; padding: .3rem .5rem; border: 1px solid var(--accent); color: var(--accent); font-size: .72rem; font-weight: 800; letter-spacing: .06em; line-height: 1.25; text-align: right; text-transform: uppercase; overflow-wrap: anywhere; }
.gate-row-reason { margin-bottom: .85rem; }
.gate-row-facts { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: .75rem 1rem; margin: 0; }
.gate-footer { margin-top: 1.5rem; padding-top: 1rem; border-top: 1px solid var(--line); color: var(--muted); font-size: .9rem; }
.gate-footer p { margin-bottom: .35rem; }
.gate-footer p:last-child { margin-bottom: 0; font-weight: 700; }
@media (max-width: 640px) {
  .gate-shell { width: min(100% - 1rem, 58rem); padding: 1.5rem 0 2rem; }
  .gate-header { display: block; }
  .gate-date { margin-top: .5rem; }
  .gate-overview-grid, .gate-counts, .gate-row-facts { grid-template-columns: 1fr; }
  .gate-row-heading { display: block; }
  .gate-row-decision { display: inline-block; max-width: none; margin-top: .25rem; text-align: left; }
}
@media screen and (prefers-color-scheme: dark) {
  :root { --canvas: var(--dark-canvas); --surface: var(--dark-surface); --ink: var(--dark-ink); --muted: var(--dark-muted); --line: #5f718e; --accent: #8eb2ff; --continuity-marker-ink: #101a35; --accent-soft: #b8c4d8; }
  .gate-card, .gate-row { box-shadow: none; }
}
@media (prefers-contrast: more) {
  .gate-card, .gate-row { border-width: 2px; }
  .gate-next, .gate-row { border-left-width: .65rem; }
  .continuity-rail { border-width: 2px; }
  .continuity-rail__marker { border-width: 2px; }
}
@media (forced-colors: active) {
  .gate-card, .gate-row { forced-color-adjust: none; border: 2px solid CanvasText; background: Canvas; color: CanvasText; box-shadow: none; }
  .gate-next, .gate-row { border-left: .65rem solid CanvasText; }
  .skip-link { background: CanvasText; color: Canvas; }
  .skip-link:focus-visible, main:focus-visible { outline: 3px solid Highlight; outline-offset: 3px; }
  .gate-row-decision { border-color: CanvasText; color: CanvasText; }
}
@media (prefers-reduced-motion: reduce) { html { scroll-behavior: auto; } }
@media print {
  html { color-scheme: light; }
  body { background: #fff; color: #000; }
  .gate-shell { width: 100%; padding: 0; }
  .gate-card, .gate-row { box-shadow: none; break-inside: avoid; page-break-inside: avoid; }
  .skip-link { display: none; }
}

.continuity-rail { margin: 1rem 0 1.5rem; padding: .85rem 1rem 1rem; border: 1px solid currentColor; border-radius: .8rem; color: var(--ink); }
.continuity-rail__label { margin: 0 0 .65rem; color: var(--muted); font-size: .76rem; font-weight: 800; letter-spacing: .08em; text-transform: uppercase; }
.continuity-rail ol { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: .4rem; margin: 0; padding: 0; list-style: none; }
.continuity-rail li { display: flex; min-width: 0; gap: .45rem; align-items: flex-start; padding: .55rem .45rem; border-top: .2rem solid transparent; color: var(--muted); }
.continuity-rail li[data-state="current"] { border-top-color: var(--accent); background: var(--canvas); color: var(--ink); }
.continuity-rail__marker { display: grid; flex: 0 0 1.45rem; width: 1.45rem; height: 1.45rem; place-items: center; border: 1px solid currentColor; border-radius: 50%; font-size: .75rem; font-weight: 800; }
.continuity-rail li[data-state="current"] .continuity-rail__marker { background: var(--accent); border-color: var(--accent); color: var(--continuity-marker-ink); }
.continuity-rail__copy { display: grid; gap: .15rem; min-width: 0; font-size: .8rem; line-height: 1.25; }
.continuity-rail__copy strong { overflow-wrap: anywhere; }
.continuity-rail__status { color: var(--accent); font-size: .7rem; font-weight: 800; text-transform: uppercase; }
@media (max-width: 720px) { .continuity-rail ol { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
@media screen and (max-width: 420px) { .continuity-rail ol { grid-template-columns: 1fr; } }
@media (min-width: 721px) and (max-width: 900px) { .continuity-rail ol { grid-template-columns: repeat(3, minmax(0, 1fr)); } }
@media (forced-colors: active) { .continuity-rail, .continuity-rail li { border-color: CanvasText; } .continuity-rail li[data-state="current"] { background: Canvas; } .continuity-rail li[data-state="current"] .continuity-rail__marker { background: Highlight; border-color: CanvasText; color: HighlightText; } }
@media print { .continuity-rail { break-inside: avoid; page-break-inside: avoid; } .continuity-rail ol { grid-template-columns: repeat(2, minmax(0, 1fr)); } .continuity-rail__copy strong { overflow-wrap: normal; hyphens: auto; } }
```
