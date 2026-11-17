# Senario design notes (2026-11-18, first pass)

Everything below is what was **decided or assumed** while turning the brief into the first schematic and placement. Items marked **? ** need your word.

## The brief, as built

| Brief | Built |
|---|---|
| 22HP, Daisy Seed2 DFM | board 108 x 126 mm (panel 111.76 x 128.5). Seed2 DFM on SMT sockets (`DAISY_SEED2_DFM`), **back side** |
| Front = controls you solder by hand, back = Seed + all SMD | exactly that: 56 front parts (all through-hole), 216 back parts (Seed, ICs, 0603 passives, LD1117, ...) |
| 4ms LED slider, the longer one | `Pot_Slider_LED_30mm_RA3045F` (4ms library, 30 mm; the other is 20 mm). Placed horizontally between the two keys |
| MX matrix 4 x 2, normal red LED | 8 x `SW_Cherry_MX_PCB_1.00u`, 19.05 mm pitch, each with a 3 mm red THT LED in the switch window (`LED_D3.0mm`, 5.08 mm below the key centre) |
| 6 C&K buttons with LED on top | **? ** placeholder: `SW_Tact_LED_Hroparts_K6-6140A_THT` (6 pads: 2 switch contacts + LED). Give me the C&K part number and I swap the footprint (one line in `design.py`) |
| 4 encoders with switch | `ENC_SPST_12mm` x 4, on the I/O expander |
| 2 Bourns PTL30 + 2 pots | `Bourns_PTL30_Slide_LED` x 2 (vertical, left and right of the matrix), Alpha 9 mm pots x 2 |
| OLED HS96L01W4S03 | datasheet fetched from LCSC (C5139758): 0.96", SSD1315, 128 x 64, 4-wire SPI, 7-pin header. New footprint + symbol in KicadLibs (`Daisy_Seed_Misc:OLED_0.96in_SPI_Module_HS96L01W4S03`, `Display_OLED:OLED_HS96L01W4S03`); the window to cut in the faceplate is drawn on `Dwgs.User` (22.74 x 11.86) |
| 4 audio in (extra codec like the Daisy Patch) | Seed codec = 2 in; **PCM3060** (as the Patch Rev8, H/W mode, on SAI2) = 2 in. Front ends copied from the Patch Rev8 and the Seed2 DFM datasheet (Figures 1.3 and 1.5) |
| Audio out main + send | 4 jacks: MAIN L/R from the Seed codec (differential-to-single-ended stage, DFM Fig. 1.5), SEND L/R from the PCM3060 (Patch Rev8 stage) |
| CV / gate (to determine) | **fully wired**: 4 CV in, 2 CV out (the two DACs), 2 gate in, 2 gate out, MIDI in + out (TRS type A). Circuits from the Seed3 Eurorack Dev Kit |
| MIDI | TRS 3.5 mm, type A: H11L1 receiver, 33 R (0.5 W, 1210) / 10 R transmitter, 3.3 V values of CA-033 |

## Floorplan (top to bottom, as in the brief)

1. Jacks, 3 rows of 7 (20 used, 1 free): row 1 AIN1-4, CV out 1-2, MIDI in; row 2 OUT main L/R, send L/R, gate in 1-2, MIDI out; row 3 CV in 1-4, gate out 1-2.
2. OLED on the left, then the 4 encoders in one row.
3. Matrix 4 x 2 with a PTL30 slider on each side.
4. The two buttons with the 4ms slider between them.
5. The 4 buttons in a row, with the 2 pots at the two ends.

**? The vertical fit is the tight point.** The controls need about 125 mm of the 128.5 mm panel height, so the board is 126 mm tall, which puts the top jack row and the bottom button row inside the 10 mm that the case rails occupy. Check the real standoff height against your rails (low parts there only), or take height out: fewer jacks (a 4th row is not needed, but 2 rows x 10 is possible with 11.5 mm pitch), or move the pots. I read "the encoder down it the switch then the OLED aligned then the 3 data encoders" as: OLED, then 4 encoders on the same line (the first is the main one); say if you meant the main encoder below the OLED (that costs about 20 mm more height).

## Back side

The generator places the back side automatically: the Seed (pad-level check against the front through-hole pads; it sits low, its micro-USB / BOOT / RESET end toward the left edge, reachable from the back), then ICs, then every passive next to the part it connects to, without overlapping anything. It is a starting point for you to improve, not a finished placement: ICs are grouped under the jack area, and decoupling is near the IC, not at the pin.

Seed module: Seed2 DFM has no USB-C on the carrier here: program through the **module's own micro-USB**, BOOT and RESET (all on its top, which faces the back of the module).

## Power

Eurorack 10-pin header (4ms symbol: pins 1-2 -12 V, 3-8 GND, 9-10 +12 V; red stripe on -12 V). Series Schottky + ferrite bead + 100 nF / 10 uF / 100 uF per rail (Dev Kit). Seed VIN through 2 x 3R3 and 2 x 100 uF (Dev Kit). **+5 V** from an LD1117S50 (PCM3060 analog supply, LED anodes, gate-out buffers); **-10 V reference** from an LM4040-10 (CV inputs). Everything 3.3 V comes from the **Seed's `3V3_D`** (codec digital, expanders, LED drivers, OLED, MIDI) and **`3V3_A`** (op-amps, pots, mux), the way the Dev Kit and the Patch do it.

**? Budgets to confirm with Electrosmith:** current available on the DFM's `3V3_D` pads (this design loads it with roughly 40-60 mA: 2 x MCP23017, 2 x PCA9685, PCM3060 VDD, OLED, MIDI) and on `3V3_A`; LD1117 heat with all 17 LEDs lit (+5 V at 330 R is about 9 mA per LED; the 12 V to 5 V drop makes 0.1 W per 15 mA, so cap the LED brightness in firmware).

## Open points and things to verify on real parts

- **C&K button**: part number and footprint (see above).
- **MIDI jacks**: the pad order of the 4ms `PJ366ST` footprint (symbol `Senario:Jack_TRS`: 1 tip, 2 sleeve, 3 ring) is assumed; check with the jack in hand.
- **PTL30 and slider LED polarity**, **K6 LED polarity**: not verifiable from the datasheets (same open points as in the Tanghim audit).
- **PCM3060 strapping**: MODE = 220K to VDD (single-ended), FMT high (24-bit left-justified, as the Patch note), DEMP low, IFMD low (slave). Confirm against libDaisy's SAI2 set-up for the Patch.
- **CV ranges**: CV in is +-5 V (Dev Kit), CV out 0-5 V. The Patch does 0-10 V out; changing it is two resistor values.
- **LCSC numbers**: filled where known from the Tanghim BOM (`docs/bom.csv`); `?` where I could not confirm (TL074, MCP6004, PCM3060, MCP23017, 74HC4051, LM4040, 47 pF, ...).
- **Not routed**: no tracks, no zones, no stackup, no net classes. 499 unrouted connections.
- **Mounting**: 4 x M2.5 holes in the corners. Faceplate and standoff height are not designed yet.

## Sources used

Daisy Patch Rev8 schematic and Seed2 DFM v1.0.12 datasheet (`KicadLibs/datasheets/`), Seed3 Eurorack Dev Kit Rev3 (`github.com/daisyaudio/Seed3-DevKit-Eurorack`, power, CV, gate, MIDI, pot mux), PCM3060 datasheet (TI SLAS533B), HS96L01 datasheet (`docs/datasheets/`), and your Tanghim hardware audit (`TanghimHardware/docs/wiring-audit.md`: PCA9685 open-drain LED rail, MIDI 3.3 V resistors, mux filter).
