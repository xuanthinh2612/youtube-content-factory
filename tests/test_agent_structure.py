
import unittest
from pathlib import Path

class AgentStructureTests(unittest.TestCase):
    def test_every_agent_has_prompt(self):
        root=Path(__file__).resolve().parents[1]
        missing=[]
        for content_type in ("fact", "news", "music", "story", "video"):
            for agent_role in ("director", "writer", "editor"):
                if not (root/"service"/"agents"/"prompts"/f"{content_type}_{agent_role}.md").exists():
                    missing.append(f"{content_type}_{agent_role}")
        self.assertEqual(missing,[])

if __name__=="__main__":
    unittest.main()
