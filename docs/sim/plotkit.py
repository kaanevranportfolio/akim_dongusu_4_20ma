"""Result plots for QSPICE testbenches (CLAUDE.md Figures; 00_coordination/T029). Generic part of the per-testbench result.py.

Input is the small CSV written by tools\\qraw_export.py (line 1 "# testbench=...", line 2 "step,<abscissa>,<signals>", complex
data as <signal>_re/<signal>_im); no .qraw is read. Trace names are the .save names of the testbench (case does not matter for
the lookup, the label shows the .save spelling).

Legacy look: every plotted trace is named in a LEGEND with exactly its .save name (no extra words) - the same spelling as the
red boxed probe label in circuit.png, so circuit and result are matched by name; there are no red boxes in a result plot. Traces
get an ordered palette (blue, red, amber, green, purple, black; contrast >= 3:1 on white) and alternate solid / dashed line
styles (the dashed one drawn on top, so coincident traces both stay visible). Notes box, legend and [M] labels are placed on free
spots automatically (no overlap with each other or with a trace). Measurements are printed as "[M] <label>: <value> (<formula or
window>)" (measured from the CSV); spec limits are dashed lines tagged with their SPEC number ("K03 max 8.2 V") or "[A]" and are
judged PASS/FAIL from the data. A limit without a K<nn> or [A] tag is refused. The footer carries the SHA-256 of the testbench
and of every model file, the .tran/.ac/.step lines and the run date (an argument, no clock, no repository state).
Same inputs -> same bytes (SVG and PNG).

Declarative use (docs\\sim\\result_template.py): run(CONFIG, argv) reads --cir --csv --out --date, plots, prints PASS/FAIL per limit and
returns 1 on FAIL or on a failed self-check (every .save name is plotted or listed in not_plotted with a reason).
"""
import argparse
import datetime
import hashlib
import pathlib
import re
import sys
import textwrap

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

matplotlib.rcParams["svg.fonttype"] = "none"      # text stays text: names are greppable in the SVG
matplotlib.rcParams["svg.hashsalt"] = "plotkit"   # deterministic ids
matplotlib.rcParams["font.sans-serif"] = ["Arial", "DejaVu Sans"]   # a sans face the PNG renderer knows (as the legacy plots)

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

INK, GREY, RED = "#0f172a", "#64748b", "#b91c1c"   # RED only colours a FAILED limit; signal names are in the legend, not in red boxes
SPEC_RE = re.compile(r"K\d{2}|\[A\]")
SI = [(1e9, "G"), (1e6, "M"), (1e3, "k"), (1, ""), (1e-3, "m"), (1e-6, "u"), (1e-9, "n"), (1e-12, "p")]


class PlotkitError(ValueError):
    pass


