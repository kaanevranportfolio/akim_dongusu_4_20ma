"""Draw the circuit schematic of a QSPICE testbench from its .cir netlist (CLAUDE.md Figures rule 1; T027, T028).

  python docs\sim\circuits.py <tb>.cir --out <dir> --layout <tb dir>\circuit_layout.py [--pin-map <module>\FACTS.md]
                               [--part XU1=MPN ...] [--date YYYY-MM-DD]
  python docs\sim\circuits.py <tb>.cir --draft <layout.py>          first-draft layout script, then edit it by hand

Writes <dir>\circuit.svg (source) and <dir>\circuit.png (view, PyMuPDF). Exit 0 = drawn and verified, 1 = verification
failed (every violation is printed, nothing is written), 2 = the netlist, a layout script or an option cannot be used.

* The netlist is PARSED (R C L V I D Q M X; .subckt bodies skipped; .param/.include noted or ignored; .model types, .save,
  .meas, .tran, .step noted). An element letter that is not supported raises an error: it is never skipped.
* FINAL FIGURE = hand layout: a layout script written by the module agent (docs\sim\<tb>\circuit_layout.py), a file that
  defines layout(sh, nl) and calls the classic symbols of docs\sim\symbols.py at absolute coordinates (resistor, capacitor,
  inductor, diode, vsource, isource, opamp, bjt, mosfet, subckt; rot 0/90/180/270), wires with Manhattan helpers (wire, route),
  ground, net-name flags (byname) and red probe boxes (probe_node, probe_diff, probe_current, probe_pin); junction dots are
  automatic. Optional TITLE, WIDTH, HEIGHT. --draft writes a starting script (every element placed, net-name flags instead of
  wires, probes) to edit.
* Without --layout (or with a grid-hints .json) the old automatic layout runs: a first DRAFT only, marked "automatic DRAFT,
  not a final figure" in the footer. Hints {"R_SENSE": {"row": 0, "col": 2, "rot": 180}} move elements on its grid.
* finish() verifies: every netlist element is drawn exactly once with all its terminals; nothing is drawn that is not in the
  netlist; every net has >= 2 terminals (or is a probe or ground); all terminals of a net are connected by a wire, a ground
  symbol or the same net name; every .save signal has a probe label.
* Terminal names: with --pin-map every subcircuit instance gets DS / SP / TB boxes (docs\\sim\\pin_map.py; the Part key is the
  .subckt name unless --part XU1=MPN); without it TB boxes only and the footer says "pin map: none".
* Footer: testbench file, SHA-256 of the .cir and of every referenced model file, date (--date, default today), pin map, label.
  No repository state is read. Same input and options -> same bytes.
"""
import argparse
import datetime
import hashlib
import importlib.util
import json
import pathlib
import re
import sys

import pymupdf

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import pin_map  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ALLOWED = "RCLVIDQMX"
GROUND = "0"
INK, GREY, BLUE, RED = "#0f172a", "#64748b", "#0369a1", "#b91c1c"
FONT = "Segoe UI, Arial, sans-serif"
MARGIN, PITCH, ROW_MAX = 30, 26, 5
ROLES = {"V": ["+", "-"], "I": ["+", "-"], "D": ["A", "K"], "Q": ["C", "B", "E", "S"], "M": ["D", "G", "S", "B"],
         "R": ["1", "2"], "C": ["1", "2"], "L": ["1", "2"]}


class NetlistError(ValueError):
    pass


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def key(net):
    """QSPICE net names are case-insensitive."""
    return net.upper()


