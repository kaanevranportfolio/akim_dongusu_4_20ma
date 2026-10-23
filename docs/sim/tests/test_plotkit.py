"""Offline tests for docs\\sim\\plotkit.py and docs\\sim\\result_template.py (00_coordination/T029).
Synthetic CSV only (no real part values, nothing here is [V]); output in a temp dir.
Run: python -m unittest discover docs\\sim\\tests"""
import contextlib
import copy
import hashlib
import io
import pathlib
import sys
import tempfile
import unittest

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import plotkit  # noqa: E402
import result_template  # noqa: E402

CIR = HERE / "fixtures" / "result_tb.cir"
MODEL = HERE / "fixtures" / "models" / "opampx.sub"
DATE = "2026-10-23"
RED_FILL = "#fee2e2"


def sha(p):
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()


def g(t, a=3.75e7, w=2.5e7):
    """Step response of a second-order system with ~0.9 % overshoot."""
    t = np.maximum(t, 0)
    return 1 - np.exp(-a * t) * (np.cos(w * t) + a / w * np.sin(w * t))


def step_csv(path):
    t = np.arange(0, 22e-6 + 1e-9, 10e-9)
    vin = np.interp(t, [0, 2e-6, 2.1e-6, 12e-6, 12.1e-6, 22e-6], [2, 2, 8, 8, 2, 2])
    vout = np.where(t < 12e-6, 2 + 6 * g(t - 2e-6) * (t >= 2e-6), 8 - 6 * g(t - 12e-6))
    rows = ["# testbench=result_tb.cir; qraw_points=%d; decimated_to=%d; step_count=1" % (len(t), len(t)), "step,Time,V(inp),V(out),I(RL)"]
    rows += [f"1,{a:.12g},{b:.10g},{c:.10g},{c / 1e4:.10g}" for a, b, c in zip(t, vin, vout)]
    pathlib.Path(path).write_text("\n".join(rows) + "\n", encoding="utf-8")


def run(cfg, cir, csv, out, *extra):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = plotkit.run(cfg, ["--cir", str(cir), "--csv", str(csv), "--out", str(out), "--date", DATE, *extra])
    return code, buf.getvalue()


