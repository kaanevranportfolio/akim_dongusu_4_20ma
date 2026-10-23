"""check_pdf.py: turn a markdown check table into a PDF for the engineer, with a clickable Crop column.

Usage (from the project root):
    python ..\\tools\\check_pdf.py docs\\FOOTPRINTS.md            -> docs\\FOOTPRINTS.pdf
    python ..\\tools\\check_pdf.py docs\\review\\erc_findings.md --out docs\\review\\erc_findings.pdf
    python ..\\tools\\check_pdf.py <md> --crops docs\\ref\\_crops docs\\figures docs\\review\\crops

Rules (kit CLAUDE.md "Human reading" and "PDF crop link"):
- The md file stays the source; the PDF is generated output and is never edited by hand.
- Every table row that names a crop PNG anywhere in its cells (datasheet crop D<nn>_p<page>_<topic>.png, or a kicad-cli
  schematic/board export PNG) gets a "Crop" cell: crop name + PDF page number, an internal link to that page.
- Each distinct crop is placed once on its own page (after the tables), with a caption and "back to table" links
  (one per table row that cites the crop, up to 12; each jumps to that row).
- A named crop that is not found in any crops folder is printed on the page and in the script output (no failure).
- Same inputs -> same output (reportlab invariant mode: no creation date).
Needs: reportlab (pip install reportlab). Arial is used when present (Windows), else Helvetica.
"""
import argparse
import pathlib
import re
import sys

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, Frame, Image, PageBreak, PageTemplate, Paragraph, Spacer, Table,
                                TableStyle)

ROOT = pathlib.Path.cwd()  # module folder (pipeline copy: run from the module)
DEFAULT_CROPS = ["docs/ref/_crops", "../02_simulasyon/out/freeze/figures", "docs/figures", "docs/review/crops", "docs/review"]
PAGE = landscape(A4)
MARGIN = 14 * mm
FRAME_W = PAGE[0] - 2 * MARGIN
FRAME_H = PAGE[1] - 2 * MARGIN - 8 * mm
CROP_RE = re.compile(r"([A-Za-z0-9][\w.\-]*\.png)", re.I)

WIN = pathlib.Path(r"C:\Windows\Fonts")
FONT, FONTB = "Helvetica", "Helvetica-Bold"
if (WIN / "arial.ttf").exists() and (WIN / "arialbd.ttf").exists():
    pdfmetrics.registerFont(TTFont("Arial", str(WIN / "arial.ttf")))
    pdfmetrics.registerFont(TTFont("Arial-Bold", str(WIN / "arialbd.ttf")))
    pdfmetrics.registerFontFamily("Arial", normal="Arial", bold="Arial-Bold", italic="Arial", boldItalic="Arial-Bold")
    FONT, FONTB = "Arial", "Arial-Bold"

