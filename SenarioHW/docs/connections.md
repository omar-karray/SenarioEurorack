# Senario wiring map (2026-11-22)

What connects to the Daisy Seed2 DFM, as the spec stands (`spec-beta.md`). Mermaid: GitHub renders it, VS Code needs a Mermaid preview extension. **Dashed red boxes are decisions still open** (the op-amp stages). Nothing is built.

## Signals

```mermaid
flowchart LR
  subgraph SEED["DAISY SEED2 DFM"]
    A_CODEC["Onboard codec<br/>audio in 1-2 · out 1-2"]
    A_SAI["SAI2<br/>D24 MCLK · D25 SD_B · D26 SD_A<br/>D27 FS · D28 SCK"]
    A_I2C["I2C1<br/>D11 SCL · D12 SDA"]
    A_INT["D23 I2C_INT"]
    A_ADC["ADC D15<br/>POT_MUX"]
    A_CVI["ADC D17 · D18 · D21 · D31<br/>CV in 1 to 4"]
    A_GI["GPIO in<br/>D19 gate 1 · D32 gate 2<br/>D0 clock"]
    A_GO["GPIO out<br/>D20 gate 1 · D22 gate 2<br/>D16 clock"]
    A_UART["USART1<br/>D13 TX · D14 RX"]
    A_USB["USB HS<br/>D29 D- · D30 D+"]
    A_SD["SDMMC1 4-bit<br/>D1 DAT3 · D2 DAT2 · D3 DAT1<br/>D4 DAT0 · D5 CMD · D6 CLK"]
    A_SPI["SPI1<br/>D8 SCK · D10 MOSI · D7 DC"]
    A_LED["D9 LED_DATA"]
  end

  %% inputs come in from the left
  JCVI["Jacks<br/>CV in 1-4"] --> OPCI["Op-amp stage<br/>to decide<br/>+-5 V to 3.3 .. 0 V"] --> A_CVI
  JGI["Jacks<br/>gate in 1-2 · clock in"] --> GST["Transistor stage<br/>inverting"] --> A_GI
  PANEL["7 panel analogs<br/>2 PTL20 · Alps slider<br/>2 tall trim pots · 2 Alpha pots"] --> MUX["74HC4051<br/>mux"] --> A_ADC

  %% audio
  A_CODEC <--> FE1["Op-amp stage<br/>to decide"] <--> J1["Jacks<br/>audio in 1-2 · out 1-2"]
  A_SAI <--> PCM["PCM3060 codec"] <--> FE2["Op-amp stage<br/>to decide"] <--> J2["Jacks<br/>audio in 3-4 · out 3-4"]

  %% outputs go out to the right
  A_GO --> GBUF["0 / 5 V buffers"] --> JGO["Jacks<br/>gate out 1-2 · clock out"]
  A_UART <--> MIDI["MIDI<br/>opto in · 3.3 V out"] <--> JMIDI["MIDI jacks TRS<br/>in · out"]
  A_USB <--> ESD["USBLC6 ESD<br/>2 x 5K1 on CC"] <--> USBC["USB-C<br/>Hroparts D-15C"]
  A_SD <--> SDS["microSD slot<br/>vertical Yamaichi<br/>47K pull-ups"]
  A_SPI --> OLED["OLED 0.96 in<br/>CS tied low"]
  A_LED --> LS["74AHCT1G125<br/>level shifter"] --> SK["8 x SK6812<br/>under the MX keys"]

  %% the I2C bus
  A_I2C <--> BUS(("I2C bus"))
  BUS <--> IO1["MCP23017 0x20"]
  BUS <--> IO2["MCP23017 0x21"]
  BUS <--> IO3["MCP23017 0x22"]
  BUS <--> PCA1["PCA9685 0x40"]
  BUS <--> PCA2["PCA9685 0x41"]
  BUS <--> DAC["MCP4728 DAC<br/>4 ch 12-bit"]
  IO1 & IO2 & IO3 -.->|"open-drain INT"| A_INT
  SW["30 switch inputs<br/>4 Bourns encoders A B push<br/>10 RGB buttons · 8 MX keys"] --> IO1
  SW --> IO2
  IO3 -->|"selects A B C"| MUX
  IO3 -.->|"RES"| OLED
  IO3 -.->|"LED_OE"| PCA1
  IO3 -.->|"LED_OE"| PCA2
  PCA1 & PCA2 --> LEDS["32 LED channels<br/>10 RGB buttons = 30<br/>2 PTL20 lever LEDs"]
  DAC --> OPCO["Op-amp stage<br/>to decide<br/>gain about 2.44 for 0-5 V"] --> JCVO["Jacks<br/>CV out 1-2"]

  classDef seed fill:#dbe7ff,stroke:#3b5bdb,color:#10204a
  classDef jack fill:#e3f4ea,stroke:#2b8a3e,color:#0f2e1a
  classDef chip fill:#f1f3f5,stroke:#868e96,color:#1a1b1e
  classDef tbd fill:#fff5f5,stroke:#c92a2a,stroke-dasharray:4 3,color:#5c0f0f
  classDef ctl fill:#fff0d9,stroke:#d9730d,color:#3a2105
  class A_CODEC,A_SAI,A_I2C,A_INT,A_ADC,A_CVI,A_GI,A_GO,A_UART,A_USB,A_SD,A_SPI,A_LED seed
  class JCVI,JGI,J1,J2,JGO,JMIDI,USBC,JCVO,SDS,OLED jack
  class PCM,MUX,GST,GBUF,MIDI,ESD,LS,IO1,IO2,IO3,PCA1,PCA2,DAC,BUS chip
  class OPCI,FE1,FE2,OPCO tbd
  class PANEL,SW,LEDS,SK ctl
```

