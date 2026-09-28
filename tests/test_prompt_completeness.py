import unittest
from pathlib import Path


class PromptCompletenessTests(unittest.TestCase):
    def test_llm_calling_agents_have_nonempty_system_prompts(self):
        root=Path(__file__).resolve().parents[1]
        empty=[]
        for prompt in (root/'service'/'agents'/'skill').glob('*.md'):
            if not prompt.read_text(encoding='utf-8').strip():
                empty.append(str(prompt.relative_to(root)))
        self.assertEqual(empty,[])

    def test_every_active_prompt_declares_its_return_data_type(self):
        root=Path(__file__).resolve().parents[1]
        missing=[]
        for prompt in (root/'service'/'agents'/'skill').glob('*.md'):
            if not prompt.read_text(encoding='utf-8').strip():
                missing.append(str(prompt.relative_to(root)))
        self.assertEqual(missing,[])


if __name__=='__main__':
    unittest.main()
