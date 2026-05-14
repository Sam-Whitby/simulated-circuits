# Assembly Instructions — MIDI Logger — ESP32-S3 USB host + Micro SD Card (Point-to-Point)

> **Generated deterministically from `pointtopoint.yaml`.**
> No breadboard required.

---

## Overview

Point-to-point (P2P) wiring connects component leads directly with jumper wires — no breadboard is used.  Lay the ESP32 flat on a non-conductive surface (foam, cardboard, or a silicone mat).  Keep wires short and label or colour-code them to match this guide.

For junction nodes (nets with 3 or more endpoints), the first endpoint listed is the hub: additional wires daisy-chain from that hub wire.

In P2P mode the ESP32 is NOT inserted into a breadboard, so left-header pins are accessible: plug female-to-male jumper wires directly onto the pin stubs that protrude below the underside of the PCB.

---

## Power

**The ESP32-S3-DevKitC-1 has two USB-C ports:**

| Port | Silk label | Purpose |
|------|------------|---------|
| COM  | `COM`      | Power in + serial/programming (CH340 bridge) |
| USB  | `USB`      | USB host — receives MIDI data from keyboard  |

**Always power via COM.** The USB port carries keyboard data only — it does
not power the board.

> **LED behaviour is normal:** plugging into the USB (OTG) port lights the red
> LED as the USB host driver initialises; plugging into the COM port may show
> no LED — the CH340 bridge has a separate power path.  Both states are correct.

**For programming (one cable):** COM → computer.

**For standalone operation (two cables simultaneously):**

| Cable | From | To |
|-------|------|----|
| Power | COM port | USB power bank (≥ 500 mA) |
| MIDI data | USB port | MIDI keyboard |

---

## Wire-by-Wire Assembly

Total wires to connect: **6**


### Net: VCC_3V3

**Step 1.** Take a **red** jumper wire.
- Connect one end to: **esp32.3V3 (left header, pin 1 — top-left)** — female end onto ESP32 header pin: 3V3 (left header, pin 1 — top-left)
- Connect the other end to: **sdcard.VCC** — sdcard external — connect to VCC header pin
- _Purpose: 3.3 V directly from ESP32 left-header pin 3V3.1 to SD card VCC (P2P; no rail)_


### Net: GND

**Step 2.** Take a **black** jumper wire.
- Connect one end to: **esp32.GND (left header, pin 22 — bottom-left)** — female end onto ESP32 header pin: GND (left header, pin 22 — bottom-left)
- Connect the other end to: **sdcard.GND** — sdcard external — connect to GND header pin
- _Purpose: Ground directly from ESP32 left-header pin GND.1 to SD card GND (P2P; no rail)_


### Net: SD_MOSI

**Step 3.** Take a **yellow** jumper wire.
- Connect one end to: **esp32.GPIO35 (right header, pin 13)** — female end onto ESP32 header pin: GPIO35 (right header, pin 13)
- Connect the other end to: **sdcard.MOSI** — sdcard external — connect to MOSI header pin
- _Purpose: SPI data host→card (GPIO35, right header I13, tap J13)_


### Net: SD_MISO

**Step 4.** Take a **blue** jumper wire.
- Connect one end to: **esp32.GPIO37 (right header, pin 11)** — female end onto ESP32 header pin: GPIO37 (right header, pin 11)
- Connect the other end to: **sdcard.MISO** — sdcard external — connect to MISO header pin
- _Purpose: SPI data card→host (GPIO37, right header I11, tap J11)_


### Net: SD_SCK

**Step 5.** Take a **green** jumper wire.
- Connect one end to: **esp32.GPIO36 (right header, pin 12)** — female end onto ESP32 header pin: GPIO36 (right header, pin 12)
- Connect the other end to: **sdcard.SCK** — sdcard external — connect to SCK header pin
- _Purpose: SPI clock (GPIO36, right header I12, tap J12)_


### Net: SD_CS

**Step 6.** Take a **orange** jumper wire.
- Connect one end to: **esp32.GPIO38 (right header, pin 10)** — female end onto ESP32 header pin: GPIO38 (right header, pin 10)
- Connect the other end to: **sdcard.CS** — sdcard external — connect to CS header pin
- _Purpose: SPI chip-select (GPIO38, right header I10, tap J10)_


---

## Verification

1. Trace every wire against the list above before powering on.
2. Confirm no two wires share the same two endpoints (no duplicates).
3. Verify all junction nodes have their hub wire connected before adding spoke wires.
4. Connect USB-C and verify the system starts up correctly.

---

## Firmware

All commands run from the project directory:

```
cd /Users/samwhitby/Documents/PlatformIO/Projects/Test/midi_logger
```

> The firmware is currently configured for **Wokwi simulation**
> (`-DWOKWI_SIMULATION=1`).  The commands below switch modes automatically.

### Flash to real hardware

```
python3 ../configure_firmware.py hw && pio run --target upload && python3 ../configure_firmware.py sim
```

Switches to hardware mode → uploads → restores simulation mode.

> Note: the full USB MIDI host driver is currently stubbed.
> See `src/main.cpp` for implementation notes.

### Switch mode manually

```
python3 ../configure_firmware.py hw      # real hardware (USB OTG enabled)
python3 ../configure_firmware.py sim     # Wokwi simulation
python3 ../configure_firmware.py status  # show current mode
```

### Monitor

```
pio device monitor --baud 115200
```

Expected serial output after successful SD initialisation:

```json
{"status":"SD_OK"}
{"t":12345,"note":60,"vel":64,"type":"noteOn","ch":1}
```

If the SD card is absent or fails you will see `{"status":"SD_FAIL"}` instead.
