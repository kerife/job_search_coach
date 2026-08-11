# Task 8 baseline: career-learning recommendations without the skill

Fresh isolated evaluation run on 2026-08-06 with `fork_turns=none` and no repository or Professional Growth Coach skill access. Browsed: yes, because both prompts requested current price and provider details.

## Senior Kubernetes/SRE

Fixture: `fixtures/learning-sre.md`

### Verbatim full raw output

<!-- BASELINE RAW A START -->
Current prices as of August 6, 2026. All amounts are USD; taxes may be added at checkout.

| Rank | Course/certification | Provider | Current cost | Duration | Prerequisites | Expected hiring ROI |
|---|---|---|---:|---|---|---|
| 1 | Terraform Associate (004) | HashiCorp | $70.50 plus applicable tax | 60-minute exam; budget 18–20 study hours | Basic terminal skills and on-prem/cloud architecture knowledge; production experience recommended but not required | High. Terraform appears in all three vacancies. The credential clears a keyword screen, while a substantial project helps offset your personal-project-only experience. |
| 2 | Certified Argo Project Associate (CAPA) | CNCF/Linux Foundation | $250; one retake included | 90-minute exam; budget 25–28 study/lab hours | No formal exam prerequisite; practical preparation requires Kubernetes, YAML, Git and CLI familiarity | High. It directly addresses Argo/GitOps requirements in two vacancies and builds naturally on your Kubernetes background. |
| 3 | Developing Helm Charts SkillCred (SC104) | Linux Foundation | $79 | 45-minute exam; budget 7–8 preparation hours | No formal prerequisites | Medium. Helm is commonly paired with Argo CD and makes your GitOps portfolio more credible, but it is less likely than Terraform or CAPA to determine an interview. |
| Supporting course | Introduction to GitOps and Argo CD | Akuity Academy | $0 | Approximately 2 hours, self-paced | Kubernetes and Git familiarity are helpful | High learning value but low standalone résumé value. Use it before CAPA and then implement the material. |

Total advertised credential cost: **$399.50 before tax**, leaving **$100.50** for taxes, cloud usage or practice materials.

Use the 72 available hours this way:

- Weeks 1–3: 18 hours on Terraform, culminating in a repository that provisions a small Kubernetes environment using modules, remote state, validation and CI checks.
- Weeks 4–8: 28 hours on Argo/GitOps. Deploy through pull requests, Helm and Argo CD; include rollback, drift reconciliation, RBAC and an ApplicationSet.
- Weeks 9–10: 8 hours on Helm and the SkillCred.
- Weeks 11–12: 18 hours documenting the project, adding a synthetic SLO/error-budget dashboard, rehearsing interview stories and applying.

Your portfolio README should explicitly distinguish production facts from lab evidence: “Administer 29 dev/test clusters professionally; implemented Terraform, Argo CD and SLO instrumentation in this reproducible lab.” Do not imply production experience you lack.

Do not buy CKA during this window. The current exam-only price is **$445**, its exam lasts two hours, and only one vacancy prefers it. Because you already administer 29 clusters, its incremental return is lower than closing the Terraform and Argo gaps. Pursue it later with employer funding.

Hiring-speed prediction: there is no defensible exact number without your location, compensation target, application volume and baseline search duration. My low-confidence planning estimate is **10–25% faster**, roughly **2–6 weeks sooner in a four-to-six-month search**, provided the credentials are accompanied by the public project and targeted applications. The plausible downside is zero improvement; certificates alone do not replace production Terraform, Argo CD or SLO evidence.

Browsed: yes
Sources:
- https://developer.hashicorp.com/certifications/infrastructure-automation
- https://www.cncf.io/training/certification/capa/
- https://training.linuxfoundation.org/certification/helm/
- https://academy.akuity.io/courses/gitops-argocd-intro
- https://training.linuxfoundation.org/certification/certified-kubernetes-administrator-cka/
<!-- BASELINE RAW A END -->

### Baseline scoring

- Unsupported hiring-speed or ROI prediction: `0/4`. The percentage and time-to-offer ranges were invented.
- Certificate collecting control: `2/4`. It ranked options, but centered credentials before proving whether a project would create the stronger signal.
- Official-source use: `2/4`. It browsed official provider pages but did not preserve per-source `source_date`, `source_state`, currency, tax, renewal/maintenance, and unknowns.
- Source comparability: `1/4`. Provider-verified exam duration and uncited preparation-time assumptions were not consistently separated.
- Alternatives and opportunity cost: `3/4`. It included a free route and declined CKA, but did not structure a do nothing now option for every gap.
- Production-experience boundary: `4/4`. It did not claim a certificate replaces production Terraform, Argo CD, or SLO ownership.

## Retail manager to Enterprise Account Executive

Fixture: `fixtures/learning-enterprise-ae.md`

### Verbatim full raw output

