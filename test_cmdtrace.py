
import unittest
from cmdtrace import analyze


class TestCmdtrace(unittest.TestCase):

    def test_pwd_is_low_risk(self):
        self.assertEqual(analyze("pwd").risk, "LOW")

    def test_ls_is_low_risk(self):
        self.assertEqual(analyze("ls -la").risk, "LOW")

    def test_rm_file_is_medium(self):
        self.assertEqual(analyze("rm file.txt").risk, "MEDIUM")

    def test_recursive_rm_is_high(self):
        self.assertEqual(analyze("rm -rf old_folder").risk, "HIGH")

    def test_rm_special_path_is_high(self):
        self.assertEqual(analyze("rm -r ./folder").risk, "HIGH")

    def test_mv_is_medium(self):
        self.assertEqual(analyze("mv file.txt ./temp/").risk, "MEDIUM")

    def test_chmod_777_is_high(self):
        self.assertEqual(analyze("chmod 777 file.txt").risk, "HIGH")

    def test_sudo_rm_is_high(self):
        self.assertEqual(analyze("sudo rm file.txt").risk, "HIGH")

    def test_unknown_command(self):
        self.assertEqual(analyze("madeupcommand").risk, "UNKNOWN")

    def test_empty_input(self):
        self.assertEqual(analyze("").risk, "UNKNOWN")

    def test_pipeline_is_unknown(self):
        self.assertEqual(
            analyze("cat file.txt | grep secret").risk,
            "UNKNOWN"
        )

    def test_redirection_is_unknown(self):
        self.assertEqual(
            analyze("echo hello > output.txt").risk,
            "UNKNOWN"
        )

    def test_variable_is_unknown(self):
        self.assertEqual(analyze("rm $FILE").risk, "UNKNOWN")

    def test_unmatched_quote_is_unknown(self):
        self.assertEqual(analyze('cat "unfinished').risk, "UNKNOWN")

    def test_execution_is_not_performed(self):
        self.assertIn(
            "Not performed.",
            analyze("pwd").display()
        )


if __name__ == "__main__":
    unittest.main()
