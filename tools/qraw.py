"""Minimal reader for QSPICE .qraw files (LTspice-style header + binary block). Pure Python.

    from qraw import read_qraw
    r = read_qraw("sim/x.qraw")   # r.vars: [names], r.steps: list of {name: [values]}

Layout, inferred from the file size and checked by an exact size match:
  real data:    abscissa float64, other vars float64 or float32
  complex data: abscissa float64 (real), other vars complex128
"""
import re, struct, sys
from types import SimpleNamespace


def read_qraw(path):
    raw = open(path, "rb").read()
    hdr_end = raw.index(b"Binary:\n") + len(b"Binary:\n")
    hdr = raw[:hdr_end].decode("ascii", "replace")
    flags = re.search(r"Flags:\s*(.*)", hdr).group(1)
    npts = int(re.search(r"No\. Points:\s*(\d+)", hdr).group(1))
    names = re.findall(r"^\t\d+\t(\S+)\t", hdr, re.M)
    nv = len(names)
    data = raw[hdr_end:]
    complex_ = "complex" in flags
    layouts = ([("<d" + "dd" * (nv - 1), True)] if complex_ else
               [("<" + "d" * nv, False), ("<d" + "f" * (nv - 1), False)])
    for fmt, cplx in layouts:
        if struct.calcsize(fmt) * npts == len(data):
            break
    else:
        raise ValueError(f"{path}: no known layout matches {len(data)} bytes for {npts} pts x {nv} vars")
    size = struct.calcsize(fmt)
    cols = [[] for _ in names]
    for i in range(npts):
        vals = struct.unpack_from(fmt, data, i * size)
        if cplx:
            cols[0].append(vals[0])
            for k in range(1, nv):
                cols[k].append(complex(vals[2 * k - 1], vals[2 * k]))
        else:
            for k in range(nv):
                cols[k].append(vals[k])
    # stepped runs restart the abscissa; split there
    x = cols[0]
    starts = [0] + [i for i in range(1, npts) if abs(x[i]) < abs(x[i - 1]) and (complex_ or x[i] == 0 or x[i] < x[i - 1])]
    bounds = starts + [npts]
    steps = [{n: cols[k][a:b] for k, n in enumerate(names)} for a, b in zip(bounds, bounds[1:])]
    return SimpleNamespace(vars=names, flags=flags, steps=steps, header=hdr)


def meas_values(meas_txt, name):
    """Per-step values of one .meas result from a QPOST output file (sim/out/<name>.meas.txt).

    With .save active, .step parameters are no longer stored as data columns, so testbenches echo
    them with `.meas <type> <name> PARAM <param>` and analyzers read them back with this.
    """
    lines = open(meas_txt, encoding="utf-8", errors="replace").read().splitlines()
    head = next(i for i, l in enumerate(lines) if re.match(rf"\.meas\s+\w+\s+{re.escape(name)}\s", l, re.I))
    vals = []
    for l in lines[head + 1:]:
        if l.startswith(".meas"):
            break
        # stepped runs:   "   1    3.27975    0.00095"  (step index, value[, at-time])
        # unstepped runs: "       0.631937      1e-06" (value[, at-time])  - no step index
        toks = re.findall(r"[-+]?(?:\d+\.?\d*(?:[eE][-+]?\d+)?|\.\d+(?:[eE][-+]?\d+)?)|nan", l.replace("(", " ").replace(",", " "))
        if not toks:
            continue
        stepped = len(toks) >= 2 and re.fullmatch(r"\d+", toks[0]) is not None
        vals.append(float(toks[1] if stepped else toks[0]))
    return vals


def stream_real(path, names, windows=None):
    """Memory-light reader for large *real* (transient) .qraw files.

    Memory-maps the file and unpacks only the requested columns. `names` are matched by prefix
    (case-insensitive). `windows` is an optional list of (t0, t1) abscissa ranges to keep.
    Returns {"steps": [ {name: [values], ...}, ... ], "vars": all_names}.
    """
    import mmap
    with open(path, "rb") as fh:
        mm = mmap.mmap(fh.fileno(), 0, access=mmap.ACCESS_READ)
        hdr_end = mm.find(b"Binary:\n") + len(b"Binary:\n")
        hdr = mm[:hdr_end].decode("ascii", "replace")
        if "complex" in re.search(r"Flags:\s*(.*)", hdr).group(1):
            raise ValueError("stream_real() handles real (transient) data only")
        npts = int(re.search(r"No\. Points:\s*(\d+)", hdr).group(1))
        allnames = re.findall(r"^\t\d+\t(\S+)\t", hdr, re.M)
        nv = len(allnames)
        nbytes = len(mm) - hdr_end
        if 8 * nv * npts == nbytes:
            widths = [8] * nv
        elif (8 + 4 * (nv - 1)) * npts == nbytes:
            widths = [8] + [4] * (nv - 1)
        else:
            raise ValueError(f"{path}: no known layout matches {nbytes} bytes")
        offs = [sum(widths[:k]) for k in range(nv)]
        rec = sum(widths)
        pick = []
        for want in names:
            k = next(i for i, n in enumerate(allnames) if n.upper().startswith(want.upper()))
            pick.append((want, offs[k], "<d" if widths[k] == 8 else "<f"))
        steps, cur, prev_t = [], None, None
        for i in range(npts):
            base = hdr_end + i * rec
            t = struct.unpack_from("<d", mm, base)[0]
            if prev_t is None or t < prev_t:          # new .step segment
                cur = {w: [] for w, _, _ in pick}
                steps.append(cur)
            prev_t = t
            if windows and not any(a <= t <= b for a, b in windows):
                continue
            for w, o, f in pick:
                cur[w].append(struct.unpack_from(f, mm, base + o)[0])
        mm.close()
    return {"steps": steps, "vars": allnames}


if __name__ == "__main__":
    r = read_qraw(sys.argv[1])
    print(r.flags, "| vars:", len(r.vars), "| steps:", len(r.steps), "| pts/step:", [len(s[r.vars[0]]) for s in r.steps])
