# Theme

## Compact token summary

This plugin has **no shared Tailwind config, CSS module system, theme provider, or global stylesheet**. Each rendered offline artifact inlines exactly one co-located CSS file. There is no `.dark` selector; the compact receipt styles declare `color-scheme: light dark`, while the dossier/practice/triage styles are light documents.

### Palette

| Family | Tokens / values |
| --- | --- |
| Dossier | `--paper #f6f4ee`, `--forest #173e30`, `--ink #1a1a1a`, `--muted #e2ddd6`, `--coral #d96c52`, `--gold #be9338`, `--surface #ffffff`, `--forest-soft #dce5e0`, `--coral-soft #f7e4df`, `--gold-soft #f5ecd8` |
| Practice / triage | `--paper #f6f4ee`, `--surface #ffffff`, `--ink #1b1c1a`, `--forest #173e30`, `--forest-soft #dce5e0`, `--coral #b9513a`, `--coral-soft #f6e0da`, `--line #b8c7c0` |
| Checkpoint / outcome | `--ink #172033`, `--muted #536174`, `--surface #fff`, `--accent #315bd6`, `--line #d9dfeb`; document background `#f4f6fa` |

### Typography and dimensions

- **Serif display:** `Georgia, "Times New Roman", Times, serif`.
- **Sans body:** `-apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif`; compact receipts use `system-ui, sans-serif`.
- **Base:** 16px / 1.55 on dossier, practice, and triage; compact receipts use 100% / 1.5.
- **Display scale:** dossier title `clamp(2rem, 5vw, 3.45rem)`; practice/triage H1 `clamp(2rem, 6vw, 3.25rem)`; compact H1 `clamp(1.6rem, 4vw, 2.35rem)`; H2 usually `clamp(1.35rem, 3vw, 2rem/1.85rem)`.
- **Content measure:** `--measure: 72ch`; main document widths: 1160px dossier, 920px practice/triage, 48rem compact receipts.
- **Spacing:** no named scale; repeated steps range from `.25rem` to `3rem`, with `.5rem`, `.75rem`, `1rem`, `1.5rem`, and `2rem` most common.
- **Radius:** dossier/practice/triage remain square; compact receipt cards use `1rem`.
- **Shadows:** dossier none; practice/triage `0 1px 0 rgb(23 62 48 / 10%)`; compact cards `0 .5rem 2rem rgb(23 32 51 / .08)`.
- **Breakpoints:** dossier: 900px, 680px, 480px; practice/triage: 640px; compact receipts: `min-width: 40rem`. All families include print, reduced-motion, forced-color, and high-contrast handling.

## Raw source dumps

### `plugins/professional-growth-coach/assets/executive-career-dossier-v1.css`