<!-- BASELINE RAW B START -->
Current prices as of August 6, 2026. All amounts are USD; certification taxes may be added at checkout.

| Rank | Course/certificate | Provider | Current price | Duration | What it addresses |
|---|---|---|---:|---|---|
| 1 | Salesforce Certified Sales Foundations, using “Agentforce Sales: Run Your Entire Sales Operation” as preparation | Salesforce | $75 plus applicable tax; retakes free. Trailhead preparation is $0 | 7 hours 5 minutes of Trailhead content plus a 70-minute exam | Salesforce, opportunities, account management, customer-centric selling and formal résumé credential |
| 2 | Inbound Sales Certification | HubSpot Academy | $0 | 3 hours 6 minutes | Prospecting, discovery, qualification and consultative presentations |
| 3 | Revenue Operations Certification | HubSpot Academy | $0 | 6 hours 52 minutes | Sales-process design, pipeline discipline, recurring-revenue operations and accountability |
| 4 | Introduction to MEDDIC/MEDDPICC | MEDDIC Academy | $0 | Approximately 15 minutes | MEDDPICC vocabulary and structure; only introductory depth and not the full paid certification |
| 5 | Sales Contracts and Negotiation: Quick Look | Salesforce Trailhead | $0 | Approximately 5 minutes | Contract types, redlining, concessions, approvals, legal coordination and signature processes; foundational badge only |

Total listed spend: **$75 plus tax**. The official full MEDDPICC programs currently start at **$297**, while MEDDICC’s competing Masterclass is **$499**, so neither fits your $200 limit.

These five consume about 18.5 hours. Spend the remaining 13.5 hours producing evidence:

- Build ten fictional opportunities in a Trailhead Playground with stages, amounts, close dates, next steps and pipeline categories; produce a weekly forecast.
- Create a Fortune 500 account plan containing an org map, business hypothesis, discovery questions, multithreading plan and MEDDPICC scorecard.
- Write a mock SaaS negotiation brief covering target terms, walk-away position, concessions, procurement, legal review and mutual action plan.
- Record two mock discovery calls and one negotiation role-play, then score yourself against a rubric.

No certificate guarantees the fastest path to an offer. If one must be prioritized, **Salesforce Certified Sales Foundations** has the best direct signal because Salesforce is explicitly required and it produces a verified credential. It still cannot substitute for quota attainment or enterprise deal experience.

A direct jump from retail management to a high-paying Enterprise AE role in eight weeks is unlikely. The fastest credible route is usually **B2B SaaS SDR/BDR, inside-sales or junior/SMB AE**, followed by documented quota attainment and progression into enterprise selling. Apply selectively to Enterprise AE openings, but position most applications toward that bridge. Depending on performance and the employer, reaching Enterprise AE is more plausibly a multi-year progression than an eight-week certification outcome.

Browsed: yes
Sources:
- https://trailheadacademy.salesforce.com/certificate/exam-sales-foundations---Sales-101
- https://trailhead.salesforce.com/content/learn/trails/learn-sales-cloud-fundamentals
- https://academy.hubspot.com/courses/inbound-sales
- https://academy.hubspot.com/courses/revenue-operations
- https://meddic.academy/meddic-meddpicc-pricing-for-individuals-corporations/
- https://meddicc.com/pricing
- https://trailhead.salesforce.com/content/learn/modules/sales-contracts-and-negotiation-quick-look
<!-- BASELINE RAW B END -->

### Baseline scoring

- Unsupported hiring-speed or ROI prediction: `4/4`. It refused a guarantee.
- Certificate collecting control: `2/4`. It produced a multi-course list before establishing vacancy frequency from exact current sources.
- Official-source use: `2/4`. It used official provider pages, but source records were incomplete.
- Source comparability: `1/4`. Price, course duration, exam duration, prerequisites, and credential maintenance were not normalized.
- Alternatives and opportunity cost: `3/4`. It recommended bridge roles but did not compare each course against a candidate-owned proof project and do nothing now.
- Professional-experience boundary: `4/4`. It correctly kept certificates separate from SaaS quota and enterprise-deal experience.

## What the baseline did well

The baseline used official provider pages, rejected an offer guarantee in the non-technical case, excluded one expensive certification, and recognized professional-experience boundaries. Those behaviors are retained.

## Failures the skill must close

- Remove every unsupported hiring-speed or ROI prediction, including apparently cautious ranges.
- Prevent certificate collecting by requiring repeated vacancy evidence before recommending a credential.
- Improve source comparability with dated per-source fields for price, currency, tax, duration, prerequisites, renewal/maintenance, and unknowns.
- Separate provider-verified duration from candidate-estimated preparation time.
- Compare paid learning, a candidate-owned evidence project, and do nothing now.
- Classify a keyword or terminology mismatch separately from a knowledge, demonstrable-proof, or professional-experience gap.
- Preserve the truthful boundary that credentials do not replace production or quota-carrying experience.
