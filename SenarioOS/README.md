# SenarioOS

Firmware for the Senario Looper / MultiFX (Daisy Seed2 DFM, STM32H750).

Empty for now. The hardware's signal and pin map for the firmware is in [docs/pinmap.md](docs/pinmap.md) (generated from the hardware design, so it stays in step with the board).

Planned layout: libDaisy as a submodule (as in the other Daisy projects on this machine), `src/` for the instrument, a board layer for the pin map.
