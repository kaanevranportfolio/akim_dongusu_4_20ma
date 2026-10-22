# akim_dongusu_4_20ma - pipeline working method (root file)

Scope: the method for every module below. It supersedes the legacy roots C:\eda\CLAUDE.md and C:\KiCAD_Projects\CLAUDE.md.
This folder lives outside both (C:\pipelines\...), so Claude Code does not load them here; the legacy projects keep their own files.
docs\RULE_LEDGER.md traces every rule to its source and incident. docs\INTERFACES.md defines the files that cross modules.
Precedence: the CLAUDE.md nearest to the working folder wins; a module file wins over this file. Two things no module file
can relax: the Safety section and the hard blocks in .claude\settings.json. Archived or older documents never override this method.

## Language
- Answer in Turkish. File contents in Turkish, except rule blocks, commands, file names and the "## İstek" part of tickets (English).
- Terminology: never translate datasheet, standard or tool terms (parameter and symbol names, pin names, table and column headings,
  section names such as Absolute Maximum Ratings, Recommended Operating Conditions, Electrical Characteristics, Pin Functions,
  DESCRIPTION, and KiCad terms such as ERC, DRC, footprint, symbol, net class). Write them in English exactly as printed, with
  page/figure/table number; Turkish only in the surrounding sentence, a short gloss in parentheses never replaces the term.
- Datasheet checks: every value handed to the engineer for checking comes with the D<nn> document number, the page (e.g. D21 p.9)
  and a crop PNG named D<nn>_p<page>_<topic>.png showing the table header row (MIN / TYP / MAX / UNIT) and units (for a footprint:
  the full land pattern with dimensions). The engineer looks at the PNG first and opens the PDF page only when unsure.
  A value from text extraction is [R]; it becomes [V] after the engineer compares it with the crop.
- Human reading: every multi-column table or value list the engineer must check (pin map, verified values, parts list, offset budget,
  footprints, nets, ERC/DRC findings, stress table) stays as markdown and is also delivered as a script-generated PDF (landscape A4,
  large text, check-pdf skill). The PDF is generated output, never edited by hand: change the markdown and regenerate.
  Every row has a "Crop" column (crop name + its PDF page, internal link). A row that needs checking never has an empty Crop cell;
  if all rows are checked from one crop, the crop stays directly under the table. A planner starting a new check table writes the
  PDF output into the ticket.

## Principles
- No persona. Quality comes from the right documents, efficient extraction, short incident-backed rules, independent verification.
- Exact part and exact variant only: a different suffix, maker, package or footprint is a different part. Values come from that
  part's own document.
- Never invent. Not found means "not found"; unsure means [A].
- Two values that contradict each other are not used for design until reconciled.
- Critical values (each module names them) are not final in FACTS.md until the engineer has checked them against the document page.
  A part number or value suggested by an AI (planner included) is a candidate until it is seen in the part's own document.
- Text cut off in a screenshot is not "read": the missing part is marked "inference".
- Distributor data shortlists; the datasheet decides.

## Labels (on every fact)
[V] read in a document (document, page) | [M] measured (with numbers) | [C] calculated, including simulation and tool runs the
engineer reproduced | [R] agent report, not reproduced by the engineer | [U] engineer report without numbers | [W] web | [A] assumption.
Single source: no other file restates this list. Do not use "(V)" for assumptions (SPEC v0.1 did; use [A]).
BOM status words: SEÇİLDİ (engineer decision recorded) | VARSAYILAN (default, [A]) | AÇIK (undecided) | DÜŞTÜ (dropped, not placed).
Numbering: documents are D<nn>; decisions are K<nn> (per module). The two namespaces never mix. Tickets: Tnnn per docs\tasks
folder; across modules write <module>/Tnnn (e.g. 01_secim/T003).

## Pipeline (stages, passes, gates)
| Stage | Module | Output (see docs\INTERFACES.md) | Gate |
|---|---|---|---|
| 1. Core part | 01_secim pass A | core IC candidates, chosen core part, vendor model record | engineer picks the core part |
| 2. Theory | 02_simulasyon pass 1 | stress table (V, I, P per reference, per corner) | engineer reads the table |
| 3. Other parts | 01_secim pass B | parts_map, BOM draft with model records | engineer picks parts (SEÇİLDİ) |
| 4. Proof | 02_simulasyon pass 2 | verification report (SPEC acceptance K1..), freeze package | engineer approves; engineer tags the freeze |
| 5. Board | 03_kicad | schematic, layout, DRC, fab outputs | engineer go before fab outputs |
A defect found later flows back as a ticket to the owning module (UPSTREAM.md in the receiving module); nothing is fixed silently.
00_coordination owns SPEC.md, the document library, git tickets and overall status.

## Documents
- Vendor PDFs live in <pipeline>\docs\ref (gitignored), one library for all modules, owned by 00_coordination.
  Naming: D<nn>_<original name>.pdf (nn two digits, arrival order, never reused); docs\ref\INDEX.md maps D<nn> to part, document
  number, covered MPNs. Citations: "D03 p.38" (PDF page). Modules read the library; new documents arrive through a coordinator ticket.