def sha256(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def si(value, unit=""):
    """12.5e-9, 's' -> '12.5 ns'."""
    if value == 0 or not np.isfinite(value):
        return f"{value:g} {unit}".strip()
    for scale, pre in SI:
        if abs(value) >= scale:
            return f"{value / scale:.4g} {pre}{unit}".strip()
    return f"{value:.4g} {unit}".strip()


# ---------------------------------------------------------------- data
class Data:
    """CSV of tools\\qraw_export.py: meta, abscissa name, per step a dict of signal arrays (complex signals combined)."""

    def __init__(self, path):
        self.path = pathlib.Path(path)
        lines = self.path.read_text(encoding="utf-8", errors="replace").splitlines()
        self.meta = dict(kv.split("=", 1) for kv in lines[0].lstrip("# ").split("; ") if "=" in kv)
        head = lines[1].split(",")
        self.xname, cols = head[1], head[2:]
        rows = {}
        for ln in lines[2:]:
            a = ln.split(",")
            rows.setdefault(int(a[0]), []).append([float(v) for v in a[1:]])
        self.steps = {}
        for k, r in rows.items():
            arr = np.array(r)
            d = {self.xname: arr[:, 0]}
            for j, c in enumerate(cols, 1):
                if c.endswith("_im"):
                    continue
                if c.endswith("_re"):
                    base = c[:-3]
                    d[base] = arr[:, j] + 1j * arr[:, cols.index(base + "_im") + 1]
                else:
                    d[c] = arr[:, j]
            self.steps[k] = d
        self.names = [c for c in dict.fromkeys(re.sub(r"_(re|im)$", "", c) for c in cols)]

    def series(self, name, step=1):
        """(x, y) of signal `name` (case-insensitive) in `step`."""
        d = self.steps[step]
        for n in d:
            if n.lower() == name.lower() and n != self.xname:
                return d[self.xname], d[n]
        raise PlotkitError(f"signal {name} not in {self.path.name} (columns: {', '.join(self.names)})")


def cross(x, y, level, rising=True, start=0.0):
    """First interpolated x at or after `start` where y crosses level (rising or falling), or None."""
    for i in range(1, len(x)):
        if x[i] < start:
            continue
        a, b = y[i - 1] - level, y[i] - level
        if (rising and a < 0 <= b) or (not rising and a > 0 >= b):
            return x[i - 1] + (x[i] - x[i - 1]) * (-a) / (b - a) if b != a else x[i]
    return None


def window(x, y, w):
    if w is None:
        return x, y
    m = (x >= w[0]) & (x <= w[1])
    if not m.any():
        raise PlotkitError(f"window {w} contains no samples")
    return x[m], y[m]


# ---------------------------------------------------------------- measurements and limits
def measure(data, spec, step, xunit):  # xunit = base unit of the abscissa ("s", "Hz" or "")
    """One declarative measurement -> dict(label, text, value, point). Every value is read from the CSV [M]."""
    kind, sig = spec["kind"], spec["signal"]
    x, y = data.series(sig, step)
    y = np.real(y)
    label = spec["label"]
    xu = xunit
    pt = None
    if kind == "crossing":
        lvl, rising = spec["level"], spec.get("rising", True)
        after = spec.get("after", 0.0)
        v = cross(x, y, lvl, rising, after)
        if v is None:
            raise PlotkitError(f"measurement {label}: {sig} never crosses {lvl:g} ({'rising' if rising else 'falling'}) after {after:g}")
        text = f"{si(v, xu)}  (first {'rising' if rising else 'falling'} crossing of {lvl:g}, linear interpolation, after {si(after, xu)})"
        pt = (v, lvl)
        val = v
    elif kind == "steady":
        xs, ys = window(x, y, spec["window"])
        val = float(np.mean(ys))
        w = spec["window"]
        text = f"{si(val, spec.get('unit', 'V'))}  (mean of {sig} over {si(w[0], xu)} .. {si(w[1], xu)})"
        pt = (float(np.mean(xs)), val)
    elif kind == "overshoot":
        xs, ys = window(x, y, spec["window"])
        _, yr = window(x, y, spec["ref_window"])
        ref = float(np.mean(yr))
        i = int(np.argmax(ys)) if spec.get("direction", "up") == "up" else int(np.argmin(ys))
        val = float(ys[i] - ref)
        text = (f"{si(val, spec.get('unit', 'V'))}  (peak of {sig} in {si(spec['window'][0], xu)} .. {si(spec['window'][1], xu)} "
                f"minus mean over {si(spec['ref_window'][0], xu)} .. {si(spec['ref_window'][1], xu)})")
        pt = (float(xs[i]), float(ys[i]))
    elif kind == "minmax":
        xs, ys = window(x, y, spec.get("window"))
        which = spec["which"]
        i = int(np.argmax(ys)) if which == "max" else int(np.argmin(ys))
        val = float(ys[i])
        w = spec.get("window")
        text = f"{si(val, spec.get('unit', 'V'))}  ({which} of {sig}" + (f" over {si(w[0], xu)} .. {si(w[1], xu)})" if w else " over the whole run)")
        pt = (float(xs[i]), val)
    else:
        raise PlotkitError(f"unknown measurement kind '{kind}'")
    return dict(label=label, text=text, value=val, point=pt, signal=sig, line=f"[M] {label}: {text}")


def judge(data, spec, steps):
    """Spec limit -> dict(spec, kind, value, unit, observed, ok, line). The tag must be K<nn> or [A]."""
    tag = spec.get("spec", "")
    if not SPEC_RE.fullmatch(tag):
        raise PlotkitError(f"limit on {spec.get('signal')} has no SPEC tag: spec must be 'K<nn>' or '[A]' (got {tag!r}); a limit is never invented")
    vals = []
    for s in steps:
        x, y = data.series(spec["signal"], s)
        _, yy = window(x, np.real(y), spec.get("window"))
        vals.append(yy)
    allv = np.concatenate(vals)
    obs = float(allv.max() if spec["kind"] == "max" else allv.min())
    ok = obs <= spec["value"] if spec["kind"] == "max" else obs >= spec["value"]
    unit = spec.get("unit", "V")
    word = "PASS" if ok else "FAIL"
    return dict(spec=tag, kind=spec["kind"], value=spec["value"], unit=unit, signal=spec["signal"], observed=obs, ok=ok,
                line=f"{word} {tag} {spec['signal']} {spec['kind']} {spec['value']:g} {unit}: observed {spec['kind']} {obs:.6g} {unit} [M]")


def unplotted(saves, panels, not_plotted):
    """.save names that are neither plotted nor listed (with a reason) in not_plotted."""
    shown = {t["name"].lower() for p in panels for t in p["traces"]} | {k.lower() for k in not_plotted}
    return [s for s in saves if s.lower() not in shown]


# ---------------------------------------------------------------- footer
def analysis_lines(cir_text):
    out = []
    for ln in cir_text.splitlines():
        t = ln.split(";")[0].strip()
        if re.match(r"\.(tran|ac|dc|op|noise|step)\b", t, re.I):
            out.append(t)
    return out


def model_files(cir_path, cir_text):
    out = []
    for ln in cir_text.splitlines():
        m = re.match(r"\s*\.(?:include|inc|lib)\s+\"?([^\"\s]+)\"?", ln, re.I)
        if m:
            p = pathlib.Path(m.group(1))
            out.append((m.group(1), p if p.is_absolute() else pathlib.Path(cir_path).parent / p))
    return out


def footer(cir_path, csv_path, source, date, cir_text=None):
    cir_path = pathlib.Path(cir_path)
    text = cir_text if cir_text is not None else cir_path.read_text(encoding="utf-8", errors="replace")
    lines = [f"Testbench: {cir_path.name}  SHA256 {sha256(cir_path)}  |  data: {pathlib.Path(csv_path).name}"]
    for name, p in model_files(cir_path, text):
        lines.append(f"Model: {name}  SHA256 {sha256(p) if p.is_file() else 'NOT FOUND'}")
    lines.append("Analysis: " + "  |  ".join(analysis_lines(text)))
    lines.append(f"{source}  |  run date {date}  |  label [C]; [M] = measured from the CSV")
    return lines


# ---------------------------------------------------------------- palette
# One ordered palette, assigned in trace order per panel (Okabe-Ito based; amber, red and purple are darkened to read on white:
# contrast against white >= 3:1, see contrast()). Line style alternates solid, dashed, solid, dashed ...: the dashed trace is
# drawn on top of the solid one, so two coincident traces (input = output) both stay visible; same width, no other styles, no
# default markers. Override per trace with color / ls / marker in CONFIG.
PALETTE = [("blue", "#0072B2"), ("red", "#C62828"), ("amber", "#A66F00"), ("green", "#009E73"), ("purple", "#6A3D9A"), ("black", "#000000")]
STYLES = ["-", "--"]          # "--" at lw 1.8 is a 6.7 pt dash and a 2.9 pt gap (14 px / 6 px in the 150 dpi PNG)


def luminance(hexcolor):
    r, g, b = (int(hexcolor.lstrip("#")[i:i + 2], 16) / 255 for i in (0, 2, 4))
    f = lambda c: c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)


