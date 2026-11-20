# Faceplate (3D check, and the start of a JLCPCB faceplate PCB)

A 24HP Eurorack panel (121.5 x 128.5 mm) as a **1.6 mm PCB with black solder mask** (a standard JLCPCB board), with a cutout for every front control, shown in KiCad's 3D viewer
with its **underside on the housing top of the Thonkiconn jacks**: 9.0 mm above the board. Nothing here is built or ordered.

## The jack height (verified)
The Thonk drawing of the Thonkiconn (`Thonkiconn_Jack_Datasheet`, model PJ398SM / PJ301M-12, from thonk.co.uk) gives the housing as **9 mm along the barrel axis** (the jack stands with the barrel up,
pins down) and the bushing as **5.5 mm more** (thread 4.5). The 4ms 3D model we use agrees: black housing from the board up to **9.0**, then the bushing. So the panel underside is at z = 9.0 and a 1.6 mm
panel covers 9.0 to 10.6; the thread then sticks out about 3.9 mm above the panel (top at about 14.5). (An earlier version of this page said 6.0: that was a misreading of the STEP file points.)

## How it is made
* `scripts/gen_faceplate.py` (run by `scripts/build.sh`, KiCad's Python) reads the final front-side positions from `Senario.kicad_pcb` and writes
  * `faceplate/Faceplate.kicad_pcb`: the panel outline and the cutouts as Edge.Cuts shapes, stackup with **black solder mask** and white silkscreen, 1.6 mm. This file is the starting point of the real faceplate PCB (no copper, no silkscreen yet),
  * `models/Faceplate_24HP.step`: that file exported by `kicad-cli pcb export step --board-only --include-soldermask` (origin = board origin),
  * `lib/Senario.pretty/Faceplate_24HP.kicad_mod` and the footprint **FACEPLATE1** on the board: no pads, only the 3D model, with its underside at z = 9.0.
* The panel is centred on the 120 x 108 board: 0.75 mm wider on each side, 10.25 mm taller at top and bottom (the rails). Its 4 mounting holes: dia 3.2, 3 mm from the top / bottom edge, 7.5 mm from the left edge and 21 HP x 5.08 mm further right (Doepfer).
* `scripts/faceplate_toggle.py on|off` hides / shows the model; `scripts/previews.sh` renders the board without it (`pcb_3d_front.png`) and with it (`pcb_3d_front_faceplate.png`, `pcb_3d_faceplate_angle.png`, `pcb_3d_faceplate_side.png`).
* The board file is generated: **"Update PCB from Schematic" in KiCad offers to delete FACEPLATE1** (it has no symbol). Say no, or run `FORCE=1 scripts/build.sh`.

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
| USB-C | 9.4 x 3.6 stadium | shell 8.94 x 3.16 + 0.4 (see the USB note below) |

## Reading of the 3D check (heights from our models, panel underside at 9.0, top at 10.6)
| Control | Seat (what the panel would rest on) | Gap under the panel | Sticks out above the panel top |
|---|---|---|---|
| Jacks | housing top 9.0 | seated | thread about 3.9 (top 14.5) |
| Pots RK09K | about 8.0 | 1.0 | shaft 20 mm: about 9.4 |
| Encoders EC12PL | body 7.8 | 1.2 | bushing top about 14.8: 4.2 of thread |
| K6 round buttons | housing 7.7 | 1.3 | cap 13.0: 2.4 |
| Alps slider | housing 7.0 | 2.0 | lever 22: 11.4 |
| PTL20 sliders | housing 6.6 | 2.4 | lever 21.6: 11.0 |
| HOOYA buttons | flange 5.8 | 3.2 | pillar 16.2: 5.6 |
| Cherry MX | about 5.0 | 4.0 | switch top about 11.6: a 14 mm hole, no clips on a 1.6 mm panel at this height |
| OLED module | bottom at 8.5 | glass would pass through the panel | the module has to sit lower: its glass top must be 9.0 or less |
| USB-C (Molex) | shell top 9.05 | 0 | recessed 1.55 below the panel top |

With the panel on the jacks nothing collides any more (the earlier 6.0 mm plane had the pots, encoders and K6 housings 1 to 2 mm into the panel), but every other control sits 1 to 4 mm **below** the panel: they
need spacers, standoffs or taller parts to be held by the panel (nuts on the encoders, screws on the sliders), and the MX switches and the OLED module need a different mounting.
The PTL20, Alps, encoder and OLED heights come from placeholder models drawn from datasheets: confirm them with the real parts.

## Notes for a real JLCPCB faceplate
* JLCPCB routes the outline and inner cutouts with a 2 mm bit: **inner corners (the 14 x 14 MX squares, the OLED window) come out rounded, radius about 1 mm**. Round them in the file if the parts need the square.
* **USB-C:** the receptacle shell is 1.55 mm below the top of the panel. A plug's moulded body is much bigger than the shell, so with a 9.4 x 3.6 hole it stops at the panel and does not reach the receptacle: the opening should be at least as large as the plug body (about 12.5 x 6.5), or the connector has to sit flush with the panel top.
* A black solder mask board has dark edges; silkscreen is white. Labels and graphics can be added later as silkscreen in `Faceplate.kicad_pcb`.
