# SenarioHW

Hardware of the Senario Looper / MultiFX: a 24HP Eurorack module on a Daisy Seed2 DFM.

| Path | What |
|---|---|
| `Kicad/` | the KiCad 10 project `Senario.kicad_pro` (schematic: root + 5 sheets, PCB: primary placement, unrouted) |
| `Kicad/scripts/` | the generators; `design.py` is the design (every part, net and the floorplan) |
| `Kicad/lib/` | project symbols (`Senario.kicad_sym`, generated) |
| `docs/` | `design-notes.md` (read this first), `bom.csv`, `previews/` (schematic PDF, front and back placement, 3D renders), datasheets are in `KicadLibs/datasheets/` |

Libraries come from the `KicadLibs` submodule at the repository root (`${KIPRJMOD}/../../KicadLibs`); stock KiCad libraries for the rest.

## Generated, not drawn

The schematic and the PCB are written by scripts from `Kicad/scripts/design.py`, the same way the Tanghim boards are:

```
cd SenarioHW/Kicad
FORCE=1 scripts/build.sh      # project files, schematic sheets, PCB placement (needs KiCad 10)
scripts/previews.sh           # schematic PDF, front / back PNG, bom.csv
```

`build.sh` refuses to run when `Senario.kicad_pcb` exists, because it **overwrites the schematic and any placement you did by hand**. Use it until you start moving parts in KiCad; from then on edit in KiCad (or export your placement before rebuilding).

Checks that pass on this version: ERC 0 violations; the schematic's netlist and the PCB pad nets are identical (`scripts/check_netlist.py`, 841 pads); DRC shows no placement errors, only the unrouted connections (499) and silkscreen warnings.
