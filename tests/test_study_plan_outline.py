import unittest

from backend.database import build_checkpoint_days


class StudyPlanOutlineTests(unittest.TestCase):
    def test_checkpoint_days_stay_between_round_one_and_round_two(self):
        round_one_days = [2, 5, 8, 11, 14, 17]
        round_two_days = [19, 20, 21, 23, 24, 25]

        checkpoint_days = build_checkpoint_days(round_one_days, round_two_days)

        self.assertEqual(len(checkpoint_days), len(round_one_days))
        for checkpoint_day, round_one_day, round_two_day in zip(checkpoint_days, round_one_days, round_two_days):
            self.assertGreater(checkpoint_day, round_one_day)
            self.assertLess(checkpoint_day, round_two_day)

        self.assertGreater(len(set(checkpoint_days)), 4)
        self.assertLess(min(checkpoint_days), 15)
        self.assertGreater(max(checkpoint_days), 18)


if __name__ == "__main__":
    unittest.main()
