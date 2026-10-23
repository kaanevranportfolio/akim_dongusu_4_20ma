"""Hand layout of opa2192_buffer_step.cir (acceptance test for 00_coordination/T028: recreate the legacy figure).
Coordinates follow the legacy figure (op-amp at 520,300; supply rail y=100; feedback below); the wires are Manhattan."""
TITLE = "opa2192_buffer_step: circuit (opa2192\\opa2192_buffer_step.cir)"
WIDTH, HEIGHT = 1300, 560


def layout(sh, nl):
    sh.opamp("XU1", 520, 300, "OPA2192 model OPAx192 (one half)")
    sh.vsource("VCC", 760, 190, note="supply; V- = 0 V")
    sh.ground(("VCC", 1))
    sh.wire(("VCC", 0), sh.T("XU1", "VCC"), via=[(760, 100), (565, 100)])
    sh.dot(760, 100)
    sh.ground(sh.T("XU1", "VEE"))
    sh.vsource("VIN", 120, 260, note="input step")
    sh.wire(("VIN", 0), sh.T("XU1", "INP"), via=[(190, 220), (190, 272)])
    sh.ground(("VIN", 1))
    sh.resistor("RL", 860, 420, vertical=True, note="load")
    sh.wire(sh.T("XU1", "OUT"), ("RL", 0), via=[(860, 300)])
    sh.ground(("RL", 1))
    sh.wire(sh.T("XU1", "INN"), sh.T("XU1", "OUT"), via=[(470, 328), (470, 470), (700, 470), (700, 300)])
    sh.probe_node("V(OUT)", sh.T("XU1", "OUT"), 14, -24)
    sh.probe_node("V(INP)", sh.T("XU1", "INP"), -110, 16)
    sh.notes([f"Analysis: {nl.tran}. Unity-gain buffer (IN- tied to OUT), slew rate from the 10-90 % slope of the 6 V output step."])
