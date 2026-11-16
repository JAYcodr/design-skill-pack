"""quick_check.py 的回归测试。运行：python3 -m unittest discover -s scripts/tests"""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))

import quick_check  # noqa: E402

FIXTURES = Path(__file__).resolve().parent / "fixtures"


class QuickCheckTest(unittest.TestCase):
    def test_clean_passes_without_hard_or_warn(self):
        result = quick_check.check_file(FIXTURES / "clean.html")
        self.assertEqual(result["hard"], [])
        self.assertEqual(result["warn"], [])

    def test_sloppy_flags_hard_issues(self):
        result = quick_check.check_file(FIXTURES / "sloppy.html")
        joined = "\n".join(result["hard"])
        self.assertIn("title", joined)
        self.assertIn("assets/hero.png", joined)
        self.assertIn("app.js", joined)

    def test_sloppy_flags_warnings(self):
        result = quick_check.check_file(FIXTURES / "sloppy.html")
        joined = "\n".join(result["warn"])
        self.assertIn("viewport", joined)
        self.assertIn("媒体查询", joined)
        self.assertIn("外链资源", joined)
        self.assertIn("alt", joined)
        self.assertIn("字号低于正文下限 14px", joined)
        self.assertIn("占位", joined)

    def test_rem_and_clamp_font_sizes(self):
        with tempfile.TemporaryDirectory() as tmp:
            page = Path(tmp) / "rem.html"
            page.write_text(
                '<!doctype html><html lang="zh"><head>'
                '<meta name="viewport" content="width=device-width">'
                '<title>rem 样本</title><style>body{background:#fff}'
                'p{font-size:0.6rem} h1{font-size:clamp(2rem,5vw,4rem)}</style></head>'
                '<body><p>正文</p></body></html>',
                encoding="utf-8")
            result = quick_check.check_file(page)
        self.assertIn("字号低于正文下限", "\n".join(result["warn"]))

    def test_cli_exit_codes(self):
        clean = subprocess.run(
            [sys.executable, str(SCRIPTS / "quick_check.py"), str(FIXTURES / "clean.html")],
            capture_output=True, text=True)
        sloppy = subprocess.run(
            [sys.executable, str(SCRIPTS / "quick_check.py"), str(FIXTURES / "sloppy.html")],
            capture_output=True, text=True)
        self.assertEqual(clean.returncode, 0, clean.stderr)
        self.assertEqual(sloppy.returncode, 1)
        self.assertIn("脚本没检查", clean.stdout + sloppy.stdout)

    def test_cli_json_output(self):
        proc = subprocess.run(
            [sys.executable, str(SCRIPTS / "quick_check.py"), str(FIXTURES / "clean.html"), "--json"],
            capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertEqual(len(payload), 1)
        self.assertEqual(payload[0]["hard"], [])

    def test_missing_file_returns_2(self):
        proc = subprocess.run(
            [sys.executable, str(SCRIPTS / "quick_check.py"), "/tmp/definitely-not-here.html"],
            capture_output=True, text=True)
        self.assertEqual(proc.returncode, 2)


if __name__ == "__main__":
    unittest.main()
