"""Shared helpers for the datasheet-lookup scripts: variant gate, printed page, report line."""
import json
import os
import pathlib
import re
import sys

import pymupdf

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

SKILL = pathlib.Path(__file__).resolve().parent
FACTS = pathlib.Path(os.environ["FACTS_MD"]) if os.environ.get("FACTS_MD") else pathlib.Path.cwd() / "FACTS.md"  # module FACTS.md (cwd); pipeline copy of the skill
MAX_LINES = 60


def fail(msg):
    print(msg, file=sys.stderr)
    sys.exit(2)


def gate(pdf_path, doc):
    """Stop (exit 2) unless the document matches its registry entry and FACTS.md.

    Prints one GATE line. Documents not in the registry are refused."""
    reg = json.loads((SKILL / "doc_registry.json").read_text(encoding="utf-8"))
    name = pathlib.Path(pdf_path).name
    e = reg.get(name)
    if e is None:
        fail(f"GATE FAIL: {name} is not in doc_registry.json. Identify part, variant and "
                 "revision from the document, compare with FACTS.md, then add it. Lookup stopped.")
    facts = FACTS.read_text(encoding="utf-8") if FACTS.exists() else ""
    problems = []
    if e["part"] not in facts:
        problems.append(f"part '{e['part']}' not found in FACTS.md")
    texts = [p.get_text() for p in doc]
    whole = "\n".join(texts)
    head = "\n".join(texts[:3])
    for s in e.get("require", []):
        if s not in whole:
            problems.append(f"required text '{s}' not in document")
    for s in e.get("forbid", []):
        if s in head:
            problems.append(f"forbidden text '{s}' on pages 1-3 (different part?)")
    rev = [s for s in e.get("revision", []) if s in "\n".join(texts[:2])]
    if e.get("revision") and not rev:
        problems.append(f"revision {e['revision']} not on pages 1-2")
    if problems:
        fail("GATE FAIL: " + "; ".join(problems) + ". Lookup stopped; report to the engineer.")
    print(f"GATE OK: {name} = {e['part']}; revision {', '.join(rev) or 'not required'}; "
          f"{len(doc)} PDF pages")


def printed_page(doc, n):
    """Printed page label of PDF page n, or None when it cannot be determined."""
    t = doc[n - 1].get_text()
    m = re.search(r"Page (\d+) of \d+", t)
    if m:
        return m.group(1)
    lines = [x.strip() for x in t.splitlines() if x.strip()]
    for x in reversed(lines[-6:]):
        if re.fullmatch(r"\d{1,3}", x):
            return x
    return None


def page_tag(doc, n):
    p = printed_page(doc, n)
    if p is None:
        return f"PDF p.{n} (printed page: not determinable)"
    return f"PDF p.{n}" + ("" if p == str(n) else f" (printed p.{p})") + ("" if p != str(n) else " (printed same)")


def report(lines=0, tables=0, images=0):
    print(f"REPORT: lines_read={lines} tables_used={tables} images_used={images}")
