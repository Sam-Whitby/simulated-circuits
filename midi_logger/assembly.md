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

**ESP32 power source**: Connect a USB-C cable to the **COM port** (the USB-C
port on the ESP32-S3-DevKitC-1 connected to the on-board USB bridge chip).
Plug the other end into a computer or USB charger (≥ 500 mA).

**The ESP32-S3-DevKitC-1 has two USB-C ports:**

| Port | Label | Purpose |
|------|-------|---------|
| COM  | `COM` | Power in, serial monitor, firmware upload |
| OTG  | `USB` | USB host — receives MIDI data from keyboard |

> The keyboard USB cable carries **MIDI data only**.  It does **not** power
> the ESP32.  Always connect the COM port to power before use.
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

All commands must be run from the PlatformIO project directory.

```
cd /Users/samwhitby/Documents/PlatformIO/Projects/Test/midi_logger
```

> **Warning — `WOKWI_SIMULATION=1` is active.**  The current `platformio.ini`
> builds firmware that generates a **synthetic MIDI arpeggio** instead of
> reading from a real keyboard.
>
> To target real hardware, edit `platformio.ini`:
> 1. Remove `-DWOKWI_SIMULATION=1` from `build_flags`.
> 2. Add `-DARDUINO_USB_MODE=0` (enables native USB OTG host mode).
>
> Note: the full USB MIDI host driver is currently stubbed.
> See `src/main.cpp` for implementation notes.

### Upload

```
pio run --target upload
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
