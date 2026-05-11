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

11. Write breadboard.yaml — the machine-readable physical layout.

    Do NOT start until steps 7–10 have all passed.

    breadboard.yaml specifies every component placement and every jumper wire using the
    coordinate system defined in breadboard_validator.py (columns A–J, rows 1–63).

    Critical rules for writing breadboard.yaml:
    - A breadboard hole accepts exactly ONE lead or pin. Two items cannot share a hole.
    - Every jumper wire endpoint must be in a DIFFERENT hole from any component pin, even
      if that pin is in the same row-half (i.e. electrically the same node). Use an
      adjacent column in the same row-half for the wire — e.g. if GPIO4 is at A4, connect
      the wire to B4 (same node, free hole), NOT A4.
    - Compute the PCB body bounding box from board.json dimensions:
        bottom-row = last_pin_row + ceil((board_height - last_pin_y) / 2.54)
      No component may be placed inside this bounding box.
    - For the LDR voltage divider, the LDR and 10K resistor share one junction node but
      must NOT share a hole. Place them in adjacent columns of the same row (e.g. H29
      and G29) so they are electrically connected without occupying the same hole.

    Derived layout for ESP32-S3-DevKitC-1 (from board.json: height=70.057mm,
    last pin at y=61.007mm, pin-1 at y=7.667mm, 22 pins per side):
    - Left header: col A, rows 1–22
    - Right header: col I, rows 1–22
    - Body bounding box: rows 1–26, cols A–J  ← nothing else may go here

12. Run the breadboard validator (no token required, no quota):

        python3 breadboard_validator.py breadboard.yaml

    Zero errors required. Fix breadboard.yaml and re-run until it exits 0.
    This catches: occupied-hole wire conflicts, PCB body overlaps, oversized layouts.

13. Generate assembly.md from the validated breadboard.yaml.

    Because the layout passed step 12, every hole reference in assembly.md is
    provably unoccupied and accessible.

    assembly.md must contain:

    **Parts List** — every component including passives needed to replace simulation
    modules (e.g. LDR + 10K resistor to replace wokwi-photoresistor-sensor).

    **Breadboard primer** — rows 1–63, columns A–E / F–J, row-half connectivity rule,
    (+)/(−) rail convention.

    **ESP32-S3 Pin Reference Table** — all 44 pins (22 per side), exact holes, which are
    used. Warn that GPIO numbers do not correspond to row numbers.

    **Step-by-step assembly** — derived directly from breadboard.yaml:
      Part A — Place MCU board
      Part B — Set up power rails
      Part C — Light sensor (LDR + resistor, from breadboard.yaml component positions)
      Part D — Potentiometer
      Part E — LCD1602 (pin table showing exact E-column holes)
      Part F — Verification checklist (all 20 wires) and power-on test

    One action per step. Every hole reference must match breadboard.yaml exactly.
    After generating, cross-check: count wires in assembly.md == count in breadboard.yaml.

    Note on light sensor polarity: the physical LDR divider (3.3V → LDR → junction →
    10K → GND, ADC at junction) produces CORRECT behaviour (bright = high %). This
    differs from the Wokwi sensor module which had inverted output. No firmware change
    is needed.
