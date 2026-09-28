import unittest
from pathlib import Path


class PromptCompletenessTests(unittest.TestCase):
    def test_llm_calling_agents_have_nonempty_system_prompts(self):
        root=Path(__file__).resolve().parents[1]
        empty=[]
        for agent in (root/'agents').rglob('agent.py'):
            code=agent.read_text(encoding='utf-8')
            # Provider-only agents may inherit BaseAgent but never call self.text/json.
            if 'self.text(' not in code and 'self.json(' not in code:
                continue
            prompt=agent.parent/'prompt.md'
            if not prompt.exists() or not prompt.read_text(encoding='utf-8').strip():
                empty.append(str(agent.parent.relative_to(root)))
        self.assertEqual(empty,[])

    def test_every_active_prompt_declares_its_return_data_type(self):
        root=Path(__file__).resolve().parents[1]
        missing=[]
        for agent in (root/'agents').rglob('agent.py'):
            code=agent.read_text(encoding='utf-8')
            prompt=agent.parent/'prompt.md'
            if not prompt.exists():continue
            text=prompt.read_text(encoding='utf-8').lower()
            if 'self.json(' in code:
                valid=('json' in text and '{' in text and ('return' in text or 'output type' in text))
            elif 'self.text(' in code:
                valid=('return' in text and any(kind in text for kind in ('markdown','plain text','script','prose','section','lyrics')))
            else:
                continue
            if not valid:missing.append(str(agent.parent.relative_to(root)))
        self.assertEqual(missing,[])


if __name__=='__main__':
    unittest.main()
