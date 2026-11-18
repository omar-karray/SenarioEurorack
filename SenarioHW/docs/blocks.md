# Blocks of the Senario board (front controls and the SMD parts behind them)

Generated from the saved board (`Senario.kicad_pcb`), 2026-11-18. Coordinates in mm, origin = top-left of the board (120 x 108). "Behind" = the SMD parts that
belong to the block by their nets: they should sit on the back, under or next to the block. Nothing here is built or tested on hardware.

## Front blocks (what the user sees on the panel)

| # | Block | Front parts | Area on the board (x0, y0 - x1, y1) |
|---|---|---|---|
| 1 | **Slider block**: Alps RS6011 slider at the bottom + the 2 round K6 buttons | SL1, SW_BTN1 (red), SW_BTN2 (green) | 8.0, 96.6 - 111.0, 106.7 |
| 2 | **Cherry MX 4 x 2** | SW_MX1..8, LED_MX1..8 | 24.3, 58.7 - 95.7, 92.2 |
| 3a | **Left column**: PTL slider + 2 knobs (pots) + orange button | PTL1, VR1, VR3, SW_BTN7 | 0.6, 29.2 - 20.8, 95.7 |
| 3b | **Right column** (mirror): PTL slider + 2 knobs + orange button | PTL2, VR2, VR4, SW_BTN8 | 99.2, 29.2 - 119.4, 95.7 |
| 4 | **Button row** (4 blue HOOYA) + the two middle mounting holes H5, H6 | SW_BTN3..6 | 26.9, 46.9 - 93.1, 55.9 |
| 5 | **Encoders** (4, illuminated) | ENC1..4 | 24.1, 29.1 - 95.9, 46.2 |
| 6 | **OLED** | J_OLED1 | 46.2, 0.6 - 74.1, 29.0 |
| 7 | **USB-C** | J_USB1 | 0.6, 46.1 - 7.5, 56.7 |
| 8 | **Jack I/O** (16 jacks: audio, CV, gate, MIDI) | J_AIN1..4, J_CVIN1/2, J_GATEIN1, J_MIDIIN1, J_AOUT1..4, J_CVOUT1/2, J_GATEOUT1, J_MIDIOUT1 | 1.7, 0.5 - 117.4, 29.0 |

Not a front block, but fixed on the board: H1..H4 (corner / side holes), H5, H6 (middle holes, in block 4).

## Back-only blocks (no front part)

| Block | Parts | Area on the back |
|---|---|---|
| **Seed2 DFM** + 5 sockets | U_SEED1, J_SEED_A..E | 58.7, 73.7 - 114.4, 102.1 (sockets at the ends) |
| **Power** | J_PWR1 (header), 2 regulators, diodes, ferrites, 19 capacitors, 3 resistors: 29 parts | header 1.8, 56.3 - 12.1, 78.7 |
| **microSD** | J_SD1 + 5 pull-ups + 2 bypass caps: 8 parts | 36.8, 90.4 - 55.2, 107.7 (bottom edge) |

## SMD parts that serve each block (by nets; supply rails and the I2C bus do not count)

| Block | Behind it | Count |
|---|---|---|
| 1 Slider block | LED resistors R120, R121 | 2 |
| 2 MX matrix | LED resistors R112..R119 (one per key LED) | 8 |
| 3a Left column | LED resistors R126 (PTL1), R128 (BTN7) | 2 |
| 3b Right column | LED resistors R127 (PTL2), R129 (BTN8) | 2 |
| 4 Button row | LED resistors R122..R125 | 4 |
| 5 Encoders | R92..R111: per encoder 3 LED resistors + the 10K / 15K divider on the push switch | 20 |
| 6 OLED | nothing by signal; only its 3V3 bypass caps (C76, C77) | 0 (+2 caps) |
| 7 USB | U_USB1 (USBLC6 ESD array), the two 5K1 CC resistors R9, R10 | 3 |
| 8 Jack I/O | the whole analog and audio chain, 117 parts: jack input / output conditioning, op-amps (U_A1..3, U_CVI1, U_CVO1), the PCM3060 codec (U_CODEC1), the MIDI opto (U3, U4), the gate transistor (Q1), their resistors and capacitors | 117 |

## Shared chips (they serve several blocks: place them centrally)

| Chip | Serves |
|---|---|
| U_IO1 (MCP23017 0x20) | encoders (12 inputs) + BTN1..4 |
| U_IO2 (MCP23017 0x21) | BTN5..8, the 8 MX keys, LED_OE |
| U_LED1 (PCA9685 0x40) | MX LEDs, BTN1..6 LEDs, PTL1/PTL2 LEDs |
| U_LED2 (PCA9685 0x41) | the 4 encoder RGB LEDs, BTN7 / BTN8 LEDs |
| U_MUX1 (74HC4051) | PTL1, PTL2, Alps slider, VR1..VR4 (channels 0..6) |
| plus their 8 bypass caps C68..C75 and the I2C / INT / OE pull-ups R88..R91 | |

## What limits the back placement

* The **Seed module and its sockets** (58.7, 73.7 - 114.4, 102.1) are right behind the **right half of the MX matrix, the Alps slider, the right column and BTN2**: no SMD of those blocks can sit directly behind them. The same area holds the Seed's own USB-C.
* The **power header** (1.8, 56.3 - 12.1, 78.7) is behind the **left column** and just below the USB.
* The **microSD slot** (36.8, 90.4 - 55.2, 107.7) is behind the **Alps slider** and the lower MX row.
* Free back areas: behind the **encoders, button row, OLED, the left half of the MX matrix** and the **top strip** (Jack I/O): the top strip is already where the Jack I/O chain sits.
* Front through-hole pads (pots, sliders, encoders, jacks, MX switches, LEDs) go through to the back: the SMD parts must avoid them (the placer does).