S_CELL = ParagraphStyle("cell", fontName=FONT, fontSize=9, leading=11.2)
S_HEAD = ParagraphStyle("head", fontName=FONTB, fontSize=9, leading=11.2, textColor=colors.white)
S_TITLE = ParagraphStyle("title", fontName=FONTB, fontSize=17, leading=21, spaceAfter=4)
S_H2 = ParagraphStyle("h2", fontName=FONTB, fontSize=13, leading=16, spaceBefore=8, spaceAfter=3)
S_BODY = ParagraphStyle("body", fontName=FONT, fontSize=10, leading=13)
S_CAP = ParagraphStyle("cap", fontName=FONT, fontSize=10, leading=13, textColor=colors.HexColor("#334155"))
S_MISS = ParagraphStyle("miss", fontName=FONTB, fontSize=9, leading=11, textColor=colors.HexColor("#b91c1c"))


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def md(s):
    s = esc(s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    return re.sub(r"`(.+?)`", r"<font name='Courier'>\1</font>", s)


def anchor(name):
    return "crop_" + re.sub(r"\W", "_", name)


def parse(text):
    """-> list of blocks: ("h", level, text) | ("p", text) | ("t", header, rows)."""
    blocks, lines, i = [], text.splitlines(), 0
    while i < len(lines):
        ln = lines[i]
        if ln.startswith("#"):
            lvl = len(ln) - len(ln.lstrip("#"))
            blocks.append(("h", lvl, ln.lstrip("#").strip()))
        elif ln.strip().startswith("|") and i + 1 < len(lines) and re.match(r"^\s*\|[\s:\-|]+\|\s*$", lines[i + 1]):
            cells = lambda s: [c.strip() for c in s.strip().strip("|").split("|")]
            head, rows = cells(ln), []
            i += 2
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append(cells(lines[i]))
                i += 1
            blocks.append(("t", head, rows))
            continue
        elif ln.strip():
            blocks.append(("p", ln.strip()))
        i += 1
    return blocks


def find_crop(name, dirs):
    for d in dirs:
        p = d / name
        if p.exists():
            return p
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("md")
    ap.add_argument("--out")
    ap.add_argument("--crops", nargs="*")
    a = ap.parse_args()
    src = pathlib.Path(a.md)
    src = src if src.is_absolute() else ROOT / src
    out = pathlib.Path(a.out) if a.out else src.with_suffix(".pdf")
    out = out if out.is_absolute() else ROOT / out
    dirs = [ROOT / d for d in (a.crops or DEFAULT_CROPS)]
    blocks = parse(src.read_text(encoding="utf-8"))

    # pass 1: which crops, in order of first use
    order = []
    for b in blocks:
        if b[0] == "t":
            for r in b[2]:
                for n in CROP_RE.findall(" ".join(r)):
                    if n not in order:
                        order.append(n)
    # table pages are counted by a first build; crop page numbers = table pages + 1 + index
    def build(table_pages):
        story, page_of = [], {n: table_pages + 1 + k for k, n in enumerate(order)}
        uses, tno = {}, 0  # crop name -> [(row anchor, label)] for the "back to table" links
        title = next((b[2] for b in blocks if b[0] == "h"), src.stem)
        story.append(Paragraph(esc(title), S_TITLE))
        story.append(Paragraph(f"Generated from {esc(src.name)}; edit the md, regenerate the PDF. Crops: {len(order)}.", S_CAP))
        first_h = True
        for b in blocks:
            if b[0] == "h":
                if first_h:
                    first_h = False
                    continue
                story.append(Paragraph(md(b[2]), S_H2))
            elif b[0] == "p":
                story.append(Paragraph(md(b[1]), S_BODY))
                story.append(Spacer(1, 2))
            else:
                head, rows = b[1], b[2]
                tno += 1
                data = [[Paragraph(esc(h), S_HEAD) for h in head] + [Paragraph("Crop", S_HEAD)]]
                for ri, r in enumerate(rows, 1):
                    rid = f"row_{tno}_{ri}"
                    names = []
                    for n in CROP_RE.findall(" ".join(r)):
                        if n not in names:
                            names.append(n)
                    links = []
                    for n in names:
                        if find_crop(n, dirs):
                            links.append(f'<link href="#{anchor(n)}" color="#1d4ed8"><u>{esc(n)}</u></link> (p.{page_of[n]})')
                        else:
                            links.append(f"{esc(n)} (MISSING)")
                    for n in names:
                        uses.setdefault(n, []).append((rid, f"T{tno} r{ri}: {r[0][:50]}"))
                    cells = [Paragraph(md(c), S_CELL) for c in r]
                    if cells:
                        cells[0] = Paragraph(f'<a name="{rid}"/>' + md(r[0]), S_CELL)
                    data.append(cells + [Paragraph("<br/>".join(links) or "-", S_CELL)])
                t = Table(data, repeatRows=1)
                t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
                                       ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#94a3b8")),
                                       ("VALIGN", (0, 0), (-1, -1), "TOP"),
                                       ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f1f5f9")])]))
                story.append(t)
                story.append(Spacer(1, 6))
        for k, n in enumerate(order):
            story.append(PageBreak())
            p = find_crop(n, dirs)
            use = uses.get(n, [])
            back = " &nbsp;|&nbsp; ".join(f'<link href="#{rid}" color="#1d4ed8"><u>{esc(lbl)}</u></link>'
                                         for rid, lbl in use[:12])
            if len(use) > 12:
                back += f" &nbsp;|&nbsp; (+{len(use) - 12} more rows)"
            head = [Paragraph(f'<a name="{anchor(n)}"/>{esc(n)}', S_H2),
                    Paragraph("&#8592; Tabloya dön: " + (back or "-"), S_BODY)]
            story.extend(head)
            if p is None:
                story.append(Paragraph(f"MISSING: {esc(n)} not found in {', '.join(str(d.relative_to(ROOT)) for d in dirs)}", S_MISS))
                continue
            from reportlab.lib.utils import ImageReader
            iw, ih = ImageReader(str(p)).getSize()
            cap = Paragraph(f"Source file: {esc(str(p.relative_to(ROOT)))}", S_CAP)
            # reserve the real height of heading, back links and caption (the link line wraps with many rows)
            used = sum(x.wrap(FRAME_W, FRAME_H)[1] + x.getSpaceBefore() + x.getSpaceAfter() for x in head + [cap]) + 12
            sc = min(FRAME_W / iw, (FRAME_H - used) / ih)
            story.append(Image(str(p), width=iw * sc, height=ih * sc))
            story.append(cap)
        return story

    def run(table_pages):
        doc = BaseDocTemplate(str(out), pagesize=PAGE, leftMargin=MARGIN, rightMargin=MARGIN, topMargin=MARGIN,
                              bottomMargin=MARGIN, invariant=1, title=src.stem)
        doc.addPageTemplates([PageTemplate(id="p", frames=[Frame(MARGIN, MARGIN, FRAME_W, FRAME_H + 8 * mm, id="f")])])
        doc.build(build(table_pages))
        return doc.page

    # table page count: build once with a guess, then rebuild until stable (page numbers in links depend on it)
    guess = 1
    for _ in range(4):
        total = run(guess)
        tp = total - len(order)
        if tp == guess:
            break
        guess = tp
    missing = [n for n in order if find_crop(n, dirs) is None]
    print(f"OK {out.relative_to(ROOT) if out.is_relative_to(ROOT) else out}: {total} pages, {len(order)} crops, {len(missing)} missing")
    for n in missing:
        print("MISSING crop:", n)
    return 0


if __name__ == "__main__":
    sys.exit(main())
