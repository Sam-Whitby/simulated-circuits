# Assembly Instructions — MIDI Logger — ESP32-S3 USB host + Micro SD Card


> **Generated deterministically from a validated `breadboard.yaml` layout.**
> Every hole reference was verified by `breadboard_validator.py`.


---


## Parts List

| Qty | Component | Notes |
|-----|-----------|-------|
| 1 | ESP32-S3-DevKitC-1 | The microcontroller board |
| 1 | Micro SD card SPI reader module | Connected via 6 jumper wires — does NOT sit on the breadboard |
| 1 | Full-size breadboard (830 points, 63 rows) | |
| — | Jumper wires (8 male-to-male + 2 female-to-male) | Assorted colours |
| 1 | USB-C cable | To power the ESP32 and upload firmware |

---


## Breadboard Primer

A full-size breadboard has:
- **Rows 1–63**, numbered from top to bottom.
- **Columns A–J**, labelled across each row.
- A **centre gap** that splits each row into two independent halves:
  - Left half: columns A–E (all five holes in the same row are connected).
  - Right half: columns F–J (same rule — connected within the half).
- **Power rails** running the full length on each side: `(+)` and `(−)`.

**The one-hole-one-pin rule**: each hole holds exactly one lead or one wire pin.
If a component occupies A4, a wire to the same node must use a different free
hole in the same row-half.

**The ESP32 body rule**: the ESP32-S3-DevKitC-1 PCB physically covers
**rows 1–26, columns A–I**.  Only the actual header pin holes (A1–A22 and
I1–I22) are accessible in this zone.  For left-header pins with no free
adjacent hole, use a female-to-male jumper wire plugged directly onto the
exposed pin above the PCB board.  For right-header GPIO pins, use column J
(same right-half row — J is outside the PCB body and always accessible).

---


## ESP32-S3 Pin Reference

GPIO numbers do **not** equal row numbers (e.g. GPIO8 is at row 12).
The board body covers **rows 1–26, cols A–I** — only the header pin holes
and col J (outside body) are accessible in that zone.

| Row | Left (col A) | Used? | Row | Right (col I) | Used? |
|-----|-------------|-------|-----|--------------|-------|
| 1 | **3V3.1** | VCC_3V3 | 1 | GND.2 | — |
| 2 | 3V3.2 | — | 2 | TX | — |
| 3 | RST | — | 3 | RX | — |
| 4 | 4 | — | 4 | 1 | — |
| 5 | 5 | — | 5 | 2 | — |
| 6 | 6 | — | 6 | 42 | — |
| 7 | 7 | — | 7 | 41 | — |
| 8 | 15 | — | 8 | 40 | — |
| 9 | 16 | — | 9 | 39 | — |
| 10 | **17** | SD_CS | 10 | **38** | SD_CS |
| 11 | **18** | SD_MISO | 11 | **37** | SD_MISO |
| 12 | **8** | SD_SCK | 12 | **36** | SD_SCK |
| 13 | **3** | VCC_3V3 | 13 | **35** | SD_MOSI |
| 14 | 46 | — | 14 | 0 | — |
| 15 | 9 | — | 15 | 45 | — |
| 16 | 10 | — | 16 | 48 | — |
| 17 | 11 | — | 17 | 47 | — |
| 18 | 12 | — | 18 | 21 | — |
| 19 | 13 | — | 19 | 20 | — |
| 20 | 14 | — | 20 | 19 | — |
| 21 | 5V | — | 21 | GND.3 | — |
| 22 | **GND.1** | GND | 22 | GND.4 | — |

---


## Step-by-Step Assembly

Work in order. Complete each step before moving on.


---


### Part A — Place the ESP32-S3 board

**A1.** Orient the breadboard with row 1 at the top.

**A2.** Hold the ESP32-S3-DevKitC-1 with the USB-C port facing away from you.

**A3.** Press the board firmly into the breadboard so that:
- The left header pins go into **column A, rows 1–22**.
- The right header pins go into **column I, rows 1–22**.
- The board straddles the centre gap.

The board PCB covers rows 1–26, cols A–I.  Do not place anything in that zone.
Column J (rows 1–22) is outside the board body and accessible for wiring.


### Part B — Set up the power rails


**B1.** Take a **gray female-to-male** jumper wire.  Plug the **female (socket) end** directly onto the ESP32 header pin `3V3.1` (the pin protrudes above the PCB).  Insert the **male end** into the (+) power rail.

**B2.** Take a **gray female-to-male** jumper wire.  Plug the **female (socket) end** directly onto the ESP32 header pin `GND.1` (the pin protrudes above the PCB).  Insert the **male end** into the (−) power rail.

**B3.** Take a **gray** jumper wire.  Insert one end into sdcard module pin VCC.  Connect the other end to the (+) power rail.

**B4.** Take a **gray** jumper wire.  Insert one end into sdcard module pin GND.  Connect the other end to the (−) power rail.


### Part C — External component connections


**Micro SD card SPI reader module** (`sdcard`) — connect via jumper wires:


| Module pin | Connect to | Wire colour | Purpose |

|------------|------------|-------------|---------|

| VCC | (+) power rail | — | power |

| GND | (−) power rail | — | power |

| VCC | the (+) power rail | gray | SD_VCC |

| GND | the (−) power rail | gray | SD_GND |

| MOSI | hole J13 (row 13, right half) | gray | SD_MOSI |

| MISO | hole J11 (row 11, right half) | gray | SD_MISO |

| SCK | hole J12 (row 12, right half) | gray | SD_SCK |

| CS | hole J10 (row 10, right half) | gray | SD_CS |





### Part D — Verification checklist and power-on test


Verify all wires before applying power:


| # | From | To | Colour | Purpose |

|---|------|----|--------|---------|

| 1 | ESP32 pin 3V3.1 (female) | (+) rail | gray | VCC_3V3 |

| 2 | ESP32 pin GND.1 (female) | (−) rail | gray | GND |

| 3 | sdcard pin VCC | (+) rail | gray | SD_VCC |

| 4 | sdcard pin GND | (−) rail | gray | SD_GND |

| 5 | J13 | sdcard pin MOSI | gray | SD_MOSI |

| 6 | J11 | sdcard pin MISO | gray | SD_MISO |

| 7 | J12 | sdcard pin SCK | gray | SD_SCK |

| 8 | J10 | sdcard pin CS | gray | SD_CS |


**Power-on checklist:**


1. Confirm all wires are connected as above.

2. Connect the USB-C cable to the ESP32.

3. Open a serial monitor at 115200 baud.

4. Confirm you see {"status":"SD_OK"} or {"status":"SD_FAIL"}.

5. Connect the keyboard via USB cable → Mepsies OTG adapter → ESP32 USB port.

6. Play a note — a JSON line with "note": should appear in the serial log.