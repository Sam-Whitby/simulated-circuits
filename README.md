# Simulated Circuits

**AI-assisted embedded hardware design with autonomous closed-loop simulation and verification.**

This repository demonstrates a workflow in which an AI coding agent (Claude Code) designs, builds, simulates, and verifies working circuits entirely autonomously — including debugging and iterating — before producing assembly instructions for a human to wire up the physical hardware.

Two circuits are included:

| Circuit | Directory | Assembly mode | Description |
|---------|-----------|---------------|-------------|
| Ambient light sensor | `/` (root) | Breadboard | LDR voltage divider → ESP32-S3 ADC → LCD1602 percentage display |
| MIDI logger | `midi_logger/` | Point-to-point | Yamaha keyboard USB MIDI → ESP32-S3 → micro SD card JSON log |

---

## Table of Contents

1. [The Problem: AI Hallucination in Hardware Design](#the-problem-ai-hallucination-in-hardware-design)
2. [The Solution: Closed-Loop Simulation](#the-solution-closed-loop-simulation)
3. [How the Workflow Operates](#how-the-workflow-operates)
4. [Project Structure](#project-structure)
5. [Getting Started](#getting-started)
6. [The Ambient Light Sensor Circuit](#the-ambient-light-sensor-circuit)
7. [Fritzing and Visual Assembly Instructions](#fritzing-and-visual-assembly-instructions)
8. [Market Analysis](#market-analysis)
9. [Critical Analysis and Next Steps](#critical-analysis-and-next-steps)

---

## The Problem: AI Hallucination in Hardware Design

AI language models hallucinate. In software, hallucinations are quickly caught — the code either compiles and runs or it doesn't. In hardware design, hallucinations are expensive:

- A wrong component name in `diagram.json` produces no error — the wire just silently goes nowhere.
- An undocumented pin naming convention means the LCD powers on but displays nothing.
- An inverted ADC mapping means the sensor reads 0% in bright light and 100% in the dark.
- None of these errors produce a compiler warning. They only appear when a human looks at the physical device.

The traditional chatbot approach to hardware design is an inherently **open loop**:

```
AI writes code → Human builds circuit → Human reports failure → AI guesses fix → repeat
```

Each iteration requires a human to physically observe the device, describe what they saw, and wait for the AI to reason about what might have gone wrong. This is slow, imprecise, and error-prone. The AI is working from a verbal description of a failure, not from the actual error.

This project was itself built this way initially. The result was four rounds of user-reported failures before the circuit worked:

1. `esp:GPIO4` used — Wokwi requires `esp:4` (numeric, not GPIO-prefixed). Silent failure.
2. `wokwi-photoresistor` used — pins undocumented, ADC floated at 0V. Always 0%.
3. Replaced with `wokwi-photoresistor-sensor` — correct, but behaviour inverted.
4. `$serialMonitor` connections missing from `diagram.json` — CLI produced no serial output.

Every one of these failures could have been caught programmatically, without any human involvement.

---

## The Solution: Closed-Loop Simulation

The key insight is that embedded firmware and circuit diagrams are **testable artefacts** — just like software. The tools exist to run them headlessly and assert against their output. The missing piece was using those tools systematically.

This workflow replaces the open loop with a **closed loop**:

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                  │
│   Research ──► Design ──► Build ──► Lint ──► Simulate ──► Assert│
│       ▲                                                   │      │
│       └──────────────── iterate if fail ──────────────────┘      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

Each stage produces a machine-readable pass/fail result. The AI parses the result and iterates without human involvement. The human only receives the final verified output.

### What changes

| Traditional (open loop) | This workflow (closed loop) |
|---|---|
| AI reasons from memory about pin names | AI fetches the board file and reads exact names |
| Human reports "nothing displayed" | `wokwi-cli lint` flags unknown part type or disconnected pin |
| Human reports "always 0%" | Scenario test asserts pct > 50 at full lux; fails → AI investigates |
| Human reports "serial doesn't work" | Boot smoke test exits 42; AI reads error and fixes diagram |
| 4–6 human iterations | 0 human iterations before working circuit |

### Analogy to Claude Code for software

Claude Code is more effective than pasting code into ChatGPT because it can **execute**, observe the result, and iterate. It doesn't rely on the human to run the code and describe the error. This workflow applies exactly the same principle to hardware:

| Software (Claude Code) | Hardware (this workflow) |
|---|---|
| `npm run build` → compiler output | `pio run` → build output |
| Type checker output | `wokwi-cli lint` → diagram validation |
| Test runner output | `wokwi-cli --expect-text` → boot validation |
| Integration test suite | `wokwi-cli --scenario` → behavioural test |
| Parse error, fix, re-run | Parse failure, fix diagram/firmware, re-run |

The AI spends time **executing tools and reading structured output**, not reasoning verbally about what might be wrong. This is faster, cheaper (less AI time), and more reliable.

---

## How the Workflow Operates

The canonical workflow is defined in `WORKFLOW.md`. Here is what each step does and why it exists.

### Step 1 — Read specifications

Read `CIRCUIT_SPEC.md` (what the circuit must do) and `COMPONENTS.md` (what hardware is available). This is the only purely verbal reasoning step: translating requirements into a circuit design.

### Step 2 — Fetch board pin names

```bash
curl https://raw.githubusercontent.com/wokwi/wokwi-boards/main/boards/esp32-s3-devkitc-1/board.json
```

This eliminates the single most common hallucination: wrong pin names. The board file definitively lists every pin name. GPIO pins on the ESP32-S3-DevKitC-1 are numbered `"4"`, `"5"`, `"43"` — not `"GPIO4"`, `"GPIO5"`, `"GPIO43"`. Without fetching this file, the AI guesses based on training data that is often wrong.

### Step 3 — Fetch component documentation

```
https://docs.wokwi.com/parts/{component-type}
```

Confirms the exact Wokwi part type (e.g., `wokwi-photoresistor-sensor` not `wokwi-photoresistor`) and its pin names (VCC, GND, AO, DO). Cross-reference `WOKWI_PARTS.md` for physical→simulation component mapping.

### Step 4 — Design circuit and write diagram.json

Wire up the circuit using the verified pin names. For ESP32-S3, two non-obvious requirements apply:

```json
["esp:TX", "$serialMonitor:RX", "", []],
["esp:RX", "$serialMonitor:TX", "", []]
```

These `$serialMonitor` connections are mandatory for `wokwi-cli` to capture serial output. They are not documented prominently — this was discovered by reading the Wokwi CLI source code.

### Step 5 — Write firmware

Firmware must emit **structured serial output on every sensor reading**:

```
{"raw":1001,"pct":24}
```

This is the observable output that simulation tests assert against. A display-only firmware (LCD only, no serial) cannot be tested automatically.

### Step 6 — Build

```bash
/Users/samwhitby/.platformio/penv/bin/pio run
```

Catches: compile errors, missing libraries, type errors. If this fails, fix and re-run. Do not proceed until it passes.

### Step 7 — Lint the diagram

```bash
~/.wokwi/bin/wokwi-cli lint
```

Catches: unknown part types, unknown pin names, disconnected required pins. No token required. This is a static check that runs in milliseconds. **This alone would have caught every pin naming error in this project's initial version.**

### Step 8 — Boot smoke test

```bash
~/.wokwi/bin/wokwi-cli . \
  --timeout 5000 \
  --serial-log-file boot.log \
  --expect-text '"pct":'
```

Verifies: firmware boots, serial is captured, first reading is emitted within 5 seconds. Exit code 0 = pass. If this fails, the diagram or firmware has a fatal issue. Inspect `boot.log` to diagnose.

### Step 9 — Write scenario.yaml

A scenario exercises the circuit across its input range using programmatic component control:

```yaml
steps:
  - delay: 2500ms
  - set-control:
      part-id: ldr
      control: lux
      value: 50000        # bright light
  - delay: 1200ms
  - wait-serial: '"pct":'
  - set-control:
      part-id: ldr
      control: lux
      value: 10           # dark
  - delay: 1200ms
  - wait-serial: '"pct":'
```

This is the hardware equivalent of an integration test suite. It verifies that the circuit responds correctly across its operating range without any human interaction.

### Step 10 — Run scenario

```bash
~/.wokwi/bin/wokwi-cli . \
  --scenario scenario.yaml \
  --serial-log-file sim.log \
  --timeout 10000
grep '"pct"' sim.log
```

Parse the log. Assert that readings change as lux changes. If the sensor always reads 0%, the ADC is floating. If it never changes, the wiring is wrong. The AI fixes the specific identified problem and returns to Step 6.

### Step 3.5 — Build the physical component library

Before writing `breadboard.yaml`, every component type must have an entry in
`parts_library.yaml` with its exact body dimensions and pin-layout offsets.
The AI fetches each component's datasheet online (once) and records:

- Body dimensions in mm (width × height)
- Pin count and arrangement type (e.g., "2+1" for the ELEGOO potentiometer)
- Exact pin-to-pin spacing
- Whether the component is `external_only` (too large to place on a standard
  breadboard alongside an ESP32-S3-DevKitC-1)

The library is **cached** — the AI only fetches a component's specs once and
commits the result to `parts_library.yaml`.  No network access is needed for
subsequent runs.

### Step 11 — Assembly instructions (three sub-steps)

#### 11a — Write breadboard.yaml

A machine-readable layout file specifying every component placement and every
jumper wire.  Each component has a `type:` field matching `parts_library.yaml`.
Components whose type is `external_only: true` are declared in
`external_components:` instead of `components:`, with wire endpoints expressed
as `ext:id:PIN`.

#### 11b — Run the breadboard validator

```bash
python3 breadboard_validator.py breadboard.yaml
```

The validator catches five classes of physical error:

| Check | What it catches |
|-------|----------------|
| Hole conflict | Two pins assigned to the same hole |
| Wire in occupied hole | A jumper endpoint lands on a component pin |
| Pin layout mismatch | Declared pin positions don't match library spacing |
| Body footprint overlap | Full PCB body (from library) overlaps another component |
| External-only violation | A too-large component is placed on-board |

The validator uses **library-derived body footprints** rather than the
bounding box of pin holes — so an LCD module whose PCB extends 14 columns and
30 rows beyond its pins will be caught, even if only the pins were declared.

Zero errors required before proceeding.

#### 11c — Generate assembly.md

Only produced after 11b passes.  Because the layout was validated, every hole
reference in assembly.md is provably unoccupied and physically accessible.

---

## Project Structure

```
.
├── README.md                  # This file
├── DEPENDENCIES.md            # Tools, libraries, and services required
├── COMPONENTS.md              # Available physical hardware components
├── CIRCUIT_SPEC.md            # What this circuit must do (functional requirements)
├── WORKFLOW.md                # AI agent workflow prompt (copy into agent context)
├── WOKWI_PARTS.md             # Physical component → Wokwi simulation part mapping
│
├── parts_library.yaml         # Physical component specs (body size, pin layout)
├── breadboard_validator.py    # Physical-layout constraint checker
├── breadboard_placer.py       # Auto-places components into breadboard.yaml
├── p2p_layout.py              # Generates pointtopoint.yaml from netlist.yaml
├── assembly_generator.py      # Generates assembly.md from a validated layout
├── configure_firmware.py      # Switches platformio.ini between sim and hw modes
│
├── netlist.yaml               # Logical circuit connections (input to layout tools)
├── breadboard.yaml            # Breadboard placement + wiring (validated layout)
├── assembly.md                # Step-by-step build instructions (generated)
├── platformio.ini             # PlatformIO build config (sim mode by default)
├── wokwi.toml                 # Wokwi simulation configuration
├── diagram.json               # Wokwi circuit diagram
├── scenario.yaml              # Automated simulation test scenario
├── src/main.cpp               # ESP32-S3 Arduino firmware
│
└── midi_logger/               # Second circuit: USB MIDI → SD card logger
    ├── netlist.yaml           # MIDI logger logical connections
    ├── pointtopoint.yaml      # P2P wire list (generated from netlist.yaml)
    ├── assembly.md            # MIDI logger build instructions (generated)
    ├── platformio.ini         # MIDI logger PlatformIO config (sim mode by default)
    ├── diagram.json           # Wokwi circuit diagram
    ├── scenario.yaml          # Wokwi simulation scenario
    └── src/main.cpp           # MIDI logger firmware
```

### Key file relationships

```
CIRCUIT_SPEC.md    ──► drives ──► diagram.json + src/main.cpp
COMPONENTS.md      ──► constrains ──► diagram.json parts
WOKWI_PARTS.md     ──► maps to ──► diagram.json part types + pin names
scenario.yaml      ──► tests ──► src/main.cpp serial output
parts_library.yaml ──► validates ──► breadboard.yaml component types + body sizes
netlist.yaml       ──► drives ──► breadboard.yaml (via breadboard_placer.py)
                              └──► pointtopoint.yaml (via p2p_layout.py)
validated layout   ──► drives ──► assembly.md (via assembly_generator.py)
platformio.ini     ──► managed by configure_firmware.py (sim ↔ hw)
WORKFLOW.md        ──► instructs ──► AI agent (Claude Code)
```

---

## Getting Started

### Prerequisites

See `DEPENDENCIES.md` for full list. Minimum requirements:

- VS Code with PlatformIO and Wokwi extensions
- `wokwi-cli` installed and `WOKWI_CLI_TOKEN` set in your shell environment

### Install wokwi-cli

```bash
curl -L https://wokwi.com/ci/install.sh | sh
source ~/.zshrc
```

### Get a Wokwi CI token

1. Sign in at https://wokwi.com
2. Go to https://wokwi.com/dashboard/ci
3. Generate a new token
4. Add to `~/.zshrc`: `export WOKWI_CLI_TOKEN=<your-token>`

### Build the firmware

```bash
cd /path/to/this/repo
pio run
```

### Run all verification gates

```bash
# Lint diagram
wokwi-cli lint

# Boot smoke test (must exit 0)
wokwi-cli . --timeout 5000 --serial-log-file boot.log --expect-text '"pct":'

# Scenario test (must exit 0)
wokwi-cli . --scenario scenario.yaml --serial-log-file sim.log --timeout 10000
grep '"pct"' sim.log
```

All three must pass before trusting the assembly instructions below.

### Assemble and flash the physical circuit

Complete wiring and flashing instructions are in `assembly.md` (ambient light sensor) and `midi_logger/assembly.md` (MIDI logger). Each file covers:

1. Parts list
2. Step-by-step wiring (with hole references for breadboard, or pin-to-pin for P2P)
3. Power overview (which USB port to connect, what powers what)
4. Single-command firmware flashing (no manual file editing)
5. Serial monitor expected output

#### Firmware modes — `configure_firmware.py`

Each `platformio.ini` ships in Wokwi simulation mode. `configure_firmware.py`
switches between modes without any manual file editing:

```bash
# Flash MIDI logger to real hardware and restore simulation mode:
cd midi_logger
python3 ../configure_firmware.py hw && pio run --target upload && python3 ../configure_firmware.py sim

# Flash light sensor to real hardware (no mode change needed — no sim flags):
pio run --target upload

# Check current mode:
python3 configure_firmware.py status
```

**Components needed (ambient light sensor):** ESP32-S3 DevKitC-1, LCD1602, photoresistor (LDR), 10K resistor, potentiometer, breadboard, jumper wires.

**Photoresistor voltage divider:**

```
3.3V ── LDR ── (GPIO1/ADC) ── 10K ── GND
```

**LCD1602 (4-bit mode):**

| LCD pin | ESP32-S3 GPIO |
|---|---|
| VSS | GND |
| VDD | 3.3V |
| V0 | Potentiometer wiper |
| RS | GPIO4 |
| RW | GND |
| E | GPIO5 |
| D4 | GPIO6 |
| D5 | GPIO7 |
| D6 | GPIO8 |
| D7 | GPIO9 |
| A (backlight+) | 3.3V |
| K (backlight−) | GND |

**Potentiometer (contrast):** Connect across 3.3V and GND; wiper to LCD V0. Adjust until characters are visible.

**Note on voltage:** The LCD1602 is rated for 5V but runs at 3.3V in simulation and typically works at 3.3V in practice. For guaranteed reliability on the bench, power VDD from 5V and add 10K pull-downs on D4–D7, or use an I2C LCD backpack module which handles level-shifting internally.

---

## Fritzing and Visual Assembly Instructions

[Fritzing](https://fritzing.org) is an open-source electronics design tool that produces breadboard-view diagrams — step-by-step visual layouts that look like the physical breadboard you would use to assemble a circuit. The question is whether Fritzing could be added to this workflow to produce "LEGO manual" style assembly instructions automatically.

### What Fritzing provides

Fritzing has three views: schematic, PCB, and breadboard. The breadboard view is the relevant one — it renders a realistic top-down view of a solderless breadboard with components placed on it and colour-coded wires connecting them. When exported as a PDF or image, it is immediately useful as a build guide.

Fritzing can be scripted. Its parts library is stored in an SQLite database, and diagrams are stored as XML (`.fzz` files). A script could in principle read `diagram.json` and produce a Fritzing breadboard layout.

### What would be required

Converting from Wokwi `diagram.json` to Fritzing programmatically would require:

1. **Part mapping**: Each Wokwi part type (e.g., `wokwi-lcd1602`) must map to a Fritzing part (e.g., `LCD1602` from the Fritzing parts library). This is a lookup table problem, solvable.

2. **Position translation**: Wokwi uses pixel coordinates. Fritzing uses breadboard hole coordinates. Converting between them requires deciding where on the breadboard each component lands — a layout problem that is non-trivial to automate well.

3. **Wire routing**: Wokwi wires are abstract connections. Fritzing breadboard wires must follow specific physical paths. Auto-routing is possible but Fritzing's built-in auto-router is not reliable for complex circuits.

4. **Part availability**: Not all Wokwi parts have Fritzing equivalents. The `wokwi-photoresistor-sensor` module, for example, has no direct Fritzing counterpart. You would need to use the bare photoresistor + resistor and draw the voltage divider manually.

### Practical assessment

Fritzing is **not well-suited to full automation** in its current form. The tool was designed for human-driven layout, and its scripting API is limited. Key problems:

- **Maintenance state**: Fritzing moved to a paid model in 2016 and development has been slow. The open-source version is stale. Long-term sustainability is uncertain.
- **No CLI**: Fritzing has no headless/CLI mode for generating diagrams programmatically. It requires a running GUI application.
- **Layout quality**: Auto-generated Fritzing breadboard layouts tend to be cluttered and hard to follow. The value of a "LEGO manual" is in its clarity, which typically requires human curation.

### Better alternatives for this workflow

| Option | Pros | Cons |
|---|---|---|
| Wokwi GUI | Already exists, interactive, looks like real hardware | No CLI export of breadboard view |
| AI-generated step-by-step text | What this workflow already does (assembly instructions) | No visual |
| Fritzing scripted | Familiar tool, good visual quality if done well | No CLI, layout problem, maintenance risk |
| KiCad scripted | Professional, active, Python API | Steep learning curve, aimed at PCB not breadboard |
| Custom SVG generator | Full control, good output | Significant development work |
| Tinkercad | Good breadboard view, widely understood | No API, web-only |

The most practical near-term addition to this workflow is a **Python script that generates a Fritzing `.fzz` file** from `diagram.json` using the Fritzing XML format directly, without running the Fritzing GUI. This is technically feasible but is a non-trivial engineering project (~1–2 weeks of work).

For the purposes of this workflow, the assembly instructions produced in Step 11 (textual table with GPIO mappings + wiring description) are sufficient for experienced builders. Fritzing integration would primarily benefit beginners who need visual guidance.

---

## Market Analysis

### The existing market

**Electronics prototyping tools** is a mature, fragmented market. Key segments:

- **Hobbyist/maker**: Arduino, Raspberry Pi, ESP32 community. Enormous in volume, minimal willingness to pay. Dominated by free tools (Arduino IDE, PlatformIO, Tinkercad, Fritzing). Market size: ~$2B in hardware sales, but almost no revenue in software/tooling.

- **STEM education**: Schools, universities, maker spaces. Pays for structured curricula and tools. Key players: littleBits, Arduino Education, Adafruit. Software tools priced at $10–50/month per seat. Accessible market for a well-packaged product.

- **IoT product development**: Small companies and freelancers building connected products. Time is money; prototype cycles are expensive. Willing to pay for tools that compress development time. Market size: IoT devices market is ~$500B by 2030; tooling is a small fraction but the buyers are commercial.

- **Electronics consulting**: Freelancers helping clients build bespoke embedded systems. Currently rely on manual design → simulation → physical prototyping. A tool that compresses this cycle has clear value.

### Emerging markets

**AI-assisted hardware design** is genuinely nascent. As of 2025, no dominant player exists. Relevant trends:

- **AI for EDA (Electronic Design Automation)**: Large players like Cadence and Synopsys are adding AI to their tools, but these target chip design, not embedded systems prototyping. The hobbyist/IoT space is largely untouched.

- **Digital twin adoption**: Industrial IoT increasingly uses digital twins (simulation models of physical systems) before deploying hardware. Wokwi is a primitive form of this. The digital twin market is growing at ~60% CAGR.

- **Autonomous coding agents**: GitHub Copilot, Cursor, Claude Code — the market for AI that writes and verifies code autonomously is growing rapidly. This workflow extends that paradigm to hardware. The analogous market for hardware does not yet have a dominant product.

- **Low-code/no-code IoT**: Platforms like Node-RED, Losant, and AWS IoT Core are reducing the barrier to building connected systems. The missing layer is the hardware-side design: "describe what you want → receive a working verified circuit".

### Competitive landscape

| Player | Approach | Gap |
|---|---|---|
| Wokwi | Simulation tool | No AI integration, no CI workflow |
| Arduino Cloud | IDE + IoT platform | No simulation, limited AI |
| Tinkercad Circuits | Visual circuit builder | No AI, no verification loop |
| EasyEDA | Schematic/PCB tool | No simulation, limited AI |
| Altium/Cadence | Professional EDA | Aimed at chip design, not prototyping |
| ChatGPT/Claude (web) | Verbal circuit advice | Open loop, no execution |

No current product occupies the position: **"describe your circuit requirements → receive a verified working simulation and assembly instructions"**. This is the gap this workflow fills.

### Revenue models

| Model | Viability |
|---|---|
| SaaS subscription (per seat) | Viable for STEM education and IoT companies. ~$20–100/month |
| Usage-based (per simulation run) | Viable alongside free tier. Mirrors Wokwi's own model |
| Enterprise licensing | Viable for IoT product companies wanting on-premise |
| Open-source core + paid services | Community adoption driver, monetise on support/hosted service |
| Hardware bundles | Partner with component suppliers; generate circuits for specific kits |

### Key risks to the market opportunity

1. **Wokwi itself may add AI**: If Wokwi integrates an AI assistant with circuit generation and closed-loop testing, the core workflow of this project becomes a feature, not a product. Wokwi is well-positioned to do this.

2. **Component simulation coverage**: The value of the closed loop depends on the simulated behaviour matching the real hardware. Wokwi's component library is strong but not complete. Analog edge cases, motor driver behaviour, and RF components are poorly simulated.

3. **Simulation ≠ hardware**: A circuit that passes all simulation tests may still fail on the bench due to power supply noise, timing sensitivity, component tolerances, or assembly errors. The workflow reduces but does not eliminate the need for physical testing.

4. **AI model costs**: The closed-loop workflow consumes more AI API calls than a single-shot response (research, design, debug iterations). At scale, this is a cost to manage.

5. **Fragmentation**: The embedded systems world is fragmented across MCU families, frameworks, and toolchains. A workflow that works for ESP32/Arduino must be substantially reworked for STM32/Zephyr or NXP/FreeRTOS.

---

## Critical Analysis and Next Steps

### What is fragile or unexplored

**1. The `$serialMonitor` requirement is undocumented**

The single biggest latent failure mode is that Wokwi CLI requires explicit `$serialMonitor` connections in `diagram.json` to capture serial output. This is not stated clearly in any public documentation — it was discovered by reading the Wokwi CLI source code on GitHub. Any future project that omits these connections will produce no serial log, with no error message explaining why. This must be in `WORKFLOW.md` as a mandatory step.

**2. ESP32-S3 USB CDC mode requires a build flag**

The ESP32-S3 board forces `ARDUINO_USB_MODE=1` (native USB JTAG/CDC) in its PlatformIO board definition. Without `-DARDUINO_USB_CDC_ON_BOOT=0`, `Serial` routes through USB CDC, which Wokwi CLI does not capture. This is a per-board quirk. Other MCUs (regular ESP32, AVR) do not have this problem. Any new board requires a fresh investigation of which serial interface Wokwi captures.

**3. Scenario assertions are weak**

The current `scenario.yaml` only checks that `"pct":` appears in the serial log — it does not assert that the value is within an expected range. As a result, the test would pass even if the sensor read the same value regardless of lux (the test would have passed even when the sensor was broken). Proper assertions need a post-processing script that extracts numeric values from the log and checks ranges.

**4. Wokwi pin naming is not self-documenting**

The numeric pin name convention (`esp:4` not `esp:GPIO4`) is discovered by fetching the board file from GitHub. If the board file is wrong, out-of-date, or the convention differs by board family, the AI will produce wrong connections. `wokwi-cli lint` is the backstop, but lint only catches unknown pin names — not a wrong pin that happens to exist (e.g., connecting to GPIO8 when you meant GPIO4).

**5. The analog inversion is not caught**

The photoresistor sensor produces an inverted reading: 0% at full light, 100% in darkness. This is a firmware logic bug (wrong `map()` direction) that the scenario test does not catch, because the test only checks for presence of output, not correctness. A properly written test would assert:

```
after lux=50000: pct > 70
after lux=10: pct < 20
```

This requires a script that parses the JSON from `sim.log` and applies numeric assertions, not just text matching.

**6. Physical layout validation closes one important gap**

Assembly instructions used to contain hallucinated hole references: wires
directed into holes already occupied by component pins, and components placed
under the ESP32-S3 board body.  The addition of `parts_library.yaml` +
`breadboard_validator.py` closes this class of error:

- The validator knows the real body size of every component (from datasheet
  specs cached in `parts_library.yaml`) and checks full body overlap.
- The validator knows each component's pin layout and checks that declared hole
  positions match the physical spacing.
- Components too large to place on the breadboard (e.g., LCD1602A) are flagged
  `external_only` and must be declared in `external_components:` — attempting
  to place them on-board is a validator error.

What the validator still cannot catch: bad solder joints, pin swaps during
assembly, voltage level incompatibilities (LCD1602 is rated 5V; running at
3.3V is marginal), breadboard contact issues, and power supply noise.

**7. Wokwi free tier quota**

The free tier provides 50 simulation minutes per month. Each full scenario run consumes approximately 10–15 seconds. This is ~200 runs/month — adequate for individual use but a real constraint for automated CI pipelines or team use. Pro tier provides 2000 minutes/month.

### Recommended next steps

**Immediate (low effort):**

1. Strengthen scenario assertions with a Python post-processor that extracts `"pct"` values from `sim.log` and checks that they change in the expected direction across the lux range.

2. Add a `test/` directory with PlatformIO native unit tests for firmware logic (the `map()` calculation, display formatting). These run on the Mac in milliseconds and catch logic bugs before consuming Wokwi quota.

3. Add the `$serialMonitor` wiring and `-DARDUINO_USB_CDC_ON_BOOT=0` flag to `WORKFLOW.md` as mandatory boilerplate for ESP32-S3 projects.

**Medium term:**

4. Expand `WOKWI_PARTS.md` with pin names discovered from live Wokwi board file fetches, not manually maintained. A script that reads all Wokwi board JSON files from GitHub and builds the lookup table automatically.

5. Add Fritzing export: a Python script that converts `diagram.json` to a Fritzing `.fzz` file using the Fritzing XML format. Even a rough layout is more useful than no layout for beginners.

6. Add a multi-environment `platformio.ini` with a `native` env for unit tests and the existing `esp32-s3-devkitc-1` env for hardware builds.

**Longer term:**

7. Generalise `WORKFLOW.md` so it works for any MCU/board, not just ESP32-S3. This requires parametrising the board file fetch, the serial configuration, and the Wokwi component lookup.

8. Explore physical hardware validation: flash the firmware to real hardware, read its serial port, and assert the same JSON output that the simulation produces. This would close the gap between simulation and physical behaviour.

9. Investigate GitHub Actions integration: run `wokwi-cli lint`, boot test, and scenario test automatically on every push. This makes the verification loop part of CI/CD, not just a local development step.

### The principle to preserve

The defining property of this workflow — the thing that makes it different from a chatbot — is that **AI reasoning is minimised in favour of AI execution**. Every decision that can be made by fetching a document, running a build, or parsing a log should be made that way. Verbal AI reasoning is slow, expensive, and unreliable. Execution is fast, cheap, and deterministic.

The worst failure mode for this workflow is an AI agent that skips the research steps and instead reasons from memory about pin names and component types. Every shortcut taken in the execution phase reintroduces the hallucination risk that the workflow is designed to eliminate.

The test of whether any change to the workflow is an improvement is simple: does it reduce the number of decisions the AI makes by reasoning, and increase the number of decisions made by executing and reading results?