def contrast(hexcolor, background="#ffffff"):
    """WCAG contrast ratio of a colour against the background."""
    a, b = sorted((luminance(hexcolor), luminance(background)), reverse=True)
    return (a + 0.05) / (b + 0.05)


def trace_style(i, spec=None):
    """Colour, line style and marker of trace number i (0-based) of a panel; spec keys color / ls / marker override."""
    spec = spec or {}
    color = PALETTE[i % len(PALETTE)][1]
    return dict(color=spec.get("color", color), ls=spec.get("ls", STYLES[i % len(STYLES)]), marker=spec.get("marker"))


# ---------------------------------------------------------------- placement (free spots, no overlap)
def dense(points, step=0.01):
    """Points along the polyline (axes fractions), at most `step` apart, so a steep edge counts as covered."""
    out = [points[:1]]
    for a, b in zip(points[:-1], points[1:]):
        n = min(60, 1 + int(np.hypot(*(b - a)) / step))
        out.append(np.linspace(a, b, n + 1)[1:])
    return np.vstack(out)


def hits(pts, rect):
    x0, y0, x1, y1 = rect
    return int(((pts[:, 0] >= x0) & (pts[:, 0] <= x1) & (pts[:, 1] >= y0) & (pts[:, 1] <= y1)).sum())


