"""Offline tests for docs\\sim\\circuits.py (00_coordination/T027). Fixtures only (no real part values); output in a temp dir.
Run: python -m unittest discover docs\\sim\\tests"""
import contextlib
import hashlib
import io
import json
import pathlib
import sys
import tempfile
import unittest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import circuits  # noqa: E402

FIX = HERE / "fixtures"
CIR = FIX / "loop_tb.cir"
FACTS = FIX / "FACTS_loop_sample.md"
DATE = "2026-10-23"


def run(*args):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = circuits.main([*map(str, args), "--date", DATE])
    return code, buf.getvalue()


def sha(p):
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()


class Circuits(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.d = pathlib.Path(cls.tmp.name)
        cls.code, cls.stdout = run(CIR, "--out", cls.d / "a", "--pin-map", FACTS)
        cls.svg = (cls.d / "a" / "circuit.svg").read_text(encoding="utf-8")
        cls.plain_code, cls.plain_out = run(CIR, "--out", cls.d / "plain")
        cls.plain = (cls.d / "plain" / "circuit.svg").read_text(encoding="utf-8")

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def cir(self, text, name="t.cir"):
        p = self.d / name
        p.write_text(text, encoding="utf-8")
        return p

    def test_run_ok_and_png(self):
        self.assertEqual(self.code, 0, self.stdout)
        self.assertTrue((self.d / "a" / "circuit.png").stat().st_size > 5000)
        self.assertIn("8 elements drawn once", self.stdout)

    def test_every_element_drawn_once(self):
        nl = circuits.Netlist(CIR)
        sh, _ = circuits.draw(nl)
        self.assertEqual(sh.finish(), [])
        self.assertEqual(sorted(sh.drawn), sorted(nl.comps))
        self.assertEqual(len(nl.comps), 8)
        for name in nl.comps:
            self.assertIn(f">{name}</text>", self.svg)

    def test_dropped_element_fails_finish(self):
        nl = circuits.Netlist(CIR)
        sh, _ = circuits.draw(nl, skip={"R_SENSE"})
        self.assertTrue(any("R_SENSE not drawn" in v for v in sh.finish()))

    def test_drawn_but_not_in_netlist_fails_finish(self):
        nl = circuits.Netlist(CIR)
        sh, _ = circuits.draw(nl)
        with self.assertRaises(KeyError):
            sh.comp("GHOST")
        sh.drawn["GHOST"] = set()
        self.assertTrue(any("GHOST drawn but not in the netlist" in v for v in sh.finish()))

    def test_unknown_element_letter_errors(self):
        for line in ("E1 a b c d 2", "B1 a b I=1", "K1 L1 L2 0.9"):
            p = self.cir(f"R1 a 0 1k\nR2 a b 1k\n{line}\n")
            code, out = run(p, "--out", self.d / "bad")
            self.assertEqual(code, 2, line)
            self.assertIn("unsupported element", out)
        with self.assertRaises(circuits.NetlistError):
            circuits.Netlist(self.cir("Z9 a b 1\n"))

    def test_subckt_body_is_skipped(self):
        p = self.cir(".subckt SUBX a b\nE1 a b a b 2\n.ends\nR1 n1 0 1k\nR2 n1 0 1k\n")
        self.assertEqual(list(circuits.Netlist(p).comps), ["R1", "R2"])

    def test_floating_net_is_a_violation(self):
        p = self.cir("R1 a 0 1k\nR2 a 0 1k\nR_X FLOAT_N 0 1k\n")
        code, out = run(p, "--out", self.d / "float")
        self.assertEqual(code, 1)
        self.assertIn("VIOLATION: net FLOAT_N: only 1 terminal", out)
        self.assertFalse((self.d / "float" / "circuit.svg").exists())

    def test_save_of_unknown_signal_is_a_violation(self):
        p = self.cir("R1 a 0 1k\nR2 a 0 1k\n.save V(NOPE) I(R_NONE) X(a)\n")
        code, out = run(p, "--out", self.d / "save")
        self.assertEqual(code, 1)
        self.assertEqual(out.count("VIOLATION"), 3)

    def test_probe_labels_present(self):
        self.assertIn("V(SENSE_N)", self.svg)
        self.assertIn("I(R_SENSE)", self.svg)

    def test_determinism(self):
        code, _ = run(CIR, "--out", self.d / "b", "--pin-map", FACTS)
        self.assertEqual(code, 0)
        self.assertEqual((self.d / "b" / "circuit.svg").read_bytes(), (self.d / "a" / "circuit.svg").read_bytes())
        self.assertEqual((self.d / "b" / "circuit.png").read_bytes(), (self.d / "a" / "circuit.png").read_bytes())

    def test_layout_hints_override(self):
        nl = circuits.Netlist(CIR)
        auto = circuits.place(nl, {})
        self.assertNotEqual(auto[0][0]["name"], "R_SENSE")
        hints = self.d / "hints.json"
        hints.write_text(json.dumps({"R_SENSE": {"row": 0, "col": 0, "rot": 180}}), encoding="utf-8")
        self.assertEqual(circuits.place(nl, circuits.load_hints(hints, nl))[0][0], dict(name="R_SENSE", rot=180))
        code, _ = run(CIR, "--out", self.d / "h", "--layout", hints)
        self.assertEqual(code, 0)
        self.assertNotEqual((self.d / "h" / "circuit.svg").read_bytes(), (self.d / "plain" / "circuit.svg").read_bytes())
        self.assertIn("layout: hints.json", (self.d / "h" / "circuit.svg").read_text(encoding="utf-8"))

    def test_bad_layout_hint_errors(self):
        hints = self.d / "bad.json"
        hints.write_text(json.dumps({"NOT_THERE": {"row": 0}}), encoding="utf-8")
        code, out = run(CIR, "--out", self.d / "h2", "--layout", hints)
        self.assertEqual(code, 2)
        self.assertIn("not an element", out)

    def test_pin_map_prefixes(self):
        for s in ("DS 3 IN+ D92 p.3", "SP 1 inp", "TB REF_N", "Legend"):
            self.assertIn(s, self.svg)
        self.assertIn("UNMAPPED TERMINALS: 1", self.svg)  # V- node name is "?"
        self.assertIn("SP ?", self.svg)

    def test_without_pin_map(self):
        self.assertIn("pin map: none", self.plain)
        self.assertNotIn("UNMAPPED", self.plain)
        self.assertNotIn('class="DS', self.plain)
        self.assertNotIn('class="SP', self.plain)
        self.assertIn("TB REF_N", self.plain)

    def test_part_override_and_missing_row_warning(self):
        code, out = run(CIR, "--out", self.d / "p", "--pin-map", FACTS, "--part", "XU1=OTHERPART")
        self.assertEqual(code, 0)
        self.assertEqual(out.count("WARNING"), 5)  # no table rows for OTHERPART

    def test_footer_hashes_and_date(self):
        self.assertIn(sha(CIR), self.svg)
        self.assertIn(sha(FIX / "models" / "opampx.sub"), self.svg)
        self.assertIn(DATE, self.svg)
        self.assertIn("loop_tb.cir", self.svg)

    def test_missing_model_file_is_marked(self):
        p = self.cir(".include models/none.sub\nR1 a 0 1k\nR2 a 0 1k\n")
        code, out = run(p, "--out", self.d / "m")
        self.assertEqual(code, 0)
        self.assertIn("WARNING: model file models/none.sub not found", out)
        self.assertIn("NOT FOUND", (self.d / "m" / "circuit.svg").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
