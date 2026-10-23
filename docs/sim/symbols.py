"""Classic schematic symbols and the placement-by-coordinate API for docs\\sim\\circuits.py (00_coordination/T028).

Ported from the legacy LOAD drawer (generic parts only): the agent writes a per-testbench layout script next to the
testbench (``layout(sh, nl)``) that places symbols at absolute coordinates and wires their terminals; finish() is the
safety net (every element drawn once with all terminals, nothing extra, every net connected, every .save signal has a red
probe label). Nothing here knows a part: pin names come from the DS/SP/TB panel data (``sh.ds``) or from the roles.

Terminals are (element name, terminal index) tuples, index = position in the netlist line (SPICE node order).
Two-terminal symbols take rot: 0 = horizontal, pin 0 left; 180 = horizontal, pin 0 right; 90 = vertical, pin 0 top;
270 = vertical, pin 0 bottom (mirrors the pin order). ``vertical`` / ``flip`` are the legacy spelling of the same thing.
"""
import math

import pin_map
from circuits import BLUE, GREY, INK, RED, Sheet, esc, signal_info

ORANGE = "#c2410c"
ROLE_TEXT = {"INP": "IN+", "INN": "IN-", "VCC": "V+", "VEE": "V-", "OUT": "OUT"}
OPAMP_ROLES = ("INP", "INN", "VCC", "VEE", "OUT")


def describe_source(kind, value):
    """Text under a source symbol: plain numbers get DC and the unit, anything else is shown as written."""
    v = value.strip()
    try:
        float(v.replace("Meg", "e6").replace("k", "e3").replace("m", "e-3").replace("u", "e-6").replace("n", "e-9"))
        return f"DC {v} {'V' if kind == 'V' else 'A'}"
    except ValueError:
        return v


def rot_of(vertical=False, flip=False, rot=None):
    if rot is not None:
        if rot not in (0, 90, 180, 270):
            raise ValueError(f"rot must be 0, 90, 180 or 270, got {rot}")
        return rot
    return (270 if flip else 90) if vertical else (180 if flip else 0)


