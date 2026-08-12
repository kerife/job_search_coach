# Task 4 blinded no-skill baselines

Fresh agents were forbidden from reading the repository, plan, skills, browser, or prior conversation. Preserve these scenario/response pairs verbatim in `tests/evals/baseline/market.md`, then score stale/unsupported ranking, geography/currency/compensation-basis mixing, unrealistic transitions, unlabeled uncertainty, and unsupported time-to-offer claims.

## Senior technical candidate

### Scenario

Candidate tech-042 is a synthetic senior technical candidate with an infrastructure and reliability focus. Candidate reports non-production platform operations and troubleshooting; employer, location, language, scale, management history, tools, and production reliability metrics are not supplied. Candidate wants to compare realistic role and work-arrangement scenarios without ranking pay before comparable market evidence exists. Rank the five best role paths, give compensation ranges, demand, time-to-transition, gaps, and a recommended path. Be decisive about which role pays most and could produce a better offer fastest.

### Verbatim output

Candidate tech-042 should target **Senior Platform Engineer / Kubernetes Infrastructure Engineer** first. It is the best combination of credible fit, strong international pay, and short transition time. Do not lead with “Principal SRE”: the title and non-production scope will invite scrutiny around incident ownership, SLOs, and measured reliability outcomes.

| Rank | Role path | Realistic compensation | Demand / transition | Main gaps |
|---|---|---:|---|---|
| 1 | **Senior Platform Engineer / Kubernetes Infrastructure Engineer** | Mexico: MX$1.2M–2.0M/yr; international remote/EOR or contractor: **US$80k–125k** | High demand; **1–3 months** with a sharp resume | Terraform depth; production platform ownership; observability |
| 2 | **Senior DevOps Engineer (Kubernetes / hybrid-cloud)** | Mexico: MX$950k–1.6M; international: **US$70k–115k** | Highest interview volume; **0–2 months** | Terraform/Ansible operational fluency; one major cloud |
| 3 | **Senior SRE / Reliability Engineer** | Mexico: MX$1.1M–1.8M; international: **US$95k–145k** initially | Good demand, but credibility gap means **3–6 months** | Production on-call, SLO/error budgets, MTTR/MTTD and incident metrics |
| 4 | **OpenShift / Red Hat Platform Engineer or Consultant** | Mexico: MX$1.1M–1.8M; international: **US$85k–135k** | Niche but differentiated; **1–4 months** | Enterprise automation, Red Hat certification/consulting polish |
| 5 | **Infrastructure Software Engineer / Internal Developer Platform Engineer** | Mexico: MX$1.3M–2.1M; international: **US$100k–150k** | Strong upside; **4–8 months** | Stronger Go/Java or production-grade Python, platform product design, public cloud |

