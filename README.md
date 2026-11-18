# SenarioEurorack

Senario Looper / MultiFX: a 24HP Eurorack module on a Daisy Seed2 DFM.

| Folder | What |
|---|---|
| [SenarioHW/](SenarioHW/README.md) | the hardware: KiCad project (schematic and primary placement), BOM, design notes |
| [SenarioOS/](SenarioOS/README.md) | the firmware (empty for now; the pin map is in `SenarioOS/docs/pinmap.md`) |
| `KicadLibs/` | git submodule: the shared KiCad libraries (private repository `omar-karray/KicadLibs`) |

## Clone

```bash
git clone --recurse-submodules https://github.com/omar-karray/SenarioEurorack.git
```

The submodule is private: you need access to `omar-karray/KicadLibs`. KiCad 10 resolves the libraries through the project's own tables (`${KIPRJMOD}/../../KicadLibs`), so no global set-up is needed for this project.

Start with [SenarioHW/docs/design-notes.md](SenarioHW/docs/design-notes.md).
