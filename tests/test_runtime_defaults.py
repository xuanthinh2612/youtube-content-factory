import unittest
from service.settings import ApplicationSettings

# Defaults tests must not read the developer's real .env overrides.
app_settings=ApplicationSettings(_env_file=None)

class RuntimeDefaultsTests(unittest.TestCase):
    def test_three_shared_agent_tiers(self):
        self.assertEqual(app_settings.tier_director,"HARD")
        self.assertEqual(app_settings.tier_writer,"HARD")
        self.assertEqual(app_settings.tier_editor,"HARD")

    def test_concurrency_default(self):
        self.assertEqual(app_settings.max_concurrent_projects,2)

if __name__=="__main__":unittest.main()
