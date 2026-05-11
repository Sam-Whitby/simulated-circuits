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

3.5. Build or update parts_library.yaml with physical specs for every component.

    For each component type that will appear in breadboard.yaml:
      a. Check if an entry already exists in parts_library.yaml.
      b. If not, fetch the component's datasheet or manufacturer specs online.
         Extract: body dimensions (mm), pin count, pin arrangement type, and
         exact pin-to-pin spacing.  Note the source URL.
      c. Add the entry following the format in the existing parts_library.yaml.
      d. Mark external_only: true for any component whose PCB body is too large
         to place on a standard 63-row breadboard alongside an ESP32-S3-DevKitC-1.

    The library is cached — run this step only for new component types.
    NEVER hard-code physical dimensions inside breadboard_validator.py.

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

11a. Write breadboard.yaml — the machine-readable physical layout.

    Do NOT start until steps 7–10 have all passed.

    breadboard.yaml specifies every component placement and every jumper wire using the
    coordinate system defined in breadboard_validator.py (columns A–J, rows 1–63).

    Critical rules for writing breadboard.yaml:
    - Every component must have a `type:` field matching an entry in parts_library.yaml.
    - A breadboard hole accepts exactly ONE lead or pin. Two items cannot share a hole.
    - Every jumper wire endpoint must be in a DIFFERENT hole from any component pin, even
      if that pin is in the same row-half (i.e. electrically the same node). Use an
      adjacent column in the same row-half for the wire.
    - Compute the PCB body bounding box from board.json dimensions:
        bottom-row = last_pin_row + ceil((board_height - last_pin_y) / 2.54)
      No component may be placed inside this bounding box.
    - For the LDR voltage divider, the LDR and 10K resistor share one junction node but
      must NOT share a hole. Place them in adjacent columns of the same row so they are
      electrically connected without occupying the same hole.
    - For any component marked external_only: true in parts_library.yaml, add it to the
      `external_components:` section (not `components:`). List its connection points so
      assembly.md can document the wiring.
    - For the potentiometer (2+1 pin type): rotate 90° so the two terminals are in the
      SAME COLUMN but different rows (2 rows apart), with the wiper 2 columns to the
      right in the middle row. This prevents the terminals from being shorted by the
      breadboard row-half connection.
    - Use `ext:component:PIN` as the wire `to:` endpoint for external component pins.
      These are skipped by the validator's hole-conflict check.

    Derived layout for ESP32-S3-DevKitC-1 (from board.json: height=70.057mm,
    last pin at y=61.007mm, pin-1 at y=7.667mm, 22 pins per side):
    - Left header: col A, rows 1–22
    - Right header: col I, rows 1–22
    - Body bounding box: rows 1–26, cols A–J  ← nothing else may go here

11b. Run the breadboard validator (no token required, no quota):

        python3 breadboard_validator.py breadboard.yaml

    The validator checks:
      (a) Hole occupancy conflicts — two pins in the same hole.
      (b) Wire endpoints in occupied holes.
      (c) Pin layout validation — declared pin positions must match the
          parts_library.yaml spacing for each component type.
      (d) Full body footprint overlap — uses library dimensions (not just the
          declared body box) so oversized components are caught even if the
          declared body is too small.
      (e) external_only flag — errors if an external-only component is placed
          on-board.
      (f) Breadboard capacity — layout must fit within 63 rows.

    Zero errors required. Fix breadboard.yaml and re-run until it exits 0.

11c. Generate assembly.md from the validated breadboard.yaml.

    Because the layout passed step 11b, every hole reference in assembly.md is
    provably unoccupied and physically accessible, and every component is in its
    correct physical position.

    assembly.md must contain:

    **Parts List** — every component including passives; note which components are
    connected externally (not placed on the breadboard).

    **Breadboard primer** — rows 1–63, columns A–E / F–J, row-half connectivity
    rule, (+)/(−) rail convention.

    **Potentiometer pin identification** — explain the 2+1 arrangement and the
    90° rotation required for breadboard use. Include the exact hole positions.

    **ESP32-S3 Pin Reference Table** — all 44 pins (22 per side), exact holes,
    which are used. Warn that GPIO numbers do not correspond to row numbers.

    **Step-by-step assembly** — derived directly from breadboard.yaml:
      Part A — Place MCU board
      Part B — Set up power rails
      Part C — Light sensor (LDR + resistor)
      Part D — Potentiometer (with rotation instructions)
      Part E — External component connections (e.g. LCD via jumper wires)
      Part F — Verification checklist (all wires) and power-on test

    One action per step. Every hole reference must match breadboard.yaml exactly.
    After generating, cross-check: count wires in assembly.md == count in breadboard.yaml.

    Note on light sensor polarity: the physical LDR divider (3.3V → LDR → junction →
    10K → GND, ADC at junction) produces CORRECT behaviour (bright = high %). This
    differs from the Wokwi sensor module which had inverted output. No firmware change
    is needed.
