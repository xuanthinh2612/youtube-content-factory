import unittest
from core.config import settings
class Tests(unittest.TestCase):
    def test_tiers(self):
        self.assertEqual(settings.model_for_tier("FAST"),settings.model_fast)
        self.assertEqual(settings.model_for_tier("MIDDLE"),settings.model_middle)
        self.assertEqual(settings.model_for_tier("HARD"),settings.model_hard)
if __name__=="__main__":unittest.main()