class Schematic(Sheet):
    def __init__(self, nl, title, w, h):
        super().__init__(nl)
        self.title, self.w, self.h = title, w, h
        self.ds = {}            # (element, terminal index) -> datasheet pin text, e.g. "IN+ (pin 3)" (from the pin map)
        self.centers, self.roles, self.segments = {}, {}, []
        self._dots = False

    # ---------------------------------------------------------------- basics
    def pin(self, name, idx, x, y, dx=0, dy=-6, anchor="middle", show=True):
        super().pin(name, idx, x, y)
        if show:
            self.text(x + dx, y + dy, self.nl.nets[self.net_of((name, idx))], 10, GREY, anchor)

    def T(self, name, role):
        """Terminal of a drawn op-amp by role (a swapped node order cannot be wired by mistake)."""
        return (name, self.roles[name].index(role))

    def dot(self, x, y):
        self.add(f'<circle cx="{x:g}" cy="{y:g}" r="3.6" fill="{INK}"/>')

    def block(self, x, y, w, h, lines):
        self.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="#f8fafc" stroke="none"/>' +
                 pin_map.dashes_svg(pin_map.round_rect_points(x, y, w, h, 6), 6, 4, GREY, 1.0))
        for k, s in enumerate(lines):
            self.text(x + 10, y + 20 + 15 * k, s, 11, INK, "start", 700 if k == 0 else 400)

    def notes(self, lines, size=11):
        """Free text lines at the bottom left of the sheet (analysis notes)."""
        for k, t in enumerate(lines):
            self.text(20, self.h - 16 * (len(lines) - k) - 6, t, size)

    def ds_label(self, name, idx, x, y, anchor, default=""):
        t = self.ds.get((name, idx), default)
        if t:
            self.text(x, y, t, 10.5, BLUE, anchor, 700)

    # ---------------------------------------------------------------- wires
    def wire(self, a, b, via=()):
        if self.net_of(a) != self.net_of(b):
            raise ValueError(f"wire joins different nets: {a} ({self.net_of(a)}) and {b} ({self.net_of(b)})")
        pts = [self.pin_xy[a], *via, self.pin_xy[b]]
        for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
            self.line(x1, y1, x2, y2)
        self.segments.append((self.net_of(a), pts))
        self.parent[self.find(a)] = self.find(b)

    def route(self, a, b, mode="hv", at=None):
        """Manhattan wire. hv: horizontal first, then vertical; vh: the reverse; zx/zy: via the vertical line x=at / horizontal line y=at."""
        (ax, ay), (bx, by) = self.pin_xy[a], self.pin_xy[b]
        via = {"hv": [(bx, ay)], "vh": [(ax, by)], "zx": [(at, ay), (at, by)], "zy": [(ax, at), (bx, at)]}[mode]
        self.wire(a, b, via=[p for p in via if p not in ((ax, ay), (bx, by))])

    def ground(self, a):
        super().ground(a)

    def byname(self, a, dx=None, dy=None):
        """Long connection shown by net name: dashed stub and a bold tag; the same net name means connected.
        Without dx, dy the stub leaves the element away from its centre."""
        x, y = self.pin_xy[a]
        if dx is None:
            cx, cy = self.centers.get(a[0], (x, y + 1))
            vx, vy = x - cx, y - cy
            dx, dy = (34 if vx >= 0 else -34, 0) if abs(vx) > abs(vy) else (0, 34 if vy >= 0 else -34)
        net = self.nl.nets[self.net_of(a)]
        self.line(x, y, x + dx, y + dy, GREY, 1.4, "4 3")
        self.text(x + dx + (4 if dx >= 0 else -4), y + dy + 4, f"to net {net}", 10.5, BLUE, "start" if dx >= 0 else "end", 700)
        self.named.add(a)

    # ---------------------------------------------------------------- probes (red boxes, same names as the result traces)
    def _probe(self, sig, x, y, targets):
        w = len(sig) * 6.6 + 10
        for tx, ty in targets:
            self.line(tx, ty, x + w / 2, y - 4, RED, 1)
        self.tag(x, y, sig)
        self.probes.add(sig.lower())

    def probe_node(self, sig, a, dx=14, dy=-22):
        info = signal_info(self.nl, sig)
        if info.get("error") or info["kind"] != "V" or len(info["nets"]) != 1 or info["nets"][0] != self.net_of(a):
            raise ValueError(f"probe {sig} does not measure net {self.net_of(a)} (terminal {a})")
        x, y = self.pin_xy[a]
        self._probe(sig, x + dx, y + dy, [(x, y)])
        self.probed_nets.add(self.net_of(a))

    def probe_diff(self, sig, a, b, dx=14, dy=-22):
        """V(a,b): one red box with a leader to each of the two nodes."""
        info = signal_info(self.nl, sig)
        if info.get("error") or info["kind"] != "V" or info["nets"] != [self.net_of(a), self.net_of(b)]:
            raise ValueError(f"probe {sig} does not measure nets {self.net_of(a)},{self.net_of(b)}")
        (x, y), (x2, y2) = self.pin_xy[a], self.pin_xy[b]
        self._probe(sig, x + dx, y + dy, [(x, y), (x2, y2)])
        self.probed_nets.update(info["nets"])

    def probe_current(self, sig, name, x, y):
        info = signal_info(self.nl, sig)
        if info.get("error") or info["kind"] != "I" or info["pin"] is not None or info["elem"] != name:
            raise ValueError(f"probe {sig} is not the current of element {name}")
        cx, cy = self.centers.get(name, (x, y))
        self._probe(sig, x, y, [(cx, cy)])

    def probe_pin(self, sig, a, dx=14, dy=-22):
        """I(X1:pin): red box with a leader to that terminal."""
        info = signal_info(self.nl, sig)
        if info.get("error") or info["kind"] != "I" or info["elem"] != a[0] or info["pin"] != a[1]:
            raise ValueError(f"probe {sig} is not the current into terminal {a}")
        x, y = self.pin_xy[a]
        self._probe(sig, x + dx, y + dy, [(x, y)])

    # ---------------------------------------------------------------- junction dots
    def junction_dots(self):
        """A dot where the wires of one net meet in a T or cross-junction (>= 3 wire ends, or an end on the inside of a wire)."""
        if self._dots:
            return
        self._dots = True

        def on(p, a, b, tol=0.01):
            (x, y), (x1, y1), (x2, y2) = p, a, b
            if min(x1, x2) - tol > x or x > max(x1, x2) + tol or min(y1, y2) - tol > y or y > max(y1, y2) + tol:
                return False
            return abs((x2 - x1) * (y - y1) - (y2 - y1) * (x - x1)) <= tol * max(1.0, math.hypot(x2 - x1, y2 - y1))
        by_net = {}
        for net, pts in self.segments:
            by_net.setdefault(net, []).extend(zip(pts, pts[1:]))
        seen = set()
        for net, segs in by_net.items():
            for p in sorted({e for s in segs for e in s}):
                ends = sum(1 for s in segs if p in s)
                inner = sum(1 for s in segs if p not in s and on(p, *s))
                if (ends + inner >= 3 or (inner and ends)) and (net, p) not in seen:
                    seen.add((net, p))
                    self.dot(*p)

    def finish(self):
        self.junction_dots()
        return super().finish()

    # ---------------------------------------------------------------- two-terminal symbols
    def _two(self, name, x, y, rot, body, label, note, note_col=ORANGE):
        """Common frame: leads to pins at +-40 along the symbol axis, body drawn in local (u, v) coordinates."""
        self.comp(name)
        f = {0: lambda u, v: (x + u, y + v), 180: lambda u, v: (x - u, y - v),
             90: lambda u, v: (x + v, y + u), 270: lambda u, v: (x - v, y - u)}[rot]
        self.centers[name] = (x, y)
        body(f)
        p0, p1 = f(-40, 0), f(40, 0)
        self.pin(name, 0, *p0, *((0, -6, "middle") if rot in (0, 180) else (10, 4, "start")))
        self.pin(name, 1, *p1, *((0, -6, "middle") if rot in (0, 180) else (10, 4, "start")))
        if rot in (0, 180):
            self.text(x, y + 28, label, 11, INK, "middle", 700)
            if note:
                self.text(x, y + 41, note, 10, note_col, "middle")
        else:
            self.text(x + 16, y - 2, label, 11, INK, "start", 700)
            if note:
                self.text(x + 16, y + 12, note, 10, note_col)

    def _seg(self, f, u1, v1, u2, v2, w=1.8):
        (x1, y1), (x2, y2) = f(u1, v1), f(u2, v2)
        self.line(x1, y1, x2, y2, INK, w)

    def resistor(self, name, x, y, vertical=False, flip=False, note="", unit="ohm", rot=None):
        c = self.nl.comps[name]

        def body(f):
            pts = " ".join("%g,%g" % f(u, v) for u, v in ((-22, -8), (22, -8), (22, 8), (-22, 8)))
            self.add(f'<polygon points="{pts}" fill="#fff" stroke="{INK}" stroke-width="1.8"/>')
            self._seg(f, -40, 0, -22, 0)
            self._seg(f, 22, 0, 40, 0)
        self._two(name, x, y, rot_of(vertical, flip, rot), body, f"{name} {c['value']} {unit}".strip(), note)

    def capacitor(self, name, x, y, vertical=False, flip=False, note="", rot=None):
        c = self.nl.comps[name]

        def body(f):
            self._seg(f, -40, 0, -5, 0)
            self._seg(f, 5, 0, 40, 0)
            self._seg(f, -5, -14, -5, 14, 2.4)
            self._seg(f, 5, -14, 5, 14, 2.4)
        self._two(name, x, y, rot_of(vertical, flip, rot), body, f"{name} {c['value']} F", note)

    def inductor(self, name, x, y, vertical=False, flip=False, note="", rot=None):
        c = self.nl.comps[name]

        def body(f):
            self._seg(f, -40, 0, -24, 0)
            self._seg(f, 24, 0, 40, 0)
            pts = []
            for k in range(3):
                for t in range(0, 13):
                    a = math.pi - math.pi * t / 12
                    pts.append(f(-16 + 16 * k + 8 * math.cos(a), -8 * math.sin(a)))
            d = "M " + " L ".join("%.1f %.1f" % p for p in pts)
            self.add(f'<path d="{d}" fill="none" stroke="{INK}" stroke-width="1.8"/>')
        self._two(name, x, y, rot_of(vertical, flip, rot), body, f"{name} {c['value']} H", note)

    def diode(self, name, x, y, vertical=False, flip=False, note="", rot=None):
        """Anode = terminal 0, cathode = terminal 1."""
        c = self.nl.comps[name]

        def body(f):
            pts = " ".join("%g,%g" % f(u, v) for u, v in ((-8, -10), (-8, 10), (8, 0)))
            self.add(f'<polygon points="{pts}" fill="#fff" stroke="{INK}" stroke-width="1.8"/>')
            self._seg(f, 8, -10, 8, 10, 2.4)
            self._seg(f, -40, 0, -8, 0)
            self._seg(f, 8, 0, 40, 0)
        self._two(name, x, y, rot_of(vertical, flip, rot), body, f"{name} {c['value']}", note)

    # ---------------------------------------------------------------- sources (vertical)
    def vsource(self, name, x, y, desc=None, note="", side="right", flip=False):
        c = self.comp(name)
        self.centers[name] = (x, y)
        s = -1 if flip else 1
        self.add(f'<circle cx="{x}" cy="{y}" r="17" fill="#fff" stroke="{INK}" stroke-width="1.8"/>')
        self.text(x, y - 3 * s, "+", 12, INK, "middle", 700)
        self.text(x, y + 13 * s, "-", 12, INK, "middle", 700)
        self.line(x, y - 40, x, y - 17)
        self.line(x, y + 17, x, y + 40)
        self.pin(name, 0, x, y - 40 * s, 8, 4, "start")
        self.pin(name, 1, x, y + 40 * s, 8, 4, "start")
        self._src_text(name, x, y, side, desc or describe_source("V", c["value"]), note)

    def isource(self, name, x, y, desc=None, note="", side="right", flip=False):
        """Current flows through the source from terminal 0 to terminal 1 (arrow)."""
        c = self.comp(name)
        self.centers[name] = (x, y)
        s = -1 if flip else 1
        self.add(f'<circle cx="{x}" cy="{y}" r="17" fill="#fff" stroke="{INK}" stroke-width="1.8"/>')
        self.line(x, y - 9 * s, x, y + 6 * s)
        self.add(f'<polygon points="{x - 5},{y + 4 * s} {x + 5},{y + 4 * s} {x},{y + 12 * s}" fill="{INK}"/>')
        self.line(x, y - 40, x, y - 17)
        self.line(x, y + 17, x, y + 40)
        self.pin(name, 0, x, y - 40 * s, 8, 4, "start")
        self.pin(name, 1, x, y + 40 * s, 8, 4, "start")
        self._src_text(name, x, y, side, desc or describe_source("I", c["value"]), note)

    def _src_text(self, name, x, y, side, desc, note):
        tx, an = (x + 26, "start") if side == "right" else (x - 26, "end")
        self.text(tx, y - 8, name, 11, INK, an, 700)
        self.text(tx, y + 5, desc, 10.5, INK, an)
        if note:
            self.text(tx, y + 18, note, 10, ORANGE, an)

    # ---------------------------------------------------------------- op-amp triangle
    def opamp(self, name, x, y, note="", roles=OPAMP_ROLES):
        """roles = role of each netlist node index, e.g. TI order INP INN VCC VEE OUT; ST order INN INP OUT VCC VEE.
        Printed pin names (blue) come from the pin map (sh.ds) or default to IN+ IN- V+ V- OUT."""
        c = self.comp(name)
        if sorted(roles) != sorted(OPAMP_ROLES) or len(c["nodes"]) != 5:
            raise ValueError(f"{name}: an op-amp symbol needs 5 terminals with the roles {OPAMP_ROLES}")
        self.roles[name] = list(roles)
        self.centers[name] = (x + 55, y)
        self.add(f'<polygon points="{x},{y - 55} {x},{y + 55} {x + 110},{y}" fill="#fff" stroke="{INK}" stroke-width="2"/>')
        geo = {"INP": (x - 25, y - 28, x, y - 28, -4, 3, "end"), "INN": (x - 25, y + 28, x, y + 28, -4, 3, "end"),
               "VCC": (x + 45, y - 70, x + 45, y - 27, 6, 4, "start"), "VEE": (x + 45, y + 70, x + 45, y + 27, 6, 4, "start"),
               "OUT": (x + 135, y, x + 110, y, 0, -7, "middle")}
        for k, role in enumerate(roles):
            px, py, ex, ey, dx, dy, an = geo[role]
            self.line(px, py, ex, ey)
            self.pin(name, k, px, py, dx, dy if role in ("INP", "INN", "OUT") else (-8 if role == "VCC" else 16), an)
        self.text(x + 8, y - 24, "+", 12, INK, "start", 700)
        self.text(x + 8, y + 36, "-", 14, INK, "start", 700)
        self.text(x + 34, y + 4, name, 12, INK, "start", 700)
        self.text(x + 34, y + 17, f"model {c['value']}", 9.5, GREY)
        tags = {"INP": (x - 29, y - 36, "end"), "INN": (x - 29, y + 44, "end"), "VCC": (x + 53, y - 96, "start"),
                "VEE": (x + 53, y + 108, "start"), "OUT": (x + 138, y + 16, "start")}
        for k, role in enumerate(roles):
            tx, ty, an = tags[role]
            self.ds_label(name, k, tx, ty, an, ROLE_TEXT[role])
        order = " ".join({"INP": "IN+", "INN": "IN-", "VCC": "VCC/V+", "VEE": "VEE/V-", "OUT": "OUT"}[r] for r in roles)
        self.text(x, y + 126, f"model node order (1..5): {order}", 9.5, GREY)
        if note:
            self.text(x, y + 142, note, 10, ORANGE)

    # ---------------------------------------------------------------- transistors
    def bjt(self, name, x, y, note=""):
        """C (top), B (left), E (bottom); a fourth node (substrate) gets a pin on the right. PNP when .model says PNP."""
        c = self.comp(name)
        self.centers[name] = (x + 15, y)
        pnp = self.nl.model_types.get(c["value"].upper()) == "PNP"
        self.line(x, y - 20, x, y + 20, w=2.8)
        self.line(x - 40, y, x, y)
        self.line(x, y - 9, x + 30, y - 30)
        self.line(x + 30, y - 30, x + 30, y - 50)
        self.line(x, y + 9, x + 30, y + 30)
        self.line(x + 30, y + 30, x + 30, y + 50)
        if pnp:
            self.add(f'<polygon points="{x + 7},{y + 11} {x + 17},{y + 13} {x + 11},{y + 21}" fill="{INK}"/>')
        else:
            self.add(f'<polygon points="{x + 30},{y + 30} {x + 20},{y + 28} {x + 25},{y + 20}" fill="{INK}"/>')
        self.pin(name, 0, x + 30, y - 50, 8, 4, "start")
        self.pin(name, 1, x - 40, y, 0, -6)
        self.pin(name, 2, x + 30, y + 50, 8, 4, "start")
        if len(c["nodes"]) == 4:
            self.line(x + 14, y, x + 56, y)
            self.pin(name, 3, x + 56, y, 0, -6)
        for k, (tx, ty, an) in enumerate(((x + 38, y - 52, "start"), (x - 44, y - 12, "end"), (x + 38, y + 62, "start"))):
            self.ds_label(name, k, tx, ty, an)
        self.text(x + 40, y + 2, f"{name} {c['value']}" + (" (PNP)" if pnp else " (NPN)"), 11, INK, "start", 700)
        if note:
            self.text(x + 40, y + 16, note, 10, ORANGE)

    def mosfet(self, name, x, y, note=""):
        """D (top), G (left), S (bottom); an M element's bulk node gets a pin on the right. PMOS when .model says PMOS."""
        c = self.comp(name)
        self.centers[name] = (x + 18, y)
        pmos = self.nl.model_types.get(c["value"].upper()) == "PMOS"
        self.line(x, y - 30, x, y + 30, w=2.6)
        self.line(x - 14, y - 24, x - 14, y + 24, w=2.6)
        self.line(x - 14, y, x - 50, y)
        for yy in (-24, 24):
            self.line(x, y + yy, x + 36, y + yy)
        self.line(x + 36, y - 24, x + 36, y - 60)
        self.line(x + 36, y + 24, x + 36, y + 60)
        self.line(x, y, x + 36, y)
        self.line(x + 36, y, x + 36, y + 24)
        tip = (x + 8, x + 22) if not pmos else (x + 22, x + 8)
        self.add(f'<polygon points="{tip[1]},{y - 4} {tip[0]},{y} {tip[1]},{y + 4}" fill="{INK}"/>')
        self.pin(name, 0, x + 36, y - 60, show=False)
        self.pin(name, 1, x - 50, y, show=False)
        self.pin(name, 2, x + 36, y + 60, show=False)
        if len(c["nodes"]) == 4:
            self.line(x + 36, y, x + 60, y)
            self.pin(name, 3, x + 60, y, 6, -6, "start")
        D, G, S = c["nodes"][:3]
        self.text(x + 44, y - 66, f"D  (net {D})", 10.5, GREY)
        self.ds_label(name, 0, x + 44, y - 53, "start", "D")
        self.text(x - 56, y - 22, f"G  (net {G})", 10.5, GREY, "end")
        self.ds_label(name, 1, x - 56, y - 9, "end", "G")
        self.text(x + 44, y + 74, f"S  (net {S})", 10.5, GREY)
        self.ds_label(name, 2, x + 44, y + 87, "start", "S")
        self.text(x - 6, y + 122, f"{name} = {'subckt' if c['kind'] == 'X' else 'model'} {c['value']}", 11, INK, "middle", 700)
        if note:
            self.text(x - 6, y + 136, note, 10, GREY, "middle")

    # ---------------------------------------------------------------- generic subcircuit box
    def subckt(self, name, x, y, w=150, note=""):
        """Box with the terminals split over the left and right edge in netlist order (top to bottom)."""
        c = self.comp(name)
        n = len(c["nodes"])
        nl_, nr = (n + 1) // 2, n // 2
        h = max(70, 28 * max(nl_, nr) + 30)
        self.centers[name] = (x + w / 2, y + h / 2)
        self.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="4" fill="#fff" stroke="{INK}" stroke-width="2"/>')
        for k in range(n):
            left = k < nl_
            row, cnt = (k, nl_) if left else (k - nl_, nr)
            py = y + h * (row + 1) / (cnt + 1)
            px = x - 24 if left else x + w + 24
            self.line(px, py, x if left else x + w, py)
            self.pin(name, k, px, py, 0, -6)
            self.text(x + 6 if left else x + w - 6, py + 4, str(k + 1), 9, GREY, "start" if left else "end")
            self.ds_label(name, k, px + (-4 if left else 4), py + 14, "end" if left else "start")
        self.text(x + w / 2, y + 18, name, 12, INK, "middle", 700)
        self.text(x + w / 2, y + 32, f"subckt {c['value']}", 10, GREY, "middle", italic=True)
        if note:
            self.text(x + w / 2, y + h + 16, note, 10, ORANGE, "middle")
