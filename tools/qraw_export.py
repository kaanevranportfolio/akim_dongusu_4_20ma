"""Export a QSPICE .qraw (only the signals that were .save'd) to a small CSV.

Usage
    python qraw_export.py <qraw> <csv> [--max-points N]      one file
    python qraw_export.py                                    as an -Analyze script of run_sim.ps1:
                                                             exports every .qraw of the batch

Mechanism for the no-argument form: run_sim.ps1 sets two environment variables before it starts the -Analyze scripts,
SIM_RAW_LIST (the .qraw paths of the batch, separated by ';') and SIM_OUT_DIR (the project's sim\\out folder); every
raw file becomes <SIM_OUT_DIR>\\<testbench>.csv. Exit code 0 = all exported, 1 = at least one failure.

CSV format
    line 1:  # testbench=<name>.cir; qraw_points=<n>; decimated_to=<m>; step_count=<k>
    line 2:  step,<abscissa>,<signal1>,<signal2>,...   (complex data: <signal>_re,<signal>_im instead of <signal>)
    then one row per kept point; every .step run has its own 1-based step index (the tag of the engine log "k of K steps").
Decimation (per step, only when a step has more than N points, default N = 5000): uniform sampling plus the first and the
last point and each signal's minimum and maximum point, so no peak is lost; the number of kept points per step is <= N.
Runs below N are written in full. Large files are read through numpy.memmap (columns are sliced, never the whole file in RAM).
"""
import os
import pathlib
import re
import struct
import sys

import numpy as np

DEFAULT_MAX = 5000


def parse_header(path):
    with open(path, "rb") as fh:
        head = fh.read(1 << 20)
    k = head.index(b"Binary:\n") + len(b"Binary:\n")
    hdr = head[:k].decode("ascii", "replace")
    flags = re.search(r"Flags:\s*(.*)", hdr).group(1)
    npts = int(re.search(r"No\. Points:\s*(\d+)", hdr).group(1))
    names = re.findall(r"^\t\d+\t(\S+)\t", hdr, re.M)
    return k, flags, npts, names


def load_columns(path):
    """Return (names, x, Y, is_complex): x = abscissa (n,), Y = signals (n, m) as float64 (or complex128)."""
    off, flags, npts, names = parse_header(path)
    nv = len(names)
    size = os.path.getsize(path) - off
    if "complex" in flags:
        dt = np.dtype([("x", "<f8")] + [(f"c{k}", "<c16") for k in range(nv - 1)])
        cplx = True
        if dt.itemsize * npts != size:
            raise ValueError(f"{path}: complex layout does not match {size} bytes")
    else:
        cplx = False
        if 8 * nv * npts == size:
            dt = np.dtype([("x", "<f8")] + [(f"c{k}", "<f8") for k in range(nv - 1)])
        elif (8 + 4 * (nv - 1)) * npts == size:
            dt = np.dtype([("x", "<f8")] + [(f"c{k}", "<f4") for k in range(nv - 1)])
        else:
            raise ValueError(f"{path}: no known layout matches {size} bytes")
    mm = np.memmap(path, dtype=dt, mode="r", offset=off, shape=(npts,))
    x = np.array(mm["x"], dtype=np.float64)
    return names, x, mm, cplx


def step_bounds(x, cplx):
    if cplx:
        starts = [0] + [i for i in range(1, len(x)) if abs(x[i]) < abs(x[i - 1])]
    else:
        starts = [0] + [i for i in range(1, len(x)) if x[i] < x[i - 1]]
    return starts + [len(x)]


def keep_indices(Yseg, n_max):
    n = Yseg.shape[0]
    if n <= n_max:
        return np.arange(n)
    m = Yseg.shape[1]
    extra = {0, n - 1}
    for j in range(m):
        col = np.abs(Yseg[:, j]) if np.iscomplexobj(Yseg) else Yseg[:, j]
        extra.add(int(np.argmin(col)))
        extra.add(int(np.argmax(col)))
    uniform = max(2, n_max - len(extra))
    idx = set(np.linspace(0, n - 1, uniform).round().astype(int).tolist()) | extra
    idx = np.array(sorted(idx))
    if len(idx) > n_max:                                 # trim uniform points only, never the extrema
        keep = sorted(extra)
        rest = [i for i in idx.tolist() if i not in extra]
        room = max(0, n_max - len(keep))
        pick = np.linspace(0, len(rest) - 1, room).round().astype(int).tolist() if rest and room else []
        idx = np.array(sorted(set(keep) | {rest[p] for p in pick}))
    return idx


def export(qraw, csv, max_points=DEFAULT_MAX):
    qraw, csv = pathlib.Path(qraw), pathlib.Path(csv)
    names, x, mm, cplx = load_columns(qraw)
    sigs = names[1:]
    bounds = step_bounds(x, cplx)
    rows_out = 0
    body = []
    for si in range(len(bounds) - 1):
        a, b = bounds[si], bounds[si + 1]
        Y = np.column_stack([np.asarray(mm[f"c{k}"][a:b]) for k in range(len(sigs))]) if sigs else np.zeros((b - a, 0))
        idx = keep_indices(Y, max_points)
        for i in idx:
            vals = []
            for j in range(len(sigs)):
                v = Y[i, j]
                if cplx:
                    vals.append("%.10g" % v.real)
                    vals.append("%.10g" % v.imag)
                else:
                    vals.append("%.10g" % v)
            body.append(f"{si + 1},{x[a + i]:.12g}," + ",".join(vals))
        rows_out += len(idx)
    head2 = ["step", names[0]]
    for s in sigs:
        head2 += [s + "_re", s + "_im"] if cplx else [s]
    csv.parent.mkdir(parents=True, exist_ok=True)
    with open(csv, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(f"# testbench={qraw.stem}.cir; qraw_points={len(x)}; decimated_to={rows_out}; step_count={len(bounds) - 1}\n")
        fh.write(",".join(head2) + "\n")
        fh.write("\n".join(body) + ("\n" if body else ""))
    del mm
    return len(x), rows_out, len(bounds) - 1


def main(argv):
    maxp = DEFAULT_MAX
    args = list(argv)
    if "--max-points" in args:
        i = args.index("--max-points")
        maxp = int(args[i + 1])
        del args[i:i + 2]
    if len(args) == 2:
        n, m, k = export(args[0], args[1], maxp)
        print(f"{args[0]} -> {args[1]}: {n} points, {m} rows written, {k} step(s)")
        return 0
    if args:
        print(__doc__)
        return 2
    raw = [r for r in os.environ.get("SIM_RAW_LIST", "").split(";") if r]
    outdir = os.environ.get("SIM_OUT_DIR")
    if not raw or not outdir:
        print("qraw_export: no arguments and SIM_RAW_LIST / SIM_OUT_DIR are not set (run it through run_sim.ps1 -Analyze)")
        return 2
    bad = 0
    for r in raw:
        p = pathlib.Path(r)
        if not p.exists():
            print(f"qraw_export: missing {r}")
            bad += 1
            continue
        try:
            n, m, k = export(p, pathlib.Path(outdir) / f"{p.stem}.csv", maxp)
            print(f"{p.name} -> {pathlib.Path(outdir) / (p.stem + '.csv')}: {n} points, {m} rows written, {k} step(s)")
        except Exception as e:                                  # report every file, then fail
            print(f"qraw_export: {r}: {e}")
            bad += 1
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
