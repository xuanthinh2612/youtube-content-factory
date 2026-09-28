import unittest
from core.schemas.job import GenerateRequest
from quality.validators.duration import estimate_seconds,length_target,validate_duration

class DurationTests(unittest.TestCase):
    def test_one_to_sixty(self):
        GenerateRequest(topic="abc",niche="story",duration_minutes=1)
        GenerateRequest(topic="abc",niche="story",duration_minutes=60)

    def test_writer_target_and_validator_share_japanese_character_rate(self):
        target=length_target("ja",600)
        text="あ"*target["target"]
        measured=validate_duration(text,"ja",10)
        self.assertEqual(target["metric"],"cjk_chars")
        self.assertAlmostEqual(estimate_seconds(text,"ja"),600,delta=2)
        self.assertTrue(measured["pass"])

    def test_vietnamese_and_english_use_their_configured_word_rates(self):
        self.assertEqual(length_target("vi",600)["target"],1450)
        self.assertEqual(length_target("en",600)["target"],1500)

if __name__=="__main__":
    unittest.main()
