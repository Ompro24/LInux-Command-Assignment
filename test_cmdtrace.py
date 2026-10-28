import unittest
from cmdtrace import analyze_command


class TestCmdtrace(unittest.TestCase):

    def test_pwd_is_low_risk(self):
        result = analyze_command("pwd")
        self.assertEqual(result["risk"], "LOW")

    def test_rm_is_high_risk(self):
        result = analyze_command("rm -rf ./temp")
        self.assertEqual(result["risk"], "HIGH")

    def test_empty_command(self):
        result = analyze_command("")
        self.assertEqual(result["risk"], "UNKNOWN")


if __name__ == "__main__":
    unittest.main()