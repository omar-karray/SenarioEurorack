# Senario specs, version-beta (2026-11-22)

The platform brief of 2026-11-22, written down as a spec, and how it connects to the Daisy Seed2 DFM. It **replaces the "brief, as built" table of `design-notes.md`** (that was the first pass); the first-pass notes stay valid for everything this page does not change (power chain, back-side placement, 3D models, open points). The KiCad design (`design.py`) is **not rebuilt yet**: this page is what it will be rebuilt from. Nothing has been built or run on hardware.

**Decided by you (2026-11-22):** the OLED stays; the microSD keeps the standard 4-bit wiring; the pots are the Alps (tall) and the Alpha RD901F (regular); the panel plane is decided later; **an external DAC is allowed if the pins need it.**

Where a number comes from the repo (pin map, KicadLibs previews) it is stated as such; **what is my assumption or a guess is marked "?"**.

## 1. The spec

**24HP Eurorack, one PCB 120 x 108 mm, Daisy Seed2 DFM on the back, controls on the front** (unchanged).

### I/O (22 jacks)

| | Inputs (12 jacks) | Outputs (10 jacks) |
|---|---|---|
| Audio | 4 | 4 |
| CV | 4 | 2 |
| Gate | 2 | 2 |
| Clock | 1 | 1 |
| MIDI (TRS, 3.3 V) | 1 | 1 |

Plus **USB-C** (MIDI I/O and firmware update, vertical Hroparts TYPE-C-31-D-15C) and **microSD** (vertical, Yamaichi PJS008U-3000-0).

### Controls

| Section | Parts | Count |
|---|---|---|
| **Control** | 6 illuminated RGB buttons, Lakeview **TL1-DNNFN-RCWN** (LCSC C39501039, "little cap" dia 5.6, 16.4 mm high) | 6 |
| **Slider** | 1 Alps RS6011 60 mm slider + 2 RGB buttons Lakeview **TL16-NND6W-FN** (LCSC C55788158, 9 mm cap, 14.35 mm high) | 1 + 2 |
| **Cherry MX matrix** | 4 x 2 Cherry MX + one RGB SMD LED each (? SK6812-EC20, the part of `SW_Cherry_MX_SK6812-EC20`) | 8 + 8 |
| **Sides** (one column per stereo input pair, left and right) | 1 RGB button (TL1, 5.6 cap), 1 Bourns PTL20 slider, 1 trim pot (Alps RK09K A5R, knurled 20 mm, C209779), 1 regular pot (? Alpha RD901F-40-15F-B10K) | 2 x 4 |
| **Encoders** | 4 standard Bourns (PEC11R, no LED) | 4 |

**The two Lakeview RGB parts are the only buttons**: TL1 (8 of them: 6 control + 2 sides) and TL16 (2: the slider section). That is **10 RGB buttons = 30 LED channels** (common anode, one R / G / B cathode each). The orange / blue HOOYA TC-1198A and the K6-6272S round buttons of the first pass are **gone** from the board.

**The display stays**: the Hansheng HS96L01W4S03 0.96" OLED (LCSC C5139758, SSD1315, 128 x 64, 4-wire SPI, window 22.74 x 11.86). It is in the library with a 3D model and in InvenTree; the **1.3" HS13L01W4S01** (SH1106, 35.4 x 33.5 mm, window 31.42 x 16.70, LCSC C5139764) is in the library too as the larger alternative, which model the design uses is decided later (the larger one makes the placement problem worse). **The display does not fit the top jack band any more: see section 4.**

### Totals

22 jacks, 10 RGB buttons, 8 MX keys (8 RGB LEDs), 4 encoders, 3 sliders (2 PTL20 + 1 Alps), 4 pots, OLED, USB-C, microSD. **Controls to read:** 30 switch inputs (10 buttons + 8 keys + 4 x A / B / switch), 7 analog (2 PTL, Alps, 4 pots), **LED outputs:** 32 constant-current channels (30 button + 2 PTL lever LEDs) + 8 addressable LEDs.

## 2. How it connects to the Seed2 DFM

The Seed provides (as used in the first pass, `SenarioOS/docs/pinmap.md`): its own stereo codec (2 in / 2 out), 2 DACs (D22 / D23), ADC-capable pins, SAI2, SDMMC1, USB, one UART, I2C, SPI, plain GPIO. **The pins are the limit, not the peripherals**: the first pass used all 33 (D0 to D32).

