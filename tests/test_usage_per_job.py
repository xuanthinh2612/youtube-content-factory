import unittest
from observability.usage import UsageTracker
from observability.execution import execution_context


class UsagePerJobTests(unittest.TestCase):
    def test_concurrent_job_buckets_do_not_mix(self):
        tracker=UsageTracker()
        with execution_context("a"):
            tracker.add("m",100,20)
        with execution_context("b"):
            tracker.add("m",7,3)
        self.assertEqual(tracker.snapshot("a")["total_tokens"],120)
        self.assertEqual(tracker.snapshot("b")["total_tokens"],10)

    def test_call_log_keeps_language_unit_retry_and_context_size(self):
        tracker=UsageTracker()
        with execution_context("a"):
            tracker.add("m",100,20,node="fact_writer",context_chars=900,
                retry_count=1,language="Vietnamese",unit="u2")
        call=tracker.snapshot("a")["calls"][0]
        self.assertEqual(call,{"agent":"fact_writer","language":"Vietnamese","unit":"u2",
            "input_tokens":100,"output_tokens":20,"retry_count":1,"context_chars":900})


if __name__=="__main__":
    unittest.main()
