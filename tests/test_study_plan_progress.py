import unittest

from backend.database import build_study_plan_progress, clear_study_step_completion_snapshot


class StudyPlanProgressTests(unittest.TestCase):
    def test_clear_completion_snapshot_removes_quiz_review_fields(self):
        snapshot = {
            "headline": "Graphs checkpoint quiz",
            "best_score": 100,
            "attempt_count": 2,
            "last_score": 100,
            "last_quiz_result": {"score": 100},
            "last_quiz_review": [{"quiz_item_id": "quiz_1"}],
            "last_completed_at": "2026-04-16T10:00:00Z",
        }

        cleared = clear_study_step_completion_snapshot(snapshot)

        self.assertEqual(cleared["headline"], "Graphs checkpoint quiz")
        self.assertEqual(cleared["best_score"], 100)
        self.assertEqual(cleared["attempt_count"], 2)
        self.assertNotIn("last_score", cleared)
        self.assertNotIn("last_quiz_result", cleared)
        self.assertNotIn("last_quiz_review", cleared)
        self.assertNotIn("last_completed_at", cleared)

    def test_progress_ignores_scores_from_reset_steps(self):
        plan = {"target_days": 14}
        steps = [
            {
                "step_id": "step-1",
                "phase_key": "reinforcement",
                "step_type": "mcq_quiz",
                "status": "planned",
                "scheduled_label": "Day 2",
                "topic_id": "graphs",
                "topic_title": "Graphs",
                "snapshot": {
                    "headline": "Graphs checkpoint quiz",
                    "last_score": 100,
                },
            },
            {
                "step_id": "step-2",
                "phase_key": "reinforcement",
                "step_type": "topic_round",
                "status": "done",
                "scheduled_label": "Day 3",
                "topic_id": "graphs",
                "topic_title": "Graphs",
                "snapshot": {
                    "headline": "Graphs round 1",
                    "last_score": 80,
                },
            },
        ]

        progress = build_study_plan_progress(plan, steps)

        self.assertEqual(progress["average_score"], 80)
        self.assertEqual(progress["phase_breakdown"][0]["average_score"], 80)
        self.assertEqual(progress["topic_progress"][0]["average_score"], 80)
        self.assertEqual(progress["score_history"], [80])


if __name__ == "__main__":
    unittest.main()
