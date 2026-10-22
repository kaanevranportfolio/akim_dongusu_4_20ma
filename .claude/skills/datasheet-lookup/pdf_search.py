"""Page-marked text search/read for a PDF (PyMuPDF). Output is capped at 60 lines.

  pdf_search.py <pdf> "<term>" [--context N]     search, hits with page markers; tries the
                                                 document's synonyms (VDD/VCC/supply voltage...)
                                                 before reporting "no match"
  pdf_search.py <pdf> --page N [--from L --to L] read lines of one page (1-based)
"""
import argparse
import re
import sys

import pymupdf

from _common import MAX_LINES, gate, page_tag, report

# Document-own synonyms, tried in order when the exact term has no match.
SYNONYMS = [
    ["vdd", "vcc", "supply voltage", "power supply", "v dd"],
    ["esr", "equivalent series resistance"],
    ["iq", "quiescent", "ground pin current", "supply current", "idd", "icc"],
    ["output capacitor", "cout", "output capacitance"],
    ["absolute maximum", "abs. max", "maximum ratings"],
    ["dropout", "vin - vout", "vin-vout"],
    ["rθja", "thermal resistance", "theta", "rja"],
]


def page_lines(doc, n):
    return doc[n - 1].get_text("text").splitlines()


def search(doc, t, ctx):
    out = []
    for n in range(1, len(doc) + 1):
        ls = page_lines(doc, n)
        idx = [i for i, x in enumerate(ls) if t in x.lower()]
        if not idx:
            continue
        out.append(f"=== {page_tag(doc, n)} ===")
        shown = set()
        for i in idx:
            for j in range(max(0, i - ctx), min(len(ls), i + ctx + 1)):
                if j not in shown:
                    shown.add(j)
                    out.append(f"{j + 1}: {ls[j]}")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("term", nargs="?")
    ap.add_argument("--context", type=int, default=1)
    ap.add_argument("--page", type=int)
    ap.add_argument("--from", dest="l0", type=int, default=1)
    ap.add_argument("--to", dest="l1", type=int)
    a = ap.parse_args()
    doc = pymupdf.open(a.pdf)
    gate(a.pdf, doc)
    out = []
    tried = []
    if a.page:
        if not 1 <= a.page <= len(doc):
            sys.exit(f"page out of range 1..{len(doc)}")
        ls = page_lines(doc, a.page)
        l1 = a.l1 or a.l0 + MAX_LINES - 1
        out.append(f"=== {page_tag(doc, a.page)} (lines {a.l0}-{min(l1, len(ls))} of {len(ls)}) ===")
        out += [f"{i}: {t}" for i, t in enumerate(ls, 1) if a.l0 <= i <= l1]
    elif a.term:
        terms = [a.term.lower()]
        for grp in SYNONYMS:
            if any(a.term.lower() == g for g in grp):
                terms += [g for g in grp if g != a.term.lower()]
        for t in terms:
            tried.append(t)
            out = search(doc, t, a.context)
            if out:
                if len(tried) > 1:
                    out.insert(0, f"(no match for '{terms[0]}'; synonym hit: '{t}')")
                break
    else:
        ap.error("give a term or --page")
    if not out:
        out = ["no match after trying: " + ", ".join(tried) if tried else "no match"]
    if len(out) > MAX_LINES:
        extra = len(out) - MAX_LINES
        out = out[:MAX_LINES] + [f"... {extra} more lines cut; narrow the term or use --page"]
    print("\n".join(out))


if __name__ == "__main__":
    main()
