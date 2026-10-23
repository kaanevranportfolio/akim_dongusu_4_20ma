"""Hand layout of the 4-20 mA-like fixture loop (loop_tb.cir; 00_coordination/T028). Loop supply and load on top, op-amp
driving the pass transistor, sense resistor to ground, feedback line under the circuit."""
TITLE = "4-20 mA-like loop (fixture): circuit (loop_tb.cir)"
WIDTH, HEIGHT = 1300, 700


def layout(sh, nl):
    sh.vsource("V_LOOP", 120, 260, note="loop supply")
    sh.ground(("V_LOOP", 1))
    sh.vsource("VREF", 240, 420, note="reference")
    sh.ground(("VREF", 1))
    sh.opamp("XU1", 440, 380, "fixture op-amp")
    sh.ground(sh.T("XU1", "VEE"))
    sh.wire(("VREF", 0), sh.T("XU1", "INP"), via=[(240, 352)])
    sh.resistor("RB", 760, 380, note="base resistor")
    sh.wire(sh.T("XU1", "OUT"), ("RB", 0))
    sh.bjt("Q1", 1000, 420, "pass transistor")
    sh.wire(("RB", 1), ("Q1", 1), via=[(960, 380)])
    sh.resistor("R_LOAD", 1030, 200, vertical=True, note="loop load")
    sh.wire(("R_LOAD", 1), ("Q1", 0))
    sh.wire(("V_LOOP", 0), ("R_LOAD", 0), via=[(120, 90), (1030, 90)])
    sh.wire(("V_LOOP", 0), sh.T("XU1", "VCC"), via=[(120, 90), (485, 90)])
    sh.resistor("R_SENSE", 1030, 560, vertical=True, note="sense resistor")
    sh.wire(("Q1", 2), ("R_SENSE", 0))
    sh.ground(("R_SENSE", 1))
    sh.capacitor("C_FILT", 900, 560, vertical=True, note="filter")
    sh.ground(("C_FILT", 1))
    sh.wire(("C_FILT", 0), ("R_SENSE", 0), via=[(900, 495), (1030, 495)])
    sh.wire(sh.T("XU1", "INN"), ("R_SENSE", 0), via=[(380, 408), (380, 495), (1030, 495)])
    sh.probe_node("V(SENSE_N)", ("R_SENSE", 0), 60, -40)
    sh.probe_current("I(R_SENSE)", "R_SENSE", 1090, 610)
    sh.notes([f"Analysis: {nl.tran}; the feedback line from the sense node returns to IN- of the op-amp."])
