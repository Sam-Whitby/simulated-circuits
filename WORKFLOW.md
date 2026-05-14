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

11a. Write netlist.yaml — the machine-readable logical netlist.

    Do NOT start until steps 7–10 have all passed.

    netlist.yaml expresses the validated circuit from diagram.json in terms of physical
    component pins and named nets. It is the single source of truth for all physical
    assembly steps and is read by both breadboard_placer.py and p2p_layout.py.

    Format:
      components: list of {id, type, note, external: true (if too large for breadboard)}
      nets: list of {name, pins: [comp_id.pin_name, ...], rails: [rail:plus/rail:minus],
                     note: "..." (optional)}

    Every pin of every component must appear in exactly one net.
    Use rail:plus for 3.3V and rail:minus for GND.
    Mark large external components (e.g. LCD1602) with `external: true`.

11b. Run the breadboard placer (algorithmic layout — no guessing):

        python3 breadboard_placer.py netlist.yaml breadboard.yaml

    Exit 0 → breadboard.yaml written; proceed to 11c.
    Exit 2 → breadboard INFEASIBLE. Reason and suggestion are printed to stdout.
             Read the suggestion. Options:
               (a) Fix the issue (reassign GPIOs, reduce components, adjust
                   parts_library.yaml) and re-run from 11b.
               (b) Proceed to 11e for point-to-point assembly instead.
    Exit 1 → tool error (bad input); fix and re-run.

    The placer enforces all physical constraints by construction:
      • Hole occupancy — no two pins in the same hole
      • Wire endpoints — never inside a component body zone
      • Component body zones — no overlaps, no pins in foreign body zones
      • ESP32 body (rows 1–26, cols A–I) — nothing placed inside it
      • Right-header GPIOs (col I) tapped via col J (outside body — always accessible)
      • Left-header GPIOs (col A) connected via `pin:esp32.X` female jumpers
      • External components — listed in external_components: section, not placed on board
      • Breadboard capacity — all placements within 63 rows

11c. (Breadboard path) Run the validator — safety net:

        python3 breadboard_validator.py breadboard.yaml

    Zero errors required. The validator is a final safety check; if errors appear after
    the placer exits 0, that is a placer bug — report it.

    The validator checks:
      (a) Hole occupancy conflicts — two pins in the same hole
      (b) Wire endpoints in occupied holes
      (b2) Wire endpoints inside component body zones (WIRE IN BODY ZONE)
      (b3) Component pins inside foreign body zones (PIN IN FOREIGN BODY)
      (c) Pin layout validation — declared pin positions match parts_library.yaml spacing
      (d) Full body footprint overlap — library dimensions cross-checked against declared box
      (e) external_only flag — errors if an external-only component is placed on-board
      (f) Breadboard capacity — layout must fit within 63 rows
      (g) pin: wire endpoints — must reference a real declared component pin

11d. (Breadboard path) Generate assembly.md:

        python3 assembly_generator.py breadboard.yaml assembly.md

    Because the layout passed steps 11b and 11c, every hole reference in assembly.md is
    provably unoccupied and physically accessible, and every component is in its correct
    physical position. The generator is deterministic — no AI writes hole references.

    The generated assembly.md contains: parts list, breadboard primer, potentiometer
    orientation guide, ESP32 pin reference table, step-by-step wiring instructions,
    and a verification checklist. Wire count in assembly.md == wire count in breadboard.yaml.

11e. (P2P path — when breadboard is infeasible or user prefers it)
     Generate point-to-point wiring layout from the netlist:

        python3 p2p_layout.py netlist.yaml pointtopoint.yaml

    P2P assembly: no breadboard required. Components sit on a non-conductive surface.
    Connections are made with jumper wires directly lead-to-lead (or female-to-male
    for ESP32 header pins). Always feasible for any valid netlist.

    Exit 0 always (only check: NET_SHORT — rail:plus and rail:minus in same net → exit 2).

11f. (P2P path) Generate P2P assembly instructions:

        python3 assembly_generator.py --mode p2p pointtopoint.yaml assembly.md

    Produces step-by-step wire connection instructions for P2P assembly. Deterministic —
    all wire counts and connection descriptions derived from pointtopoint.yaml.

    Note on light sensor polarity: the physical LDR divider (3.3V → LDR → junction →
    10K → GND, ADC at junction) produces CORRECT behaviour (bright = high %). This
    differs from the Wokwi sensor module which had inverted output. No firmware change
    is needed.
