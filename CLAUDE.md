# CLAUDE.md

Senario Looper / MultiFX, 24HP Eurorack, Daisy Seed2 DFM. See README.md and SenarioHW/docs/design-notes.md.

- **The KiCad project is generated**: `SenarioHW/Kicad/scripts/design.py` is the source (parts, nets, floorplan); `build.sh` writes the schematic and the PCB. It refuses to overwrite an existing `Senario.kicad_pcb` without `FORCE=1`, because that destroys hand placement. Change the design in `design.py`, not in the `.kicad_sch` files.
- After a rebuild run `scripts/check_netlist.py` (schematic vs PCB nets; needs KiCad's Python and `kicad-cli sch export netlist --format kicadxml`), ERC and DRC. The last good state: ERC 0, netlist 0 mismatches, DRC only unrouted + silkscreen.
- Symbol pin numbers must equal the footprint pad numbers, otherwise "Update PCB from Schematic" breaks the nets (that is why `Senario.kicad_sym` has `SW_Tact_LED_6pin` and `Jack_TRS`).
- `KicadLibs` is a submodule (private). A change there is two commits: in the submodule on a branch, then the pointer here. Never commit a pointer to a commit that is not pushed to KicadLibs' `main`.
- Nothing has been built or run on hardware: never claim a feature works.
