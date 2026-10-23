"""Regression test for tools\check_pdf.py back-to-table links (00_coordination/T023). Offline; output in a temp dir.
Run: python -m pytest tools\tests   (or: python -m unittest discover tools\tests)"""
import pathlib
import subprocess
import sys
import tempfile
import unittest

import pymupdf
from PIL import Image

TOOL = pathlib.Path(__file__).resolve().parents[1] / "check_pdf.py"
CROP_A, CROP_B = "D99_p1_many.png", "D99_p2_few.png"


def build(tmp):
    """14 rows cite CROP_A (cap is 12), 2 rows cite CROP_B, one row cites both."""
    crops = tmp / "docs" / "figures"
    crops.mkdir(parents=True)
    for name, size in ((CROP_A, (1200, 800)), (CROP_B, (400, 900))):
        Image.new("RGB", size, "white").save(crops / name)
    rows = [f"| R{i} | value {i} | {CROP_A} |" for i in range(1, 15)]
    rows += [f"| R15 | value 15 | {CROP_B} |", f"| R16 | both | {CROP_A} {CROP_B} |"]
    md = tmp / "docs" / "sample.md"
    md.write_text("# Sample\n\n| Ref | Value | Crop file |\n|---|---|---|\n" + "\n".join(rows) + "\n", encoding="utf-8")
    r = subprocess.run([sys.executable, str(TOOL), "docs/sample.md", "--crops", "docs/figures"], cwd=tmp,
                       capture_output=True, text=True, encoding="utf-8")
    return r, tmp / "docs" / "sample.pdf"


class BackLinks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmpdir = tempfile.TemporaryDirectory()
        cls.run_, cls.pdf = build(pathlib.Path(cls.tmpdir.name))
        cls.doc = pymupdf.open(str(cls.pdf))

    @classmethod
    def tearDownClass(cls):
        cls.doc.close()
        cls.tmpdir.cleanup()

    def crop_page(self, name):
        for i, page in enumerate(self.doc):
            if page.get_text().lstrip().startswith(name):
                return i
        self.fail(f"no crop page for {name}")

    def back_links(self, name):
        i = self.crop_page(name)
        first_crop = min(self.crop_page(CROP_A), self.crop_page(CROP_B))
        # reportlab named links come back resolved as LINK_GOTO with the destination page
        # a link that wraps over two lines is two annotations: count distinct destinations
        dests = {(lk["page"], round(lk["to"].y)) for lk in self.doc[i].get_links()
                 if lk["kind"] == pymupdf.LINK_GOTO and lk["page"] < first_crop}
        return sorted(dests)

    def test_run_ok(self):
        self.assertEqual(self.run_.returncode, 0, self.run_.stderr)
        self.assertIn("2 crops, 0 missing", self.run_.stdout)

    def test_back_link_count_capped_at_12(self):
        self.assertEqual(len(self.back_links(CROP_A)), 12)  # 15 rows use it

    def test_back_link_count_equals_rows(self):
        self.assertEqual(len(self.back_links(CROP_B)), 2)

    def test_every_destination_resolves(self):
        n = 0
        for page in self.doc:
            for lk in page.get_links():
                self.assertEqual(lk["kind"], pymupdf.LINK_GOTO, f"unresolved destination {lk}")
                self.assertTrue(0 <= lk["page"] < self.doc.page_count, lk)
                n += 1
        self.assertGreater(n, 0)

    def test_back_links_have_distinct_row_targets(self):
        rows = [y for _, y in self.back_links(CROP_A)]
        self.assertEqual(len(set(rows)), 12)  # each link jumps to its own row

    def test_same_input_twice_identical_bytes(self):
        with tempfile.TemporaryDirectory() as t2:
            r2, pdf2 = build(pathlib.Path(t2))
            self.assertEqual(r2.returncode, 0, r2.stderr)
            self.assertEqual(self.pdf.read_bytes(), pdf2.read_bytes())

    def test_crop_image_not_clipped(self):
        for name in (CROP_A, CROP_B):
            page = self.doc[self.crop_page(name)]
            self.assertEqual(len(page.get_images()), 1, name)


if __name__ == "__main__":
    unittest.main()