def sha256(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


# ---------------------------------------------------------------- netlist
class Netlist:
    def __init__(self, path):
        self.path = pathlib.Path(path)
        self.comps = {}                       # name -> dict(kind, nodes, value), netlist order
        self.saves, self.steps, self.meas, self.tran, self.models = [], [], [], None, []
        self.nets = {}                        # net key -> display name (first spelling)
        self.subckts, self.model_types = {}, {}   # SUBCKT NAME -> [node names]; MODEL NAME -> TYPE (NPN, PMOS ...)
        lines = []
        for raw in self.path.read_text(encoding="utf-8").splitlines():
            ln = raw.split(";")[0].strip()
            if not ln or ln.startswith("*"):
                continue
            if ln.startswith("+") and lines:
                lines[-1] += " " + ln[1:].strip()
            else:
                lines.append(ln)
        depth = 0
        for ln in lines:
            tok = ln.split()
            head = tok[0]
            if head.startswith("."):
                d = head.lower()
                if d == ".subckt":
                    if depth == 0 and len(tok) > 1:
                        self.subckts[tok[1].upper()] = [t for t in tok[2:] if "=" not in t and t.lower() != "params:"]
                    depth += 1
                elif d == ".ends":
                    depth = max(0, depth - 1)
                elif depth:
                    continue
                elif d == ".model" and len(tok) > 2:
                    self.model_types[tok[1].upper()] = re.split(r"[(\s]", tok[2])[0].upper()
                elif d == ".save":
                    self.saves += tok[1:]
                elif d == ".step":
                    self.steps.append(ln)
                elif d == ".meas":
                    self.meas.append(ln)
                elif d == ".tran":
                    self.tran = ln
                elif d in (".include", ".inc", ".lib") and len(tok) > 1:
                    self.models.append(tok[1].strip('"'))
                continue
            if depth:
                continue
            name, comp = self.element(tok, ln)
            if any(name.upper() == n.upper() for n in self.comps):
                raise NetlistError(f"duplicate element name {name}")
            self.comps[name] = comp
            for n in comp["nodes"]:
                self.nets.setdefault(key(n), n)
        for m in self.models:                  # subcircuit pin names of the referenced model files (for I(X1:pin))
            mp = pathlib.Path(m)
            mp = mp if mp.is_absolute() else self.path.parent / mp
            if not mp.is_file():
                continue
            joined = []
            for raw in mp.read_text(encoding="utf-8", errors="replace").splitlines():
                t = raw.split(";")[0].strip()
                if t.startswith("+") and joined:
                    joined[-1] += " " + t[1:].strip()
                elif t:
                    joined.append(t)
            for t in joined:
                w = t.split()
                if w[0].lower() == ".subckt" and len(w) > 1:
                    self.subckts.setdefault(w[1].upper(), [x for x in w[2:] if "=" not in x and x.lower() != "params:"])

    @staticmethod
    def element(tok, ln):
        head = tok[0]
        kind = head[0].upper()
        if kind not in ALLOWED:
            raise NetlistError(f"unsupported element '{head}' (letter {kind}; supported: {' '.join(ALLOWED)}) in line: {ln}")
        args = [t for t in tok[1:] if "=" not in t]

        def need(n):
            if len(args) < n:
                raise NetlistError(f"element {head}: expected at least {n} fields in line: {ln}")
        if kind in "RCL":
            need(3)
            return head, dict(kind=kind, nodes=args[0:2], value=args[2])
        if kind in "VI":
            if len(tok) < 4:
                raise NetlistError(f"element {head}: expected nodes and a value in line: {ln}")
            return head, dict(kind=kind, nodes=tok[1:3], value=" ".join(tok[3:]))
        if kind == "D":
            need(3)
            return head, dict(kind="D", nodes=args[0:2], value=args[2])
        if kind == "Q":
            need(4)
            n = 4 if len(args) >= 5 else 3
            return head, dict(kind="Q", nodes=args[0:n], value=args[n])
        if kind == "M":
            need(5)
            return head, dict(kind="M", nodes=args[0:4], value=args[4])
        need(2)
        return head, dict(kind="X", nodes=args[:-1], value=args[-1])

    def pin_index(self, elem, pin):
        """Terminal index of subcircuit pin `pin` (a .subckt node name or a 1-based number) of element `elem`, or None."""
        c = self.comps[elem]
        if pin.isdigit():
            return int(pin) - 1 if 1 <= int(pin) <= len(c["nodes"]) else None
        names = [n.lower() for n in self.subckts.get(c["value"].upper(), [])]
        return names.index(pin.lower()) if pin.lower() in names and len(names) == len(c["nodes"]) else None

    def terminals(self):
        """net key -> [(element, terminal index)] in netlist order."""
        out = {}
        for name, c in self.comps.items():
            for i, n in enumerate(c["nodes"]):
                out.setdefault(key(n), []).append((name, i))
        return out


SIG_V = re.compile(r"V\(([^,():]+)(?:,([^,():]+))?\)", re.I)
SIG_I = re.compile(r"I\(([^,():]+)(?::([^,():]+))?\)", re.I)


def signal_info(nl, sig):
    """Decode a .save signal: V(net), V(a,b), I(element), I(X1:pin).
    -> dict(kind, nets (keys), elem, pin (terminal index or None)) or dict(error=message)."""
    m = SIG_V.fullmatch(sig)
    if m:
        nets = [n for n in m.groups() if n]
        for n in nets:
            if key(n) not in nl.nets:
                return dict(error=f"net {n} is not in the netlist")
        return dict(kind="V", nets=[key(n) for n in nets], elem=None, pin=None)
    m = SIG_I.fullmatch(sig)
    if m:
        elem = next((n for n in nl.comps if n.lower() == m.group(1).lower()), None)
        if elem is None:
            return dict(error=f"element {m.group(1)} is not in the netlist")
        pin = None
        if m.group(2):
            if nl.comps[elem]["kind"] != "X":
                return dict(error=f"{elem} is not a subcircuit instance; I({elem}:pin) needs an X element")
            pin = nl.pin_index(elem, m.group(2))
            if pin is None:
                return dict(error=f"pin {m.group(2)} not found in .subckt {nl.comps[elem]['value']} (not in the netlist or the model files)")
        return dict(kind="I", nets=[], elem=elem, pin=pin)
    return dict(error="only V(net), V(a,b), I(element) and I(X1:pin) are supported")


def validate_saves(nl):
    """{signal: message} for every .save signal that cannot be drawn."""
    out = {}
    for s in nl.saves:
        info = signal_info(nl, s)
        if "error" in info:
            out[s] = info["error"]
    return out


# ---------------------------------------------------------------- layout
def bfs_order(nl):
    names = list(nl.comps)
    by_net = nl.terminals()
    seen, order = set(), []
    starts = [n for n in names if nl.comps[n]["kind"] in "VI"] + names
    for s in starts:
        if s in seen:
            continue
        seen.add(s)
        queue = [s]
        while queue:
            cur = queue.pop(0)
            order.append(cur)
            for node in nl.comps[cur]["nodes"]:
                if key(node) == GROUND:
                    continue
                for other, _ in by_net[key(node)]:
                    if other not in seen:
                        seen.add(other)
                        queue.append(other)
    return order


def load_hints(path, nl):
    if not path:
        return {}
    hints = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    for name, h in hints.items():
        if name not in nl.comps:
            raise NetlistError(f"layout hint for '{name}': not an element of the netlist")
        bad = set(h) - {"row", "col", "rot"}
        if bad or h.get("rot", 0) not in (0, 180):
            raise NetlistError(f"layout hint for '{name}': allowed keys row, col, rot (0 or 180); got {h}")
    return hints


def place(nl, hints, skip=()):
    """-> list of rows; each row a list of dicts(name, rot). Hinted cells first, the rest filled row-major, five per row."""
    order = [n for n in bfs_order(nl) if n not in skip]
    cells = {}
    for n in order:
        h = hints.get(n, {})
        if "row" in h or "col" in h:
            cell = (h.get("row", 0), h.get("col", 0))
            if cell in cells:
                raise NetlistError(f"layout hints: cell {cell} used by {cells[cell]} and {n}")
            cells[cell] = n
    r = c = 0
    for n in order:
        if n in hints and ("row" in hints[n] or "col" in hints[n]):
            continue
        while (r, c) in cells:
            c += 1
            if c >= ROW_MAX:
                r, c = r + 1, 0
        cells[(r, c)] = n
        c += 1
        if c >= ROW_MAX:
            r, c = r + 1, 0
    rows = {}
    for (r, c), n in sorted(cells.items()):
        rows.setdefault(r, []).append(dict(name=n, rot=hints.get(n, {}).get("rot", 0)))
    return [rows[r] for r in sorted(rows)]


# ---------------------------------------------------------------- sheet
class Sheet:
    """Collects what is drawn so finish() can check it against the netlist."""

    def __init__(self, nl):
        self.nl = nl
        self.out, self.drawn, self.pin_xy = [], {}, {}
        self.parent, self.named, self.probes, self.probed_nets = {}, set(), set(), set()
        self.violations = []

    def add(self, s):
        self.out.append(s)

    def text(self, x, y, s, size=11, col=INK, anchor="start", weight=400, italic=False):
        st = ' font-style="italic"' if italic else ""
        self.add(f'<text x="{x:g}" y="{y:g}" font-size="{size}" fill="{col}" text-anchor="{anchor}" font-weight="{weight}"{st}>{esc(s)}</text>')

    def line(self, x1, y1, x2, y2, col=INK, w=1.8, dash=None):
        """dash = "on off" (e.g. "4 3"): drawn as separate short segments, not with stroke-dasharray (the PNG renderer ignores it)."""
        if dash:
            on, off = (float(v) for v in dash.split())
            self.add(pin_map.dashes_svg([(x1, y1), (x2, y2)], on, off, col, w, closed=False))
            return
        self.add(f'<line x1="{x1:g}" y1="{y1:g}" x2="{x2:g}" y2="{y2:g}" stroke="{col}" stroke-width="{w}"/>')

    def comp(self, name):
        c = self.nl.comps[name]  # KeyError: not in the netlist
        if name in self.drawn:
            raise ValueError(f"{name} drawn twice")
        self.drawn[name] = set()
        return c

    def net_of(self, a):
        return key(self.nl.comps[a[0]]["nodes"][a[1]])

    def pin(self, name, idx, x, y):
        self.drawn[name].add(idx)
        self.pin_xy[(name, idx)] = (x, y)
        self.parent[(name, idx)] = (name, idx)
        self.add(f'<circle cx="{x:g}" cy="{y:g}" r="2.6" fill="{INK}"/>')

    def find(self, a):
        while self.parent[a] != a:
            self.parent[a] = self.parent[self.parent[a]]
            a = self.parent[a]
        return a

    def ground(self, a):
        x, y = self.pin_xy[a]
        self.line(x, y, x, y + 10)
        for k, wd in enumerate((14, 9, 4)):
            self.line(x - wd, y + 10 + 4 * k, x + wd, y + 10 + 4 * k)
        self.named.add(a)

    def tag(self, x, y, label):
        w = len(label) * 6.6 + 10
        self.add(f'<rect x="{x - 3:g}" y="{y - 11:g}" width="{w:.0f}" height="15" rx="3" fill="#fee2e2" stroke="{RED}"/>')
        self.text(x + 1, y, label, 10.5, RED, "start", 700)

    def finish(self):
        """-> list of violations (empty = verified)."""
        v = list(self.violations)
        for name, c in self.nl.comps.items():
            if name not in self.drawn:
                v.append(f"netlist element {name} not drawn")
            elif self.drawn[name] != set(range(len(c["nodes"]))):
                v.append(f"{name}: terminals drawn {sorted(self.drawn[name])}, netlist has {len(c['nodes'])}")
        for name in self.drawn:
            if name not in self.nl.comps:
                v.append(f"{name} drawn but not in the netlist")
        for net, terms in self.nl.terminals().items():
            shown = self.nl.nets[net]
            if len(terms) < 2 and net != GROUND and net not in self.probed_nets:
                v.append(f"net {shown}: only {len(terms)} terminal (not a probe, not ground)")
            drawn = [t for t in terms if t in self.pin_xy]
            unnamed = [t for t in drawn if t not in self.named]
            if len({self.find(t) for t in unnamed}) > 1:
                v.append(f"net {shown}: terminals not connected by wire, ground or name: {sorted(unnamed)}")
        bad = validate_saves(self.nl)
        v += [f".save signal {s}: {msg}" for s, msg in bad.items()]
        for s in self.nl.saves:
            if s not in bad and s.lower() not in self.probes:
                v.append(f".save signal {s} has no probe label")
        return v


class AutoSheet(Sheet):
    '''Sheet used by the automatic DRAFT layout: lane wires and stacked net-name tags.'''

    def wire_net(self, terms, lane_y):
        """Lane wire for the terminals of one net: vertical stubs from the pin to the lane and one trunk."""
        xs = []
        for a in terms:
            x, y = self.pin_xy[a]
            self.line(x, y, x, lane_y)
            self.add(f'<circle cx="{x:g}" cy="{lane_y:g}" r="3.2" fill="{INK}"/>')
            xs.append(x)
            self.parent[self.find(a)] = self.find(terms[0])
        self.line(min(xs), lane_y, max(xs), lane_y)
        return min(xs), max(xs)

    def byname(self, a, level=0):
        """Dashed stub and "net X" tag; level 0..2 staggers the tag height so neighbouring tags do not overlap."""
        x, y = self.pin_xy[a]
        net = self.nl.nets[self.net_of(a)]
        ty = y - 24 - 14 * level
        self.line(x, y, x, ty + 6, GREY, 1.4, "4 3")
        self.text(x, ty, f"net {net}", 10.5, BLUE, "middle", 700)
        self.named.add(a)
        return x + len(net) * 3.4 + 24, ty


def glyph(sh, kind, cx, cy):
    """Small symbol inside a two-terminal box."""
    if kind == "R":
        sh.add(f'<rect x="{cx - 22:g}" y="{cy - 7:g}" width="44" height="14" fill="#fff" stroke="{INK}" stroke-width="1.8"/>')
    elif kind == "C":
        sh.line(cx - 4, cy - 12, cx - 4, cy + 12, w=2.4)
        sh.line(cx + 4, cy - 12, cx + 4, cy + 12, w=2.4)
        sh.line(cx - 20, cy, cx - 4, cy)
        sh.line(cx + 4, cy, cx + 20, cy)
    elif kind == "L":
        d = f"M {cx - 24:g} {cy:g} " + " ".join(f"a 8 8 0 0 1 16 0" for _ in range(3))
        sh.add(f'<path d="{d}" fill="none" stroke="{INK}" stroke-width="1.8"/>')
    elif kind in "VI":
        sh.add(f'<circle cx="{cx:g}" cy="{cy:g}" r="14" fill="#fff" stroke="{INK}" stroke-width="1.8"/>')
        if kind == "V":
            sh.text(cx, cy - 2, "+", 11, INK, "middle", 700)
            sh.text(cx, cy + 10, "-", 12, INK, "middle", 700)
        else:
            sh.line(cx, cy + 8, cx, cy - 8)
            sh.add(f'<polygon points="{cx - 4:g},{cy - 3:g} {cx + 4:g},{cy - 3:g} {cx:g},{cy - 10:g}" fill="{INK}"/>')
    elif kind == "D":
        sh.add(f'<polygon points="{cx - 8:g},{cy - 10:g} {cx - 8:g},{cy + 10:g} {cx + 8:g},{cy:g}" fill="#fff" stroke="{INK}" stroke-width="1.8"/>')
        sh.line(cx + 8, cy - 10, cx + 8, cy + 10, w=2.4)


def draw(nl, hints=None, skip=()):
    """Build the sheet. -> (Sheet, geometry dict). skip = element names left out (test hook for finish())."""
    hints = hints or {}
    sh = AutoSheet(nl)
    rows = place(nl, hints, skip)
    by_net = nl.terminals()
    # geometry: widths, pin x, rows
    geo, y = [], 56
    max_w = 0
    net_pos, cur_pos = {}, {}   # where a probe tag of a net / element current goes
    row_info = []
    for row in rows:
        x, items = MARGIN, []
        for e in row:
            c = nl.comps[e["name"]]
            idxs = list(range(len(c["nodes"])))
            bottom = [i for i in idxs if key(c["nodes"][i]) == GROUND]
            top = [i for i in idxs if i not in bottom]
            if e["rot"] == 180:
                top, bottom = top[::-1], bottom[::-1]
            w = max(120, 34 * max(len(top), len(bottom), 1) + 60, int(len(e["name"]) * 8 + 40))
            h = 96 if c["kind"] in "RCLVID" else 104
            items.append(dict(name=e["name"], x=x, w=w, h=h, top=top, bottom=bottom))
            x += w + 60
        max_w = max(max_w, x - 60 + MARGIN)
        row_info.append(items)
    # lanes
    for items in row_info:
        pos = {}
        for it in items:
            for k, i in enumerate(it["top"]):
                pos[(it["name"], i)] = it["x"] + it["w"] * (k + 1) / (len(it["top"]) + 1)
        in_row = {n for n in (it["name"] for it in items)}
        lanes = []
        for net, terms in by_net.items():
            if net == GROUND:
                continue
            drawn = [t for t in terms if t[0] in in_row]
            if len(terms) >= 2 and len(drawn) == len(terms):
                lanes.append((min(pos[t] for t in terms), nl.nets[net], net, terms))
        lanes.sort(key=lambda t: (t[0], t[1]))
        nlanes = len(lanes)
        ytop = y + 22 + PITCH * nlanes + 70
        hmax = max(it["h"] for it in items)
        geo.append(dict(items=items, pos=pos, lanes=lanes, y=y, ytop=ytop, hmax=hmax))
        y = ytop + hmax + 64 + 16
    # draw
    for g in geo:
        ytop = g["ytop"]
        for it in g["items"]:
            name, x, w, h = it["name"], it["x"], it["w"], it["h"]
            c = sh.comp(name)
            kind = c["kind"]
            sh.add(f'<rect x="{x:g}" y="{ytop:g}" width="{w}" height="{h}" rx="4" fill="#f8fafc" stroke="{GREY}" stroke-width="1.2"/>')
            roles = ROLES.get(kind) or [str(i + 1) for i in range(len(c["nodes"]))]
            for k, i in enumerate(it["top"]):
                px = g["pos"][(name, i)]
                sh.pin(name, i, px, ytop)
                sh.text(px, ytop + 13, roles[i], 9, GREY, "middle")
            for k, i in enumerate(it["bottom"]):
                px = x + w * (k + 1) / (len(it["bottom"]) + 1)
                sh.pin(name, i, px, ytop + h)
                sh.text(px, ytop + h - 5, roles[i], 9, GREY, "middle")
                sh.ground((name, i))
                net_pos.setdefault(GROUND, (px + 20, ytop + h + 24))
            cur_pos[name] = (x + 6, ytop + h + 50)
            cx = x + w / 2
            sh.text(cx, ytop + 32, name, 12, INK, "middle", 700)
            val = c["value"]
            maxc = max(8, int(w / 6.2))
            shown = val if len(val) <= maxc else val[:maxc - 1] + "~"
            if kind in "RCLVID":
                glyph(sh, kind, cx, ytop + 52)
                sh.text(cx, ytop + 76, shown, 10.5, INK, "middle")
            else:
                sh.text(cx, ytop + 52, ("subckt " if kind == "X" else "model ") + shown, 10.5, INK, "middle", italic=True)
                sh.text(cx, ytop + 68, f"{len(c['nodes'])} terminals, node order = netlist order", 9, GREY, "middle")
        for xmin, shown, net, terms in g["lanes"]:
            lane_y = g["y"] + 22 + PITCH * g["lanes"].index((xmin, shown, net, terms))
            xlo, xhi = sh.wire_net(terms, lane_y)
            sh.text(xlo + 4, lane_y - 4, shown, 10.5, BLUE, "start", 700)
            net_pos[net] = (xlo + 10 + len(shown) * 6.6, lane_y - 4)
        laned = {t for *_, terms in g["lanes"] for t in terms}
        nbn = 0
        for it in g["items"]:
            for i in it["top"]:
                a = (it["name"], i)
                if a not in laned:
                    net_pos.setdefault(sh.net_of(a), sh.byname(a, nbn % 3))
                    nbn += 1
    used = {}
    for sig in nl.saves:                    # red probe boxes: V(a[,b]) at the first net, I(...) under the element
        info = signal_info(nl, sig)
        if "error" in info:
            continue                        # finish() reports it
        if info["kind"] == "V":
            pos = net_pos.get(info["nets"][0])
            step = (len(sig) * 6.6 + 14, 0)
            probed = info["nets"]
        else:
            pos = cur_pos.get(info["elem"])
            step = (0, 18)
            probed = []
        if pos is None:
            continue
        n = used.get(pos, 0)
        used[pos] = n + 1
        sh.tag(pos[0] + n * step[0], pos[1] + n * step[1], sig)
        sh.probes.add(sig.lower())
        sh.probed_nets.update(probed)
    return sh, dict(rows=geo, bottom=y, width=max_w)


# ---------------------------------------------------------------- output
def model_hashes(nl):
    out = []
    for m in nl.models:
        p = pathlib.Path(m)
        p = p if p.is_absolute() else nl.path.parent / p
        out.append((m, sha256(p) if p.exists() else None))
    return out


def load_layout(path):
    """Hand layout script: defines layout(sh, nl); optional TITLE, WIDTH, HEIGHT. -> dict(fn, title, width, height)."""
    spec = importlib.util.spec_from_file_location("circuit_layout_" + pathlib.Path(path).stem, str(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    if not callable(getattr(mod, "layout", None)):
        raise NetlistError(f"layout script {path} must define layout(sh, nl)")
    return dict(fn=mod.layout, title=getattr(mod, "TITLE", None), width=getattr(mod, "WIDTH", 1300),
                height=getattr(mod, "HEIGHT", 800))


def build_svg(nl, hints, pin_map_path, rows, parts, date, layout_name, skip=(), layout=None):
    """-> (svg text or None, violations, warnings, unmapped). layout = load_layout() dict: hand layout (the final figure);
    without it the automatic DRAFT layout is drawn."""
    warns = []
    blocks, ds = [], {}
    mapped = pin_map_path is not None
    for name, c in nl.comps.items():
        if c["kind"] != "X" or name in skip:
            continue
        part = parts.get(name, c["value"])
        if mapped:
            terms, w = pin_map.terminals(c["nodes"], part, rows)
            warns += [f"{name}: {x[len('WARNING: '):]}" for x in w]
            for r in rows:
                if r["Part"] == part and r[".SUBCKT node position"].isdigit() and pin_map.UNKNOWN not in (r["Pkg pin no"], r["Datasheet pin name"]):
                    ds[(name, int(r[".SUBCKT node position"]) - 1)] = f"{r['Datasheet pin name']} (pin {r['Pkg pin no']})"
        else:
            terms = [dict(pos=i, net=n, ds=None, sp=None) for i, n in enumerate(c["nodes"], 1)]
        blocks.append((f"{name} = {part}", terms))
    if layout:
        import symbols
        sh = symbols.Schematic(nl, layout["title"] or f"Circuit: {nl.path.name}", layout["width"], layout["height"])
        sh.ds = ds
        layout["fn"](sh, nl)
        g = dict(bottom=sh.h, width=sh.w)
    else:
        sh, g = draw(nl, hints, skip)
    violations = sh.finish()
    y = g["bottom"]
    left = MARGIN
    body, unmapped = [], 0
    pw = (3 if mapped else 1) * (pin_map.BW + 12)
    if blocks:
        body, y, unmapped = pin_map.panel(blocks, mapped, left, y)
        if mapped:
            lg, ly = pin_map.legend(left + pw + 30, g["bottom"])
            body += lg
            y = max(y, ly)
        right = left + pw + (30 + 400 if mapped else 0)
    else:
        right = 0
    width = int(max(g["width"], right + MARGIN, 640))
    notes = []
    if nl.tran:
        notes.append(nl.tran)
    notes += nl.steps
    notes += nl.meas[:6] + ([f"... {len(nl.meas) - 6} more .meas lines"] if len(nl.meas) > 6 else [])
    if nl.saves:
        notes.append(".save " + " ".join(nl.saves))
    foot = [f"Testbench: {nl.path.name}  SHA256 {sha256(nl.path)}"]
    for m, h in model_hashes(nl):
        foot.append(f"Model: {m}  SHA256 {h or 'NOT FOUND'}")
        if h is None:
            warns.append(f"model file {m} not found; footer shows NOT FOUND")
    foot.append(f"pin map: {pin_map_path or 'none'}" + (f"  |  UNMAPPED TERMINALS: {unmapped}" if mapped else ""))
    foot.append(f"layout: {layout_name}  |  {date}  |  label [C]  |  generated by docs\\sim\\circuits.py from the netlist")
    y += 14
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{{H}}" viewBox="0 0 {width} {{H}}" font-family="{FONT}">',
           f'<rect width="{width}" height="{{H}}" fill="#fff"/>',
           f'<text x="{MARGIN}" y="32" font-size="19" font-weight="700" fill="{INK}">{esc(sh.title) if layout else "Circuit: " + esc(nl.path.name)}</text>']
    out += sh.out + body
    for k, t in enumerate(notes):
        out.append(f'<text x="{MARGIN}" y="{y + 14 * k:g}" font-size="10.5" fill="{GREY}">{esc(t[:170])}</text>')
    y += 14 * len(notes) + 10
    out.append(f'<line x1="{MARGIN}" y1="{y - 8:g}" x2="{width - MARGIN}" y2="{y - 8:g}" stroke="#cbd5e1"/>')
    for k, t in enumerate(foot):
        out.append(f'<text x="{MARGIN}" y="{y + 8 + 14 * k:g}" font-size="10" fill="{GREY}">{esc(t)}</text>')
    height = int(y + 8 + 14 * len(foot) + 10)
    out.append("</svg>")
    svg = "\n".join(out).replace("{H}", str(height))
    return svg, violations, warns, unmapped


def write_draft(nl, hints, path):
    """First-draft hand layout script from the automatic grid: every element placed with its symbol, ground symbols and
    net-name flags instead of wires, red probe boxes. The module agent edits coordinates and replaces flags by wires."""
    rows = place(nl, hints)
    lines = [f"# DRAFT layout for {nl.path.name}, generated by circuits.py --draft. Edit the coordinates, replace the net-name",
             "# flags (sh.byname) by wires (sh.wire / sh.route), swap sh.subckt for sh.opamp(...) where it is an op-amp, then run:",
             f"#   python docs\\sim\\circuits.py {nl.path.name} --layout <this file> --out <dir>",
             f"TITLE = {('Circuit: ' + nl.path.name)!r}",
             f"WIDTH = {200 + max(len(r) for r in rows) * 300 + 300}",
             f"HEIGHT = {240 + len(rows) * 330 + 100}",
             "", "", "def layout(sh, nl):"]
    pos = {}
    calls = {"R": "resistor", "C": "capacitor", "L": "inductor", "D": "diode", "V": "vsource", "I": "isource",
             "Q": "bjt", "M": "mosfet", "X": "subckt"}
    for r, row in enumerate(rows):
        for c, e in enumerate(row):
            x, y = 200 + c * 300, 200 + r * 330
            pos[e["name"]] = (x, y)
            lines.append(f"    sh.{calls[nl.comps[e['name']]['kind']]}({e['name']!r}, {x}, {y})")
    lines.append("    # connections: net-name flags and ground symbols (replace by wires)")
    for name, c in nl.comps.items():
        for i, n in enumerate(c["nodes"]):
            lines.append(f"    sh.ground(({name!r}, {i}))" if key(n) == GROUND else f"    sh.byname(({name!r}, {i}))")
    lines.append("    # probes: the .save signals, red boxes")
    seen = {}
    for sig in nl.saves:
        info = signal_info(nl, sig)
        if "error" in info:
            lines.append(f"    # {sig}: {info['error']}")
        elif info["kind"] == "V":
            ts = [nl.terminals()[k][0] for k in info["nets"]]
            k = seen.get(ts[0], 0)
            seen[ts[0]] = k + 1
            if len(ts) == 1:
                lines.append(f"    sh.probe_node({sig!r}, {ts[0]!r}, 14, {-22 - 18 * k})")
            else:
                lines.append(f"    sh.probe_diff({sig!r}, {ts[0]!r}, {ts[1]!r}, 14, {-22 - 18 * k})")
        elif info["pin"] is not None:
            t = (info["elem"], info["pin"])
            k = seen.get(t, 0)
            seen[t] = k + 1
            lines.append(f"    sh.probe_pin({sig!r}, {t!r}, 14, {-22 - 18 * k})")
        else:
            x, y = pos[info["elem"]]
            k = seen.get(info["elem"], 0)
            seen[info["elem"]] = k + 1
            lines.append(f"    sh.probe_current({sig!r}, {info['elem']!r}, {x + 30}, {y - 60 - 18 * k})")
    if nl.tran:
        lines.append(f"    sh.notes([{('Analysis: ' + nl.tran)!r}])")
    pathlib.Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("cir")
    ap.add_argument("--out")
    ap.add_argument("--pin-map")
    ap.add_argument("--layout", help="hand layout script (.py, the final figure) or grid hints (.json, automatic DRAFT)")
    ap.add_argument("--draft", metavar="LAYOUT.py", help="write a first-draft layout script and exit")
    ap.add_argument("--part", nargs="*", default=[], help="XU1=MPN (default: the .subckt name)")
    ap.add_argument("--date", default=datetime.date.today().isoformat())
    a = ap.parse_args(argv)
    if not a.out and not a.draft:
        ap.error("--out is required (or --draft)")
    hand = bool(a.layout) and a.layout.lower().endswith(".py")
    try:
        nl = Netlist(a.cir)
        hints = load_hints(a.layout, nl) if a.layout and not hand else {}
        if a.draft:
            write_draft(nl, hints, a.draft)
            print(f"OK {a.draft}: draft layout for {len(nl.comps)} elements (edit it, then run with --layout)")
            return 0
        layout = load_layout(a.layout) if hand else None
        parts = dict(p.split("=", 1) for p in a.part)
        rows = pin_map.parse_pin_map(pathlib.Path(a.pin_map).read_text(encoding="utf-8")) if a.pin_map else []
        name = pathlib.Path(a.layout).name if a.layout else ""
        label = (f"{name} (hand layout)" if hand else f"{name} (grid hints, automatic DRAFT, not a final figure)" if a.layout
                 else "automatic DRAFT, not a final figure")
        svg, violations, warns, unmapped = build_svg(nl, hints, a.pin_map, rows, parts, a.date, label, layout=layout)
    except (NetlistError, ValueError, OSError, KeyError, AttributeError, TypeError, AssertionError) as e:
        print(f"ERROR: {type(e).__name__}: {e}")
        return 2
    for w in warns:
        print("WARNING:", w)
    if violations:
        for v in violations:
            print("VIOLATION:", v)
        print(f"FAILED: {len(violations)} violation(s); nothing written")
        return 1
    out = pathlib.Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    svg_path = out / "circuit.svg"
    svg_path.write_text(svg, encoding="utf-8")
    pymupdf.open(str(svg_path))[0].get_pixmap(dpi=150).save(str(svg_path.with_suffix(".png")))
    print(f"OK {svg_path}: {len(nl.comps)} elements drawn once, {len(nl.nets)} nets, UNMAPPED TERMINALS: "
          f"{unmapped if a.pin_map else 'n/a (pin map: none)'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