### 2.1 Which interface serves which part

| Function | Interface | Chip / circuit | Seed pins |
|---|---|---|---|
| Audio in 1-2, out 1-2 | the Seed's codec | op-amp front ends (Dev Kit / Patch) | audio pads |
| Audio in 3-4, out 3-4 | **SAI2** + PCM3060 (as the Daisy Patch Rev8) | op-amp front ends | D24 to D28 (5) |
| CV in 1-4 | 4 x ADC, +-5 V in, inverting stage to 3.3 .. 0 V | op-amps (the Dev Kit stage, twice more) | D17, D18, **D21, D31** |
| CV out 1-2 | **external DAC on I2C: MCP4728** (decided 2026-11-22; 4 channels 12 bit, LCSC C108207, 4018 in stock, 2.44 USD, Extended: 2 channels used, 2 spare), 0 .. 5 V | DAC + op-amps | I2C only (**D22 / D23 are freed**) |
| Gate in 1-2, clock in | GPIO, inverting transistor stage (Dev Kit gate in), clock in on an EXTI-capable pin | 1 transistor each | D19, **D32**, **D0** |
| Gate out 1-2, clock out | GPIO, 0 / 5 V buffer (Dev Kit gate out, from the +5V analog rail) | 1 buffer each | D20, **D9**, **D16** (an output: see the D16 note) |
| MIDI in / out | UART (USART1), TRS type A, optocoupler in | 2 jacks + opto | D13, D14 |
| USB-C | USB OTG HS port in FS mode (the Seed's "external" USB pins) | USBLC6-2SC6 ESD + 2 x 5K1 on CC | D29, D30 |
| microSD | SDMMC1 4-bit (as the Dev Kit) | 47K pull-ups | D1 to D6 |
| 30 switch inputs | I2C: 2 x MCP23017 (0x20, 0x21) | 30 of 32 pins used | D11, D12 + INT |
| 32 LED channels | I2C: 2 x PCA9685 (0x40, 0x41), open drain, anodes on +5V_LED | 330R / 220R per colour | I2C |
| 8 MX RGB LEDs | **one data line** (SK6812 chain) through a 5 V level shifter (? 74AHCT1G125), driven from a timer pin with DMA | 8 x SK6812-EC20 | **D9** (PB4, TIM3_CH1: ? check the alternate function on the Seed2 pinout) |
| OLED | 4-wire SPI (SPI1), CS tied low, DC on a Seed pin, RES from the expander | HS96L01W4S03 | D8 (SCK), D10 (MOSI), D7 (DC) |
| 7 panel analogs | 74HC4051 (7 of 8 channels), one ADC, **selects from a third MCP23017** (0x22) which also holds `LED_OE`, OLED `RES` | MCP23017 + mux | D15 + I2C |

### 2.2 Pin allocation (proposed). Bold = changed from `pinmap.md`

| Pin | Net | | Pin | Net |
|---|---|---|---|---|
| **D0** | **CLOCK_IN** (was OLED_RES) | | D17 | CV_IN_1 |
| D1 to D6 | SDMMC 4-bit (unchanged) | | D18 | CV_IN_2 |
| **D7** | **OLED_DC** (was OLED_CS) | | D19 | GATE_IN_1 |
| D8 | OLED_SCK (unchanged) | | D20 | GATE_OUT_1 |
| **D9** | **LED_DATA** (was OLED_DC) | | **D21** | **CV_IN_3** (was MUX_A) |
| D10 | OLED_MOSI (unchanged) | | **D22** | **GATE_OUT_2** (was CV_OUT_2 DAC) |
| D11 / D12 | I2C_SCL / I2C_SDA | | **D23** | **I2C_INT** (was CV_OUT_1 DAC) |
| D13 / D14 | MIDI_TX / MIDI_RX | | D24 to D28 | SAI2 (unchanged) |
| D15 | POT_MUX (ADC) | | D29 / D30 | USB HS D- / D+ |
| **D16** | **CLOCK_OUT** (was I2C_INT) | | **D31 / D32** | **CV_IN_4 / GATE_IN_2** (were MUX_B / MUX_C) |

**All 33 pins are used, none spare.** How it adds up: the fixed part is 17 pins (SD 6, USB 2, SAI2 5, I2C 2, MIDI 2); then the mux ADC 1, CV in 4, gate / clock in 3, gate / clock out 3, LED data 1, OLED 3 (SCK, MOSI, DC), INT 1 = 33. **What makes it fit with the OLED and the 4-bit SD kept:** (a) the **external DAC** frees D22 / D23 (the Seed's two DACs); (b) the **mux selects leave the Seed** (a third MCP23017, 0x22: it also takes `LED_OE`, OLED `RES` and has 9 pins spare); (c) the OLED's CS is tied low (the OLED is alone on its SPI bus) and its `RES` is an expander pin; (d) D16 is an output (clock out), which settles the first pass's "D16 is output only" doubt, and the interrupt moves to D23. **ADC-capable pins in use:** D15, D17, D18, D21, D31 (5).

**Without the external DAC it does not fit:** 35 signals for 33 pins. The other way out would be 1-bit SD (frees D1 to D3); you chose to keep the standard 4-bit wiring, so the DAC it is.

**What the external DAC costs:** CV outs become **control-rate** (an I2C write of a channel is about 50 us at 1 MHz, shared with the expanders and LED drivers: about 1 kHz updates are realistic), where the Seed's own DACs can be fed by DMA at audio rate. For a looper's CV (clock-synced, envelopes, pitch steps) that is fine; **if you want audio-rate CV out, use an SPI DAC instead** (then it needs its own CS and the pin count is short again by one).

**Expander budgets:** U_IO1 + U_IO2: 30 of 32 inputs. **The standard Bourns encoders have no LED, so their push switch is a plain switch to GND: the 10K / 15K dividers and the active-high exception of the first pass go away** and all 30 inputs are ordinary pull-up switches. U_IO3: 7 of 16 pins used. PCA9685: 32 of 32 channels, no spare (a third chip is the way to add anything). Polling the three expanders instead of using the interrupt is possible if D23 is ever needed.

### 2.2b Timing: gates and clocks are GPIO, only CV goes over I2C

Decided: **CV out is control-rate** (MCP4728 on I2C, about 1 kHz, 12-bit, own 2.048 V reference at gain 1, **powered from 3V3** (its I2C inputs need a logic high of 0.7 x VDD, so VDD = 5 V would not accept our 3.3 V bus): full scale 2.048 V, so the op-amp stage needs a gain of about 2.44 for 0 .. 5 V: Rf 68K / Rg 47K = 2.447; the two values are `CVO_RF` / `CVO_RG` in design.py). **Gate out, clock out, gate in and clock in are plain GPIO pins of the Seed, never on I2C or an expander:**

| Signal | Pin | How the firmware deals with it |
|---|---|---|
| Gate out 1 / 2, clock out | D20 / D22 / D16 (outputs) | The edge is set from the audio callback, so its timing is one audio block: with a block size of 4 to 6 samples that is under 0.15 ms at 48 kHz (a block of 48 would be 1 ms). If an edge must land on an exact sample, start it from a hardware timer (output compare) instead of the callback. 0 / 5 V buffer from the +5V analog rail, as the Dev Kit. |
| Gate in 1 / 2, clock in | D19 / D32 / D0 (inputs, EXTI lines 6 / 3 / 12: all different) | Interrupt on both edges, with a hardware timer timestamp (tempo and swing are measured from the timestamps, not from polling). Inverting transistor stage as the Dev Kit: a high gate reads 0. |
| CV out 1 / 2 | MCP4728 over I2C | Written from the main loop at about 1 kHz, **with slew or interpolation in firmware** so the output does not step audibly. |

**CV and gate that belong together (pitch + gate, an envelope that starts on a gate):** the gate is immediate but the CV arrives up to about 1 ms later (I2C and the shared bus). **Write the CV first and raise the gate 1 to 2 ms later**, the usual Eurorack practice. If the I2C bus is busy with the LED drivers, give the DAC write priority, or send the LED updates in the gaps.

### 2.3 Open on the Seed side

1. **Firmware update over the panel USB-C.** Wiring the USB-C to D29 / D30 gives a USB MIDI port (? the "external USB" of libDaisy), but **the STM32 ROM DFU listens on the Seed's own micro-USB**, not on these pins: to update through the panel you need a bootloader that runs on the HS port, or a flash from the **SD card** (the card is on the module anyway). Until that is checked, keep the Seed's micro-USB reachable inside the case. **Decide the update path before the panel.**
2. **LED brightness and the 12 V budget.** 10 RGB buttons (about 10 mA per colour) + 8 SK6812 (up to about 60 mA each lit white) + 2 lever LEDs can draw **0.8 A at 5 V = about 0.4 A from +12 V** at full white; the AP63205 (2 A) copes, **a Eurorack bus does not like it**: cap the brightness in firmware (25 % is about 0.1 A at 12 V).
3. **3V3_D / 3V3_A budgets** as in the first pass (now 3 expanders + 2 PCA9685 + DAC + PCM3060 + MIDI + OLED): confirm the current with Electrosmith.
4. **SK6812 data at 3.3 V** is out of spec for a 5 V chain (VIH = 0.7 x VDD): the level shifter is not optional.

## 3. The panel: heights (from the KicadLibs panel preview)

Panel as modelled: 1.6 mm faceplate, **underside at z = 9.0** (the Thonkiconn housing), top at 10.6. "Needs" = what the part asks of the panel at that plane.

| Part | Top above the board | At the 9.0 plane |
|---|---|---|
| Jacks (WQP-PJ398SM) | 9.0 housing | seat on the panel: defines the plane |
| TL1 button (cap dia 5.6) | 16.4 | cap 5.8 above the panel top, hole dia 6.0 |
| TL16 button (cap dia 9) | 14.4 | cap 3.8 above the panel top, hole dia 9.6 |
| USB-C Hroparts D-15C | 10.5 | mouth 0.1 mm below the panel top = flush, opening 9.6 x 3.8 |
| microSD Yamaichi (vertical) | 14.2 with a card | card 3.6 above the panel top, slot 13.6 x 3.1 |
| PTL20 slider | body 7.0 | lever through a 2.8 x 27 slot; **2.0 mm spacers** under the panel screws |
| Alps RS6011 slider | body 8.0 | **1.0 mm spacers** |
| Bourns PEC11R **15 mm** | shaft tip 21.6 | shoulder 6.6: **2.4 mm spacer**; bushing top 11.6 = only 1.0 above the panel: **too short for a 2.0 mm nut** |
| Bourns PEC11R **20 mm** | shaft tip 26.6 | shoulder 6.6: 2.4 mm spacer; bushing top 13.6 = 3.0 above the panel: **the nut fits** |
| Alps RK09K tall (A70, 30 mm) | shaft 30.0 | shoulder 6.8: 2.2 mm spacer, no nut (lugs only) |
| **Alpha RD901F** (your regular pot) | shaft 25.0 | **shoulder at 10.0: the body does NOT fit under a 9.0 underside** (it needs 10.0; then the bushing top is 15.0, 3.4 above a 1.6 mm panel: the nut fits) |
| Cherry MX + cap | stem 15.4, cap from 12.0 | the cap goes up to the panel opening; see `design-notes` / the preview row (opening 18.8 square) |

**One decision settles most of it: the panel underside plane.** At **9.0** (jack plane) the RD901F does not fit and the encoders need a 2.4 mm spacer and the 20 mm version. At **10.0** the RD901F fits, the USB-C mouth sits 1.1 mm below the panel top (a plug normally still reaches: ? check), the jacks' bushing (5.5 mm above the housing) still passes the panel with room for its nut (? thread length), and every spacer grows by 1 mm (PTL 3.0, Alps 2.0, encoders 3.4). I lean to **10.0** because it keeps your RD901F; if you would rather keep 9.0, use the RK09K for both pots. (The faceplate generator takes the plane as one number.)

## 4. Does it fit on the board? (first-order, before rebuilding)

**Not with the OLED where it was.** The numbers:

* **Jacks:** 22 jacks = **11 columns of 2 at 10.8 mm** = 117 mm of the 120 mm board: a full-width band 29 mm tall, with **no room for the OLED** (the first pass had 16 jacks in 8 columns and the OLED in the middle: that is the whole reason it fitted).
* **The OLED module** is 27.3 x 27.8 mm and sits at z 8.5 to 10.9 (on its header; the window 22.74 x 11.86 is what shows). It needs a **free rectangle of that size on the board**, no taller part under it except what stays below 8.5 mm (the jacks' housings go to 9.0).
* **The rest of the stack is full:** jacks 29, encoders 17 (with the side pots at the same height), buttons 10, MX matrix 33.5, slider 10.5 = 100 of 108 mm.

So something has to give. **Options, for you to choose (I can try each in the generator and show the result):**

| | Idea | What it costs |
|---|---|---|
| A | **OLED in the middle of the encoder + button band** (x 21 to 99, y 29 to 56: 78 x 27 mm): OLED centred, **2 encoders on each side of it**; the 6 control buttons move to a row above the MX matrix or beside the slider | the button row loses its place: 6 TL1 (8 mm bodies) need about 70 x 10 mm elsewhere, and the encoders are no longer in one row |
| B | **Move the 6 non-audio jacks** (clock in / out, MIDI in / out, gate out 2 ...) out of the top band to a **third row** under the OLED's flanks, as the first pass did with 16 jacks in 8 columns | jacks and encoders compete for the band y 29 to 46; the encoder row would have to shrink to 2 + 2 beside the OLED anyway |
| C | **Put the OLED on the left or right edge strip, vertical** (window 11.86 wide x 22.74 tall, module 27.8 x 27.3) | the USB-C, microSD and the OLED all want the two edge strips (about 9 mm wide each): they do not fit |
| D | A smaller display (0.91 in, 128 x 32, a 12 mm tall band) | you want the HS96L01W4S03 |

**My suggestion: A**. It keeps the 22 jacks in one band and puts the display between the encoders, where you look. The microSD slot then takes one edge strip and the USB-C the other (both strips are free below the side pots).

* **Below the jacks** otherwise as the first pass: the 4 x 2 MX matrix, the Alps slider with a TL16 on each side, the side columns (PTL20, tall trim, regular pot, TL1) at x about 14.8 and 105.2.
* **Back side:** the Seed, 3 expanders, 2 PCA9685, mux, PCM3060, DAC, CV / audio op-amps, MIDI optos and power fit the area budget of the first pass; the extra analog chains are about 6 jacks' worth of parts and need space behind the wider jack band. Not placed yet.

## 5. Decisions

| # | Decision | State |
|---|---|---|
| 1 | OLED | **stays** (your decision); placement: choose A, B, C or D in section 4 |
| 2 | Pins | **MCP4728 on I2C (decided)** + third MCP23017; SD stays 4-bit (your decision); CV out is control-rate |
| 3 | Firmware update path (panel USB-C vs Seed micro-USB vs SD) | open: decide before the panel |
| 4 | MX LEDs: SK6812-EC20 (1 pin + level shifter) or discrete RGB (+24 channels = 2 more PCA9685, no pin) | I suggest SK6812; pins are all used, so discrete RGB would need a fourth chip and another I2C bus load |
| 5 | Panel underside plane 9.0 or 10.0 | **10.0** (set 2026-11-22 in gen_faceplate.py, `Z_PANEL`; the RD901F needs it; the jacks then stand 1.0 mm below the panel) |
| 6 | Pots | **Alps trim (RK09K A5R knurled 20 mm, C209779; was the 30 mm A70) + Alpha RD901F** (your decision); the RD901F needs the 10.0 plane, so decision 5 matters |
| 7 | Encoder: PEC11R 20 mm with or without switch, F or K shaft | open; I suggest 20 mm with switch |
| 8 | Buttons: TL1 for the 6 control + 2 side, TL16 for the 2 slider buttons | as in the brief |
| 9 | LED brightness cap in firmware | suggest 25 % default |
| 10 | microSD slot place and its panel slot | in the generator, after decision 1 |

## 6. What changes in the repo when this is accepted

`design.py`: keep the OLED (its pins change), remove the HOOYA and K6 buttons, the encoder LEDs and dividers; add 6 jacks and their chains, the third MCP23017, the DAC, the 8 SK6812 + level shifter, the 8 TL1 + 2 TL16, the Bourns encoders, the D-15C, the vertical microSD, the new pin map (section 2.2); then `FORCE=1 build.sh` (it overwrites hand placement: there is none worth keeping yet), `check_netlist.py`, ERC, DRC, `gen_pinmap.py`. The footprints and 3D models of all parts are already in KicadLibs.
