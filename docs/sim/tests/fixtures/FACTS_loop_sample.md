# FACTS (test fixture for circuits.py, not a real module file)

## Pin eşleme

| Part | Doc (D<nn>) | Page | Pkg pin no | Datasheet pin name | Model file | .SUBCKT node position | SPICE node name | Label | Note |
|---|---|---|---|---|---|---|---|---|---|
| OPAMPX | D92 | 3 | 3 | IN+ | models\opampx.sub | 1 | inp | [R] | |
| OPAMPX | D92 | 3 | 2 | IN- | models\opampx.sub | 2 | inn | [R] | |
| OPAMPX | D92 | 3 | 7 | V+ | models\opampx.sub | 3 | vcc | [R] | |
| OPAMPX | D92 | 3 | 4 | V- | models\opampx.sub | 4 | ? | [R] | node name not read yet |
| OPAMPX | D92 | 3 | 6 | OUT | models\opampx.sub | 5 | out | [R] | |
