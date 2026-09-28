import unittest
from service.settings import app_settings
class Tests(unittest.TestCase):
    def test_tiers(self):
        self.assertEqual(app_settings.model_for_tier("FAST"),app_settings.model_fast)
        self.assertEqual(app_settings.model_for_tier("MIDDLE"),app_settings.model_middle)
        self.assertEqual(app_settings.model_for_tier("HARD"),app_settings.model_hard)
if __name__=="__main__":unittest.main()
