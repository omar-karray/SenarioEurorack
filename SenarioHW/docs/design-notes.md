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
| 24HP, Daisy Seed2 DFM | board 120 x 108 mm. Seed2 DFM on SMT sockets (`DAISY_SEED2_DFM`), **back side** |
| Front = controls you solder by hand, back = Seed + all SMD | exactly that: 52 front parts (all through-hole), 195 back parts (Seed, ICs, 0603 passives, LD1117, ...) |
| Slider between the two keys | **Alps RS6011**, 60 mm travel, 76 x 10 mm body, no LED (4ms library `Pot_Slider_60mm_10k`). The 4ms library has no 100 mm slider; the Top-Up 60RFT2-B dual (88.7 x 20.7 mm) does not fit |
| MX matrix 4 x 2, normal red LED | 8 x `SW_Cherry_MX_PCB_1.00u`, 19.05 mm pitch, each with a 3 mm red THT LED in the switch window (`LED_D3.0mm`, 5.08 mm above the key centre, window facing the top of the panel, LED centred on the key axis) |
| 6 C&K buttons with LED on top | **?** placeholder: `SW_Tact_LED_Hroparts_K6-6140A_THT` (2 switch contacts + LED). Give me the C&K part number and I swap the footprint |
| 4 encoders with switch | `ENC_SPST_12mm` x 4, on the I/O expander |
| 2 sliders left and right | **Bourns PTL20** (20 mm travel, LED), vertical, 38.5 mm long, left and right of the matrix |
| 2 pots | Alpha 9 mm D-shaft, 10K linear |
| OLED HS96L01W4S03 | datasheet fetched from LCSC (C5139758): 0.96", SSD1315, 128 x 64, 4-wire SPI, 7-pin header. New footprint + symbol in KicadLibs (`Daisy_Seed_Misc:OLED_0.96in_SPI_Module_HS96L01W4S03`, `Display_OLED:OLED_HS96L01W4S03`); the window to cut in the faceplate is on `Dwgs.User` (22.74 x 11.86) |
| 4 audio in (extra codec like the Daisy Patch) | Seed codec = 2 in; **PCM3060** (as the Patch Rev8, H/W mode, on SAI2) = 2 in. Front ends from the Patch Rev8 and the Seed2 DFM datasheet (Figures 1.3 and 1.5) |
| Audio out main + send | 4 jacks: MAIN L/R from the Seed codec, SEND L/R from the PCM3060 |
| CV / gate (to determine) | **16 jacks fit in 108 mm**: 2 CV in, 2 CV out (the two DACs), 1 gate in, 1 gate out, MIDI in + out (TRS type A). **?** The earlier 4 CV in / 2 gate in / 2 gate out do not fit with the OLED beside the jacks; say if you want fewer audio jacks instead. Circuits from the Seed3 Eurorack Dev Kit |

## Floorplan (top to bottom)

1. Jacks, 2 rows of 8 (turned 90 degrees, 11 mm pitch), inputs on top (AIN1-4, CV in 1-2, gate in, MIDI in), outputs below (OUT main L/R, send L/R, CV out 1-2, gate out, MIDI out). **The OLED sits to the right of the jacks.**
2. The 4 encoders in one row.
3. Matrix 4 x 2 with a PTL20 slider on each side.
4. The 4 buttons in a row with the 2 pots at its ends.
5. The Alps slider with a button on each side.

I changed the order from your description (OLED and encoders were one band under the jacks) because 108 mm does not leave room for a separate OLED band. If you meant the main encoder below the OLED, something else has to give.

## Back side

The generator places the back side automatically: the Seed (pad-level check against the front through-hole pads; it sits low, its micro-USB / BOOT / RESET end toward the left edge, reachable from the back), then ICs, then every passive next to the part it connects to, without overlapping anything. It is a starting point for you to improve, not a finished placement: ICs are grouped under the jack area, and decoupling is near the IC, not at the pin.

Seed module: Seed2 DFM has no USB-C on the carrier here: program through the **module's own micro-USB**, BOOT and RESET (all on its top, which faces the back of the module).

## Power

Eurorack 10-pin header (4ms symbol: pins 1-2 -12 V, 3-8 GND, 9-10 +12 V; red stripe on -12 V). Series Schottky + ferrite bead + 100 nF / 10 uF / 100 uF per rail (Dev Kit). Seed VIN through 2 x 3R3 and 2 x 100 uF (Dev Kit). **+5 V** from an LD1117S50 (PCM3060 analog supply, LED anodes, gate-out buffer); **-10 V reference** from an LM4040-10 (CV inputs). Everything 3.3 V comes from the **Seed's `3V3_D`** (codec digital, expanders, LED drivers, OLED, MIDI) and **`3V3_A`** (op-amps, pots, mux), the way the Dev Kit and the Patch do it.

**? Budgets to confirm with Electrosmith:** current available on the DFM's `3V3_D` pads (this design loads it with roughly 40-60 mA: 2 x MCP23017, 1 x PCA9685, PCM3060 VDD, OLED, MIDI) and on `3V3_A`; LD1117 heat with all 16 LEDs lit (+5 V at 330 R is about 9 mA per LED; the 12 V to 5 V drop makes 0.1 W per 15 mA, so cap the LED brightness in firmware).

## Open points and things to verify on real parts

- **C&K button**: part number and footprint (see above).
- **MIDI jacks**: the pad order of the 4ms `PJ366ST` footprint (symbol `Senario:Jack_TRS`: 1 tip, 2 sleeve, 3 ring) is assumed; check with the jack in hand.
- **PTL20 LED polarity**, **K6 LED polarity**: not verifiable from the datasheets (same open points as in the Tanghim audit).
- **PCM3060 strapping**: MODE = 220K to VDD (single-ended), FMT high (24-bit left-justified, as the Patch note), DEMP low, IFMD low (slave). Confirm against libDaisy's SAI2 set-up for the Patch.
- **CV ranges**: CV in is +-5 V (Dev Kit), CV out 0-5 V. The Patch does 0-10 V out; changing it is two resistor values.
- **LCSC numbers**: filled where known from the Tanghim BOM (`docs/bom.csv`); `?` where I could not confirm (TL074, MCP6004, PCM3060, MCP23017, 74HC4051, LM4040, 47 pF, ...).
- **Not routed**: no tracks, no zones, no stackup, no net classes. 499 unrouted connections.
- **Mounting**: 4 x M2.5 holes (two on the side edges, two in the bottom corners). Faceplate and standoff height are not designed yet.

## Sources used

Daisy Patch Rev8 schematic and Seed2 DFM v1.0.12 datasheet (`KicadLibs/datasheets/`), Seed3 Eurorack Dev Kit Rev3 (`github.com/daisyaudio/Seed3-DevKit-Eurorack`, power, CV, gate, MIDI, pot mux), PCM3060 datasheet (TI SLAS533B), HS96L01 datasheet (`docs/datasheets/`), and your Tanghim hardware audit (`TanghimHardware/docs/wiring-audit.md`: PCA9685 open-drain LED rail, MIDI 3.3 V resistors, mux filter).
