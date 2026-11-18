# Senario design notes (2026-11-18, first pass)

Everything below is what was **decided or assumed** while turning the brief into the first schematic and placement. Items marked **?** need your word.

## Eurorack dimensions used

| What | Value | Source |
|---|---|---|
| Panel height | 128.5 mm (3U = 133.4 mm, minus the rail lips) | [Doepfer A-100 construction details](https://doepfer.de/a100_man/a100m_e.htm) |
| Panel width, 22HP / 20HP / 28HP | 111.40 / 101.30 / 141.90 mm (5.08 x HP minus 0.30 to 0.36) | same page. **24HP is not in Doepfer's table**: 24 x 5.08 = 121.92 mm nominal, so I assume about 121.55 mm real |
| Panel mounting holes | 3 mm from the top and bottom edge (122.5 mm apart), hole spacing a multiple of 5.08 mm, M3x6 screws | the hole drawing on Doepfer's page is an image I could not read; 3 mm and 122.5 mm are from the [sdiy.info wiki](https://sdiy.info/wiki/Eurorack_parts?oldid=3017) |
| **PCB height** | **108 mm** (= 128.5 - 2 x 10 mm rail clearance - 0.5). Elby Designs gives 110 mm as the maximum | [Elby Designs mechanical specification](https://elby-designs.com/webtek/documents/eurosynth/mechanical_specification.htm), sdiy.info wiki |
| PCB width | 120 mm (panel about 121.55 mm minus about 1.5 mm gap) | my choice |

Doepfer publishes no PCB height or rail profile (the rail drawing is an image; the PDF I fetched is only an assembly manual). **? Check the 10 mm clearance against your own rails** before ordering: it is the community rule, not a Doepfer number. All through-hole parts are inside the 108 mm, none sits in the rail zone.

## The brief, as built

| Brief | Built |
|---|---|
| 24HP, Daisy Seed2 DFM | board 120 x 108 mm. Seed2 DFM plugged into **five 2 x 5 1.27 mm female SMD sockets** (Boomele 1.27-2*5PLTM, LCSC C59983, the part already sourced for Tanghim), **back side**, with the Electrosmith 3D model on top |
| Front = controls you solder by hand, back = Seed + all SMD | exactly that: 52 front parts (all through-hole), 195 back parts (Seed, ICs, 0603 passives, LD1117, ...) |
| Slider between the two keys | **Alps RS6011**, 60 mm travel, 76 x 10 mm body, no LED (4ms library `Pot_Slider_60mm_10k`). The 4ms library has no 100 mm slider; the Top-Up 60RFT2-B dual (88.7 x 20.7 mm) does not fit |
| MX matrix 4 x 2, normal red LED | 8 x `SW_Cherry_MX_PCB_1.00u`, 19.05 mm pitch, each with a 3 mm red THT LED in the switch window (`LED_D3.0mm`, 5.08 mm above the key centre, window facing the top of the panel, LED centred on the key axis) |
| Push buttons with LED on top | 2 x **Hroparts K6-6272S** (left **S02 red**, JLCPCB C128970; right **S04 green**, C693827; same 10 mm drawing, the blue S03 is C693826): SMD vertical, 10 mm round cap, 13 mm high; LED pins 5 = anode, 6 = cathode, the opposite of the K6-6140A), one under each PTL slider (on the pot and slider axis), and 4 x **HOOYA TC-1198A-L-E-C2** (blue LED, JLCPCB C7428718: 7.5 mm square cap, dia 5.3 pillar, **16.2 mm high**) in a row under the slider. The HOOYA has the K6-6140A hole pattern and the same pad numbering, so it is a footprint change only (`Daisy_Seed_Misc:SW_Tact_LED_Hooya_TC-1198A_THT`, datasheet in KicadLibs); **its pad numbering and which pads are joined are the K6 convention, not on the drawing: check with a meter on the first sample.** LEDs from +5 V through 330R (red) and 150R (blue, Vf about 3.2 V gives about 10 mA; the datasheet has no LED electrical data), the first PCA9685 sinks them. Nothing is hidden any more (`PCB_HIDE_*` in `design.py` is empty) |
| 2 more orange buttons | 2 x **HOOYA TC-1198A-O-E-C2** (orange LED, JLCPCB C7428717, same drawing as the blue ones: 7.5 mm square cap, **16.2 mm high**, through-hole, hand-soldered), SW_BTN7 beside the left PTL slider (on its left) and SW_BTN8 beside the right one (on its right), the bottom edge of the cap level with the bottom of the slider body (y = 94.1 mm), x = 5.1 and 114.9 mm. Resistor 330R (about 9 mA at Vf about 2 V; the datasheet gives no LED data: check). On `U_IO2` (inputs) and `U_LED2` (LED channels 12, 13) |
| 4 illuminated encoders (RGB LED in the shaft) | **Top-Up EC12PL illuminated 12 mm encoder, SparkFun COM-15141** (`EC12PLRGBSDVBF-D-25K-24-24C-8RU(R)`: 24 pulses, 24 detents, push switch, common-anode RGB LED), replacing the plain encoder and its separate LED. Footprint `ENC_RGB_TopUp_EC12PLRGB` drawn from the maker drawing MD-15141 (in KicadLibs with both datasheets). LED: common anode on +5 V, the **second PCA9685** (0x41, 12 of 16 channels) sinks each colour through 330R (red), 220R (green, blue); Vf is 2.0 V red and 3.3 V green and blue, so the LED needs the 5 V rail. **The push switch connects pin 3 to the common anode (+5 V)**, so each encoder has a 10K / 15K divider (3.0 V at the I/O expander, pulled low): the switch reads **active high** and its expander pin needs the internal pull-up off |
| 2 sliders left and right | **Bourns PTL20-15R** (20 mm travel, 15 mm lever, red LED), vertical, 38.5 mm long, left and right of the matrix |
| 2 pots | **Alps RK09K1130A5R** (JLCPCB **C209779**, ~1250 in stock; datasheet in `KicadLibs/datasheets/`): 9 mm vertical snap-in, 10K linear (1B), no detent, knurled insulated shaft dia 6 with **LM1 = 20 mm** from the board (knurl 7 mm), no threaded bushing. Footprint `4ms_Potentiometer:Pot_9mm_Knurl_NoDet`: pad pattern checked against Alps drawing 7 (pins 2.5 pitch, lugs 8.8 apart and 7 behind the pins). 3D: the 4ms model `RK09K1130-20.wrl` converted to VRML 2.0 (`KicadLibs/scripts/convert_vrml1_pot.py`), a simplified look. Above the two PTL sliders on their axes; the side mounting holes moved down beside the K6 buttons to make room. Shorter options in the same series: A8G (15 mm, C470294, low stock), longer: A70 (30 mm, C351173). **The 20 mm shaft is still the tallest control: decide the panel distance and knob height with it** |
| 2 more pots | **VR3 and VR4**, the same Alps RK09K1130A5R (C209779) and footprint, right above the two existing pots, on the axis of the encoders (y = 37.4 mm; x = 14.8 and 105.2 mm), read through the panel mux (channels 5 and 6, `WIP_POT3`, `WIP_POT4`). **Only 14.2 mm fit between the input jacks and the lower pots, so the pot centres are 14.0 mm apart: use knobs of 13 mm or less.** To make room the encoder row moved up 0.6 mm (y = 37.4) and the OLED too (y = 2.22: it is now centred on the jack block, y = 14.8) |
| 2 middle mounting holes | **H5 and H6**, M2.5 like H1-H4 (`MountingHole_2.7mm_M2.5`), in the middle of the board on the axis of the button row (y = 51.4 mm): H5 between the first two buttons of the row (x = 40.95 mm), H6 between the last two (x = 79.05 mm), symmetric about the board centre. H1/H2 are at y = 36 on the sides, H3/H4 in the bottom corners |
| microSD card | **HRO / Hroparts TF-01A** (JLCPCB C91145, push-push, SMD, 1.85 mm high) on the **back**, at the bottom edge with the card opening toward the edge (`BACK_FIXED` in `design.py`), wired the way the Seed3 Eurorack Dev Kit does it (U7): SDMMC1 4-bit on Seed D1-D6 (D1 D3, D2 D2, D3 D1, D4 D0, D5 CMD, D6 CK), **47K pull-ups to 3V3 on CMD and DAT0-3**, none on CLK, card detect not used, VDD from 3V3, shield to GND. Added: 10 uF + 100 nF bypass at the slot. Because D1-D6 are the SD pins, GATE_IN_1, GATE_OUT_1 and I2C_INT moved to D19, D20 and D16, and LED_OE moved to a spare GPIO of the second I/O expander (`SenarioOS/docs/pinmap.md`); no Seed pin is free now. **Open: how the card is reached once the module is in the case** (the opening faces the bottom edge of the board; there is no panel cutout) |
| USB-C | **Molex 2047110001** vertical USB-C receptacle (JLCPCB **C2909828**, Extended, 24 SMT contacts + 6 through-hole shell tabs, SMT so JLCPCB can place it; about 8500 in stock) on the **front**, turned 90 degrees (long side vertical), at the left of the left pot on the pot's horizontal axis (x = 4.5, y = 51.4 mm, about 1 mm from the board edge), mouth up toward the panel. Footprint from the Molex drawing (recommended PCB layout, in KicadLibs). Wired exactly as the Seed3 Eurorack Dev Kit (J7, U14, R1, R2): VBUS on its own net `+5V_USB` (it does **not** power the module: the Dev Kit leaves it unconnected too), CC1 and CC2 each 5K1 to GND, D+ / D- (both rows tied) through a **USBLC6-2SC6** ESD array (JLCPCB C7519, on the back behind the connector) to Seed **D30 (USB HS D+) and D29 (USB HS D-)**, SBU and the high-speed pins not connected, shell and GND to GND. Symbol: KiCad's stock `Connector:USB_C_Receptacle`. **Height: the shell top is only 9.05 mm above the board** (9.8 with the pick-and-place cap, which is removed after assembly), against about 13 to 14 mm for most other controls: **the panel distance decides whether this fits** (the Hroparts TYPE-C-31-D-16F, C22464504, 13.7 mm, through-hole, hand-soldered, has its footprint in KicadLibs as the alternative). **Check with JLCPCB:** the two side shell slots are only 0.35 mm wide. This is a second USB port, separate from the Seed's own USB-C |
| OLED HS96L01W4S03 | datasheet fetched from LCSC (C5139758): 0.96", SSD1315, 128 x 64, 4-wire SPI, 7-pin header. New footprint + symbol in KicadLibs (`Daisy_Seed_Misc:OLED_0.96in_SPI_Module_HS96L01W4S03`, `Display_OLED:OLED_HS96L01W4S03`); the window to cut in the faceplate is on `Dwgs.User` (22.74 x 11.86) |
| 4 audio in (extra codec like the Daisy Patch) | Seed codec = 2 in; **PCM3060** (as the Patch Rev8, H/W mode, on SAI2) = 2 in. Front ends from the Patch Rev8 and the Seed2 DFM datasheet (Figures 1.3 and 1.5) |
| Audio out main + send | 4 jacks: MAIN L/R from the Seed codec, SEND L/R from the PCM3060 |
| CV / gate (to determine) | **16 jacks fit in 108 mm**: 2 CV in, 2 CV out (the two DACs), 1 gate in, 1 gate out, MIDI in + out (TRS type A). **?** The earlier 4 CV in / 2 gate in / 2 gate out do not fit with the OLED between the input and output jack blocks; say if you want fewer audio jacks instead. Circuits from the Seed3 Eurorack Dev Kit |

## Floorplan (top to bottom)

1. Jacks, 8 columns of 2 (turned 90 degrees, 10.8 mm pitch). **Left block = inputs**: audio in 1-2, audio in 3-4, CV in 1-2, gate in / MIDI in. **OLED in the middle.** **Right block = outputs**: out main L-R, out send L-R, CV out 1-2, gate out / MIDI out.
2. The 4 illuminated encoders in one row (y = 37.4 mm, x = 31.4, 50.5, 69.5, 88.6 mm), with 2 more pots (VR3, VR4) on the same axis at x = 14.8 and 105.2, and the 2 pots below are on the horizontal axis of the button row below (y = 51.4 mm, x = 14.8 and 105.2 mm).
3. **The row of 4 blue HOOYA control buttons between the encoders and the matrix** (y = 51.4 mm), **on the same x axes as the encoders and the MX key columns**. Then the matrix 4 x 2 (rows at y = 66 and 85.05 mm) with a PTL20 slider on each side (centre y = 76.5 mm, 1 mm below the matrix centre to leave room for the pot above). The matrix, sliders and round buttons are 9.5 mm lower than in the first layout (`DY` in `design.py`) to make room for the button row.
4. The pots, PTL sliders and K6-6272S round buttons are in two columns at **x = 14.8 and 105.2 mm** (`COL_L`, `COL_R`): the PTL body edge is 3 mm from the keycap edge of the matrix, the same gap as the Alps slider under the keys.
5. The Alps slider under the matrix. The two K6-6272S 10 mm round buttons sit under the PTL sliders, **on the same axes as the pots and sliders** (x = 14.8 and 105.2 mm), not turned (pad span along x) so the PTL slider can come down. The side mounting holes H1/H2 are at y = 36 mm under the jacks, H3/H4 in the bottom corners.

I changed the order from your description (OLED and encoders were one band under the jacks) because 108 mm does not leave room for a separate OLED band. If you meant the main encoder below the OLED, something else has to give.

## Back side

**The Seed2 DFM** is a bought module (Electrosmith), not a PCB footprint: it plugs into five female SMD sockets (`J_SEED_A` to `J_SEED_E`, one per pad bank, 4.3 mm tall, the same part as the Tanghim board). The schematic keeps the full 50-pin Seed symbol for the nets (`U_SEED1`, not placed on the board) and each socket carries the same nets pin by pin; `scripts/seed_sockets.json` records which Seed pad each socket pin touches (computed from the two footprints by `make_seed_socket_map.py`: socket pins 1, 2, 3 ... touch pads X1, X10, X2 ...). On the board the module is the pad-less `DAISY_SEED2_DFM_3D` footprint (outline and the STEP model `ES_Daisy_Seed2_DFM_Rev5-3.step`, both in KicadLibs) placed over the sockets, so the 3D view shows the real module. The project defines `KICADLIBS` itself, so the model is found with no machine set-up.

The generator places the Seed first (its pads checked against the front through-hole pads), then the ICs, then every passive next to the part it connects to, none overlapping anything. The module outline is a keep-out for the other back-side parts; front-side leads under the module are fine (the sockets stand 4.3 mm off the board). It is a starting point for you to improve: ICs are grouped under the jack area, and decoupling is near the IC, not at the pin.

The module's **micro-USB, BOOT and RESET** are on its top, facing the back of the module; the module sits with the USB end toward the right board edge. No USB-C on the carrier: program through the module.

## 3D models

| Part | Model |
|---|---|
| Seed2 DFM | Electrosmith STEP (KicadLibs) on its five sockets |
| Jacks (all 16) | `WQP-PJ398SM.step` (Thonkiconn), KicadLibs |
| K6-6272S buttons | `Hroparts_K6-6272S_green.wrl` / `_red.wrl` (KicadLibs, generated from the datasheet drawing: housing + 10 mm cap; the blue one is `Hroparts_K6-6272S.wrl`) |
| TF-01A microSD slot | `TF-01A.step` (KicadLibs, the model that came with the Tanghim project, lying flat: rotate -90 about X, offset -0.6 / -4.5 / 0), footprint and generator `KicadLibs/scripts/gen_tf01a.py` |
| Molex 2047110001 USB-C | `USBC_Molex_2047110001.wrl` (KicadLibs, simple body from the datasheet: shell 8.94 x 3.16 up to 9.05 mm, contact feet) ; also `USBC_Hroparts_TYPE-C-31-D-16F.wrl` for the Hroparts alternative |
| HOOYA TC-1198A buttons | `Hooya_TC-1198A.wrl` (KicadLibs, simple body from the datasheet drawing) |
| Cherry MX + red LED | `SW_Cherry_MX_PCB.wrl` (keyswitch library), KicadLibs; the LED model is KiCad's |
| Illuminated encoders | **placeholder** (body 12.4 x 13.2 x 7.8, M9 bushing to 14.8 mm, dia 6 shaft to 25.3 mm, from the maker drawing). No public STEP found |
| RGB LEDs, SMD parts, power header, sockets | KiCad stock models |
| **Bourns PTL20, Alps RS6011, OLED module, encoders** | **placeholders** (`models/*.wrl`, written by `gen_placeholder_models.py`): plain bodies of the right size with a lever (PTL: **the ordered PTL20-15R, 15 mm lever** with a red lens (`LEVER_L` in `gen_placeholder_models.py`; options 10, 15, 19 mm); RS6011: **metal lever type 6, L1 = 15 mm from the housing top, so the tip is 22 mm above the board** (Alps datasheet p.390 and p.392; 20 mm is the other length)). PTL housing 6.6 mm high; **Bourns measures the lever length L from the housing top face (the face that screws to the panel), so the tip is 6.6 + L above the board**, RS6011 7 mm (Alps drawing), OLED module bottom 8.5 mm above the board (as Tanghim: **check your standoff**). No public STEP file found for them; replace the placeholders when you have real models |

The 4ms footprints point to their PCM-package folder; the project remaps those paths to `KicadLibs/3dmodels` (`MODEL_PATH_REMAP`), so no PCM install is needed.

## Encoder height and the panel

From the maker drawing: body 7.8 mm above the board, M9 x 0.75 bushing 7 mm long (to 14.8 mm), shaft to **25.3 mm**; nut 11 AF x 2, washer dia 14 x 0.4. With a 2 mm panel, nut and washer on the front, the panel's inner face has to be between about 7.8 and 10.4 mm from the board. **Check this against the jacks (Thonkiconn) and the MX switches** when you design the standoffs and the faceplate; the panel hole for the bushing is dia 9.4 (drawn on the footprint's drawing layer).

