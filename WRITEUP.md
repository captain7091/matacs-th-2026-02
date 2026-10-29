# Write-up: AI-Assisted Proposal Evaluation

Sample category: Commercial Solar Installation (150 kW rooftop, budget ceiling CAD 260,000, maximum 16 weeks). Results are in [ranking.json](ranking.json), and the process is shown in [diagram/flowchart.png](diagram/flowchart.png).

## 1. AI versus rule-based processing

| Step | Done by | Why |
|---|---|---|
| Configure criteria, weights, limits | Admin (human) | Business policy belongs to people |
| Convert uploaded files to text | Ordinary code (parser) | Mechanical and repeatable |
| Extract facts, evidence quotes, uncertainty | **AI** | Proposals are free text with different layouts and wording |
| Validate schema, types, units, quotes | Ordinary code | Must be exact and testable |
| Mandatory checks, limits, status | Ordinary code | Pass/fail rules must never vary |
| Weighted scoring and ranking | Ordinary code | Must be repeatable and auditable |
| Draft plain-English reason | **AI** (optional) | Wording only; scores are read-only |
| Review, override, final award | Human | Accountability stays with people |

AI handles language only; every eligibility, score and rank decision is deterministic code.

## 2. Consistency and explainability

**Scoring formula.** Each criterion gets a sub-score from 0 to 100. Relative sub-scores are calculated only among eligible proposals.

- Experience, 30%: `count / highest eligible count × 100`. The count is commercial installations of at least 100 kW in the last five years.
- Price, 25%: `lowest eligible price / price × 100`
- Timeline, 15%: `shortest eligible weeks / weeks × 100`
- Warranty, 15%: split equally between panel years (7.5%) and workmanship years (7.5%). Each part is `years / longest eligible years × 100`.
- Team and approach, 15%: `items present / 4 × 100`. The four items are a named lead, a crew, a safety plan and a performance monitoring plan.

`Total = Σ (sub-score × weight) / 100`, rounded to 2 decimals. The weights total 100%, so every total is between 0 and 100.

**Results:** A 98.75, E 85.53, C 77.78. Example for E: experience 57.14×0.30, price 98.14×0.25, timeline 92.31×0.15, panel warranty 100×0.075, workmanship 100×0.075 and team 100×0.15 sum to 85.53.

**Mandatory checks.** The bidder must explicitly state its own Ontario electrical contractor licence, WSIB clearance and CAD 5M liability insurance. A requirement that is not confirmed counts as a fail, so the proposal is `ineligible`. A price above the ceiling or a timeline over 16 weeks is also `ineligible`. Proposal B is ineligible because its own licence is not established. The proposal relies on a subcontractor still to be confirmed; this is not a claim that the subcontractor is unlicensed.

**Missing information.** If a proposal passes the mandatory checks but a scored fact is missing or unclear, it is `flagged`. It gets no score and no rank, and goes to a human. Proposal D gives no confirmed completion duration, so it is flagged. The system never estimates a missing value.

**Tie-break.** Proposals with equal scores are ordered by higher total score, then lower price, then shorter timeline, then proposal ID alphabetically. The same input always gives the same order.

**Explainability.** Each fact stores an exact evidence quote; each result shows sub-scores, facts used and criteria version.

## 3. Human oversight and audit

- Reviewers see each fact beside its evidence quote and can correct it. Corrected facts are re-validated and re-scored by code. A score is never edited directly.
- Flagged proposals and any `unclear` extraction need a human decision before the result is final.
- An override such as accepting late licence evidence or excluding a bidder requires a written reason and the reviewer's identity.
- The audit log is append-only. It records the uploaded file hash, extracted text, AI model and prompt version, raw AI output, validation results, criteria version, scores, every human change (old value, new value, who, when, why) and the final decision.
- Authorised staff make and sign off the final award; the system only recommends.

## 4. Changing criteria

- Criteria are configuration, not code. Each change creates a new immutable version (for example `solar-2026-v1` to `v2`), and weights must total 100% before saving.
- Each evaluation stores the version it used, so old results can always be reproduced.
- Extracted facts are kept separately from scores. When criteria change, existing proposals are re-scored from the stored facts without calling the AI again. Re-extraction is needed only when a new criterion needs a new fact.
- Re-scoring creates a new result version showing what changed; versions are never mixed in one ranking.
- Relative sub-scores depend on the eligible set, so the ranking is recalculated whenever a proposal's status changes, for example when D supplies a timeline.

## 5. Risks and safeguards

| Risk | Safeguard |
|---|---|
| Incorrect extraction | Schema and type validation, unit checks, evidence quote must appear in the source text, human review of low-confidence fields |
| Invented facts | Prompt forbids guessing, `null` is required for missing facts, quotes are verified by code, missing facts lead to flagged status |
| Bias (brand, size, writing style) | AI never scores; fixed formula on objective facts; periodic outcome review |
| Prompt injection | Documents are wrapped as untrusted data, the AI has no scoring role, and injection attempts are logged. Proposal C's "rank me first" text was ignored and had no effect on its score (77.78, rank 3) |
| Cost | Extract once, re-score from stored facts, cache by file hash |
| Privacy | Provider with no-training and data-residency terms, role-based access, encryption, retention policy |
| Parser errors (scans, tables) | Low text yield or failed OCR is detected and sent for manual entry |

**Known limitation in the sample:** Proposal C reports installations "since 2020". A reviewer should confirm that all nine fall within the five-year window before the award.
