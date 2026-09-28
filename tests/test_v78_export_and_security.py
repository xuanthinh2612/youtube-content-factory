import tempfile
import unittest
from pathlib import Path
from quality.validators.duration import clean_narration_text

ROOT=Path(__file__).resolve().parents[1]

class V78ExportAndSecurityTests(unittest.TestCase):
    def test_tts_cleaner_and_export_contract(self):
        self.assertEqual(clean_narration_text('# Title\n\n## Setup\n\n**Xin chào** bạn.'),'Xin chào bạn.')
        text=(ROOT/'exporters/content.py').read_text(encoding='utf-8')
        self.assertIn('tts_ready=False',text)
        self.assertIn('narration_text',text)
        self.assertIn('f"{stem}.txt"',text)

    def test_docker_is_localhost_bound_by_default(self):
        compose=(ROOT/'docker-compose.yml').read_text(encoding='utf-8')
        self.assertIn('${BIND_ADDRESS:-127.0.0.1}:8090:8090',compose)

    def test_optional_live_smoke_script_exists(self):
        text=(ROOT/'scripts/live_smoke_test.py').read_text(encoding='utf-8')
        self.assertIn('LIVE_SMOKE_GENERATE',text)
        self.assertIn('/health',text)

    def test_shared_agent_prompts_exist(self):
        for role in ('director','writer','editor'):
            text=(ROOT/f'agents/{role}/prompt.md').read_text(encoding='utf-8')
            self.assertTrue(text.strip(),role)
            self.assertIn(role.title(),text)

class V78E2EContractTests(unittest.TestCase):
    def test_mock_e2e_script_exists_and_covers_all_niches(self):
        text=(ROOT/'scripts/mock_e2e_test.py').read_text(encoding='utf-8')
        for niche in ('story','fact','news','music','visual'):
            self.assertIn(niche,text)
        self.assertIn('WorkflowResult',text)

    def test_all_content_types_share_three_agent_graph(self):
        text=(ROOT/'core/workflow/graphs.py').read_text(encoding='utf-8')
        for role in ('director','writer','editor'):
            self.assertIn(f'"id":"{role}"',text)
        self.assertIn('edge("director","writer")',text)
        self.assertIn('edge("writer","editor")',text)
