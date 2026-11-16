"""ledger.py 的回归测试。运行：python3 -m unittest discover -s scripts/tests"""

import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))

import ledger  # noqa: E402

WARM_PAGE = """<!doctype html><html><head><title>暖纸页</title>
<style>body{background:#f4f1ea;font-family:"Noto Serif SC",serif}p{font-size:16px}
h1{font-size:64px}main{display:grid}</style></head><body><main></main></body></html>"""

DARK_PAGE = """<!doctype html><html><head><title>深色页</title>
<style>body{background:#101418;font-family:"JetBrains Mono",monospace}
p{font-size:16px}h1{font-size:56px}</style></head><body><main></main></body></html>"""


class LedgerTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name) / "home"
        os.environ["FRONTEND_DESIGN_HOME"] = str(self.home)
        self.addCleanup(os.environ.pop, "FRONTEND_DESIGN_HOME", None)
        self.warm = Path(self.tmp.name) / "warm.html"
        self.warm.write_text(WARM_PAGE, encoding="utf-8")
        self.dark = Path(self.tmp.name) / "dark.html"
        self.dark.write_text(DARK_PAGE, encoding="utf-8")

    def run_cli(self, argv):
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = ledger.main(argv)
        return code, buf.getvalue()

    def test_fingerprint_facts(self):
        fp = ledger.fingerprint(self.warm)
        self.assertEqual(fp["bg"], "#f4f1ea")
        self.assertEqual(fp["bg_class"], "浅暖")
        self.assertEqual(fp["fonts"], ["Noto Serif SC"])
        self.assertEqual(fp["layout"]["sections"], 1)

    def test_font_var_resolution(self):
        page = Path(self.tmp.name) / "varfont.html"
        page.write_text(
            '<!doctype html><html><head><style>'
            ':root{--serif:"Noto Serif SC",serif}'
            'body{background:#efebe3;font-family:var(--serif)}'
            '</style></head><body></body></html>',
            encoding="utf-8")
        fp = ledger.fingerprint(page)
        self.assertEqual(fp["fonts"], ["Noto Serif SC"])

    def test_bg_class(self):
        self.assertEqual(ledger.bg_class("#f4f1ea"), "浅暖")
        self.assertEqual(ledger.bg_class("#eef2f5"), "浅冷")
        self.assertEqual(ledger.bg_class("#101418"), "深")

    def test_add_writes_ledger_row(self):
        code, out = self.run_cli(["add", str(self.warm), "--project", "测试项目", "--note", "来源：案例"])
        self.assertEqual(code, 0)
        self.assertIn("已记账", out)
        rows = ledger.load_rows(ledger.ledger_path())
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["project"], "测试项目")
        self.assertEqual(rows[0]["bg"], "#f4f1ea")
        self.assertEqual(rows[0]["note"], "来源：案例")

    def test_recent_reports_repeats(self):
        self.run_cli(["add", str(self.warm), "--project", "A"])
        self.run_cli(["add", str(self.warm), "--project", "B"])
        code, out = self.run_cli(["recent"])
        self.assertEqual(code, 0)
        self.assertIn("A", out)
        self.assertIn("B", out)
        self.assertIn("反复出现：浅暖×2", out)

    def test_check_detects_same_background(self):
        self.run_cli(["add", str(self.warm), "--project", "旧项目"])
        code, out = self.run_cli(["check", str(self.warm)])
        self.assertEqual(code, 0)
        self.assertIn("同底色", out)
        self.assertIn("旧项目", out)

    def test_check_empty_ledger(self):
        code, out = self.run_cli(["check", str(self.warm)])
        self.assertEqual(code, 0)
        self.assertIn("账本为空", out)

    def test_missing_file_returns_2(self):
        code, _ = self.run_cli(["add", str(Path(self.tmp.name) / "nope.html")])
        self.assertEqual(code, 2)

    def test_ledger_is_jsonl(self):
        self.run_cli(["add", str(self.warm), "--project", "A"])
        line = ledger.ledger_path().read_text(encoding="utf-8").strip()
        payload = json.loads(line)
        self.assertIn("bg", payload)
        self.assertIn("layout", payload)


if __name__ == "__main__":
    unittest.main()
