import unittest
from core.schemas.output import LanguageOutput


class MutableDefaultsTests(unittest.TestCase):
    def test_output_defaults_not_shared(self):
        a=LanguageOutput(language="en")
        b=LanguageOutput(language="en")
        a.checks["x"]=1
        self.assertNotIn("x",b.checks)

if __name__=="__main__":
    unittest.main()
