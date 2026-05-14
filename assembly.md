# Assembly Instructions — Ambient light sensor — ESP32-S3 + LDR voltage divider + LCD1602


> **Generated deterministically from a validated `breadboard.yaml` layout.**
> Every hole reference was verified by `breadboard_validator.py`.


---


## Parts List

| Qty | Component | Notes |
|-----|-----------|-------|
| 1 | ESP32-S3-DevKitC-1 | The microcontroller board |
| 1 | GL5528 LDR (photoresistor) | Any 5 mm LDR works |
| 1 | 10 KΩ resistor (brown-black-orange) | Pull-down for the voltage divider |
| 1 | 10 KΩ potentiometer (B10K) | **2+1 pin type** — two terminals on one side, wiper on the other |
| 1 | LCD1602A (16-pin parallel) | Connected via wires — does NOT sit on the breadboard |
| 1 | Full-size breadboard (830 points, 63 rows) | |
| — | Jumper wires (18) | Assorted colours |
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
I1–I22) are accessible in this zone.  Left-header pins (col A, rows 1–22)
have no adjacent free hole — columns B–E in those rows are blocked by the
PCB body.  For right-header GPIO pins, use column J (same right-half row —
J is outside the PCB body and always accessible).

**Left-header connections**: the `parts_library.yaml` `header_info.left.tap_method`
field determines whether left-header pins can be tapped.  If `"none"` (the
default for this board variant), circuits that require left-header connections
must use point-to-point (P2P) assembly instead of a breadboard.

---


## Potentiometer Pin Identification

The potentiometer has **three pins in a 2+1 arrangement**: two terminal pins
on one face, one wiper pin on the opposite face.

1. Hold the pot with the shaft pointing up and the pins facing down.
2. On **one face** you will see **two pins** side by side — these are the terminals.
3. On the **opposite face** you will see **one pin** in the centre — the wiper.

Rotate the pot **90°** so the two terminals sit in the **same column but
different rows** (2 rows apart), with the wiper 2 columns to the right.

| Pin | Hole | Function |
|-----|------|---------|
| GND terminal (top) | C33 | → power rail (−) |
| VCC terminal (bottom) | C35 | → power rail (+) |
| Wiper | E34 | → LCD contrast wire |

---


## ESP32-S3 Pin Reference

GPIO numbers do **not** equal row numbers (e.g. GPIO8 is at row 12).
The board body covers **rows 1–26, cols A–I** — only the header pin holes
and col J (outside body) are accessible in that zone.