Inputs enter from the left, outputs leave to the right. Orange = the controls and what they drive, green = what the player touches (jacks, USB-C, microSD, OLED), grey = chips.

## Power

```mermaid
flowchart LR
  EURO["Eurorack 10-pin header<br/>+12 V · GND · -12 V"] --> PROT["Schottky + ferrite + caps<br/>on each rail"]
  PROT -->|"+12 V"| LDO["LD1117 5 V<br/>+ ferrite + 10 uF"]
  PROT -->|"+12 V"| BUCK["AP63205 step-down<br/>5 V, 2 A"]
  PROT -->|"+12 V"| VIN["Seed VIN<br/>2 x 3R3 + 2 x 100 uF"]
  PROT -->|"-12 V"| REF["LM4040<br/>-10 V reference"]
  PROT -->|"+12 V / -12 V"| OPA["Op-amp stages<br/>to decide"]
  LDO --> A5["+5V analog<br/>PCM3060 analog · gate-out buffers"]
  BUCK --> L5["+5V_LED<br/>10 RGB button anodes<br/>PTL20 LEDs · 8 SK6812"]
  REF --> CVO["CV in offset"]
  VIN --> SEED["DAISY SEED2 DFM"]
  SEED -->|"3V3_D"| D3["Expanders · PCA9685 · OLED<br/>MIDI · PCM3060 digital · MCP4728"]
  SEED -->|"3V3_A"| A3["Mux · panel pots"]

  classDef rail fill:#fff0d9,stroke:#d9730d,color:#3a2105
  classDef seed fill:#dbe7ff,stroke:#3b5bdb,color:#10204a
  classDef chip fill:#f1f3f5,stroke:#868e96,color:#1a1b1e
  classDef tbd fill:#fff5f5,stroke:#c92a2a,stroke-dasharray:4 3,color:#5c0f0f
  class EURO,PROT,LDO,BUCK,VIN,REF rail
  class SEED seed
  class A5,L5,CVO,D3,A3 chip
  class OPA tbd
```
