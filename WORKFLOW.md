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

11. Produce assembly instructions and explain all wiring.
    Only do this after all simulation tests pass.
