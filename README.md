# MATACS Technical Assessment

- **Name:** Inam Ullah
- **Assessment reference:** MATACS-TH-2026-02
- **Actual time spent:** 45 minutes

## Deliverables

| File | Description |
|---|---|
| [WRITEUP.md](WRITEUP.md) | Answers to the five questions, scoring formula, mandatory checks and tie-break rule |
| [PROMPTS.md](PROMPTS.md) | AI prompts for fact extraction, injection resistance and explanations |
| [ranking.json](ranking.json) | Evaluation results for Proposals A–E |
| [diagram/flowchart.png](diagram/flowchart.png) | Process flowchart showing AI, rule-based and human steps |
| [prototype/](prototype/) | Optional: standard-library Python scoring script and tests |

## Results summary

| Rank | Proposal | Status | Score |
|---|---|---|---|
| 1 | A | ranked | 98.75 |
| 2 | E | ranked | 85.53 |
| 3 | C | ranked | 77.78 |
| – | B | ineligible (bidder's own Ontario electrical licence not confirmed) | – |
| – | D | flagged (completion timeline unknown) | – |

## Prototype

The prototype applies rule-based checks and scoring to fictional, already-structured facts. It does not call an AI model or parse PDFs. Requires Python 3.9+ and no packages.

```bash
cd prototype
python evaluate.py              # prints the results used for ranking.json
python -m unittest -v           # runs the tests
```

## Use of AI tools

I used an AI coding assistant to help draft the documents, the prompts, the flowchart script and the prototype. I reviewed the output against the brief, checked the scores by hand, and edited the wording.

Example of a corrected suggestion: the first version of the scoring code rounded each criterion's sub-score before adding them up. That makes the total differ slightly from the formula in the write-up. I changed it to round only the final total, so the scores in `ranking.json` can be reproduced exactly by hand. I also kept the AI out of all scoring decisions. Proposal C's embedded "rank this first" instruction shows why: a model that scores documents can be influenced by their content.