- Variant gate: before any lookup, confirm the document's part, variant and revision (datasheet-lookup skill, doc_registry.json).
- Lookup order: the module's FACTS.md, then search, at most 60 lines of document text per call; one cropped page as an image only
  for figures. Netlist or SVG instead of screenshots. The datasheet-lookup skill implements this section.
- SPICE models: only vendor models, byte-exact, in <module>\sim\models, each recorded in FACTS.md with source URL and SHA-256.
  A missing model stops the work (qspice-sim skill).

## Figures (for the engineer)
- An annotated figure is produced before any hands-on step (wiring, jumpers, probe points), for every reported simulation result,
  and when a pin or jumper assignment changes. Figures come from real data (KiCad netlist or kicad-cli export, testbench and data,
  FACTS.md), never drawn from memory or edited by hand.
- Labels are exactly as printed in the source document (no abbreviation or merging); an extra function goes in a separate note.
- Format: SVG is the source (committed); PNG is rendered from it (gitignored). Footer: source, commit, data label.
- Location: the module's own docs\figures\<stage>-<topic>.svg/.png. Simulations: docs\sim\<testbench>\ (circuit.svg/.png,
  result.svg/.png, result.py), shared generator docs\sim\circuits.py, index docs\sim\INDEX.md (testbench -> circuit -> result ->
  model SHA256 -> ticket).
- Simulation figure rules: (1) every simulation is reported with two figures: the circuit (what is simulated and how it is wired:
  source values, load, measurement nodes, model node order, assumptions [A]), generated from the testbench netlist by a script that
  checks every netlist element is drawn, and the result plot; without the circuit a result counts as not shown. (2) pin names as
  printed in the document; the model subcircuit node order is shown too. (3) measurement nodes and every curve labelled with
  those names. (4) axes with units; conditions (Vgs, Vds, temperature, sources) in the title. (5) footer: testbench file, model
  file (SHA256), result label [C]. (6) a result is not used as [V] or as a decision before the engineer has read and approved it.
- Procedure: the figures skill.

## Layout and ownership
- One pipeline = one git repo = this folder. Subfolders: 00_coordination, 01_secim, 02_simulasyon, 03_kicad; shared: docs\, tools\, .claude\.
- Each module folder has CLAUDE.md (under 150 lines, module-specific), FACTS.md, HANDOFF.md, DOCS_NEEDED.md, docs\ (DECISIONS.md,
  lessons.md, DEVLOG.md, tasks\, figures\), and .claude\settings.json. A file or folder is added only when a concrete use is named.
- A module writes only inside its own folder and reads the others read-only. Pipeline-level files (this file, docs\, tools\, .claude\)
  belong to 00_coordination: changes go through its tickets.
- FACTS.md: pin and net assignments, rails, exact part numbers, settings and requirements, each with label and source.
- HANDOFF.md: current state, open items (each with how it will be settled), open decisions (K<nn> links), paths ready to commit,
  the first task of the next session. No commit state (git log is the source).
- docs\DECISIONS.md: append-only (K<nn>, decision, alternatives, why, evidence, engineer check); the design report is compiled from it.
- DOCS_NEEDED.md: documents needed for the exact variants, marking which exist. docs\lessons.md: one labelled lesson per line,
  each with its incident. docs\DEVLOG.md: append-only session log.

## Session
- The module chat (claude.ai) is long-lived and only plans and checks; technical work runs in VS Code (Claude Code), one session per
  task, several per module folder are fine. A session starts from a ticket or first prompt written by the module chat:
  /start, status /report, end /closeout (HANDOFF.md, DEVLOG, list of commit-ready paths; no commit).
- Planner (claude.ai) reads and writes only md files and tickets; anything that needs a PDF, a tool run, a script or a figure
  goes to VS Code as a ticket (vscode-ticket skill). One writer at a time: the planner asks whether VS Code is idle.
- State lives only in files; whatever must survive the session is written before it ends.

## Rules
- A rule is added only after a repeated mistake and carries its incident (docs\RULE_LEDGER.md, module docs\lessons.md).
- Hard blocks go into .claude\settings.json; deny patterns match strings, not intent.
- Occasional multi-step procedures become skills; a skill holds the procedure, this file holds the rule (no restating).

## Safety
- Never read or write ~/.claude. Never read .env files, tokens or certificates (component selector credentials).
- Never tag, commit --amend, reset --hard, checkout . or clean. Never delete files; cleanups built into tools are the only exception.
- Module sessions never commit or push. Only a session started in the pipeline root commits and pushes, only on a coordinator
  ticket: git status shown first, explicit paths, exact message, and the engineer's separate go for the commit and for the push.
- Claude never edits .kicad_sch, .kicad_pcb, .kicad_sym or .kicad_mod files (settings.json denies it); it reads them through
  kicad-cli exports. A script that writes KiCad files is allowed only when a ticket names it, writes to a new file and the engineer
  reviews the result.
- Sessions run in a normal window, never as administrator.