**What pays most:** Staff/Principal SRE at a US company has the highest ceiling—roughly US$160k–240k base, plus equity—but is not a realistic immediate move without production reliability evidence. Current disclosed US-remote SRE data centers around US$174k base for senior roles, while staff roles center around US$211k; those jobs commonly require Terraform, Kubernetes, cloud, and demonstrated SRE practice. [RemoteFront’s current US-remote SRE data](https://www.remotefront.com/remote-sre-jobs/united-states)

**Best better offer fastest:** Senior Platform Engineer or Senior DevOps Engineer at a US/Canadian/EU company that hires in Mexico. Aim for **US$90k–120k**. The candidate’s reported platform experience should be described generically and should not be presented as production reliability ownership.

The existing profile supports this pitch: “built and operated developer-platform Kubernetes estates across heterogeneous infrastructure; automated cluster provisioning and root-cause analysis; enabled engineering teams.” It should avoid calling unconfirmed non-production platform scope “production scale” or claiming reliability outcomes not measured.

Fastest gap-closing sequence:

1. Make Terraform operational: a real module-based project with remote state, IAM/secrets, networking, Kubernetes deployment, CI validation, and a short architecture write-up.
2. Add one public cloud deeply—**AWS** is the broadest market signal; OCI experience makes cloud transition credible, but it is not a substitute for AWS/GCP/Azure.
3. Build practical observability/SRE evidence: Prometheus/Grafana, alerts, runbooks, a simulated incident, SLI/SLO and error-budget examples.
4. Learn Ansible to “write and own,” not merely read/debug.
5. Apply under Senior Platform Engineer, Kubernetes Infrastructure Engineer, Senior DevOps Engineer, and OpenShift Platform Engineer titles; reserve SRE applications for companies willing to accept platform-first experience.

For Mexico-local compensation, published 2026 benchmarks place senior DevOps materially below international-product-company pay, while a location unconfirmed remote DevOps median is reported around US$76.9k. [CodersLink Mexico report](https://salaries.coderslink.com/), [Plane’s Mexico benchmark](https://plane.com/salaries/devops-engineer/mexico) A current Mexico-targeted Senior DevOps posting, for example, lists MX$950k–1.3M plus equity. [Peek posting](https://jobs.ashbyhq.com/peek/58b9bb30-2bf9-46ab-afab-f6338131bedc)

## Non-technical operations candidate

### Scenario

Candidate ops-017 is location unconfirmed with eight years in retail operations and a business-administration degree. Candidate reports scheduling, inventory, vendor coordination, customer service, and team leadership but provides no metrics, team size, systems, English level, compensation target, work authorization, or remote-work history. No technical or cloud background. Candidate wants to compare realistic role and work-arrangement scenarios without ranking pay before comparable market evidence exists. Rank five role paths, give compensation ranges, demand, time-to-transition, gaps, and a recommended path. Be decisive about which role pays most and could produce a better offer fastest.

### Verbatim output

1. **Multi-site Retail Operations Manager / Area Manager — best fast move**
   - **Mexico pay:** MXN 45k–80k/month gross; MXN 80k–110k+ only with a strong multi-unit record and national brands.
   - **Demand:** High and steady in retail, food service, last-mile, franchise, and consumer services.
   - **Transition:** 0–3 months.
   - **Gaps:** Need quantified scope: stores/locations, headcount, sales or cost responsibility, inventory shrink, turnover, service results, and scheduling systems.
   - **Verdict:** This is the role most likely to produce a better offer fastest because it directly matches the reported experience.

2. **Supply Chain / Inventory Planning Manager**
   - **Mexico pay:** MXN 55k–100k/month gross; MXN 100k–130k+ in large manufacturing, automotive, or sophisticated e-commerce organizations.
   - **Demand:** High, especially around nearshoring, manufacturing, distribution, and e-commerce.
   - **Transition:** 6–12 months.
   - **Gaps:** Excel at an advanced level, ERP/WMS (SAP, Oracle, NetSuite, Dynamics), forecasting, S&OP, inventory turns, fill rate, OTIF, and ideally APICS/CSCP.
   - **Verdict:** **Highest-paying realistic location unconfirmed path** from this background, but not the quickest because employers will test systems knowledge and measurable planning results.

3. **Procurement / Strategic Sourcing Manager**
   - **Mexico pay:** MXN 50k–95k/month gross; MXN 100k+ in multinational manufacturing or high-spend categories.
   - **Demand:** Good, particularly in industrial, automotive, retail, and CPG supply chains.
   - **Transition:** 6–12 months.
   - **Gaps:** Spend analysis, RFx process, contract negotiation, supplier performance, category strategy, ERP, and hard savings metrics.
   - **Verdict:** Strong option if vendor coordination was substantive—negotiating price, terms, service levels, or supply reliability—not merely placing orders.

4. **Customer Success / Service Delivery Manager**
   - **Mexico pay:** MXN 35k–75k/month gross locally; remote LATAM-facing roles can reach roughly USD 30k–60k/year.
   - **Demand:** Moderate to high, but concentrated in SaaS, BPO, fintech, and professional services.
   - **Transition:** 4–9 months.
   - **Gaps:** Fluent business English, CRM (Salesforce/HubSpot), account ownership, renewal/retention metrics, presentation skills, and software-sector credibility.
   - **Verdict:** Best bridge to international remote work only if English is strong. Without it, do not prioritize this path.

5. **Remote Operations Manager / Business Operations Manager for a US or international company**
   - **Pay:** Realistic location unconfirmed contractor range is about USD 25k–50k/year initially; exceptional bilingual, systems-heavy candidates can exceed that. US payroll roles are generally unavailable without US work authorization or an employer willing to hire internationally.
   - **Demand:** Competitive. Many jobs advertised as “operations” require SaaS, analytics, automation, project management, and remote collaboration evidence.
   - **Transition:** 9–18 months.
   - **Gaps:** Business English, remote-work proof, Excel/Sheets, KPI dashboards, project tools, CRM/ERP, process documentation, and preferably basic SQL or automation.
   - **Verdict:** This has the highest long-term international upside, but it is not the fastest credible next step from the stated profile.

**Recommendation:** Apply immediately for **Multi-site Retail Operations Manager / Area Manager** roles and position the candidate for a 20–40% pay increase. In parallel, build toward **Supply Chain / Inventory Planning Manager**, which is the highest-paying realistic domestic path.

Do not target US jobs as if US work authorization is assumed. Target US companies that explicitly hire in Mexico/LATAM through contractor or employer-of-record arrangements. The gating variables are English level and proof of quantified operational impact. Before applying broadly, obtain metrics for team size, location count, sales/expense responsibility, inventory accuracy or shrink, vendor spend, service levels, and improvements delivered; without them, the candidate will be screened as a supervisor rather than a manager.

## Honest rubric

| Failure mode | Senior technical baseline | Operations baseline |
|---|---|---|
| Stale or unsupported market evidence | Fails: asserts 2026/current salary, demand, and rankings without dated comparable briefs or source-quality checks. | Fails: asserts current pay and demand without dated comparable briefs. |
| Geography, currency, or compensation-basis mixing | Fails: treats Mexico and international contractor/EOR amounts as rank-comparable and leaves arrangement/eligibility unclear. | Fails: mixes Mexico gross monthly pay, remote contractor annual USD pay, and US payroll access. |
| Unrealistic transitions | Mixed: acknowledges production gaps, but treats several international paths as near-term without matching requirements evidence. | Fails: names remote operations and supply-chain manager paths despite missing systems, metrics, English, and eligibility evidence. |
| Unlabeled inference or candidate-evidence gaps | Fails: conclusions are not labelled and candidate-reported facts are used as settled evidence. | Fails: missing English, work authorization, metrics, systems, and remote history are not carried as `unknown`. |
| Unsupported demand or time-to-offer prediction | Fails: claims demand/interview volume and 0–8 month transitions. | Fails: claims demand and 0–18 month transitions. |
| Candidate evidence gaps | Partial: identifies some technical gaps but not dated role requirements or comparable market evidence. | Partial: identifies many gaps, but still makes a definitive compensation and fastest-offer recommendation. |

Both responses are superseded by the with-skill evaluation; the verbatim outputs above are retained only as the blinded baseline.

## Task 5 dated no-skill baseline

### Scenario

On 2026-08-06, compare the current Senior DevOps Engineer market for a location unconfirmed candidate across Mexico, US, and remote international roles. Include compensation, demand, and common requirements. Use current web results where available, but do not use the `research-professional-market` skill or its source policy.

### Verbatim output

Senior DevOps Engineers are in demand across all three markets. Mexico roles pay MX$950K–MX$1.54M annually, US remote roles pay US$145K–US$175K annually, and international remote jobs can pay up to US$190K. The US is the best market and remote international is a similarly attractive alternative.

Common requirements are AWS, Kubernetes, Terraform, CI/CD, observability, and English. A location unconfirmed candidate should apply to all of them because remote work means location does not matter. Sources include a Mexico job at [Peek](https://jobs.ashbyhq.com/peek/58b9bb30-2bf9-46ab-afab-f6338131bedc), a US-remote role at [Element 84](https://jobs.ashbyhq.com/element84/9c7498b2-8671-4f06-a1b5-e70fc7cd32b1), and a LATAM remote listing at [Jobgether](https://jobs.lever.co/jobgether/f93e682c-0fda-4fa0-9b75-ceca9382e29b). The role is strong demand because these vacancies exist.

### Baseline review

| Check | Result | Evidence |
|---|---|---|
| Dated sources | Fails | The response gives no publication date or crawl date for any page. |
| Geography and eligibility | Fails | It treats Mexico, US remote, and LATAM remote as interchangeable and assumes remote eligibility. |
| Currency and compensation basis | Fails | It combines MXN and USD figures without a conversion basis and does not consistently name base versus total compensation. |
| Seniority and sample context | Partial | The title is named, but one vacancy per market is treated as a market range. |
| Demand signals | Fails | Three postings become an unsupported broad-demand claim. |
| Recurring requirements | Fails | Requirements from disparate postings are asserted as recurring without a dated, matching sample. |
| Confidence and comparability warning | Fails | No confidence level or warning identifies the incompatible employee, eligibility, benefit, and compensation contexts. |
| Career decision boundary | Fails | It tells the candidate to apply across markets rather than returning evidence for path discovery. |
