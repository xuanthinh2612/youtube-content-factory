import tempfile
import unittest
from pathlib import Path
from service.exporters.content_exporter import write_content_files

ROOT=Path(__file__).resolve().parents[1]

class V78ExportAndSecurityTests(unittest.TestCase):
    def test_export_writes_only_one_markdown_and_one_json(self):
        with tempfile.TemporaryDirectory() as directory:
            paths=write_content_files(Path(directory),'Title',{
                'outputs':{'vi':{'content':'Xin chào'},'en':{'content':'Hello'}}
            })
            self.assertEqual(set(paths),{'md','json'})
            self.assertEqual(
                {path.name for path in Path(directory).iterdir()},
                {'content.md','content.json'},
            )

    def test_docker_is_localhost_bound_by_default(self):
        compose=(ROOT/'docker-compose.yml').read_text(encoding='utf-8')
        self.assertIn('${BIND_ADDRESS:-127.0.0.1}:8090:8090',compose)

    def test_shared_agent_prompts_exist(self):
        for content_type in ('fact','news','music','story','video'):
            for agent_role in ('director','writer','editor'):
                text=(ROOT/f'service/agents/prompts/{content_type}_{agent_role}.md').read_text(encoding='utf-8')
                self.assertTrue(text.strip(),f'{content_type}_{agent_role}')

class V78E2EContractTests(unittest.TestCase):
    def test_all_content_types_share_three_agent_graph(self):
        text=(ROOT/'service/workflows/content_generation.py').read_text(encoding='utf-8')
        self.assertIn('director.plan(cfg',text)
        self.assertIn('writer.write(cfg,language,plan)',text)
        self.assertIn('editor.edit(cfg,language,plan,draft)',text)
