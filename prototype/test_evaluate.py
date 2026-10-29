"""Basic tests using small fictional fixtures. Run: python -m unittest -v"""
import unittest
from pathlib import Path

from evaluate import evaluate, load_json, validate_config

CONFIG = {
    "criteria": [
        {"field": "price", "weight": 60, "direction": "lower_is_better", "missing_reason": "Price unknown."},
        {"field": "weeks", "weight": 40, "direction": "lower_is_better", "missing_reason": "Completion timeline unknown."},
    ],
    "mandatory": [
        {"field": "licensed", "fail_reason": "Bidder's own licence not confirmed."},
    ],
    "tie_break": [{"field": "price", "direction": "lower_is_better"}],
}


def p(pid, price, weeks, licensed=True):
    return {"id": pid, "facts": {"price": price, "weeks": weeks, "licensed": licensed}}


def by_id(result):
    return {r["proposal"]: r for r in result}


class EvaluateTests(unittest.TestCase):
    def test_statuses(self):
        r = by_id(evaluate([p("A", 100, 10), p("B", 90, 10, licensed=None), p("C", 110, None)], CONFIG))
        self.assertEqual(r["A"]["status"], "ranked")
        self.assertEqual(r["B"]["status"], "ineligible")
        self.assertEqual(r["C"]["status"], "flagged")
        for pid in ("B", "C"):
            self.assertIsNone(r[pid]["rank"])
            self.assertIsNone(r[pid]["score"])

    def test_missing_timeline_is_flagged(self):
        r = by_id(evaluate([p("D", 100, None)], CONFIG))
        self.assertEqual(r["D"]["status"], "flagged")
        self.assertEqual(r["D"]["reason"], "Completion timeline unknown.")

    def test_score_bounds(self):
        result = evaluate([p("A", 100, 8), p("B", 250, 30), p("C", 120, 12)], CONFIG)
        for r in result:
            self.assertGreaterEqual(r["score"], 0)
            self.assertLessEqual(r["score"], 100)
        self.assertEqual(by_id(result)["A"]["score"], 100.0)

    def test_tie_break_is_deterministic(self):
        # Equal score and price: proposal ID decides, whatever the input order.
        first = evaluate([p("Y", 100, 10), p("X", 100, 10)], CONFIG)
        second = evaluate([p("X", 100, 10), p("Y", 100, 10)], CONFIG)
        self.assertEqual(first, second)
        self.assertEqual(by_id(first)["X"]["rank"], 1)

    def test_over_limit_is_ineligible(self):
        config = dict(CONFIG, limits=[{"field": "price", "max": 200, "fail_reason": "Over budget."}])
        r = by_id(evaluate([p("A", 100, 10), p("B", 250, 10)], config))
        self.assertEqual(r["B"]["status"], "ineligible")
        self.assertIsNone(r["B"]["score"])

    def test_sample_data(self):
        here = Path(__file__).parent
        config = load_json(here / "config.json")
        data = load_json(here / "proposals.json")
        r = by_id(evaluate(data["proposals"], config))
        self.assertEqual(r["B"]["status"], "ineligible")
        self.assertEqual(r["D"]["status"], "flagged")
        self.assertEqual([r[x]["rank"] for x in "ACE"], [1, 3, 2])
        self.assertEqual([r[x]["score"] for x in "ACE"], [98.75, 77.78, 85.53])
        # Proposal C's embedded instruction is recorded but never read by the scoring code.
        self.assertNotEqual(r["C"]["rank"], 1)

    def test_weights_must_total_100(self):
        bad = dict(CONFIG, criteria=[dict(CONFIG["criteria"][0], weight=50), CONFIG["criteria"][1]])
        with self.assertRaises(ValueError):
            validate_config(bad)


if __name__ == "__main__":
    unittest.main()
