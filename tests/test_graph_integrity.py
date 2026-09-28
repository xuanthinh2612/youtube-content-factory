import unittest
from core.workflow.graphs import graph_for
from core.workflow.graph_state import reduce_graph


class GraphIntegrityTests(unittest.TestCase):
    def test_every_edge_endpoint_exists(self):
        for niche in ("story","fact","news","music","visual"):
            graph=graph_for(niche)
            ids={n["id"] for n in graph["nodes"]}
            for edge in graph["edges"]:
                self.assertIn(edge["source"],ids,(niche,edge))
                self.assertIn(edge["target"],ids,(niche,edge))

    def test_step_event_updates_node(self):
        spec=graph_for("fact")
        state=reduce_graph(spec,[{
            "type":"step","node":"writer","status":"running","message":"writing"
        }],"running")
        row=next(x for x in state["nodes"] if x["id"]=="writer")
        self.assertEqual(row["status"],"running")

    def test_completed_project_marks_completed_node(self):
        spec=graph_for("story")
        state=reduce_graph(spec,[],"completed")
        row=next(x for x in state["nodes"] if x["id"]=="completed")
        self.assertEqual(row["status"],"success")


if __name__=="__main__":
    unittest.main()
