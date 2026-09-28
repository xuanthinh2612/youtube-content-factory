import unittest
from core.workflow.graphs import graph_for

class GraphTests(unittest.TestCase):
    def test_every_content_type_uses_the_same_three_roles(self):
        expected=["director","writer","editor","export","completed"]
        for niche in ("story","fact","news","music","visual"):
            graph=graph_for(niche)
            ids=[n["id"] for n in graph["nodes"]]
            self.assertEqual(ids,expected,niche)
            edges=[(e["source"],e["target"]) for e in graph["edges"]]
            self.assertEqual(edges,[
                ("director","writer"),("writer","editor"),
                ("editor","export"),("export","completed"),
            ],niche)

if __name__=="__main__":unittest.main()
