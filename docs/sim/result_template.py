"""Result script template (00_coordination/T029). Copy to docs\sim\<testbench>\result.py and edit CONFIG; keep the rest.

  python docs\sim\<tb>\result.py --cir <module>\sim\<tb>.cir --csv <module>\sim\out\<tb>.csv --out docs\sim\<tb> [--date YYYY-MM-DD]

Writes result.svg + result.png, prints every measurement ("[M] ...") and PASS/FAIL per limit, exits 1 on FAIL and 2 when the
input is unusable (also when a .save name is neither plotted nor listed in not_plotted with a reason).
Rules: signal names are the .save names of the testbench (they must read exactly like the red probe boxes of circuit.png);
a limit is never invented: every limit carries spec="K<nn>" (SPEC.md acceptance criterion) or spec="[A]" (assumption);
measurement windows and levels are in base units (seconds, Hz, volts, amperes). The values below are PLACEHOLDERS of the
plotkit fixture (a unity-gain buffer step), not design numbers.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import plotkit  # noqa: E402

CONFIG = dict(
    title="PLACEHOLDER: testbench title, supply, load, stimulus",
    source="PLACEHOLDER: where pin names and limits come from (SPEC K<nn>, D<nn> p.<n>)",
    xkind="time",                 # "time" (SI unit chosen from the span), "freq" (log axis) or "x" (abscissa name of the CSV)
    steps=[1],                    # .step runs to draw (1-based); measurements use the first unless a measure sets "step"
    panels=[
        dict(
            ylabel="voltage (V)",
            traces=[dict(name="V(INP)"),        # legend entry = the .save name; colour by trace order (blue, red, amber, green,
                    dict(name="V(OUT)")],       # purple, black), line style solid then dashed (alternating); override with color= ls= marker=
            measures=[
                dict(kind="crossing", signal="V(OUT)", level=5.0, rising=True, after=2e-6, label="t_cross_5V"),
                dict(kind="steady", signal="V(OUT)", window=(8e-6, 11e-6), label="v_final"),
                dict(kind="overshoot", signal="V(OUT)", window=(2e-6, 12e-6), ref_window=(10e-6, 12e-6), label="overshoot"),
                dict(kind="minmax", signal="V(OUT)", which="max", label="v_max"),
            ],
            limits=[
                dict(kind="max", signal="V(OUT)", value=8.2, unit="V", spec="[A]"),                       # replace by K<nn>
                dict(kind="min", signal="V(OUT)", value=7.9, unit="V", spec="[A]", window=(8e-6, 11e-6)),
            ],
        ),
    ],
    not_plotted={"I(RL)": "load current is listed in the report table, not plotted"},   # every other .save name must be plotted
)

if __name__ == "__main__":
    sys.exit(plotkit.run(CONFIG))
