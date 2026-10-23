"""Three names per terminal for simulation circuit figures (00_coordination/T025).

Every terminal shows three boxes so pin mix-ups between document, SPICE model and testbench are visible:
  DS  datasheet pin number + pin name + source        solid rectangle, blue     `DS 4 OUT D01 p.5`
  SP  SPICE model node (.SUBCKT position + name)      dashed rounded, orange    `SP 1 out`
  TB  testbench net                                   hexagon, thick, green     `TB VOUT_NET`
A box whose value is unknown ("?" or no table row) is hatched and reads `DS ?` / `SP ?`.

  python pin_map.py --cir <testbench.cir> --instance XU1 [XU2 ...] --part PARTA [PARTB ...] [--pin-map <module>\\FACTS.md] --out fig.svg

Pairs `--instance` and `--part` by position. Without --pin-map only the TB boxes are drawn and the footer says "pin map: none".
Table format: docs\\INTERFACES.md section 10. Prints WARNING lines for testbench terminals absent from the table.
Library use: parse_pin_map(), instance_nets(), terminals(), render().
"""
import argparse
import math
import pathlib
import re
import sys

COLS = ["Part", "Doc (D<nn>)", "Page", "Pkg pin no", "Datasheet pin name", "Model file",
        ".SUBCKT node position", "SPICE node name", "Label", "Note"]
LABELS = {"[V]", "[R]", "[A]", "[M]"}
UNKNOWN = "?"
# Okabe-Ito based (colour-blind safe); the lightness differs so the boxes also separate in grayscale
STYLE = {"DS": dict(stroke="#0072B2", fill="#d6e8f5"),
         "SP": dict(stroke="#D55E00", fill="#fbe0cf"),
         "TB": dict(stroke="#007a5a", fill="#bfeadb")}
FONT = "Arial,Helvetica,sans-serif"

try:
    sys.stdout.reconfigure(encoding="utf-8")  # "Pin eşleme" in the warning text; Windows console is cp1252
except Exception:
    pass


def _cells(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]


def parse_pin_map(text):
    """FACTS.md text -> list of row dicts (keys = COLS), only from the first table of the "Pin eşleme" section."""
    lines, rows, level, i = text.splitlines(), [], None, 0
    while i < len(lines):
        m = re.match(r"^(#+)\s*(.*)$", lines[i])
        i += 1
        if m and "pin eşleme" in m.group(2).lower():
            level = len(m.group(1))
            break
    if level is None:
        return rows
    while i < len(lines):
        ln = lines[i]
        m = re.match(r"^(#+)\s", ln)
        if m and len(m.group(1)) <= level:
            break
        if ln.strip().startswith("|"):
            head = _cells(ln)
            if head != COLS:
                raise ValueError(f"Pin eşleme header must be exactly: {' | '.join(COLS)} (got: {' | '.join(head)})")
            i += 2
            while i < len(lines) and lines[i].strip().startswith("|"):
                c = _cells(lines[i])
                if len(c) != len(COLS):
                    raise ValueError(f"Pin eşleme row has {len(c)} cells, expected {len(COLS)}: {lines[i]}")
                row = dict(zip(COLS, c))
                if row["Label"] not in LABELS:
                    raise ValueError(f"Pin eşleme label must be one of {sorted(LABELS)}: {lines[i]}")
                rows.append(row)
                i += 1
            break
        i += 1
    return rows


def instance_nets(cir_text, instance):
    """Nets of an X instance in .SUBCKT node order (last token = subcircuit name; name=value parameters dropped)."""
    for ln in cir_text.splitlines():
        t = ln.split()
        if t and t[0].upper() == instance.upper():
            toks = [x for x in t[1:] if "=" not in x]
            return toks[:-1]
    raise KeyError(f"instance {instance} not found in the testbench")


def terminals(nets, part, rows):
    """-> (terminal dicts, warnings). One terminal per node position of the instance; ds/sp None = unknown."""
    by_pos = {int(r[".SUBCKT node position"]): r for r in rows
              if r["Part"] == part and r[".SUBCKT node position"].isdigit()}
    out, warns = [], []
    for pos, net in enumerate(nets, 1):
        r = by_pos.get(pos)
        t = dict(pos=pos, net=net, ds=None, sp=None)
        if r is None:
            warns.append(f"WARNING: {part} node position {pos} (net {net}) is in the testbench but not in the Pin eşleme table")
        else:
            pin, name = r["Pkg pin no"], r["Datasheet pin name"]
            if UNKNOWN not in (pin, name, r["Doc (D<nn>)"], r["Page"]):
                t["ds"] = f"DS {pin} {name} {r['Doc (D<nn>)']} p.{r['Page']}"
            if r["SPICE node name"] != UNKNOWN:
                t["sp"] = f"SP {pos} {r['SPICE node name']}"
        out.append(t)
    return out, warns


