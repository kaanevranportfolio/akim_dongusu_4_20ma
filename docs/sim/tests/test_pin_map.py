"""Offline tests for docs\\sim\\pin_map.py (00_coordination/T025). Fixture copy only; output in a temp dir.
Run: python -m unittest discover docs\\sim\\tests"""
import contextlib
import io
import pathlib
import sys
import tempfile
import unittest

import pymupdf

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import pin_map  # noqa: E402

FACTS = HERE / "fixtures" / "FACTS_pin_map_sample.md"
CIR = HERE / "fixtures" / "sample_tb.cir"


def run(*extra, out):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = pin_map.main(["--cir", str(CIR), "--instance", "XU1", "XU2", "--part", "PARTA", "PARTB",
                             "--out", str(out), *extra])
    return code, buf.getvalue()


class PinMap(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        d = pathlib.Path(cls.tmp.name)
        cls.svg_path = d / "mapped.svg"
        cls.code, cls.stdout = run("--pin-map", str(FACTS), out=cls.svg_path)
        cls.svg = cls.svg_path.read_text(encoding="utf-8")
        plain_path = d / "plain.svg"
        cls.plain_code, cls.plain_stdout = run(out=plain_path)
        cls.plain = plain_path.read_text(encoding="utf-8")

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_parser_reads_only_the_section(self):
        rows = pin_map.parse_pin_map(FACTS.read_text(encoding="utf-8"))
        self.assertEqual(len(rows), 5)
        self.assertEqual({r["Part"] for r in rows}, {"PARTA", "PARTB"})

    def test_bad_header_or_label_rejected(self):
        with self.assertRaises(ValueError):
            pin_map.parse_pin_map("## Pin eşleme\n| Part | X |\n|---|---|\n| a | b |\n")
        txt = FACTS.read_text(encoding="utf-8").replace("| [V] |", "| V |", 1)
        with self.assertRaises(ValueError):
            pin_map.parse_pin_map(txt)

    def test_three_prefixes_and_values(self):
        for s in ("DS 4 OUT D90 p.5", "SP 1 out", "TB VOUT_NET", "DS 1 IN D90 p.5", "SP 2 in"):
            self.assertIn(s, self.svg)

    def test_mismatch_is_shown_not_an_error(self):
        # pin 4 OUT is SUBCKT position 1: shown side by side, exit code 0
        self.assertEqual(self.code, 0)
        self.assertIn("DS 4 OUT", self.svg)
        self.assertIn("SP 1 out", self.svg)

    def test_legend(self):
        self.assertIn("Legend", self.svg)
        for s in ("solid rectangle", "dashed rounded", "hexagon", "hatched"):
            self.assertIn(s, self.svg)

    def test_distinct_shapes(self):
        self.assertIn('class="dash"', self.svg)  # SP dashed edge (separate segments)
        self.assertNotIn("stroke-dasharray", self.svg)
        self.assertIn("<polygon", self.svg)          # TB hexagon

    def test_hatched_box_for_unknown(self):
        self.assertIn("hatch-line", self.svg)
        # the legend always holds one hatched sample; the figure body adds 3 more boxes (2 unmapped terminals)
        self.assertGreater(self.svg.count('class="DS missing"') + self.svg.count('class="SP missing"'),
                           self.plain.count('class="DS missing"') + self.plain.count('class="SP missing"') + 2)
        self.assertIn("SP ?", self.svg)  # SENSE node name "?"
        self.assertIn("DS ?", self.svg)  # position 3 of XU2 absent from the table

    def test_unmapped_count_and_warning(self):
        self.assertIn("UNMAPPED TERMINALS: 2", self.svg)
        warns = [ln for ln in self.stdout.splitlines() if ln.startswith("WARNING")]
        self.assertEqual(len(warns), 1)
        self.assertIn("EXTRA_NET", warns[0])

    def test_no_argument_run(self):
        self.assertEqual(self.plain_code, 0)
        self.assertIn("pin map: none", self.plain)
        self.assertNotIn("UNMAPPED", self.plain)
        self.assertNotIn("WARNING", self.plain_stdout)
        self.assertNotIn("SP ?", self.plain)
        self.assertIn("TB VOUT_NET", self.plain)

    def test_svg_renders_to_png(self):
        png = pathlib.Path(self.tmp.name) / "mapped.png"
        pymupdf.open(str(self.svg_path))[0].get_pixmap(dpi=100).save(png)
        self.assertGreater(png.stat().st_size, 1000)


if __name__ == "__main__":
    unittest.main()
