"""Rule-based evaluation of proposal facts that have already been extracted.

This prototype does not call an AI model or parse documents. It reads fictional,
already-structured facts (as the AI extraction step would produce after
validation) and applies mandatory checks, weighted scoring and ranking.

Usage: python evaluate.py [config.json] [proposals.json]
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).parent


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def validate_config(config):
    total = sum(c["weight"] for c in config["criteria"])
    if abs(total - 100) > 1e-9:
        raise ValueError(f"Criteria weights must total 100, got {total}")
    for c in config["criteria"]:
        if c["direction"] not in ("lower_is_better", "higher_is_better"):
            raise ValueError(f"Unknown direction for {c['field']}: {c['direction']}")


def check_status(proposal, config):
    """Return (status, reason). Status is 'eligible', 'ineligible' or 'flagged'."""
    facts = proposal["facts"]
    # A mandatory requirement must be confirmed by the bidder; unconfirmed means fail.
    for m in config["mandatory"]:
        if facts.get(m["field"]) is not True:
            return "ineligible", m["fail_reason"]
    # A scored fact that is missing cannot be scored fairly; send to a human.
    for c in config["criteria"]:
        value = facts.get(c["field"])
        if not isinstance(value, (int, float)) or isinstance(value, bool) or value < 0:
            return "flagged", c["missing_reason"]
    # Hard project limits (e.g. budget ceiling, maximum duration).
    for lim in config.get("limits", []):
        if facts[lim["field"]] > lim["max"]:
            return "ineligible", lim["fail_reason"]
    return "eligible", None


def criterion_score(value, values, direction, scale_max=None):
    """Score one criterion from 0 to 100.

    With scale_max the score is absolute (value / scale_max); otherwise it is
    relative to the best value among eligible proposals.
    """
    if scale_max is not None:
        return 100.0 * min(value, scale_max) / scale_max
    if direction == "lower_is_better":
        best = min(values)
        return 100.0 if value == 0 else 100.0 * best / value
    best = max(values)
    return 100.0 if best == 0 else 100.0 * value / best


def evaluate(proposals, config):
    validate_config(config)
    results, eligible = [], []
    for p in proposals:
        status, reason = check_status(p, config)
        entry = {"proposal": p["id"], "status": status, "reason": reason, "facts": p["facts"]}
        results.append(entry)
        if status == "eligible":
            eligible.append(entry)

    for c in config["criteria"]:
        values = [e["facts"][c["field"]] for e in eligible]
        for e in eligible:
            s = criterion_score(e["facts"][c["field"]], values, c["direction"], c.get("scale_max"))
            e.setdefault("breakdown", {})[c["field"]] = s

    weights = {c["field"]: c["weight"] for c in config["criteria"]}
    for e in eligible:
        total = sum(e["breakdown"][f] * w / 100 for f, w in weights.items())
        e["score"] = round(total, 2)

    # Deterministic order: higher score, then the configured tie-break fields, then proposal ID.
    def sort_key(e):
        keys = [-e["score"]]
        for t in config.get("tie_break", []):
            v = e["facts"][t["field"]]
            keys.append(v if t["direction"] == "lower_is_better" else -v)
        keys.append(e["proposal"])
        return keys

    for rank, e in enumerate(sorted(eligible, key=sort_key), start=1):
        e["rank"] = rank
        e["status"] = "ranked"

    output = []
    for e in sorted(results, key=lambda e: e["proposal"]):
        output.append({
            "proposal": e["proposal"],
            "rank": e.get("rank"),
            "status": e["status"],
            "score": e.get("score"),
            "reason": e["reason"] or "",
        })
    return output


def main(argv):
    config = load_json(argv[1] if len(argv) > 1 else HERE / "config.json")
    data = load_json(argv[2] if len(argv) > 2 else HERE / "proposals.json")
    result = evaluate(data["proposals"], config)
    # Reviewer-approved, evidence-based reasons replace the generic rule reasons.
    for r in result:
        r["reason"] = data.get("reasons", {}).get(r["proposal"]) or r["reason"]
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main(sys.argv)
