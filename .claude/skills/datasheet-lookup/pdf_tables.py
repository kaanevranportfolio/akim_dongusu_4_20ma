"""Parameter tables of one PDF page as rows with their column headers (PyMuPDF find_tables).

  pdf_tables.py <pdf> <page> [--table K] [--grep TEXT]

Lists the tables found on the page (index, size, first header cells). With --table K (or when the
page has exactly one real table) prints each row as `header=value; ...` (empty cells skipped), so
min/typ/max/unit/conditions stay attached to the value. --grep keeps only rows containing TEXT.
Output is capped at 60 lines. A row whose unit or column is in doubt is checked against the page
image (pdf_crop.py). Notes letters (a, b, ...) point to the footnotes under the table (read them
with pdf_search.py --page).
"""
import argparse
import re
import sys

import pymupdf

from _common import MAX_LINES, gate, page_tag, report


def clean(c):
    return re.sub(r"\s+", " ", (c or "").replace("\n", " ")).strip()


def split_merged(head, cells):
    """Some tables put min/typ/max in one cell ('1.238 1.25 1.262'). Never guess silently:
    split three numbers (min, typ, max), flag two as ambiguous (typ may be missing)."""
    hl = [h.upper() for h in head]
    try:
        i_min = next(i for i, h in enumerate(hl) if h.startswith("MIN"))
        i_typ = next(i for i, h in enumerate(hl) if h.startswith("TYP"))
        i_max = next(i for i, h in enumerate(hl) if h.startswith("MAX"))
    except StopIteration:
        return cells, ""
    toks = cells[i_min].split()
    if len(toks) == 1 and not cells[i_typ] and not cells[i_max] and any(c.isdigit() for c in toks[0]):
        cells = list(cells)
        return cells, "  [single value under MIN only: column may be wrong if the table merges cells; verify in image]"
    if len(toks) >= 2 and not cells[i_typ] and not cells[i_max]:
        cells = list(cells)
        if len(toks) == 3:
            cells[i_min], cells[i_typ], cells[i_max] = toks
            return cells, "  [MERGED CELL split into min/typ/max: verify in image]"
        return cells, f"  [AMBIGUOUS: '{cells[i_min]}' is one cell holding {len(toks)} values; min/typ/max unknown: verify in image]"
    return cells, ""


def around(pg, bb):
    """Text just above the table (table-wide conditions) and footnotes below it (a. b. ...)."""
    above, notes = [], []
    for b in pg.get_text("blocks"):
        x0, y0, x1, y1, txt = b[:5]
        t = clean(txt)
        if not t:
            continue
        if y1 <= bb[1] + 1 and y0 >= bb[1] - 70 and "Page " not in t and "Revision" not in t:
            above.append(t)
        elif y0 >= bb[3] - 1 and y0 <= bb[3] + 90 and re.match(r"^[a-z]\. ", t):
            notes.append(t)
    out = [f"above table (conditions?): {t}" for t in above[-2:]]
    out += [f"footnote: {t}" for t in notes]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("page", type=int)
    ap.add_argument("--table", type=int)
    ap.add_argument("--grep")
    a = ap.parse_args()
    doc = pymupdf.open(a.pdf)
    gate(a.pdf, doc)
    if not 1 <= a.page <= len(doc):
        sys.exit(f"page out of range 1..{len(doc)}")
    tabs = doc[a.page - 1].find_tables().tables
    out = [f"=== {page_tag(doc, a.page)}: {len(tabs)} table(s) found ==="]
    real = [i for i, t in enumerate(tabs) if t.row_count >= 3 and t.col_count >= 3]
    if a.table is None and len(real) == 1:
        a.table = real[0]
    if a.table is None:
        for i, t in enumerate(tabs):
            rows = t.extract()
            out.append(f"table {i}: {t.row_count} rows x {t.col_count} cols; "
                       f"first row: {[clean(c) for c in rows[0]] if rows else []}")
        out.append("choose one with --table K")
        used = 0
    else:
        if not 0 <= a.table < len(tabs):
            sys.exit(f"--table out of range 0..{len(tabs) - 1}")
        rows = tabs[a.table].extract()
        head = [clean(c) for c in rows[0]]
        out.append(f"table {a.table} headers: {head}")
        section = ""
        for r in rows[1:]:
            cells = [clean(c) for c in r]
            filled = [c for c in cells if c]
            if len(filled) == 1:                    # a section row such as "Transmit"
                section = filled[0]
                continue
            if not filled:
                continue
            cells, flag = split_merged(head, cells)
            line = "; ".join(f"{h or f'col{j}'}={c}" for j, (h, c) in enumerate(zip(head, cells)) if c)
            line += flag
            if section:
                line = f"[{section}] " + line
            if a.grep and a.grep.lower() not in line.lower():
                continue
            out.append(line)
        used = 1
        out += around(doc[a.page - 1], tabs[a.table].bbox)
    if len(out) > MAX_LINES:
        extra = len(out) - MAX_LINES
        out = out[:MAX_LINES] + [f"... {extra} more rows cut; use --grep"]
    print("\n".join(out))
    report(lines=len(out) - 1, tables=used, images=0)


if __name__ == "__main__":
    main()
