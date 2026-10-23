# FACTS (test fixture for circuits.py, not a real module file; pin names and numbers are fixture values, nothing here is [V])

## Pin eşleme

| Part | Doc (D<nn>) | Page | Pkg pin no | Datasheet pin name | Model file | .SUBCKT node position | SPICE node name | Label | Note |
|---|---|---|---|---|---|---|---|---|---|
| OPAx192 | D93 | 5 | 3 | +IN A | models\OPAx192.LIB | 1 | IN+ | [R] | fixture |
| OPAx192 | D93 | 5 | 2 | -IN A | models\OPAx192.LIB | 2 | IN- | [R] | fixture |
| OPAx192 | D93 | 5 | 8 | V+ | models\OPAx192.LIB | 3 | VCC | [R] | fixture |
| OPAx192 | D93 | 5 | 4 | V- | models\OPAx192.LIB | 4 | VEE | [R] | fixture |
| OPAx192 | D93 | 5 | 1 | OUT A | models\OPAx192.LIB | 5 | OUT | [R] | fixture |