def _esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def dash_path(pts, dash, gap, closed=True):
    """Dashes of a polyline as separate point lists: fixed `dash` / `gap` lengths along the path, corners kept. The PNG renderer
    (PyMuPDF) ignores stroke-dasharray, so dashed shapes are built from explicit segments and look the same in SVG and PNG."""
    pts = [tuple(p) for p in pts]
    if closed:
        pts = pts + [pts[0]]
    out, cur, on, left = [], [pts[0]], True, float(dash)
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        seg = math.hypot(x2 - x1, y2 - y1)
        pos = 0.0
        while seg - pos > 1e-9:
            take = min(left, seg - pos)
            pos += take
            left -= take
            px, py = x1 + (x2 - x1) * pos / seg, y1 + (y2 - y1) * pos / seg
            if on:
                cur.append((px, py))
            if left <= 1e-9:
                if on:
                    out.append(cur)
                    cur = []
                else:
                    cur = [(px, py)]
                on = not on
                left = float(dash if on else gap)
    if on and len(cur) > 1:
        out.append(cur)
    return out


def dashes_svg(pts, dash, gap, stroke, width, closed=True):
    """SVG for dash_path(): one <polyline class="dash"> per dash."""
    return "".join('<polyline class="dash" points="' + " ".join(f"{x:.2f},{y:.2f}" for x, y in seg) +
                   f'" fill="none" stroke="{stroke}" stroke-width="{width}"/>' for seg in dash_path(pts, dash, gap, closed))


def round_rect_points(x, y, w, h, r, step=1.5):
    """Outline of a rounded rectangle (r <= h/2, w/2), clockwise from the top left, arcs sampled every ~step."""
    r = min(r, h / 2, w / 2)
    n = max(4, int(math.pi * r / 2 / step))
    pts = []
    for cx, cy, a0 in ((x + w - r, y + r, -90), (x + w - r, y + h - r, 0), (x + r, y + h - r, 90), (x + r, y + r, 180)):
        for k in range(n + 1):
            a = math.radians(a0 + 90 * k / n)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def _hatch(x, y, w, h, color, step=8):
    """45-degree lines clipped to the box by geometry (an SVG <pattern> renders black in PyMuPDF)."""
    out = []
    for s in range(-int(h), int(w), step):
        x1, y1, x2, y2 = s, h, s + h, 0   # box-relative, rising to the right
        if x1 < 0:
            y1, x1 = h + x1, 0            # slope -1: moving right by d moves up by d
        if x2 > w:
            y2, x2 = y2 + (x2 - w), w
        out.append(f'<line class="hatch-line" x1="{x + x1}" y1="{y + y1}" x2="{x + x2}" y2="{y + y2}" stroke="#666" stroke-width="1.2"/>')
    return "".join(out)


def _box(kind, x, y, w, h, text):
    """One labelled box. text None -> hatched box reading '<kind> ?'."""
    st = STYLE[kind]
    fill = st["fill"] if text else "#ffffff"
    label = text or f"{kind} ?"
    if kind == "DS":
        shape = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" stroke="{st["stroke"]}" stroke-width="1.5"/>'
    elif kind == "SP":
        shape = (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{h / 2:.0f}" fill="{fill}" stroke="none"/>' +
                 dashes_svg(round_rect_points(x, y, w, h, h / 2), 5, 3, st["stroke"], 1.5))   # dashed edge from real segments
    else:
        d = h / 2
        pts = f"{x + d},{y} {x + w - d},{y} {x + w},{y + d} {x + w - d},{y + h} {x + d},{y + h} {x},{y + d}"
        shape = f'<polygon points="{pts}" fill="{fill}" stroke="{st["stroke"]}" stroke-width="3.5"/>'
    if text is None:
        shape += _hatch(x, y, w, h, st["stroke"])
        tw = 7 * len(label) + 10  # white plate so the label stays readable over the hatch
        shape += f'<rect x="{x + w / 2 - tw / 2}" y="{y + 4}" width="{tw}" height="{h - 8}" fill="#ffffff"/>'
    return (f'<g class="{kind}{"" if text else " missing"}">{shape}'
            f'<text x="{x + w / 2}" y="{y + h / 2 + 4}" text-anchor="middle" font-size="12" '
            f'font-family="{FONT}" fill="#111">{_esc(label)}</text></g>')


