"""Offline tests for the hand-layout path of docs\\sim\\circuits.py and docs\\sim\\symbols.py (00_coordination/T028).
Fixtures only; the legacy opa2192_buffer_step.cir is a test fixture, its vendor model is not available (symbol-only path).
Run: python -m unittest discover docs\\sim\\tests"""
import contextlib
import io
import pathlib
import re
import sys
import tempfile
import unittest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import circuits  # noqa: E402
import symbols  # noqa: E402


def np_arange(a, b, step):
    import numpy as np
    return np.arange(a, b, step)

FIX = HERE / "fixtures"
LOOP, LOOP_LAYOUT, LOOP_FACTS = FIX / "loop_tb.cir", FIX / "loop_tb_layout.py", FIX / "FACTS_loop_sample.md"
BUF, BUF_LAYOUT, BUF_FACTS = FIX / "opa2192_buffer_step.cir", FIX / "opa2192_buffer_step_layout.py", FIX / "FACTS_opax192_sample.md"
DATE = "2026-10-23"
RED_BOX = 'fill="#fee2e2"'


def run(*args):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = circuits.main([*map(str, args), "--date", DATE])
    return code, buf.getvalue()


class Hand(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.d = pathlib.Path(cls.tmp.name)
        cls.code, cls.out = run(LOOP, "--layout", LOOP_LAYOUT, "--pin-map", LOOP_FACTS, "--out", cls.d / "loop")
        cls.svg = (cls.d / "loop" / "circuit.svg").read_text(encoding="utf-8")
        cls.bcode, cls.bout = run(BUF, "--layout", BUF_LAYOUT, "--pin-map", BUF_FACTS, "--out", cls.d / "buf")
        cls.bsvg = (cls.d / "buf" / "circuit.svg").read_text(encoding="utf-8")

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def schematic(self, cir=LOOP):
        nl = circuits.Netlist(cir)
        return nl, symbols.Schematic(nl, "t", 600, 600)

    def write(self, name, text):
        p = self.d / name
        p.write_text(text, encoding="utf-8")
        return p

    # ---- the two figures
    def test_hand_layouts_run(self):
        self.assertEqual(self.code, 0, self.out)
        self.assertEqual(self.bcode, 0, self.bout)
        self.assertIn("8 elements drawn once", self.out)
        self.assertIn("4 elements drawn once", self.bout)
        self.assertIn("(hand layout)", self.svg)
        self.assertNotIn("DRAFT", self.svg)

    def test_every_element_drawn_once_and_finish_clean(self):
        nl, sh = self.schematic()
        circuits.load_layout(LOOP_LAYOUT)["fn"](sh, nl)
        self.assertEqual(sh.finish(), [])
        self.assertEqual(sorted(sh.drawn), sorted(nl.comps))

    def test_dropped_element_fails(self):
        keep = [ln for ln in LOOP_LAYOUT.read_text(encoding="utf-8").splitlines() if "C_FILT" not in ln]
        p = self.write("no_cfilt.py", "\n".join(keep) + "\n")
        code, out = run(LOOP, "--layout", p, "--out", self.d / "nc")
        self.assertEqual(code, 1)
        self.assertIn("VIOLATION: netlist element C_FILT not drawn", out)
        self.assertFalse((self.d / "nc" / "circuit.svg").exists())

    def test_element_twice_or_unknown_is_an_error(self):
        p = self.write("twice.py", "def layout(sh, nl):\n    sh.resistor('R1', 100, 100)\n    sh.resistor('R1', 300, 100)\n")
        code, out = run(FIX / "sample_tb.cir", "--layout", p, "--out", self.d / "tw")
        self.assertEqual(code, 2)
        p = self.write("ghost.py", "def layout(sh, nl):\n    sh.resistor('GHOST', 100, 100)\n")
        self.assertEqual(run(LOOP, "--layout", p, "--out", self.d / "gh")[0], 2)
        p = self.write("nofn.py", "X = 1\n")
        code, out = run(LOOP, "--layout", p, "--out", self.d / "nf")
        self.assertEqual(code, 2)
        self.assertIn("must define layout(sh, nl)", out)

    def test_unknown_element_letter_errors(self):
        p = self.write("bad.cir", "R1 a 0 1k\nR2 a 0 1k\nG1 a 0 b 0 1m\n")
        code, out = run(p, "--out", self.d / "bad")
        self.assertEqual(code, 2)
        self.assertIn("unsupported element", out)

    def test_wire_between_different_nets_fails(self):
        nl, sh = self.schematic()
        sh.resistor("R_SENSE", 100, 100)
        sh.resistor("RB", 300, 100)
        with self.assertRaises(ValueError):
            sh.wire(("R_SENSE", 0), ("RB", 0))

    def test_determinism(self):
        code, _ = run(LOOP, "--layout", LOOP_LAYOUT, "--pin-map", LOOP_FACTS, "--out", self.d / "again")
        self.assertEqual(code, 0)
        for f in ("circuit.svg", "circuit.png"):
            self.assertEqual((self.d / "again" / f).read_bytes(), (self.d / "loop" / f).read_bytes())

    # ---- probes
    def test_red_probe_box_for_each_save(self):
        self.assertEqual(self.svg.count(RED_BOX), 2)       # V(SENSE_N), I(R_SENSE)
        self.assertEqual(self.bsvg.count(RED_BOX), 2)      # V(OUT), V(INP)
        for sig in ("V(SENSE_N)", "I(R_SENSE)"):
            self.assertIn(f">{sig}</text>", self.svg)

    def test_probe_forms_diff_and_pin(self):
        cir = FIX / "probes_tb.cir"
        nl = circuits.Netlist(cir)
        self.assertEqual(circuits.signal_info(nl, "V(A,B)")["nets"], ["A", "B"])
        self.assertEqual(circuits.signal_info(nl, "I(XU1:out)")["pin"], 1)
        self.assertEqual(circuits.signal_info(nl, "I(XU1:2)")["pin"], 1)
        self.assertIn("error", circuits.signal_info(nl, "I(XU1:nope)"))
        self.assertIn("error", circuits.signal_info(nl, "I(V1:out)"))
        code, out = run(cir, "--out", self.d / "p")                # automatic DRAFT draws every form
        self.assertEqual(code, 0, out)
        svg = (self.d / "p" / "circuit.svg").read_text(encoding="utf-8")
        for sig in ("V(A,B)", "I(XU1:out)", "V(B)"):
            self.assertIn(f">{sig}</text>", svg)
        self.assertEqual(svg.count(RED_BOX), 3)
        draft = self.d / "probes_draft.py"                          # and the draft layout script does
        self.assertEqual(run(cir, "--draft", draft)[0], 0)
        text = draft.read_text(encoding="utf-8")
        self.assertIn("probe_diff('V(A,B)'", text)
        self.assertIn("probe_pin('I(XU1:out)'", text)
        code, out = run(cir, "--layout", draft, "--out", self.d / "pd")
        self.assertEqual(code, 0, out)
        self.assertEqual((self.d / "pd" / "circuit.svg").read_text(encoding="utf-8").count(RED_BOX), 3)

    def test_unresolvable_pin_is_a_violation(self):
        p = self.write("pin.cir", (FIX / "probes_tb.cir").read_text(encoding="utf-8").replace("I(XU1:out)", "I(XU1:nope)"))
        code, out = run(p, "--out", self.d / "np")
        self.assertEqual(code, 1)
        self.assertIn("pin nope not found in .subckt BUF", out)

    def test_probe_on_the_wrong_net_raises(self):
        nl, sh = self.schematic()
        sh.resistor("R_SENSE", 100, 100)
        with self.assertRaises(ValueError):
            sh.probe_node("V(SENSE_N)", ("R_SENSE", 1))        # that terminal is ground

    # ---- symbols
    def test_rotation_mirrors_pin_order(self):
        nl, sh = self.schematic()
        sh.resistor("R_SENSE", 100, 100, rot=0)
        sh.resistor("RB", 300, 100, rot=180)
        sh.resistor("R_LOAD", 100, 300, rot=90)
        sh.capacitor("C_FILT", 300, 300, rot=270)
        p = sh.pin_xy
        self.assertLess(p[("R_SENSE", 0)][0], p[("R_SENSE", 1)][0])
        self.assertGreater(p[("RB", 0)][0], p[("RB", 1)][0])
        self.assertLess(p[("R_LOAD", 0)][1], p[("R_LOAD", 1)][1])
        self.assertGreater(p[("C_FILT", 0)][1], p[("C_FILT", 1)][1])
        with self.assertRaises(ValueError):
            sh.resistor("V_LOOP", 0, 0, rot=45)

    def test_legacy_vertical_flip_spelling(self):
        nl, sh = self.schematic()
        sh.resistor("R_SENSE", 100, 100, vertical=True, flip=True)
        self.assertGreater(sh.pin_xy[("R_SENSE", 0)][1], sh.pin_xy[("R_SENSE", 1)][1])

    def test_opamp_roles_and_pin_names_from_the_pin_map(self):
        self.assertIn(">IN+ (pin 3)</text>", self.svg)         # DS name of the pin map, not a printed constant
        self.assertIn(">V+ (pin 7)</text>", self.svg)
        self.assertIn(">+IN A (pin 3)</text>", self.bsvg)
        nl, sh = self.schematic()
        with self.assertRaises(ValueError):
            sh.opamp("XU1", 100, 100, roles=("INP", "INN", "VCC", "VCC", "OUT"))

    def test_junction_dots_automatic(self):
        self.assertGreaterEqual(self.svg.count('r="3.6"'), 2)  # supply rail branches, sense node
        self.assertGreaterEqual(self.bsvg.count('r="3.6"'), 2)  # manual dot + feedback tee

    def test_all_element_kinds_via_draft(self):
        cir = FIX / "parts_tb.cir"
        draft = self.d / "parts_draft.py"
        self.assertEqual(run(cir, "--draft", draft)[0], 0)
        code, out = run(cir, "--layout", draft, "--out", self.d / "parts")
        self.assertEqual(code, 0, out)
        self.assertIn("6 elements drawn once", out)
        text = draft.read_text(encoding="utf-8")
        for call in ("isource", "inductor", "diode", "mosfet", "vsource", "resistor"):
            self.assertIn(f"sh.{call}(", text)

    def test_draft_is_deterministic_and_marked(self):
        a, b = self.d / "d1.py", self.d / "d2.py"
        run(LOOP, "--draft", a)
        run(LOOP, "--draft", b)
        self.assertEqual(a.read_bytes(), b.read_bytes())
        self.assertIn("DRAFT layout", a.read_text(encoding="utf-8"))
        code, _ = run(LOOP, "--out", self.d / "auto")
        self.assertIn("automatic DRAFT, not a final figure", (self.d / "auto" / "circuit.svg").read_text(encoding="utf-8"))

    # ---- dashed shapes are explicit segments (T031): identical in SVG and PNG
    def render(self, body, w, h, dpi=144):
        import pymupdf
        svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}"><rect width="{w}" height="{h}" fill="#fff"/>{body}</svg>'
        p = self.d / "dash.svg"
        p.write_text(svg, encoding="utf-8")
        pix = pymupdf.open(str(p))[0].get_pixmap(dpi=dpi)
        import numpy as np
        return np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)[:, :, :3].astype(int), pix.width / w

    def test_sp_box_is_built_from_separate_segments(self):
        import pin_map
        svg = pin_map._box("SP", 20, 20, 200, 26, "SP 1 out")
        self.assertGreaterEqual(svg.count('class="dash"'), 20)
        self.assertNotIn("stroke-dasharray", svg)
        a, k = self.render(svg, 260, 70)
        row = a[int(round(20 * k))]                                        # the top edge of the box
        x0, x1 = int((20 + 15) * k), int((20 + 200 - 15) * k)
        dark = [(p[0] > 170 and p[1] < 150 and p[2] < 90) for p in row[x0:x1]]
        changes = sum(1 for i in range(1, len(dark)) if dark[i] != dark[i - 1])
        self.assertGreaterEqual(changes, 20, "alternating stroke / fill pixels along the dashed edge, not a solid line")

    def test_to_net_stub_is_dashed_in_the_png(self):
        nl, sh = self.schematic()
        sh.resistor("R_SENSE", 100, 200, vertical=True)
        sh.byname(("R_SENSE", 0), 0, -70)
        svg = "".join(sh.out)
        self.assertGreaterEqual(svg.count('class="dash"'), 8)
        self.assertNotIn("stroke-dasharray", svg)
        a, k = self.render(svg, 300, 300)
        px, py = sh.pin_xy[("R_SENSE", 0)]
        col = [int(a[int(round(y * k)), int(round(px * k))].sum() < 3 * 215) for y in np_arange(py - 66, py - 4, 0.25)]
        changes = sum(1 for i in range(1, len(col)) if col[i] != col[i - 1])
        self.assertGreaterEqual(changes, 10)

    def test_no_stroke_dasharray_anywhere_in_circuit_output(self):
        for svg in (self.svg, self.bsvg):
            self.assertNotIn("stroke-dasharray", svg)
        code, _ = run(LOOP, "--out", self.d / "autoc")                    # automatic draft: "net X" stubs, SP-free
        self.assertNotIn("stroke-dasharray", (self.d / "autoc" / "circuit.svg").read_text(encoding="utf-8"))

    def test_out_required_without_draft(self):
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                circuits.main([str(LOOP)])


if __name__ == "__main__":
    unittest.main()