## Power

Eurorack 10-pin header (4ms symbol: pins 1-2 -12 V, 3-8 GND, 9-10 +12 V; red stripe on -12 V). Series Schottky + ferrite bead + 100 nF / 10 uF / 100 uF per rail (Dev Kit). Seed VIN through 2 x 3R3 and 2 x 100 uF (Dev Kit). **+5 V** from an LD1117S50 (PCM3060 analog supply, LED anodes, gate-out buffer); **-10 V reference** from an LM4040-10 (CV inputs). Everything 3.3 V comes from the **Seed's `3V3_D`** (codec digital, expanders, LED drivers, OLED, MIDI) and **`3V3_A`** (op-amps, pots, mux), the way the Dev Kit and the Patch do it.

**? Budgets to confirm with Electrosmith:** current available on the DFM's `3V3_D` pads (this design loads it with roughly 40-60 mA: 2 x MCP23017, 2 x PCA9685, PCM3060 VDD, OLED, MIDI) and on `3V3_A`; LD1117 heat with all 28 LED channels lit (+5 V at 330 R is about 9 mA per LED; the 12 V to 5 V drop makes 0.1 W per 15 mA, so cap the LED brightness in firmware).

## Open points and things to verify on real parts

- **MIDI jacks**: the pad order of the 4ms `PJ366ST` footprint (symbol `Senario:Jack_TRS`: 1 tip, 2 sleeve, 3 ring) is assumed; check with the jack in hand.
- **PTL20 LED polarity**, **K6 LED polarity**: not verifiable from the datasheets (same open points as in the Tanghim audit).
- **PCM3060 strapping**: MODE = 220K to VDD (single-ended), FMT high (24-bit left-justified, as the Patch note), DEMP low, IFMD low (slave). Confirm against libDaisy's SAI2 set-up for the Patch.
- **CV ranges**: CV in is +-5 V (Dev Kit), CV out 0-5 V. The Patch does 0-10 V out; changing it is two resistor values.
- **LCSC numbers**: filled where known from the Tanghim BOM (`docs/bom.csv`); `?` where I could not confirm (TL074, MCP6004, PCM3060, MCP23017, 74HC4051, LM4040, 47 pF, ...).
- **Not routed**: no tracks, no zones, no stackup, no net classes. 499 unrouted connections.
- **Mounting**: 4 x M2.5 holes (two on the side edges, two in the bottom corners). Faceplate and standoff height are not designed yet.

## Sources used

Daisy Patch Rev8 schematic and Seed2 DFM v1.0.12 datasheet (`KicadLibs/datasheets/`), Seed3 Eurorack Dev Kit Rev3 (`github.com/daisyaudio/Seed3-DevKit-Eurorack`, power, CV, gate, MIDI, pot mux), PCM3060 datasheet (TI SLAS533B), HS96L01 datasheet (`KicadLibs/datasheets/`), and your Tanghim hardware audit (`TanghimHardware/docs/wiring-audit.md`: PCA9685 open-drain LED rail, MIDI 3.3 V resistors, mux filter).