def overlap(a, b):
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def corner_spots(w, h, m=0.012):
    """Candidate rectangles with their text anchor (x, y, ha, va), legacy spot first (right middle)."""
    return [((1 - m - w, 0.5 - h / 2, 1 - m, 0.5 + h / 2), (1 - m, 0.5, "right", "center")),
            ((1 - m - w, 1 - m - h, 1 - m, 1 - m), (1 - m, 1 - m, "right", "top")),
            ((1 - m - w, m, 1 - m, m + h), (1 - m, m, "right", "bottom")),
            ((m, 1 - m - h, m + w, 1 - m), (m, 1 - m, "left", "top")),
            ((m, m, m + w, m + h), (m, m, "left", "bottom")),
            ((m, 0.5 - h / 2, m + w, 0.5 + h / 2), (m, 0.5, "left", "center")),
            ((0.5 - w / 2, 1 - m - h, 0.5 + w / 2, 1 - m), (0.5, 1 - m, "center", "top")),
            ((0.5 - w / 2, m, 0.5 + w / 2, m + h), (0.5, m, "center", "bottom"))]


def pick_spot(w, h, pts, taken):
    """Spot with the fewest trace samples under it and no overlap with `taken` rectangles. -> (cost, rect, anchor)."""
    best = None
    for rect, anchor in corner_spots(w, h):
        cost = hits(pts, rect) + 1000 * sum(overlap(rect, t) for t in taken)
        if best is None or cost < best[0]:
            best = (cost, rect, anchor)
    return best


def label_spot(px, py, w, h, pts, taken):
    """[M] label rectangle next to a point: the first offset with no overlap and no trace under it, else the cheapest."""
    d = 0.006
    offsets = [(d, -h - d), (d, d), (d, -2 * h - 2 * d), (d, h + 2 * d), (-w - d, -h - d), (-w - d, d),
               (d, -3 * h - 3 * d), (d, 2 * h + 3 * d), (-w - d, -2 * h - 2 * d), (-w - d, h + 2 * d)]
    best = None
    for dx, dy in offsets:
        rect = (px + dx, py + dy, px + dx + w, py + dy + h)
        out = (rect[0] < 0 or rect[1] < 0 or rect[2] > 1 or rect[3] > 1)
        cost = hits(pts, rect) + 1000 * sum(overlap(rect, t) for t in taken) + 5000 * out
        if best is None or cost < best[0]:
            best = (cost, rect)
        if cost == 0:
            break
    return best[1]


def loc_word(ha, va):
    v = {"top": "upper", "bottom": "lower", "center": "center"}[va]
    return "center" if (v, ha) == ("center", "center") else f"{v} {ha}"


# ---------------------------------------------------------------- plot
def view_y(y, view, name):
    if view == "mag_db":
        return 20 * np.log10(np.abs(y))
    if view == "phase_deg":
        return np.degrees(np.unwrap(np.angle(y)))
    if np.iscomplexobj(y):
        raise PlotkitError(f"{name} is complex: give view='mag_db' or 'phase_deg'")
    return y


