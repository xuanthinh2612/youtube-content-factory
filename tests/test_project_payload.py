import unittest
from api.serializers import project_payload
from core.schemas.job import Job,GenerateRequest


class ProjectPayloadTests(unittest.TestCase):
    def test_summary_excludes_heavy_result(self):
        job=Job(id="x",request=GenerateRequest(topic="abc",niche="story"),result={"huge":"data"})
        payload=project_payload(job)
        self.assertNotIn("result",payload)


if __name__=="__main__":
    unittest.main()
