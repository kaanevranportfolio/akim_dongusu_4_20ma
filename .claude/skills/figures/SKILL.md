---
name: figures
description: Produce annotated figures for the engineer (wiring, jumpers, probe points, pinouts, simulation plots) as SVG with a PNG view. Triggers: figure, şekil, diagram, wiring, jumper, bağlantı, pinout, probe, plot, grafik.
---
# figures

## Steps
1. Source: name the real data the figure comes from: KiCad netlist or schematic
   (kicad-cli export); for simulation, the testbench .cir (components, nodes, pins,
   sources, loads) and the raw data or analyzer output; or FACTS.md rows. If no source
   exists, stop: connections are never drawn from memory.
2. Draw the content originally, as SVG, by a script kept in the project (so it can be
   regenerated): pin numbers and names, net names, jumper positions, probe points with
   their expected value and label. Simulation: the testbench's node map from the .cir;
   plots from the raw data (e.g. matplotlib to SVG) with limits and measured values
   marked on the axes.
3. Footer on every figure: source file, commit (short hash), date, data label
   ([V]/[C]/[R]/[A]).
4. Save as <module>\docs\figures\<stage>-<topic>.svg; render the PNG next to it
   (PyMuPDF, no script file needed):
   python -c "import pymupdf,sys; p=sys.argv[1]; pymupdf.open(p)[0].get_pixmap(dpi=150).save(p[:-4]+'.png')" <file.svg>
5. Report both paths and what the figure shows, in one line each.

## Rules
- PyMuPDF only renders the finished SVG to PNG here. A page cropped from a datasheet
  (datasheet-lookup) is input for the agent, never a figure for the engineer.
- Never edit a figure by hand; change the source or the script and regenerate.
- If a figure and FACTS.md disagree, FACTS.md wins; regenerate the figure.
- Non-simulation figures live only in the module's own docs\figures\; never in a shared folder. Simulation figures: location, the two figures per simulation and the six rules are in the root CLAUDE.md "Figures" (single source). docs\figures holds only non-simulation figures.
- Schematic or board views and pin maps come from kicad-cli exports, never from memory.

## Verifies
Every drawn connection exists in the source; every value shown carries its label; the
PNG was rendered from the current SVG.
