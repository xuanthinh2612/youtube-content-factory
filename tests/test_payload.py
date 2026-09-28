import unittest
from service.serializers import serialize_details
from service.models import ProjectJob,ProjectGenerationRequest


class ProjectPayloadTests(unittest.TestCase):
    def test_summary_excludes_heavy_result(self):
        job=ProjectJob(id="x",request=ProjectGenerationRequest(user_promt="abc",niche="story"),result={"huge":"data"})
        payload=serialize_details(job)
        self.assertNotIn("result",payload)


if __name__=="__main__":
    unittest.main()