| Row | Left (col A) | Used? | Row | Right (col I) | Used? |
|-----|-------------|-------|-----|--------------|-------|
| 1 | **3V3.1** | ESP32 GND (right header row 1) → (-) pow | 1 | **GND.2** | ESP32 GND (right header row 1) → (-) pow |
| 2 | 3V3.2 | — | 2 | TX | — |
| 3 | RST | — | 3 | RX | — |
| 4 | **4** | LDR junction → ESP32 GPIO1 (ADC input) | 4 | **1** | LDR junction → ESP32 GPIO1 (ADC input) |
| 5 | **5** | GPIO2 → LCD RS (pin 4, data/command sele | 5 | **2** | GPIO2 → LCD RS (pin 4, data/command sele |
| 6 | **6** | GPIO42 → LCD Enable (pin 6) | 6 | **42** | GPIO42 → LCD Enable (pin 6) |
| 7 | **7** | GPIO41 → LCD D4 (pin 11) | 7 | **41** | GPIO41 → LCD D4 (pin 11) |
| 8 | **15** | GPIO40 → LCD D5 (pin 12) | 8 | **40** | GPIO40 → LCD D5 (pin 12) |
| 9 | **16** | GPIO39 → LCD D6 (pin 13) | 9 | **39** | GPIO39 → LCD D6 (pin 13) |
| 10 | **17** | GPIO38 → LCD D7 (pin 14) | 10 | **38** | GPIO38 → LCD D7 (pin 14) |
| 11 | 18 | — | 11 | 37 | — |
| 12 | 8 | — | 12 | 36 | — |
| 13 | 3 | — | 13 | 35 | — |
| 14 | 46 | — | 14 | 0 | — |
| 15 | 9 | — | 15 | 45 | — |
| 16 | 10 | — | 16 | 48 | — |
| 17 | 11 | — | 17 | 47 | — |
| 18 | 12 | — | 18 | 21 | — |
| 19 | 13 | — | 19 | 20 | — |
| 20 | 14 | — | 20 | 19 | — |
| 21 | 5V | — | 21 | GND.3 | — |
| 22 | GND.1 | — | 22 | GND.4 | — |

---


## Power

> **Warning — (+) power rail has no source.**
>
> This layout uses the (+) breadboard power rail but contains no wire that
> feeds 3.3 V into the rail.  The ESP32-S3's 3V3 pins (A1, A2) are on the
> left header where `tap_method = 'none'` — they cannot be tapped from the
> breadboard.  You must connect an external 3.3 V supply to the (+) rail
> before powering on, or rebuild this circuit in point-to-point (P2P) mode.

**ESP32 power source**: Connect a USB-C cable to the **COM port** (marked
`COM` on the board — this is the CH340 USB bridge port, not the USB OTG port).
Plug the other end into a computer or USB charger (≥ 500 mA).

---


## Step-by-Step Assembly

Work in order. Complete each step before moving on.


---


### Part A — Place the ESP32-S3 board

**A1.** Orient the breadboard with row 1 at the top.

**A2.** Hold the ESP32-S3-DevKitC-1 with: USB-C port facing away from row 1 (the top of the breadboard).

**A3.** Press the board firmly into the breadboard so that:
- The left header pins go into **column A, rows 1–22**.
- The right header pins go into **column I, rows 1–22**.
- The board straddles the centre gap.

The board PCB covers rows 1–26, cols A–I.  Do not place anything in that zone.
Column J (rows 1–22) is outside the board body and accessible for wiring.


### Part B — Set up the power rails


**B1.** Take a **black** jumper wire.  Insert one end into hole J1 (row 1, right half).  Connect the other end to the (−) power rail.


### Part C — Light sensor (LDR voltage divider)


The LDR and 10 KΩ resistor form a voltage divider.  The ESP32 reads the midpoint.

**C1.** Bend both leads straight down so tips are one row apart (2.54 mm) for vertical insertion.  Insert into **H28** and **H29** (either lead, LDR has no polarity).

**C2.** Bend the 10 KΩ resistor leads for vertical insertion.  Insert **lead-1 into G29**, **lead-2 into G31**.
  (G29 is in the same right-half row as H29 — they are connected.)


**C3.** Take a **red** jumper wire.  Insert one end into the (+) power rail.  Connect the other end to hole F28 (row 28, right half).
  _3.3V → top of LDR_

**C4.** Take a **black** jumper wire.  Insert one end into hole F31 (row 31, right half).  Connect the other end to the (−) power rail.
  _Bottom of 10K resistor → GND_

**C5.** Take a **yellow** jumper wire.  Insert one end into hole F29 (row 29, right half).  Connect the other end to hole J4 (row 4, right half).
  _LDR junction → ESP32 GPIO1 (ADC input)_


### Part D — Potentiometer (LCD contrast)


Read the Potentiometer Pin Identification section above before continuing.

**D1.** Orient the pot with the two terminals facing column C and the wiper facing column E.

**D2.** Insert the **GND terminal** into **C33**.

**D3.** Insert the **VCC terminal** into **C35**.

**D4.** Insert the **wiper** into **E34**.


**D5.** Take a **black** jumper wire.  Insert one end into hole B33 (row 33, left half).  Connect the other end to the (−) power rail.
  _Potentiometer GND terminal → (-) rail_

**D6.** Take a **red** jumper wire.  Insert one end into hole B35 (row 35, left half).  Connect the other end to the (+) power rail.
  _Potentiometer VCC terminal → (+) rail_

**D7.** Take a **green** jumper wire.  Insert one end into hole B34 (row 34, left half).  Connect the other end to LCD pin V0 (pin 3 on the LCD header).
  _Potentiometer wiper → LCD contrast (V0, pin 3)_


### Part E — LCD1602A (connected externally via jumper wires)

The LCD1602A PCB (80×36 mm) is too large to sit on the breadboard.
Place it **beside** the breadboard and wire each of its 16 pins as below.
Solder a 16-pin male header to the LCD if not already fitted.

| LCD pin | Label | Connect to | Wire colour |
|---------|-------|------------|-------------|

| 1 | VSS | the (−) power rail | black |

| 2 | VDD | the (+) power rail | red |

| 3 | V0 | hole B34 (row 34, left half) | green |

| 4 | RS | hole J5 (row 5, right half) | blue |

| 5 | RW | the (−) power rail | black |

| 6 | E | hole J6 (row 6, right half) | purple |

| 7 | D0 | *(leave unconnected — 4-bit mode)* | — |

| 8 | D1 | *(leave unconnected — 4-bit mode)* | — |

| 9 | D2 | *(leave unconnected — 4-bit mode)* | — |

| 10 | D3 | *(leave unconnected — 4-bit mode)* | — |

| 11 | D4 | hole J7 (row 7, right half) | orange |

| 12 | D5 | hole J8 (row 8, right half) | yellow |

| 13 | D6 | hole J9 (row 9, right half) | green |

| 14 | D7 | hole J10 (row 10, right half) | white |

| 15 | A | the (+) power rail | red |

| 16 | K | the (−) power rail | black |



### Part F — Verification checklist and power-on test


Verify all wires before applying power:


| # | From | To | Colour | Purpose |

|---|------|----|--------|---------|

| 1 | J1 | (−) rail | black | ESP32 GND (right header row 1) → (-) power rail |

| 2 | (+) rail | F28 | red | 3.3V → top of LDR |

| 3 | F31 | (−) rail | black | Bottom of 10K resistor → GND |

| 4 | F29 | J4 | yellow | LDR junction → ESP32 GPIO1 (ADC input) |

| 5 | B33 | (−) rail | black | Potentiometer GND terminal → (-) rail |

| 6 | B35 | (+) rail | red | Potentiometer VCC terminal → (+) rail |

| 7 | B34 | lcd pin V0 | green | Potentiometer wiper → LCD contrast (V0, pin 3) |

| 8 | (−) rail | lcd pin VSS | black | LCD VSS (pin 1) → GND |

| 9 | (+) rail | lcd pin VDD | red | LCD VDD (pin 2) → 3.3V |

| 10 | (−) rail | lcd pin RW | black | LCD RW (pin 5) → GND (write-only mode) |

| 11 | (+) rail | lcd pin A | red | LCD backlight anode (pin 15) → 3.3V |

| 12 | (−) rail | lcd pin K | black | LCD backlight cathode (pin 16) → GND |

| 13 | J5 | lcd pin RS | blue | GPIO2 → LCD RS (pin 4, data/command select) |

| 14 | J6 | lcd pin E | purple | GPIO42 → LCD Enable (pin 6) |

| 15 | J7 | lcd pin D4 | orange | GPIO41 → LCD D4 (pin 11) |

| 16 | J8 | lcd pin D5 | yellow | GPIO40 → LCD D5 (pin 12) |

| 17 | J9 | lcd pin D6 | green | GPIO39 → LCD D6 (pin 13) |

| 18 | J10 | lcd pin D7 | white | GPIO38 → LCD D7 (pin 14) |


**Power-on checklist:**


1. Confirm all wires are connected as above.

2. Turn the potentiometer knob to the mid-position.

3. Connect the USB-C cable to the ESP32.

4. The LCD backlight should illuminate within 1–2 seconds.

5. Adjust the potentiometer if the LCD text is faint or invisible.

6. Cover the LDR — the sensor reading should decrease.

7. Uncover and hold a torch close — the reading should increase.

---


## Firmware

All commands run from the project directory:

```
cd /Users/samwhitby/Documents/PlatformIO/Projects/Test
```

### Flash to real hardware

```
python3 configure_firmware.py hw && pio run --target upload && python3 configure_firmware.py sim
```

Switches to hardware mode → uploads → restores simulation mode.

### Switch mode manually

```
python3 configure_firmware.py hw      # real hardware (USB OTG enabled)
python3 configure_firmware.py sim     # Wokwi simulation
python3 configure_firmware.py status  # show current mode
```

### Monitor

```
pio device monitor --baud 115200
```

Expected serial output:

```
ADC: 2048  Lux: 245
```
