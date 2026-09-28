import unittest
from service.models import ProjectJob,ProjectGenerationRequest
from service.serializers import serialize_details
from service.execution import build_display_name


class ProjectNamingTests(unittest.TestCase):
    def test_payload_contains_name(self):
        job=ProjectJob(id='x',name='Why Day Becomes Night',request=ProjectGenerationRequest(user_promt='very long original prompt',niche='fact'))
        payload=serialize_details(job)
        self.assertEqual(payload['name'],'Why Day Becomes Night')

    def test_missing_name_uses_short_prompt_title(self):
        self.assertEqual(build_display_name('', 'A useful project topic'), 'A useful project topic')


if __name__=='__main__':
    unittest.main()
