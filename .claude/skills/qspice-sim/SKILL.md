---
name: qspice-sim
description: Write, run and evaluate QSPICE testbenches through run_sim.ps1. Triggers: simulation, QSPICE, testbench, .cir, .tran, run_sim, model, transient, loop gain.
---
# qspice-sim (consolidated from the nrf24 and tps54360 projects; pipeline copy)

## Steps
1. Model: only vendor models from <module>\sim\models, byte-exact, registered in the module FACTS.md
   with source URL and SHA-256 (docs\INTERFACES.md section 3). Before trusting any metric, state what the model represents (switching or
   averaged; losses, current limit, soft-start, thermal) and what it cannot show.
2. Fixture: read the model before designing a test fixture; write the predicted result
   before the run.
3. Testbench: every .tran has a .save list; above every .tran, the max-step derivation
   (at most 1/10 of the fastest edge, naming that edge). Steady-state starts prove
   periodicity before measuring. Runs estimated over 15 min are marked LONG.
4. Run only through the shared runner tools\run_sim.ps1 (one copy for the pipeline,
   never copied into a module). -SimDir is relative to the pipeline root:
   powershell -NoProfile -ExecutionPolicy Bypass -File <pipeline>\tools\run_sim.ps1
     -SimDir <module>\sim -Analyze <analyzer scripts, report script last>
   Raw data (step 7): add -CleanRaw and put <pipeline>\tools\qraw_export.py among the -Analyze scripts.
   Add -Long only for testbenches marked LONG. Prerequisites inside <module>\sim\:
   canary_rc.cir (copy of <pipeline>\tools\canary\canary_rc.cir; it runs
   first), models\ with the vendor files, the testbench .cir files and their analyze_*.py.
   If <pipeline>\tools\run_sim.ps1 is missing, stop and ask. Close every report PDF first.
5. Results: map .step results by their step tag, never by order. Label simulation results
   [R] (or [C] when the engineer reproduced the run).
6. Circuit figure (every testbench, before the result plot): docs\sim\<testbench>\circuit.svg/.png
   showing what is simulated and how it is connected: all components with values, sources and
   waveforms, load, measurement nodes, model node order next to the datasheet-printed pin names,
   assumptions marked [A]. Drawn by docs\sim\circuits.py, which parses the .cir and
   asserts every netlist component and node is drawn and nothing else; never from memory.
   Procedure: the figures skill. Location and rules: root CLAUDE.md "Figures". Result plot: docs\sim\<testbench>\result.svg/.png, script result.py in the same folder. A result without its circuit figure is not reported to the engineer.
7. Raw data: .save only the signals needed. Run with -CleanRaw and an -Analyze that includes qraw_export.py,
   so the small result files (sim\out\*.csv, .meas) are written first and the raw .qraw is removed by the
   tool's built-in cleanup afterwards (the one allowed deletion, never by hand). Figures and reports read the
   small result files, not the raw. Incident: raw files accumulated in sim\ (a 1.6 MB canary file for a
   trivial RC test and 24 files from diagnostics).

## Exit codes (run_sim.ps1)
0 success | 1 simulation, analyzer or report error: read the log | 3 missing model or a
symbol library used as a model: stop, the engineer supplies the vendor file | 4 .tran
without .save | 5 numerical canary failed: stop and report, never relax tolerances.

## Rules, each with its incident
- Never write, fit, edit, wrap or guess a model; a missing model stops the work. Incident:
  the LM1117 model cannot show ESR instability; only the datasheet decided C2.
- Limits come from the datasheet with margin, never from model behaviour. Incident:
  TPS54360 model minimum on-time 118 ns vs 135 ns typical in the datasheet.
- Read the model before designing a fixture. Incident: FB held at 0 V triggered frequency
  foldback; a resistive load forced 100 % duty instead of clocked pulses.
- Map results by step tag. Incident: AS BUILT and COMPARISON minima were swapped in prose.
- Always a .save list. Incident: an unrestricted run wrote a 1.5 GB raw file.
- A 0-byte raw file during a long run is normal; wait before calling it hung. Incident:
  the 1 ns pulse-load run looked stuck.
- Close report PDFs before a run. Incident: PermissionError, a .partial.pdf left behind.
- Every testbench gets its circuit figure. Incident: the first plots were delivered without any schematic and the engineer could not see what was simulated or how it was wired.

## Verifies
The canary passed, the exit code, the model's capability statement, and every reported
number traced to its .meas line or analyzer output.
