"""Offline tests for the datasheet-lookup scripts (00_coordination/T024). The variant gate is patched out (it needs the
registry and a module FACTS.md); a generated PDF in a temp dir is the fixture. Run: python -m unittest discover tools\tests"""
import contextlib
import io
import pathlib
import sys
import tempfile
import unittest
from unittest import mock

import pymupdf

SKILL = pathlib.Path(__file__).resolve().parents[2] / ".claude" / "skills" / "datasheet-lookup"
sys.path.insert(0, str(SKILL))
import pdf_crop  # noqa: E402
import pdf_search  # noqa: E402


def run(mod, argv):
    """Run mod.main() in-process with the gate disabled -> (exit code, stdout lines)."""
    buf, code = io.StringIO(), 0
    with mock.patch.object(mod, "gate", lambda *a: None), mock.patch.object(sys, "argv", ["x"] + argv), \
            contextlib.redirect_stdout(buf):
        try:
            mod.main()
        except SystemExit as e:
            code = e.code if isinstance(e.code, int) else 1
    return code, buf.getvalue().splitlines()


class Fixture(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.dir = pathlib.Path(cls.tmp.name)
        doc = pymupdf.open()
        p = doc.new_page()
        p.insert_text((72, 72), "Absolute Maximum Ratings\nsupply voltage 5 V\nESR 10 mOhm")
        p = doc.new_page()  # 100 matching lines -> truncation
        for i in range(100):
            p.insert_text((20, 10 + i * 7.5), f"bulk line {i}", fontsize=5)
        cls.pdf = str(cls.dir / "fixture.pdf")
        doc.save(cls.pdf)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()


class Search(Fixture):
    def test_report_line_is_last_on_hit(self):
        code, out = run(pdf_search, [self.pdf, "esr"])
        self.assertEqual(code, 0)
        self.assertRegex(out[-1], r"^REPORT: lines_read=\d+ tables_used=0 images_used=0$")

    def test_report_line_is_last_on_no_match(self):
        code, out = run(pdf_search, [self.pdf, "zzzzz"])
        self.assertEqual(code, 0)
        self.assertTrue(out[0].startswith("no match"))
        self.assertTrue(out[-1].startswith("REPORT:"))

    def test_report_line_is_last_in_page_mode(self):
        code, out = run(pdf_search, [self.pdf, "--page", "1"])
        self.assertEqual(code, 0)
        self.assertTrue(out[-1].startswith("REPORT:"))

    def test_limit_is_60_result_lines_plus_one_note(self):
        code, out = run(pdf_search, [self.pdf, "bulk", "--context", "0"])
        self.assertEqual(code, 0)
        body = out[:-1]  # without REPORT
        self.assertEqual(len(body), 61)
        self.assertIn("more lines cut", body[-1])
        self.assertIn("lines_read=60", out[-1])

    def test_synonym_hit(self):
        _, out = run(pdf_search, [self.pdf, "vcc"])
        self.assertIn("synonym hit: 'supply voltage'", out[0])

    def test_skill_lists_every_code_synonym(self):
        skill = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        for grp in pdf_search.SYNONYMS:
            for term in grp:
                self.assertIn(term, skill, term)


class Crop(Fixture):
    def crop(self, *args):
        return run(pdf_crop, [self.pdf, "1", *args, "--out", str(self.dir / "crops")])

    def test_full_page_rejected(self):
        code, _ = self.crop("0", "0", "1", "1")
        self.assertNotEqual(code, 0)

    def test_near_full_page_rejected(self):
        code, _ = self.crop("0", "0", "0.98", "0.98")
        self.assertNotEqual(code, 0)

    def test_partial_box_ok_and_report_last(self):
        code, out = self.crop("0", "0", "1", "0.3")
        self.assertEqual(code, 0)
        self.assertTrue(out[-1].startswith("REPORT:"))
        self.assertTrue(any((self.dir / "crops").glob("*.png")))

    def test_dpi_range(self):
        for dpi in ("99", "201"):
            code, _ = self.crop("0", "0", "1", "0.3", "--dpi", dpi)
            self.assertNotEqual(code, 0, dpi)
        for dpi in ("100", "200"):
            code, _ = self.crop("0", "0", "1", "0.3", "--dpi", dpi)
            self.assertEqual(code, 0, dpi)


if __name__ == "__main__":
    unittest.main()
