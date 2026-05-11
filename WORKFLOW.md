Read COMPONENTS.md and CIRCUIT_SPEC.md.

You may:
- edit files
- run PlatformIO builds (`/Users/samwhitby/.platformio/penv/bin/pio run`)
- run Wokwi CLI lint (`~/.wokwi/bin/wokwi-cli lint`)
- run Wokwi simulations (`~/.wokwi/bin/wokwi-cli . --timeout ... --serial-log-file ...`)
- inspect serial logs
- iterate until the system works

Your goal:

1.  Read COMPONENTS.md and CIRCUIT_SPEC.md

2.  Fetch the Wokwi board file for the target MCU and extract exact pin names:
    https://raw.githubusercontent.com/wokwi/wokwi-boards/main/boards/{board-id}/board.json
    (board-id for ESP32-S3 DevKitC-1: esp32-s3-devkitc-1)

3.  Fetch docs for every non-trivial component and confirm part type + pin names:
    https://docs.wokwi.com/parts/{component-type}
    Cross-reference WOKWI_PARTS.md for physical → simulation component mapping.

4.  Design the circuit and generate diagram.json using verified pin names.

    IMPORTANT: Every diagram.json for ESP32-S3 (and similar USB-native boards) MUST
    include $serialMonitor connections or wokwi-cli will produce no serial output:

        ["esp:TX", "$serialMonitor:RX", "", []],
        ["esp:RX", "$serialMonitor:TX", "", []]

    Also add to platformio.ini to route Serial through hardware UART (not USB CDC):

        build_flags = -DARDUINO_USB_CDC_ON_BOOT=0

5.  Write firmware. Serial output must emit structured JSON on every sensor reading,
    e.g. {"raw":2048,"pct":50}. This is what the simulation tests assert against.

6.  Verify build passes:
    /Users/samwhitby/.platformio/penv/bin/pio run

7.  Lint the diagram (no token required):
    ~/.wokwi/bin/wokwi-cli lint
    Zero errors required. Info notices about undocumented board types are acceptable.

8.  Run boot smoke test (requires WOKWI_CLI_TOKEN):
    ~/.wokwi/bin/wokwi-cli . \
      --timeout 5000 \
      --serial-log-file /tmp/boot.log \
      --expect-text '"pct":'
    Must exit 0. If it times out, firmware or diagram has a fatal issue — fix before continuing.

9.  Write scenario.yaml to exercise the circuit across its input range.
    Use set-control to change sensor state (lux, temperature, etc.), then wait-serial
    to confirm the firmware responds correctly in the serial log.

10. Run scenario test (requires WOKWI_CLI_TOKEN):
    ~/.wokwi/bin/wokwi-cli . \
      --scenario scenario.yaml \
      --serial-log-file /tmp/sim.log \
      --timeout 10000
    Parse sim.log to assert values span the expected range.
    Fix firmware or diagram if assertions fail, then re-run from step 6.

11. Generate assembly.md — step-by-step physical breadboard assembly instructions.

    Do NOT produce this file until steps 7–10 have all passed.

    assembly.md must contain these four sections in order:

    **Parts List** — every component by name and quantity, including any passive components
    (resistors, etc.) needed to replace simulation modules with real-world equivalents.
    Note any voltage constraints.

    **Understanding the Breadboard** — briefly explain the coordinate system used throughout
    the document:
    - Rows numbered 1–63 (top to bottom)
    - Columns A–E (left of centre gap), F–J (right of centre gap)
    - Top power rail: (+) = 3.3 V, (−) = GND
    - Each hole referenced as ColumnRow, e.g. "A1", "J22"
    - Explain that holes in the same row-half are electrically connected

    **ESP32-S3 Pin Reference Table** — a table mapping every breadboard hole to its ESP32
    signal, for both the left header (column A) and right header (column I), rows 1–22.
    Mark which pins are used in the circuit with ✅. Warn explicitly that GPIO numbers do NOT
    correspond to row numbers (e.g. GPIO 8 is at row 12, not row 8).

    **Step-by-Step Assembly** — numbered steps grouped into labelled parts:
      Part A — Place the MCU board
      Part B — Set up power rails
      Part C — Light sensor (real-world voltage divider replaces simulation module)
      Part D — Potentiometer (LCD contrast)
      Part E — LCD1602 display (all 16 pins, with pin table showing hole assignments)
      Part F — Final check and power-on

    Rules for each step:
    - One action per step (place one component OR insert one wire)
    - Name the exact holes involved, e.g. "Insert one end into B4 and the other into D36"
    - Include the wire colour suggestion
    - After each group of steps, add a plain-English explanation of what that group achieves
      and how, so a first-time builder understands the purpose, not just the mechanics
    - Add a "Check:" note after any step where a mistake is hard to spot later
    - Conclude Part F with a complete wire-verification table (From → To → Colour → Purpose)
      and troubleshooting tips for the most common failure modes

    Physical layout to use (verified against board.json pin coordinates):
    - ESP32-S3 DevKitC-1: left header col A rows 1–22, right header col I rows 1–22
    - LDR + 10K resistor voltage divider: col H rows 24–26 (right half)
    - Potentiometer: col C rows 29–31 (left half)
    - LCD1602 16-pin header: col E rows 33–48 (left half, pin 1 at E33, pin 16 at E48)

    Note for the light sensor: the physical LDR+resistor divider (3.3V → LDR → junction →
    10K → GND, with ADC at the junction) produces CORRECT behaviour — bright light gives a
    high percentage. This is the opposite of the Wokwi sensor module, which had inverted
    output. No firmware change is needed.
