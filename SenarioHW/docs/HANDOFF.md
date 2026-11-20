# Handoff: state of the Senario platform before `version-beta`

Written 2026-11-20 for the next session agent. The user will give the new platform specs and the components (footprints and 3D models) to integrate.
Read `CLAUDE.md`, `SenarioHW/docs/design-notes.md`, `blocks.md`, `faceplate.md` and `SenarioOS/docs/pinmap.md` first. **Nothing has been built or run on hardware: never claim a feature works.**

## How the project works
* The KiCad project is generated: `SenarioHW/Kicad/scripts/design.py` (parts, nets, floorplan, `FLOOR`, `ANCHOR`, `BACK_FIXED`, 3D overrides) feeds `gen_schematic.py`, `gen_pcb.py`, `gen_faceplate.py`.
  `FORCE=1 scripts/build.sh` rebuilds everything (it overwrites hand placement). Then run: `kicad-cli sch export netlist --format kicadxml` + `scripts/check_netlist.py <xml> Senario.kicad_pcb`,
  ERC, DRC (JSON), `scripts/previews.sh` (renders, BOM, faceplate renders), `scripts/gen_pinmap.py SenarioOS/docs/pinmap.md`. Last good state: netlist 0 mismatches, ERC 0 / 0, DRC only silkscreen warnings + unrouted nets.
* KiCad's Python (`/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3`) is needed for pcbnew. pcbnew crashes now and then when saving a board (see `gen_faceplate.py`, `build.sh` retries).
* `KicadLibs` is a private submodule. The footprints, symbols, 3D models and datasheets of this design live there (`gen_*.py` scripts in `KicadLibs/scripts`). **Open: KicadLibs PR #6 (branch `hroparts-k6-6272s`) holds all of it and is not merged; the submodule pointer in this repo is not moved** (rule in CLAUDE.md: never point at a commit that is not on KicadLibs `main`). Merge the PR (with the user's OK), then move the pointer.
* The user has installed JLCPCB MCP servers: use them for part availability / pricing / assembly checks instead of guessing LCSC numbers (LCSC product JSON `https://wmsc.lcsc.com/ftps/wm/product/detail?productCode=Cxxxx` also works; Bourns and EasyEDA APIs refuse automated access, do not circumvent).

## What the design is (24HP, board 120 x 108 mm, panel 121.5 x 128.5)
Daisy Seed2 DFM on five Boomele 2x5 1.27 mm sockets (back). Front = hand-soldered controls + a few SMT parts; back = Seed + all SMD.
* **Front blocks** (details and positions in `blocks.md`): 16 Thonkiconn jacks (inputs left, outputs right) + OLED HS96L01 between them; 4 illuminated encoders (SparkFun COM-15141 / EC12PL RGB); row of 4 blue HOOYA TC-1198A-L-E-C2 buttons between encoders and matrix, on the encoder / key axes, with 2 M2.5 holes (H5, H6) between them; Cherry MX 4 x 2 with red 3 mm LEDs; left / right columns: Bourns PTL20-15R slider + 2 Alps RK09K1130A5R pots (VR1/VR3, VR2/VR4) + an orange HOOYA TC-1198A-O-E-C2 button (BTN7 / BTN8); Alps RS6011 60 mm slider at the bottom with 2 K6-6272S round buttons (BTN1 red, BTN2 green); USB-C (Molex 2047110001, vertical SMT) on the left edge.
* **Back-only**: Seed + sockets, microSD (HRO TF-01A, wired as the Seed3 Eurorack Dev Kit), power, the Jack I/O chain (op-amps, PCM3060 codec, MIDI opto, gate / CV stages), shared chips U_IO1/U_IO2 (MCP23017), U_LED1/U_LED2 (PCA9685), U_MUX1 (74HC4051).
* **Power**: Eurorack 10-pin header, ferrite + Schottky + caps as the Dev Kit; Seed supply 2 x 3R3 + 2 x 100 uF (placed next to Seed socket A); -10 V reference LM4040; **+5V analog** = LD1117 + ferrite + 10 uF (as the Daisy Patch) for the codec and gate buffers; **+5V_LED** = AP63205 step-down for all LED anodes (about 0.3 A). The Dev Kit has no 5 V rail: that part is ours, check the 12 V budget.
* **Seed pins**: no free pin. D1-D6 = SDMMC (microSD), D29/D30 = USB HS (USB-C wired as the Dev Kit: USBLC6 + 2 x 5K1, VBUS isolated), D16 = I2C_INT, D19/D20 = gate in / out, LED_OE is a GPIO of U_IO2. See `pinmap.md`.
* **Jacks / CV**: 2 CV in, 2 CV out, 1 gate in, 1 gate out, MIDI in / out, 4 audio in, 4 audio out. Extra inputs need the panel mux (only channel 7 is free now: PTL1, PTL2, slider and the 4 pots use 0 to 6) or freeing D16 (give up the expander interrupt).

## Faceplate (see `faceplate.md`)
1.6 mm black JLCPCB panel, underside on the jack housings at **z = 9.0** (Thonkiconn: housing 9 mm, bushing 5.5 more: verified on the Thonk drawing and the 3D model), cutouts generated from the board, shown as FACEPLATE1 (`scripts/faceplate_toggle.py on|off`).
At that plane every control except the jacks is 1 to 4 mm below the panel and the OLED module and the USB-C are mis-fitted: **no single panel plane fits the current parts**. The new spec will probably settle this (component swaps, spacers, or a different plane).

## Open points (also in `design-notes.md`)
Verify with real parts / datasheets: pot part (RK09K1130A5R chosen; A8G 15 mm shaft and A70 30 mm exist), encoder bushing and cutout, PTL20 / Alps slot sizes, K6 and HOOYA LED polarity and brightness (330R / 150R, no LED data), Molex USB side-slot width (0.35 mm) and USB opening vs plug body, USBLC6 / AP63205 external parts and the inductor land pattern (stock FNR4030S footprint for the YNR4030), D16 "output only" note in the Seed2 datasheet, 3V3_D / 3V3_A current budgets, power header (Dev Kit uses the locking `EURO_PWR_HEADER_LOCK`, we use the 4ms shrouded one). The orange K6-6272S06 is not on LCSC (the HOOYA orange C7428717 is used instead). Routing, stackup and real panel artwork are not started.

## Conventions learnt in this session
Front parts get fixed `FLOOR` positions; back parts are placed by `gen_pcb.py` (ring search around anchors, passives behind the control they serve, shared chips central; `BACK_FIXED` for the microSD slot). Symbol pin numbers must equal footprint pad numbers.
Every new footprint / model goes into KicadLibs with its datasheet in `KicadLibs/datasheets` and a generator script, and is documented in `design-notes.md`. Commits end with the Co-Authored-By line given by the harness.
