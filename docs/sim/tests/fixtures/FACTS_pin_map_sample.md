# FACTS (test fixture, not a real module file)

## Modeller
| part | model_file |
|---|---|
| PARTA | sim\models\parta.sub |

## Pin eşleme

| Part | Doc (D<nn>) | Page | Pkg pin no | Datasheet pin name | Model file | .SUBCKT node position | SPICE node name | Label | Note |
|---|---|---|---|---|---|---|---|---|---|
| PARTA | D90 | 5 | 1 | IN | sim\models\parta.sub | 2 | in | [V] | |
| PARTA | D90 | 5 | 4 | OUT | sim\models\parta.sub | 1 | out | [V] | SPICE order differs from the pin order |
| PARTA | D90 | 5 | 2 | GND | sim\models\parta.sub | 3 | gnd | [R] | |
| PARTB | D91 | 7 | 1 | VDD | sim\models\partb.sub | 1 | vdd | [R] | |
| PARTB | D91 | 7 | 2 | SENSE | sim\models\partb.sub | 2 | ? | [R] | node name not read yet |

## Sonraki bölüm
| not | a table |
|---|---|
| x | y |
