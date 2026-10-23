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
- Simulation circuit schematic (rule 1), method = symbols + a layout script written by the module agent, finish() as the safety net:
  1. `python docs\sim\circuits.py <tb>.cir --draft docs\sim\<tb>\circuit_layout.py` writes a first draft (every element placed, net-name flags, ground symbols, red probe boxes). The draft only passes the checks; it is never the final figure.
  2. Edit that file by hand: `layout(sh, nl)` calls the classic symbols of docs\sim\symbols.py at absolute coordinates (`resistor capacitor inductor diode` with rot 0/90/180/270, `vsource isource opamp bjt mosfet subckt`), Manhattan wires (`sh.wire(a, b, via=[...])`, `sh.route(a, b, "hv"|"vh"|"zx"|"zy")`), `sh.ground`, `sh.byname` for long connections, `sh.T("XU1", "OUT")` for op-amp terminals by role; junction dots are automatic. Terminals are (element, index) in netlist order; optional `TITLE`, `WIDTH`, `HEIGHT`, `sh.notes([...])`.
  3. Every `.save` signal gets a RED boxed label named exactly like the trace in the result plot: `probe_node("V(net)", t, dx, dy)`, `probe_diff("V(a,b)", ta, tb)`, `probe_current("I(R1)", "R1", x, y)`, `probe_pin("I(X1:pin)", t)` (pin = .subckt node name or number).
  4. Run: `python docs\sim\circuits.py <tb>.cir --layout docs\sim\<tb>\circuit_layout.py --out docs\sim\<tb> [--pin-map <module>\FACTS.md] [--part XU1=MPN] [--date YYYY-MM-DD]` -> `circuit.svg` + `.png`. Exit 0 = verified; 1 = violations printed, nothing written (element not drawn or drawn twice, item not in the netlist, net with < 2 terminals that is not a probe or ground, terminals of a net not connected, `.save` signal without a probe box or not drawable); 2 = netlist, layout script or option unusable (an unsupported element letter is an error, never skipped).
  5. Without `--layout` (or with a grid-hints .json) the old automatic layout runs and the footer says "automatic DRAFT, not a final figure". `--pin-map` adds the DS/SP/TB panel for every subcircuit instance (pin names in the op-amp labels come from it); without it TB boxes only and footer "pin map: none". Footer: testbench file, SHA-256 of the .cir and of every `.include`/`.lib` model file (NOT FOUND is marked and warned), date, pin map, layout. Look at the PNG before reporting it; report its path.
- Simulation result plot: copy `docs\simesult_template.py` to `docs\sim\<tb>esult.py`, edit only `CONFIG` (title, source, panels with traces, measures, limits, `not_plotted`), run `python docs\sim\<tb>esult.py --cir <module>\sim\<tb>.cir --csv <module>\sim\out\<tb>.csv --out docs\sim\<tb> [--date YYYY-MM-DD]` (CSV from `tools\qraw_export.py`). Output `result.svg` + `.png`, deterministic. Signal names are the `.save` names and appear in a LEGEND with exactly that spelling (no extra words; the red boxes exist only in circuit.png, so circuit probe box = result legend entry, matched by name; no red boxes in result plots). Traces take the palette in trace order, blue `#0072B2`, red `#C62828`, amber `#A66F00`, green `#009E73`, purple `#6A3D9A`, black (each >= 3:1 on white), and a line style that alternates solid, dashed, solid, dashed (same width; the dashed trace is drawn on top, so two coincident traces such as input = output both stay visible; no other styles, no default markers; override per trace with `color`, `ls`, `marker`); notes box, legend and `[M]` labels sit on free spots automatically. The PNG is written by matplotlib (the SVG renderer of PyMuPDF draws no dashes; in the circuit figures every dashed shape, i.e. the SP box edge, the "to net" stubs and block frames, is therefore built from separate short segments, identical in SVG and PNG); measurements (`crossing`, `steady`, `overshoot`, `minmax`) are printed as `[M] label: value (formula or window)`; a limit is a dashed line tagged `K<nn>` or `[A]` and judged PASS/FAIL (a limit without such a tag is refused). Exit 0 = ok, 1 = a limit FAILED (plot still written), 2 = unusable input or failed self-check (every `.save` name must be plotted or listed in `not_plotted` with a reason). Footer: SHA-256 of the .cir and of every model file, `.tran/.ac/.step` lines, run date. Index of the testbenches: `docs\sim\INDEX_TEMPLATE.md`. Look at the PNG before reporting it; report its path.
- Simulation circuit figures: three names per terminal, each in its own box with a text prefix and shape (colour is only a help) and a legend at the side: `DS <pin no> <pin name> D<nn> p.<n>` (datasheet, solid rectangle), `SP <.SUBCKT position> <node>` (SPICE model node, dashed rounded), `TB <net>` (testbench net, hexagon). Source: the module FACTS.md table "Pin eşleme" (format: docs\INTERFACES.md section 10); datasheet cells carry [R] until the engineer's crop check, SPICE cells come from the .SUBCKT line. Unknown cell = "?" (hatched box, footer "UNMAPPED TERMINALS: n"), never guessed. A testbench terminal absent from the table prints a WARNING. Command (docs\sim\pin_map.py): `python docs\sim\pin_map.py --cir <testbench.cir> --instance XU1 [..] --part <MPN> [..] --pin-map <module>\FACTS.md --out <fig>.svg`; without `--pin-map` only TB boxes, footer "pin map: none". Position mismatch between pin order and .SUBCKT order is not an error: it is what the figure shows.

## Verifies
Every drawn connection exists in the source; every value shown carries its label; the
PNG was rendered from the current SVG.
