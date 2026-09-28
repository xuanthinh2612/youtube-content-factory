import tempfile,unittest
from pathlib import Path
from storage.files import FileStore
class Tests(unittest.TestCase):
    def test_atomic_write(self):
        # Smoke test the implementation method on a temp path.
        s=FileStore()
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"x.json";s.atomic_text(p,'{"x":1}');self.assertEqual(p.read_text(),'{"x":1}')
if __name__=="__main__":unittest.main()