def plot_result(data, panels, saves, cir, csv, out_dir, date, title="", source="", not_plotted=None, steps=(1,), xkind="time"):
    """Draw result.svg + result.png into out_dir. -> dict(measures, limits, ok, svg, png, styles, legend, label_boxes).
    Legacy look: legend with the .save names (the same spelling as the red probe boxes of circuit.png), notes box, black
    measurement dots. Raises PlotkitError for a failed self-check, an unknown signal or a limit without a SPEC tag."""
    not_plotted = not_plotted or {}
    missing = unplotted(saves, panels, not_plotted)
    if missing:
        raise PlotkitError("self-check: .save signal(s) neither plotted nor listed in not_plotted: " + ", ".join(missing))
    canon = {s.lower(): s for s in saves}
    for p in panels:
        for t in p["traces"]:
            if t["name"].lower() not in canon:
                raise PlotkitError(f"plotted signal {t['name']} is not a .save name of the testbench")
    for k, reason in not_plotted.items():
        if not reason.strip():
            raise PlotkitError(f"not_plotted {k}: a reason is required")
    xs_all = np.concatenate([data.steps[s][data.xname] for s in steps])
    if xkind == "time":
        span = float(xs_all.max() - xs_all.min()) or 1.0
        scale, shown_unit = next(((sc, u) for sc, u in ((1, "s"), (1e-3, "ms"), (1e-6, "us"), (1e-9, "ns")) if span / sc >= 1), (1e-9, "ns"))
        xlabel, xunit = f"time ({shown_unit})", "s"
    elif xkind == "freq":
        scale, xunit, xlabel = 1.0, "Hz", "frequency (Hz)"
    else:
        scale, xunit, xlabel = 1.0, "", data.xname
    figw, figh = 11.0, 3.7 * len(panels) + 1.9
    fig, axes = plt.subplots(len(panels), 1, figsize=(figw, figh), sharex=True, squeeze=False)
    axes = axes[:, 0]
    fig.subplots_adjust(bottom=0.2 if len(panels) == 1 else 0.14, top=0.9, hspace=0.14)
    measures, limits, styles, legend, label_boxes = [], [], [], {}, {}
    logx = xkind == "freq"
    for pi, (ax, p) in enumerate(zip(axes, panels)):
        series = []
        entries = []
        for i, t in enumerate(p["traces"]):
            st = trace_style(i, t)
            name = canon[t["name"].lower()]
            for si_, s in enumerate(steps):
                x, y = data.series(t["name"], s)
                y = view_y(y, t.get("view", "real"), t["name"])
                me = max(1, len(x) // 12) if st["marker"] else None
                z = 2 if st["ls"] in ("-", "solid") else 3          # the dashed trace goes on top of the solid one
                (ax.semilogx if logx else ax.plot)(x / scale, y, color=st["color"], ls=st["ls"], lw=1.8, marker=st["marker"],
                                                   ms=5, markevery=me, alpha=max(0.4, 1 - 0.25 * si_), zorder=z,
                                                   label=name if si_ == 0 else None)
                series.append((x / scale, np.real(y)))
            styles.append(dict(panel=pi, name=name, **st))
            entries.append(name)
        legend[pi] = entries
        lines, dots = [], []
        for m in p.get("measures", []):
            r = measure(data, m, m.get("step", steps[0]), xunit)
            measures.append(r)
            lines.append(r["line"])
            if r["point"]:
                ax.plot([r["point"][0] / scale], [r["point"][1]], "o", color=INK, ms=4, zorder=5)
                dots.append((r["point"][0] / scale, r["point"][1], f"[M] {r['label']}"))
        limit_marks = []
        for lim in p.get("limits", []):
            r = judge(data, lim, steps)
            limits.append(r)
            bad = not r["ok"]
            ax.axhline(r["value"], color=RED if bad else GREY, lw=1.1, ls="--")
            tag = f"{r['spec']} {r['kind']} {r['value']:g} {r['unit']}"
            limit_marks.append((r["value"], r["kind"], tag, bad))
            lines.append(r["line"])
        ax.set_ylabel(p.get("ylabel", ""))
        ax.grid(True, alpha=0.3)
        ax.relim()
        ax.autoscale_view()
        aw = ax.get_position().width * figw
        ah = ax.get_position().height * figh

        def to_frac(xv, yv):
            xlo, xhi = ax.get_xlim()
            ylo, yhi = ax.get_ylim()
            fx = (np.log10(np.maximum(xv, 1e-300)) - np.log10(xlo)) / (np.log10(xhi) - np.log10(xlo)) if logx else (xv - xlo) / (xhi - xlo)
            return fx, (yv - ylo) / (yhi - ylo)

        def traces_frac():
            pts = [dense(np.column_stack(to_frac(xv, yv))) for xv, yv in series]
            return np.vstack(pts)
        pts = traces_frac()
        taken = []
        for v, kind, tag, bad in limit_marks:                       # limit tag at the left edge, above (max) or below (min) its line
            w, h = (len(tag) * 8 * 0.55 / 72) / aw, (8 * 1.4 / 72) / ah
            fy = to_frac(0.0, v)[1]
            taken.append((0.005, fy if kind == "max" else fy - h, 0.005 + w, fy + h if kind == "max" else fy))
            ax.text(0.005, v, tag, transform=ax.get_yaxis_transform(), ha="left", va="bottom" if kind == "max" else "top", fontsize=8,
                    color=RED if bad else GREY)
        notes_rect = None
        if lines:
            wrapped = [textwrap.fill(ln, 112, subsequent_indent="    ") for ln in lines]
            nl_ = sum(w_.count("\n") + 1 for w_ in wrapped)
            w = min(0.95, (max(len(s_) for w_ in wrapped for s_ in w_.split("\n")) * 7.5 * 0.55 / 72 + 0.15) / aw)
            h = (nl_ * 7.5 * 1.45 / 72 + 0.12) / ah
            cost, rect, anchor = pick_spot(w, h, pts, taken)
            if cost > 0:                                              # no free spot: headroom above the data, notes on top
                lo, hi = ax.get_ylim()
                frac = min(0.7, h + 0.05)
                ax.set_ylim(lo, hi + (hi - lo) * frac / (1 - frac))
                pts = traces_frac()
                cost, rect, anchor = pick_spot(w, h, pts, taken)
            ax.text(anchor[0], anchor[1], "\n".join(wrapped), transform=ax.transAxes, fontsize=7.5, ha=anchor[2], va=anchor[3],
                    multialignment="left", bbox=dict(fc="#f8fafc", ec="#cbd5e1"))
            taken.append(rect)
            notes_rect = rect
        lw_ = (max(len(e) for e in entries) * 8 * 0.62 / 72 + 0.95) / aw
        lh_ = (len(entries) * 8 * 1.9 / 72 + 0.3) / ah
        lcost, lrect, anchor = pick_spot(lw_, lh_, pts, taken)
        ax.legend(loc=loc_word(anchor[2], anchor[3]), bbox_to_anchor=(anchor[0], anchor[1]), borderaxespad=0, fontsize=8)
        taken.append(lrect)
        boxes = []
        for xv, yv, text in dots:
            px, py = (float(v) for v in to_frac(xv, yv))
            w, h = (len(text) * 7 * 0.55 / 72) / aw, (7 * 1.4 / 72) / ah
            rect = label_spot(px, py, w, h, pts, taken)
            ax.text(rect[0], rect[1], text, transform=ax.transAxes, fontsize=7, color=INK, ha="left", va="bottom")
            taken.append(rect)
            boxes.append(dict(text=text, rect=rect))
        label_boxes[pi] = dict(labels=boxes, notes=notes_rect, legend=lrect, legend_hits=hits(pts, lrect),
                               notes_hits=hits(pts, notes_rect) if notes_rect else 0)
    axes[-1].set_xlabel(xlabel)
    fig.suptitle(textwrap.fill(title, 125), fontsize=10)
    cir_text = pathlib.Path(cir).read_text(encoding="utf-8", errors="replace")
    foot = "\n".join(textwrap.fill(ln, 215) for ln in footer(cir, csv, source, date, cir_text))
    for ln_not in sorted(not_plotted):
        foot += f"\nnot plotted: {ln_not}: {not_plotted[ln_not]}"
    fig.text(0.01, 0.005, foot, fontsize=6.4, color=GREY, va="bottom", ha="left")
    out_dir = pathlib.Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    svg = out_dir / "result.svg"
    fig.savefig(str(svg), format="svg", metadata={"Date": None})
    png = svg.with_suffix(".png")      # PNG straight from matplotlib: the SVG renderer of PyMuPDF draws no dashes (line styles must show)
    fig.savefig(str(png), format="png", dpi=150, metadata={"Software": None})
    plt.close(fig)
    return dict(measures=measures, limits=limits, ok=all(r["ok"] for r in limits), svg=svg, png=png, styles=styles, legend=legend,
                label_boxes=label_boxes)


def run(config, argv=None):
    """Result script entry: plots, prints [M] lines and PASS/FAIL per limit. -> exit code (0 ok, 1 FAIL, 2 unusable input)."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--cir", required=True)
    ap.add_argument("--csv", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--date", default=datetime.date.today().isoformat())
    a = ap.parse_args(argv)
    try:
        data = Data(a.csv)
        saves = []
        for ln in pathlib.Path(a.cir).read_text(encoding="utf-8", errors="replace").splitlines():
            if ln.strip().lower().startswith(".save"):
                saves += ln.split(";")[0].split()[1:]
        res = plot_result(data, config["panels"], saves, a.cir, a.csv, a.out, a.date, config.get("title", ""), config.get("source", ""),
                          config.get("not_plotted"), tuple(config.get("steps", (1,))), config.get("xkind", "time"))
    except (PlotkitError, OSError, KeyError, ValueError) as e:
        print(f"ERROR: {type(e).__name__}: {e}")
        return 2
    for m in res["measures"]:
        print(m["line"])
    for r in res["limits"]:
        print(r["line"])
    print(f"{'OK' if res['ok'] else 'FAILED'} {res['svg']}: {len(res['measures'])} measurements, {len(res['limits'])} limits")
    return 0 if res["ok"] else 1
