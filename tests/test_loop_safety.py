import unittest
from core.config import settings

class LoopSafetyTests(unittest.TestCase):
    def test_global_cap(self):
        old=settings.max_loop_rounds
        try:
            settings.max_loop_rounds=5
            self.assertEqual(settings.cap_rounds(999),5)
            self.assertEqual(settings.cap_rounds(3),3)
            self.assertEqual(settings.cap_rounds(0),1)
        finally:settings.max_loop_rounds=old

    def test_defaults_are_finite_and_cost_bounded(self):
        self.assertEqual(settings.max_loop_rounds,2)
        for value in (settings.llm_retry_attempts,):
            self.assertLessEqual(settings.cap_rounds(value),2)

if __name__=="__main__":unittest.main()