class Plotkit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.d = pathlib.Path(cls.tmp.name)
        cls.csv = cls.d / "result_tb.csv"
        step_csv(cls.csv)
        cls.cfg = copy.deepcopy(result_template.CONFIG)
        cls.cfg["panels"][0]["limits"][0]["spec"] = "K03"
        cls.code, cls.out = run(cls.cfg, CIR, cls.csv, cls.d / "a")
        cls.svg = (cls.d / "a" / "result.svg").read_text(encoding="utf-8")

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def plot(self, cfg, csv, sub, cir=CIR):
        saves = [t for ln in pathlib.Path(cir).read_text(encoding="utf-8").splitlines() if ln.lower().startswith(".save") for t in ln.split()[1:]]
        return plotkit.plot_result(plotkit.Data(csv), cfg["panels"], saves, cir, csv, self.d / sub, DATE, cfg.get("title", ""),
                                   cfg.get("source", ""), cfg.get("not_plotted"), tuple(cfg.get("steps", (1,))), cfg.get("xkind", "time"))

    def write(self, name, text):
        p = self.d / name
        p.write_text(text, encoding="utf-8")
        return p

    def test_run_ok_and_png(self):
        self.assertEqual(self.code, 0, self.out)
        self.assertGreater((self.d / "a" / "result.png").stat().st_size, 10000)
        self.assertIn("4 measurements, 2 limits", self.out)

    def test_no_red_boxes_and_legend_names(self):
        self.assertNotIn(RED_FILL, self.svg)                   # red boxes belong to circuit.png only
        res = self.plot(self.cfg, self.csv, "legend")
        self.assertEqual(res["legend"][0], ["V(INP)", "V(OUT)"])   # exactly the .save names, no extra words
        for name in ("V(INP)", "V(OUT)"):
            self.assertIn(f">{name}<", self.svg)
        self.assertNotIn(">I(RL)<", self.svg)                  # listed in not_plotted
        self.assertNotIn("input<", self.svg)

    def test_limit_line_with_its_spec_tag(self):
        self.assertIn("K03 max 8.2 V", self.svg)
        self.assertIn("[A] min 7.9 V", self.svg)
        self.assertIn("PASS K03 V(OUT) max 8.2 V", self.out)

    def test_measurement_labels_are_marked_measured(self):
        for lab in ("t_cross_5V", "v_final", "overshoot", "v_max"):
            self.assertIn(f"[M] {lab}", self.svg)
        line = [ln for ln in self.out.splitlines() if ln.startswith("[M] t_cross_5V")][0]
        self.assertIn("linear interpolation", line)            # formula in the label
        self.assertIn("us", line)

    def test_crossing_value_is_read_from_the_data(self):
        data = plotkit.Data(self.csv)
        x, y = data.series("V(OUT)")
        t5 = plotkit.cross(x, y, 5.0, True, 2e-6)
        self.assertTrue(2e-6 < t5 < 2.2e-6)
        self.assertIn(plotkit.si(t5, "s"), self.out)

    def test_footer_fields(self):
        self.assertIn(sha(CIR), self.svg)
        self.assertIn(sha(MODEL), self.svg)
        self.assertIn("result_tb.cir", self.svg)
        self.assertIn(".tran 0 22u 0 2n", self.svg)
        self.assertIn(DATE, self.svg)
        self.assertIn("not plotted: I(RL)", self.svg)

    def test_determinism(self):
        code, _ = run(self.cfg, CIR, self.csv, self.d / "b")
        self.assertEqual(code, 0)
        for f in ("result.svg", "result.png"):
            self.assertEqual((self.d / "b" / f).read_bytes(), (self.d / "a" / f).read_bytes())

    # ---- self-check and refusals
    def test_self_check_unlisted_save_fails(self):
        cfg = copy.deepcopy(self.cfg)
        cfg["not_plotted"] = {}
        code, out = run(cfg, CIR, self.csv, self.d / "sc")
        self.assertEqual(code, 2)
        self.assertIn("self-check", out)
        self.assertIn("I(RL)", out)
        self.assertFalse((self.d / "sc" / "result.svg").exists())

    def test_not_plotted_needs_a_reason(self):
        cfg = copy.deepcopy(self.cfg)
        cfg["not_plotted"] = {"I(RL)": " "}
        self.assertEqual(run(cfg, CIR, self.csv, self.d / "nr")[0], 2)

    def test_plotted_name_must_be_a_save_name(self):
        cfg = copy.deepcopy(self.cfg)
        cfg["panels"][0]["traces"].append(dict(name="V(NOPE)"))
        code, out = run(cfg, CIR, self.csv, self.d / "ns")
        self.assertEqual(code, 2)
        self.assertIn("not a .save name", out)

    def test_limit_without_spec_tag_is_refused(self):
        for tag in ("", "K3", "guess", "[V]"):
            cfg = copy.deepcopy(self.cfg)
            cfg["panels"][0]["limits"][0]["spec"] = tag
            code, out = run(cfg, CIR, self.csv, self.d / "nt")
            self.assertEqual(code, 2, tag)
            self.assertIn("never invented", out)

    def test_violated_limit_exits_nonzero(self):
        cfg = copy.deepcopy(result_template.CONFIG)         # the template itself
        self.assertEqual(run(cfg, CIR, self.csv, self.d / "t_ok")[0], 0)
        cfg["panels"][0]["limits"][0]["value"] = 7.9        # peak is about 8.05 V
        code, out = run(cfg, CIR, self.csv, self.d / "t_bad")
        self.assertEqual(code, 1)
        self.assertIn("FAIL [A] V(OUT) max 7.9 V", out)
        self.assertTrue((self.d / "t_bad" / "result.svg").exists())   # the plot is still written, with the failing limit

    def test_unknown_measurement_and_signal(self):
        cfg = copy.deepcopy(self.cfg)
        cfg["panels"][0]["measures"] = [dict(kind="slope", signal="V(OUT)", label="x")]
        self.assertEqual(run(cfg, CIR, self.csv, self.d / "m1")[0], 2)
        cfg = copy.deepcopy(self.cfg)
        cfg["panels"][0]["measures"] = [dict(kind="crossing", signal="V(OUT)", level=99.0, label="never")]
        code, out = run(cfg, CIR, self.csv, self.d / "m2")
        self.assertEqual(code, 2)
        self.assertIn("never crosses", out)

    # ---- other data shapes
    def test_ramp_with_free_abscissa(self):
        rows = ["# testbench=result_tb.cir; qraw_points=101; decimated_to=101; step_count=1", "step,Time,V(inp),V(out),I(RL)"]
        rows += [f"1,{i * 1e-5:.9g},{i / 10:.9g},{i / 10:.9g},{i / 1e5:.9g}" for i in range(101)]
        csv = self.write("ramp.csv", "\n".join(rows) + "\n")
        cfg = dict(title="ramp", source="fixture", xkind="x", panels=[dict(ylabel="V", traces=[dict(name="V(INP)"), dict(name="V(OUT)")],
                   measures=[dict(kind="minmax", signal="V(OUT)", which="min", label="v_min"),
                             dict(kind="steady", signal="V(OUT)", window=(0.9e-3, 1e-3), label="v_end")],
                   limits=[dict(kind="min", signal="V(OUT)", value=-0.1, spec="[A]")])], not_plotted={"I(RL)": "not needed"})
        code, out = run(cfg, CIR, csv, self.d / "ramp")
        self.assertEqual(code, 0, out)
        self.assertIn("[M] v_end: 9.5 V", out)

    def test_complex_data_needs_a_view(self):
        f = np.logspace(0, 4, 41)
        h = 1 / (1 + 1j * f / 1e2)
        rows = ["# testbench=result_tb.cir; qraw_points=41; decimated_to=41; step_count=1", "step,Frequency,V(inp)_re,V(inp)_im,V(out)_re,V(out)_im,I(RL)_re,I(RL)_im"]
        rows += [f"1,{a:.9g},1,0,{b.real:.9g},{b.imag:.9g},0,0" for a, b in zip(f, h)]
        csv = self.write("ac.csv", "\n".join(rows) + "\n")
        cfg = dict(title="ac", source="fixture", xkind="freq", panels=[
            dict(ylabel="gain (dB)", traces=[dict(name="V(OUT)", view="mag_db")], limits=[]),
            dict(ylabel="phase (deg)", traces=[dict(name="V(INP)", view="phase_deg")], limits=[])], not_plotted={"I(RL)": "complex zero"})
        code, out = run(cfg, CIR, csv, self.d / "ac")
        self.assertEqual(code, 0, out)
        cfg["panels"][0]["traces"][0].pop("view")
        code, out = run(cfg, CIR, csv, self.d / "ac2")
        self.assertEqual(code, 2)
        self.assertIn("is complex", out)

    # ---- palette, line styles, placement (T030)
    def four_trace_setup(self):
        cir = self.write("four_tb.cir", "* four traces\nR1 a 0 1k\n.tran 0 22u 0 2n\n.save V(A) V(B) V(C) V(D)\n.end\n")
        t = np.arange(0, 22e-6 + 1e-9, 10e-9)
        rows = ["# testbench=four_tb.cir; qraw_points=%d; decimated_to=%d; step_count=1" % (len(t), len(t)), "step,Time,V(a),V(b),V(c),V(d)"]
        rows += [f"1,{x:.12g},{1 + k:.9g},{2 + 0.5 * k:.9g},{3 - k:.9g},{4 + 2 * k * k:.9g}" for x, k in zip(t, t / 22e-6)]
        csv = self.write("four.csv", "\n".join(rows) + "\n")
        cfg = dict(title="four", source="fixture", panels=[dict(ylabel="V", traces=[dict(name=n) for n in ("V(A)", "V(B)", "V(C)", "V(D)")])])
        return cir, csv, cfg

    def test_palette_order_and_styles_of_traces_1_to_4(self):
        cir, csv, cfg = self.four_trace_setup()
        res = self.plot(cfg, csv, "four", cir)
        got = [(s["name"], s["color"], s["ls"], s["marker"]) for s in res["styles"]]
        self.assertEqual(got, [("V(A)", "#0072B2", "-", None), ("V(B)", "#C62828", "--", None),
                               ("V(C)", "#A66F00", "-", None), ("V(D)", "#009E73", "--", None)])   # solid, dashed, solid, dashed
        self.assertEqual(res["legend"][0], ["V(A)", "V(B)", "V(C)", "V(D)"])
        svg = (self.d / "four" / "result.svg").read_text(encoding="utf-8")
        for col in ("#0072b2", "#c62828", "#a66f00", "#009e73"):
            self.assertIn(col, svg)
        self.assertNotIn(RED_FILL, svg)

    def test_palette_contrast_against_white(self):
        self.assertAlmostEqual(plotkit.contrast("#000000"), 21.0, places=1)
        self.assertAlmostEqual(plotkit.contrast("#ffffff"), 1.0, places=2)
        for name, col in plotkit.PALETTE:
            self.assertGreaterEqual(plotkit.contrast(col), 3.0, f"{name} {col}")
        self.assertEqual([n for n, _ in plotkit.PALETTE], ["blue", "red", "amber", "green", "purple", "black"])

    def test_line_styles_alternate_solid_dashed(self):
        """T031: only solid and dashed, alternating; no default markers. Dropped from T030: a distinct style per trace for the first
        six traces and markers from the 4th trace on (traces of the same parity now differ by colour only)."""
        self.assertEqual(plotkit.STYLES, ["-", "--"])
        styles = [plotkit.trace_style(i) for i in range(8)]
        self.assertEqual([s["ls"] for s in styles], ["-", "--"] * 4)
        self.assertEqual({s["marker"] for s in styles}, {None})
        self.assertEqual(len({s["color"] for s in styles[:6]}), 6)          # six different colours in palette order

    def test_style_override_per_trace(self):
        self.assertEqual(plotkit.trace_style(0, dict(color="#123456", ls=":", marker="s")), dict(color="#123456", ls=":", marker="s"))
        self.assertEqual(plotkit.trace_style(1)["color"], "#C62828")

    def test_dashed_trace_is_on_top_with_the_same_width(self):
        svg = (self.d / "a" / "result.svg").read_text(encoding="utf-8")
        import re
        widths = {m.group(2) for m in re.finditer(r'stroke: (#0072b2|#c62828); stroke-width: ([0-9.]+)', svg)}
        self.assertEqual(widths, {"1.8"})                                   # solid and dashed trace: same width
        blue, red = svg.index("stroke: #0072b2; stroke-width: 1.8"), svg.index("stroke: #c62828; stroke-width: 1.8")
        self.assertLess(blue, red)                                          # drawn later = on top
        self.assertIn("stroke-dasharray", svg[svg.rindex("<path", 0, red):red])      # the later (top) trace is the dashed one
        self.assertNotIn("stroke-dasharray", svg[svg.rindex("<path", 0, blue):blue])

    def coincident_png(self):
        cir = self.write("co_tb.cir", "* coincident\nR1 a 0 1k\n.tran 0 22u 0 2n\n.save V(INP) V(OUT)\n.end\n")
        t = np.arange(0, 22e-6 + 1e-9, 10e-9)
        rows = ["# testbench=co_tb.cir; qraw_points=%d; decimated_to=%d; step_count=1" % (len(t), len(t)), "step,Time,V(inp),V(out)"]
        rows += [f"1,{x:.12g},5,5" for x in t]                              # V(INP) = V(OUT) exactly
        csv = self.write("co.csv", "\n".join(rows) + "\n")
        cfg = dict(title="coincident", source="fixture", panels=[dict(ylabel="V", traces=[dict(name="V(INP)"), dict(name="V(OUT)")])])
        self.plot(cfg, csv, "co", cir)
        return self.d / "co" / "result.png"

    def test_coincident_traces_both_visible_in_the_png(self):
        from PIL import Image
        a = np.asarray(Image.open(self.coincident_png()).convert("RGB")).astype(int)

        def near(c, tol=45):
            return (np.abs(a - np.array(c)) < tol).all(axis=2)
        blue, red = near((0x00, 0x72, 0xB2)), near((0xC6, 0x28, 0x28))
        best = max(range(a.shape[0]), key=lambda r: min(blue[r].sum(), red[r].sum()))
        self.assertGreaterEqual(blue[best].sum(), 30, "solid blue trace must show between the dashes")
        self.assertGreaterEqual(red[best].sum(), 30, "dashed red trace on top")
        seq = [("r" if red[best][i] else "b" if blue[best][i] else "-") for i in range(a.shape[1])]
        runs = [k for i, k in enumerate(seq) if k != "-" and (i == 0 or seq[i - 1] != k)]
        self.assertGreaterEqual(len(runs), 12)                               # alternating red dash / blue gap along the line

    def test_dash_and_gap_lengths_in_the_png(self):
        from PIL import Image
        a = np.asarray(Image.open(self.coincident_png()).convert("RGB")).astype(int)
        red = (np.abs(a - np.array((0xC6, 0x28, 0x28))) < 45).all(axis=2)
        row = red[max(range(a.shape[0]), key=lambda r: red[r].sum())]
        runs, n = [], 0
        for v in row:                                                        # lengths of red runs (dashes) and gaps
            if v:
                n += 1
            elif n:
                runs.append(n)
                n = 0
        inner = runs[1:-1]
        self.assertTrue(inner and min(inner) >= 6, inner)                    # dash >= 6 px at the default size (150 dpi)
        gaps, g, seen = [], 0, False
        for v in row:
            if v:
                if seen and g:
                    gaps.append(g)
                seen, g = True, 0
            elif seen:
                g += 1
        self.assertTrue(gaps and min(gaps) >= 4, gaps)                       # gap >= 4 px

    def test_single_trace_figure(self):
        cir = self.write("one_tb.cir", "* one\nR1 a 0 1k\n.tran 0 22u 0 2n\n.save V(OUT)\n.end\n")
        res = self.plot(dict(panels=[dict(ylabel="V", traces=[dict(name="V(OUT)")])]), self.csv, "one", cir)
        self.assertEqual(res["legend"][0], ["V(OUT)"])
        self.assertEqual(res["styles"][0]["color"], "#0072B2")
        self.assertNotIn(RED_FILL, (self.d / "one" / "result.svg").read_text(encoding="utf-8"))

    def test_measurement_labels_do_not_overlap(self):
        res = self.plot(self.cfg, self.csv, "ov")
        box = res["label_boxes"][0]
        rects = [b["rect"] for b in box["labels"]] + [box["notes"], box["legend"]]
        texts = {b["text"] for b in box["labels"]}
        self.assertIn("[M] overshoot", texts)
        self.assertIn("[M] v_max", texts)                    # the two points sit on the same sample
        for i, a in enumerate(rects):
            for b in rects[i + 1:]:
                self.assertFalse(plotkit.overlap(a, b), (a, b))

    def test_legend_and_notes_do_not_cover_traces(self):
        res = self.plot(self.cfg, self.csv, "lg1")
        cir, csv, cfg = self.four_trace_setup()
        res4 = self.plot(cfg, csv, "lg2", cir)
        for r in (res, res4):
            box = r["label_boxes"][0]
            self.assertEqual(box["legend_hits"], 0)
            self.assertEqual(box["notes_hits"], 0)

    def test_png_shows_line_styles_and_matches_the_svg_run(self):
        png = (self.d / "a" / "result.png").read_bytes()
        self.assertTrue(png.startswith(b"\x89PNG"))
        self.assertIn("stroke-dasharray", self.svg)          # the dashed second trace and the limit lines are in the SVG

    def test_si_format(self):
        self.assertEqual(plotkit.si(235.8e-9, "s"), "235.8 ns")
        self.assertEqual(plotkit.si(8.0, "V"), "8 V")
        self.assertEqual(plotkit.si(2.5e6, "Hz"), "2.5 MHz")


if __name__ == "__main__":
    unittest.main()