BW, BH, GAP = 230, 26, 8  # box width / height / row gap of the terminal panel


def panel(blocks, mapped, left, top):
    """Terminal rows: for every block a title line, then one row per terminal (DS SP TB, or TB only when not mapped).
    -> (svg elements, bottom y, unmapped count). Used by render() and by circuits.py."""
    out, y, unmapped = [], top, 0
    for title, terms in blocks:
        out.append(f'<text x="{left}" y="{y + 16}" font-size="14" font-weight="bold" font-family="{FONT}">{_esc(title)}</text>')
        y += BH + GAP
        for t in terms:
            x = left
            if mapped:
                out.append(_box("DS", x, y, BW, BH, t["ds"]))
                out.append(_box("SP", x + BW + 12, y, BW, BH, t["sp"]))
                x += 2 * (BW + 12)
                if t["ds"] is None or t["sp"] is None:
                    unmapped += 1
            out.append(_box("TB", x, y, BW, BH, f"TB {t['net']}"))
            y += BH + GAP
    return out, y, unmapped


def legend(lx, top):
    """Legend column at x=lx starting at y=top -> (svg elements, bottom y)."""
    out = [f'<text x="{lx}" y="{top + 16}" font-size="14" font-weight="bold" font-family="{FONT}">Legend</text>']
    ly = top + 28
    for kind, text, desc in (("DS", "DS 4 OUT D01 p.5", "datasheet pin no, name, source (solid rectangle, blue)"),
                             ("SP", "SP 1 out", ".SUBCKT position, model node (dashed rounded, orange)"),
                             ("TB", "TB VOUT_NET", "testbench net (hexagon, thick border, green)")):
        out.append(_box(kind, lx, ly, 180, BH, text))
        out.append(f'<text x="{lx}" y="{ly + BH + 14}" font-size="11" font-family="{FONT}" fill="#333">{_esc(desc)}</text>')
        ly += BH + 30
    out.append(_box("DS", lx, ly, 180, BH, None))
    out.append(f'<text x="{lx}" y="{ly + BH + 14}" font-size="11" font-family="{FONT}" fill="#333">hatched = unknown ("?") or not in the table</text>')
    return out, ly + BH + 20


def render(blocks, source, pin_map_path):
    """blocks: [(title, [terminal dicts])] -> (svg text, unmapped count). Footer: source, pin map, UNMAPPED TERMINALS."""
    mapped = pin_map_path is not None
    left, top = 20, 40
    h = top + sum(len(t) + 1 for _, t in blocks) * (BH + GAP) + 90
    lx = left + (3 if mapped else 1) * (BW + 12) + 20
    w = lx + 290
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">',
           f'<rect width="{w}" height="{h}" fill="#ffffff"/>']
    body, _, unmapped = panel(blocks, mapped, left, top)
    out += body
    out += legend(lx, top)[0]
    foot = [f"source: {source}; pin map: {pin_map_path or 'none'}"]
    if mapped:
        foot.append(f"UNMAPPED TERMINALS: {unmapped}")
    for k, ln in enumerate(foot):
        out.append(f'<text x="{left}" y="{h - 40 + 16 * k}" font-size="12" font-family="{FONT}" fill="#222">{_esc(ln)}</text>')
    out.append("</svg>")
    return "\n".join(out), unmapped


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--cir", required=True)
    ap.add_argument("--instance", nargs="+", required=True)
    ap.add_argument("--part", nargs="+", required=True)
    ap.add_argument("--pin-map")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    if len(a.instance) != len(a.part):
        ap.error("--instance and --part must pair up")
    cir = pathlib.Path(a.cir)
    cir_text = cir.read_text(encoding="utf-8")
    rows = parse_pin_map(pathlib.Path(a.pin_map).read_text(encoding="utf-8")) if a.pin_map else []
    blocks = []
    for inst, part in zip(a.instance, a.part):
        nets = instance_nets(cir_text, inst)
        if a.pin_map:
            terms, warns = terminals(nets, part, rows)
            for wn in warns:
                print(wn)
        else:
            terms = [dict(pos=i, net=n, ds=None, sp=None) for i, n in enumerate(nets, 1)]
        blocks.append((f"{inst} = {part}", terms))
    svg, unmapped = render(blocks, cir.name, a.pin_map)
    pathlib.Path(a.out).write_text(svg, encoding="utf-8")
    print(f"OK {a.out}: {sum(len(t) for _, t in blocks)} terminals, "
          f"UNMAPPED TERMINALS: {unmapped if a.pin_map else 'n/a (pin map: none)'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
