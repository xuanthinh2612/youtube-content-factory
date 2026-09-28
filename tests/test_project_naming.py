import unittest
from pathlib import Path
from core.schemas.job import Job,GenerateRequest
from api.serializers import project_payload


class ProjectNamingTests(unittest.TestCase):
    def test_project_payload_contains_name(self):
        job=Job(id='x',name='Why Day Becomes Night',request=GenerateRequest(topic='very long original prompt',niche='fact'))
        payload=project_payload(job)
        self.assertEqual(payload['name'],'Why Day Becomes Night')

    def test_prompt_analyzer_requests_project_name(self):
        root=Path(__file__).resolve().parents[1]
        prompt=(root/'agents/intake/prompt_analyzer/prompt.md').read_text(encoding='utf-8')
        self.assertIn('project_name',prompt)
        self.assertIn('3–8',prompt)


if __name__=='__main__':
    unittest.main()