```css
:root {
  --paper: #f6f4ee;
  --forest: #173e30;
  --ink: #1a1a1a;
  --muted: #e2ddd6;
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
.method-list a { word-break: break-word; }

.footer {
  padding-block: 1.5rem 2.5rem;
  border-top: 1px solid var(--forest);
  color: #39443f;
  font-size: 0.875rem;
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

@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation: none !important;
    scroll-behavior: auto !important;
    transition: none !important;
  }
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
  .footer { padding-bottom: 0; }
}

@media (forced-colors: active) {
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
.recruiter-practice-document .practice-feedback {
  padding: 1rem;
  border: 1px solid var(--line);
}

.recruiter-practice-document .practice-prompt { background: var(--forest-soft); border-left: 4px solid var(--forest); }
.recruiter-practice-document .practice-prompt p { margin: 0.55rem 0 0; max-width: var(--measure); font-family: var(--serif); font-size: clamp(1.2rem, 2.5vw, 1.55rem); line-height: 1.25; }
.recruiter-practice-document .practice-rehearsal { background: #f8f7f2; }
.recruiter-practice-document .practice-next-action { background: var(--forest); color: #fff; border: 1px solid var(--forest); padding: 1rem; }
.recruiter-practice-document .practice-next-action h2 { color: #fff; }
.recruiter-practice-document .practice-next-action p { max-width: var(--measure); margin: 0.45rem 0 0; }
.recruiter-practice-document .practice-next-action--ready_to_practice { border-left: 4px solid #9fc4b4; }
.recruiter-practice-document .practice-next-action--awaiting_answer { border-left: 4px solid #dfbf70; }
.recruiter-practice-document .practice-next-action--feedback_available { border-left: 4px solid #e8a28e; }
.recruiter-practice-document .practice-handoff { padding: 1rem; border: 1px dashed var(--forest); background: #f8f7f2; }
.recruiter-practice-document .practice-handoff h2 { font-size: 1.25rem; }
.recruiter-practice-document .practice-handoff p { max-width: var(--measure); margin: 0.45rem 0 0; }
.recruiter-practice-document .practice-handoff--dossier { border-left: 4px solid var(--forest); }
.recruiter-practice-document .practice-handoff--reply { border-left: 4px solid var(--coral); }
.recruiter-practice-document .practice-rehearsal-hint { max-width: var(--measure); margin: 0.45rem 0 0; color: #46534d; }
.recruiter-practice-document .practice-rehearsal ol { display: grid; gap: 0.5rem; margin: 0.65rem 0 0; padding-left: 1.5rem; }
.recruiter-practice-document .practice-rehearsal li::marker { color: var(--forest); font-weight: 700; }
.recruiter-practice-document .practice-evidence ul { margin: 0.65rem 0 0; padding-left: 1.25rem; }
.recruiter-practice-document .practice-evidence li + li { margin-top: 0.5rem; }
.recruiter-practice-document .practice-boundary { background: var(--coral-soft); border-color: var(--coral); }
.recruiter-practice-document .practice-boundary p { margin: 0.45rem 0 0; }
.recruiter-practice-document .practice-feedback { border-left: 4px solid var(--coral); }
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
.recruiter-practice-document .feedback-label { font-weight: 700; }
.recruiter-practice-document .feedback-label--solid { color: var(--forest); }
.recruiter-practice-document .feedback-label--confirm { color: #854117; }
.recruiter-practice-document .feedback-label--do_not_assert { color: var(--coral); }
.recruiter-practice-document .feedback-item { padding: 0.55rem 0.65rem; border-left: 3px solid var(--line); }
.recruiter-practice-document .feedback-item--solid { border-left-color: var(--forest); background: var(--forest-soft); }
.recruiter-practice-document .feedback-item--confirm { border-left-color: #854117; background: #f7ecd5; }
.recruiter-practice-document .feedback-item--do_not_assert { border-left-color: var(--coral); background: var(--coral-soft); }

.recruiter-practice-document .practice-footer {
  padding-block: 1rem 2rem;
  border-top: 1px solid var(--forest);
  color: var(--forest);
}

@keyframes practice-enter {
  from { opacity: 0; transform: translateY(4px); }
  to { opacity: 1; transform: translateY(0); }
}

@media (max-width: 640px) {
  .recruiter-practice-document .practice-shell { width: min(100% - 1rem, 920px); }
  .recruiter-practice-document .practice-header { align-items: start; flex-direction: column; }
  .recruiter-practice-document .state-chip { text-align: left; }
}

@media (prefers-reduced-motion: reduce) {
  .recruiter-practice-document *,
  .recruiter-practice-document *::before,
  .recruiter-practice-document *::after {
    animation: none !important;
    transition: none !important;
    scroll-behavior: auto !important;
  }
}

@media (forced-colors: active) {
  .recruiter-practice-document .practice-handoff { border: 1px dashed CanvasText; background: Canvas; color: CanvasText; }
  .recruiter-practice-document .practice-handoff h2 { color: CanvasText; }
  .recruiter-practice-document .practice-next-action--ready_to_practice,
  .recruiter-practice-document .practice-next-action--awaiting_answer,
  .recruiter-practice-document .practice-next-action--feedback_available { border-left-color: CanvasText; }
  .recruiter-practice-document .feedback-label--solid,
  .recruiter-practice-document .feedback-label--confirm,
  .recruiter-practice-document .feedback-label--do_not_assert { color: CanvasText; }
  .recruiter-practice-document .feedback-item--solid,
  .recruiter-practice-document .feedback-item--confirm,
  .recruiter-practice-document .feedback-item--do_not_assert { border-left-color: CanvasText; background: Canvas; }
}

@media (prefers-contrast: more) {
  .recruiter-practice-document .state-chip,
  .recruiter-practice-document .practice-next-action,
  .recruiter-practice-document .practice-handoff,
  .recruiter-practice-document .practice-feedback,
  .recruiter-practice-document .feedback-item { border-width: 2px; }
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
  .recruiter-practice-document .practice-next-action,
  .recruiter-practice-document .practice-evidence,
  .recruiter-practice-document .practice-boundary,
  .recruiter-practice-document .practice-feedback {
    break-inside: avoid;
    page-break-inside: avoid;
  }
  .recruiter-practice-document .practice-handoff {
    break-inside: avoid;
    page-break-inside: avoid;
  }
  .recruiter-practice-document .practice-session { box-shadow: none; }
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
.private-recruiter-triage-document .triage-footer { padding-block: 1rem 2rem; border-top: 1px solid var(--forest); color: var(--forest); }

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
  .private-recruiter-triage-document .triage-next-safe-action { break-inside: avoid; page-break-inside: avoid; }
  .private-recruiter-triage-document .triage-handoff-focus { break-inside: avoid; page-break-inside: avoid; }
  .private-recruiter-triage-document .triage-handoff-next-step { break-inside: avoid; page-break-inside: avoid; }
  .private-recruiter-triage-document .triage-handoff-reentry-cue { break-inside: avoid; page-break-inside: avoid; }
  .private-recruiter-triage-document .triage-handoff-receipt { break-inside: avoid; page-break-inside: avoid; }
  .private-recruiter-triage-document .triage-handoff-sequence > li { break-inside: avoid; page-break-inside: avoid; }
  .private-recruiter-triage-document .triage-card { box-shadow: none; }
}

@media (forced-colors: active) {
  .private-recruiter-triage-document .triage-handoff-sequence > li,
  .private-recruiter-triage-document .triage-handoff-step-label,
  .private-recruiter-triage-document .triage-handoff-readiness,
  .private-recruiter-triage-document .triage-handoff-focus,
  .private-recruiter-triage-document .triage-handoff-next-step,
  .private-recruiter-triage-document .triage-handoff-reentry-cue,
  .private-recruiter-triage-document .triage-next-safe-action,
  .private-recruiter-triage-document .triage-handoff-preview { border-color: CanvasText; }
  .private-recruiter-triage-document .triage-handoff-receipt { border-color: CanvasText; }
  .private-recruiter-triage-document .triage-handoff-step-label { color: CanvasText; }
  .private-recruiter-triage-document .triage-handoff-sequence > li::before { border-color: CanvasText; background: Canvas; color: CanvasText; }
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
.checkpoint-shell { max-width: 48rem; margin: 0 auto; padding: clamp(1rem, 4vw, 3rem); }
.checkpoint-card { background: var(--surface); border: 1px solid var(--line); border-radius: 1rem; padding: clamp(1.25rem, 4vw, 2.5rem); box-shadow: 0 .5rem 2rem rgb(23 32 51 / .08); }
.checkpoint-kicker { color: var(--accent); font-size: .8rem; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; }
h1 { margin-top: .25rem; font-size: clamp(1.6rem, 4vw, 2.35rem); }
.checkpoint-facts { display: grid; gap: 1rem; margin: 2rem 0; }
.checkpoint-facts div { border-top: 1px solid var(--line); padding-top: .75rem; }
dt { color: var(--muted); font-size: .85rem; font-weight: 700; }
dd { margin: .15rem 0 0; font-weight: 600; }
.checkpoint-boundary { border-left: .25rem solid var(--accent); margin: 0; padding: .75rem 1rem; color: var(--muted); }
.checkpoint-footer { max-width: 48rem; margin: 0 auto; padding: 0 clamp(1rem, 4vw, 3rem) 2rem; color: var(--muted); font-size: .85rem; }
@media (min-width: 40rem) { .checkpoint-facts { grid-template-columns: 1fr 1fr; } }
@media print { html { background: #fff; } .checkpoint-card { box-shadow: none; } .skip-link { display: none; } }
@media (prefers-reduced-motion: reduce) { *, *::before, *::after { animation-duration: .01ms !important; transition-duration: .01ms !important; scroll-behavior: auto !important; } }
@media (prefers-contrast: more) { .checkpoint-card { border: 2px solid var(--ink); box-shadow: none; } .checkpoint-facts div { border-top: 2px solid var(--ink); } .checkpoint-boundary { border-left-width: .5rem; color: var(--ink); } }
@media (forced-colors: active) { .checkpoint-card, .checkpoint-boundary { border: 1px solid CanvasText; } .checkpoint-kicker { color: LinkText; } }
```

