import tempfile,unittest
from pathlib import Path
from service.storage.file_store import ProjectFileStore
class ProjectFileStoreTests(unittest.TestCase):
    def test_write_text_atomically(self):
        # Smoke test the implementation method on a temp path.
        s=ProjectFileStore()
        with tempfile.TemporaryDirectory() as d:
            target_path=Path(d)/"x.json"
            s.write_text_atomically(target_path,'{"x":1}')
            self.assertEqual(target_path.read_text(),'{"x":1}')
if __name__=="__main__":unittest.main()
