
import unittest
from pathlib import Path

class AgentStructureTests(unittest.TestCase):
    def test_every_agent_has_prompt(self):
        root=Path(__file__).resolve().parents[1]
        missing=[]
        for agent in (root/"agents").rglob("agent.py"):
            if not (agent.parent/"prompt.md").exists():
                missing.append(str(agent.parent.relative_to(root)))
        self.assertEqual(missing,[])

if __name__=="__main__":
    unittest.main()