### `plugins/professional-growth-coach/assets/private-recruiter-conversion-outcome-v1.css`

```css
:root { color-scheme: light dark; --ink: #172033; --muted: #536174; --surface: #fff; --accent: #315bd6; --line: #d9dfeb; }
* { box-sizing: border-box; }
html { font: 100%/1.5 system-ui, sans-serif; background: #f4f6fa; color: var(--ink); }
body { margin: 0; }
.skip-link { position: absolute; left: -10000px; top: auto; }
.skip-link:focus { left: 1rem; top: 1rem; padding: .5rem; background: var(--surface); color: var(--ink); }
.outcome-shell { max-width: 48rem; margin: 0 auto; padding: clamp(1rem, 4vw, 3rem); }
.outcome-card { background: var(--surface); border: 1px solid var(--line); border-radius: 1rem; padding: clamp(1.25rem, 4vw, 2.5rem); box-shadow: 0 .5rem 2rem rgb(23 32 51 / .08); }
.outcome-kicker { color: var(--accent); font-size: .8rem; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; }
h1 { margin-top: .25rem; font-size: clamp(1.6rem, 4vw, 2.35rem); }
.outcome-facts { display: grid; gap: 1rem; margin: 2rem 0; }
.outcome-facts div { border-top: 1px solid var(--line); padding-top: .75rem; }
dt { color: var(--muted); font-size: .85rem; font-weight: 700; }
dd { margin: .15rem 0 0; font-weight: 600; }
.outcome-boundary { border-left: .25rem solid var(--accent); margin: 0; padding: .75rem 1rem; color: var(--muted); }
.outcome-footer { max-width: 48rem; margin: 0 auto; padding: 0 clamp(1rem, 4vw, 3rem) 2rem; color: var(--muted); font-size: .85rem; }
@media (min-width: 40rem) { .outcome-facts { grid-template-columns: 1fr 1fr; } }
@media print { html { background: #fff; } .outcome-card { box-shadow: none; } .skip-link { display: none; } }
@media (prefers-reduced-motion: reduce) { *, *::before, *::after { animation-duration: .01ms !important; transition-duration: .01ms !important; scroll-behavior: auto !important; } }
@media (prefers-contrast: more) { .outcome-card { border: 2px solid var(--ink); box-shadow: none; } .outcome-facts div { border-top: 2px solid var(--ink); } .outcome-boundary { border-left-width: .5rem; color: var(--ink); } }
@media (forced-colors: active) { .outcome-card, .outcome-boundary { border: 1px solid CanvasText; } .outcome-kicker { color: LinkText; } }
```
