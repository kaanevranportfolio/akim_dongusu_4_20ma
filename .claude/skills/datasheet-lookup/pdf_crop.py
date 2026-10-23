"""Crop one region of one PDF page to a PNG (PyMuPDF).

  pdf_crop.py <pdf> <page> x0 y0 x1 y1 [--dpi 150] [--out DIR]

Coordinates are fractions 0..1 of the page width/height (origin top-left). --dpi must be 100..200.
A box covering >= 95% of the page (e.g. 0 0 1 1) is rejected (non-zero exit); there is no override flag.

  pdf_crop.py <pdf> <page> --around "<label text>" [--pad-up 0.04] [--pad-down 0.10] [--dpi 150]

Equations and symbols that do not extract cleanly: finds the label text on the page and crops the
full text width around it (one image), so the equation and its label are in the same picture.
Writes <out>/<pdf-stem>_p<N>_crop.png (default out: docs/ref/_crops) and prints the path.

  ... --topic <topic> [--doc D21]

With a topic the file is named D<nn>_p<page>_<topic>.png (D<nn> = --doc, or the D<nn>_ prefix of the PDF file name);
without a topic, or when no D<nn> can be found, the old name is kept.
"""
import argparse
import pathlib
import re

import pymupdf

from _common import gate, report


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("page", type=int)
    for k in ("x0", "y0", "x1", "y1"):
        ap.add_argument(k, type=float, nargs="?")
    ap.add_argument("--around")
    ap.add_argument("--pad-up", type=float, default=0.04)
    ap.add_argument("--pad-down", type=float, default=0.10)
    ap.add_argument("--dpi", type=int, default=150)
    ap.add_argument("--out", default="docs/ref/_crops")
    ap.add_argument("--topic")
    ap.add_argument("--doc")
    a = ap.parse_args()
    if a.around is None:
        if None in (a.x0, a.y0, a.x1, a.y1):
            raise SystemExit("give x0 y0 x1 y1 or --around")
        if not (0 <= a.x0 < a.x1 <= 1 and 0 <= a.y0 < a.y1 <= 1):
            raise SystemExit("need 0 <= x0 < x1 <= 1 and 0 <= y0 < y1 <= 1")
    if not 100 <= a.dpi <= 200:
        raise SystemExit("dpi must be 100..200")
    doc = pymupdf.open(a.pdf)
    gate(a.pdf, doc)
    if not 1 <= a.page <= len(doc):
        raise SystemExit(f"page out of range 1..{len(doc)}")
    pg = doc[a.page - 1]
    r = pg.rect
    if a.around:
        hits = pg.search_for(a.around)
        if not hits:
            raise SystemExit(f"label '{a.around}' not found on page {a.page}")
        h = hits[0]
        clip = pymupdf.Rect(r.x0 + 0.05 * r.width, max(r.y0, h.y0 - a.pad_up * r.height),
                            r.x1 - 0.05 * r.width, min(r.y1, h.y1 + a.pad_down * r.height))
    else:
        clip = pymupdf.Rect(r.x0 + a.x0 * r.width, r.y0 + a.y0 * r.height,
                            r.x0 + a.x1 * r.width, r.y0 + a.y1 * r.height)
    if clip.get_area() >= 0.95 * r.get_area():
        raise SystemExit("crop covers >= 95% of the page: full-page images are not allowed; crop the figure or table only")
    pix = pg.get_pixmap(dpi=a.dpi, clip=clip)
    out = pathlib.Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    stem = pathlib.Path(a.pdf).stem
    m = re.match(r"(D\d+)_", stem)
    doc_id = a.doc or (m.group(1) if m else None)
    if a.topic and doc_id:
        f = out / f"{doc_id}_p{a.page}_{a.topic}.png"
    else:
        f = out / f"{stem}_p{a.page}_crop.png"
    pix.save(f)
    print(f, f"{pix.width}x{pix.height}")
    report(lines=0, tables=0, images=1)


if __name__ == "__main__":
    main()
