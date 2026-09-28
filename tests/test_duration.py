import unittest
from service.models import ProjectGenerationRequest
from service.agents.role_writer import length_target

class DurationTests(unittest.TestCase):
    def test_one_to_sixty(self):
        ProjectGenerationRequest(user_promt="abc",niche="story",duration_minutes=1)
        ProjectGenerationRequest(user_promt="abc",niche="story",duration_minutes=60)

    def test_writer_target_uses_japanese_character_rate(self):
        target=length_target("ja",600)
        self.assertEqual(target["metric"],"cjk_chars")
        self.assertEqual(target["target"],3200)

    def test_vietnamese_and_english_use_their_configured_word_rates(self):
        self.assertEqual(length_target("vi",600)["target"],1450)
        self.assertEqual(length_target("en",600)["target"],1500)

if __name__=="__main__":
    unittest.main()
