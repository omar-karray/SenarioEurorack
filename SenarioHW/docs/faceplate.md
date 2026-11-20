# Faceplate (3D check)

A 24HP Eurorack panel (121.5 x 128.5 mm, 2 mm) with a cutout for every front control, shown in KiCad's 3D viewer at the **jack plane**: the underside of the panel is
6.0 mm above the board, the seat of the jacks (measured on the jack model: housing top 6.0, thread up to 10.0). It is only a visual and clearance check: nothing here is built.

## How it is made
* `scripts/gen_faceplate.py` (run by `scripts/build.sh`, KiCad's Python) reads the final front-side positions from `Senario.kicad_pcb` and writes
  * `faceplate/Faceplate.kicad_pcb`: the panel outline and the cutouts as Edge.Cuts shapes (also the starting point for a real panel: a faceplate PCB, or Edge.Cuts to DXF),
  * `models/Faceplate_24HP.step`: that file exported by `kicad-cli pcb export step --board-only` (origin = board origin, z scaled to exactly 2.0 mm),
  * `lib/Senario.pretty/Faceplate_24HP.kicad_mod` and the footprint **FACEPLATE1** on the board: no pads, only the 3D model, lifted to z = 6.0.
* The panel is centred on the 120 x 108 board: 0.75 mm wider on each side, 10.25 mm taller at top and bottom (the rails). Its 4 mounting holes: dia 3.2, 3 mm from the top / bottom edge, 7.5 mm from the left edge and 21 HP x 5.08 mm further right (Doepfer).
* `scripts/faceplate_toggle.py on|off` hides / shows the model (it is a text edit of the model's `(hide yes)`); `scripts/previews.sh` renders the board without it (`pcb_3d_front.png`) and with it (`pcb_3d_front_faceplate.png`, `pcb_3d_faceplate_angle.png`, `pcb_3d_faceplate_side.png`).
* The board file is generated: **"Update PCB from Schematic" in KiCad offers to delete FACEPLATE1** (it has no symbol). Say no, or just run `FORCE=1 scripts/build.sh`.

## Cutouts (edit in `gen_faceplate.py`)
| Control | Cutout | Basis |
|---|---|---|
| Jacks (16) | dia 6.2 | 3.5 mm jack, M6 thread |
| Pots RK09K (4) | dia 7.0 | 9 mm pot, shaft dia 6 |
| Encoders EC12PL (4) | dia 9.2 | M9 bushing in the placeholder model: check the datasheet |
| Cherry MX (8) | 14.0 x 14.0 | MX plate cutout |
| PTL20 sliders (2) | slot 23.6 x 3.6 | travel 20 + lever 3.0: check the Bourns drawing |
| Alps slider | slot 65.5 x 3.0 | travel 60 + lever 5: check the Alps drawing (lever orientation) |
| K6 round buttons (2) | dia 10.5 | cap dia 10 |
| HOOYA buttons (6) | dia 5.8 | pillar dia 5.3 (the 7.5 mm flange stays under the panel) |
| OLED | 24.0 x 12.8 | viewing area 22.74 x 11.86 + 0.6 each side, from the footprint |
| USB-C | 9.4 x 3.6 stadium | shell 8.94 x 3.16 + 0.4 |

## First reading of the 3D check (from the heights in our models, a panel underside at 6.0 mm)
| Control | Seat (panel touches) | Against the panel at 6.0 |
|---|---|---|
| Jacks | 6.0 | seated; thread 2.0 mm above the panel top |
| HOOYA | 5.8 (flange) | 0.2 mm gap, fine |
| PTL20 | 6.6 | housing 0.6 mm into the panel |
| Alps slider | 7.0 | housing 1.0 mm into the panel |
| K6 round buttons | 7.7 | housing 1.7 mm into the panel |
| Encoders | 7.8 | body 1.8 mm into the panel |
| Pots RK09K | about 8.0 | body about 2.0 mm into the panel |
| Cherry MX | about 5.0 | flange 1.0 mm below the panel: the clips do not reach a 2 mm panel |
| OLED module | bottom at 8.5 | sits **above** the panel as drawn: needs a lower standoff |

The PTL20, Alps, encoder and OLED heights come from placeholder models drawn from datasheets, so confirm them with the real parts.
No single panel plane fits all the controls: either change components (lower pots and encoders, longer-thread jacks), add spacers, or move the plane up and give the jacks a taller seat.
