import unittest
from core.config import Settings

# Defaults tests must not read the developer's real .env overrides.
settings=Settings(_env_file=None)

class RuntimeDefaultsTests(unittest.TestCase):
    def test_three_shared_agent_tiers(self):
        self.assertEqual(settings.tier_director,"HARD")
        self.assertEqual(settings.tier_writer,"HARD")
        self.assertEqual(settings.tier_editor,"HARD")

    def test_concurrency_default(self):
        self.assertEqual(settings.max_concurrent_projects,2)
        self.assertEqual(settings.max_concurrent_llm_calls,4)

if __name__=="__main__":unittest.main()
