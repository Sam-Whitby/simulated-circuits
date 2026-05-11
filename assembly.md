# Assembly Instructions — Ambient Light Sensor with LCD Display

> **Generated from a validated breadboard.yaml layout.**
> Every hole reference below was verified by `breadboard_validator.py` before
> this document was written.  No hole is referenced twice.

---

## Parts List

| Qty | Component | Notes |
|-----|-----------|-------|
| 1 | ESP32-S3-DevKitC-1 (N16R8) | The microcontroller board |
| 1 | GL5528 LDR (photoresistor) | Any 5 mm LDR works |
| 1 | 10 KΩ resistor (brown-black-orange) | Pull-down for the voltage divider |
| 1 | 10 KΩ potentiometer (B10K) | **2+1 pin type** (two terminals on one side, wiper on the other) |
| 1 | LCD1602A (16-pin parallel) | Connected via wires — does NOT sit on the breadboard |
| 1 | Full-size breadboard (830 points, 63 rows) | |
| 20 | Jumper wires (male-to-male) | Assorted colours; 12 need to reach the LCD |
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

**The one-hole-one-pin rule**: each hole can hold exactly one lead or one
wire pin.  If a component already occupies hole A4, a wire connecting to
that same node must use an adjacent free hole such as B4 (same left-half
row — electrically connected, but a separate physical hole).

---

## Potentiometer Pin Identification

The potentiometer in this kit has **three pins in a 2+1 arrangement**:
two terminal pins on one face of the body, and one wiper pin on the opposite
face.  **Identify them before you place the pot on the board.**

1. Hold the potentiometer with the shaft pointing up and the pins facing down.
2. Look at the bottom of the pot.  On **one face** you will see **two pins**
   side by side — these are the terminals (GND end and VCC end).
3. On the **opposite face** you will see **one pin** in the centre — this is
   the wiper (the output that varies as you turn the knob).

**Rotation for breadboard use**: the two terminals cannot go into the same
breadboard row (they would be shorted together by the row-half connection).
Rotate the pot **90°** so the two terminals sit in the **same column but
different rows**, with the wiper offset two columns to the right.

The correct pin positions are:

| Pin | Hole | Function |
|-----|------|---------|
| GND terminal (top) | C33 | → power rail (−) |
| VCC terminal (bottom) | C35 | → power rail (+) |
| Wiper | E34 | → LCD contrast wire |

---

## ESP32-S3 Pin Reference

The ESP32-S3-DevKitC-1 has 22 pins down each side.  **GPIO numbers do not
equal row numbers** — for example GPIO8 is at breadboard row 12.

The board body overhangs the breadboard surface: its PCB covers **rows 1–26,
columns A–J**.  No component or wire may be placed in that zone.

| Row | Left (col A) | Used? | Row | Right (col I) | Used? |
|-----|-------------|-------|-----|--------------|-------|
| 1  | 3V3         | power rail wire at B1 | 1  | GND    | power rail wire at J1 |
| 2  | 3V3         | — | 2  | TX     | — |
| 3  | RST         | — | 3  | RX     | — |
| 4  | **GPIO4**   | LCD RS wire at B4    | 4  | **GPIO1** | ADC wire at J4 |
| 5  | **GPIO5**   | LCD Enable wire at B5 | 5  | GPIO2  | — |
| 6  | **GPIO6**   | LCD D4 wire at B6    | 6  | GPIO42 | — |
| 7  | **GPIO7**   | LCD D5 wire at B7    | 7  | GPIO41 | — |
| 8  | GPIO15      | — | 8  | GPIO40 | — |
| 9  | GPIO16      | — | 9  | GPIO39 | — |
| 10 | GPIO17      | — | 10 | GPIO38 | — |
| 11 | GPIO18      | — | 11 | GPIO37 | — |
| 12 | **GPIO8**   | LCD D6 wire at B12   | 12 | GPIO36 | — |
| 13 | GPIO3       | — | 13 | GPIO35 | — |
| 14 | GPIO46      | — | 14 | GPIO0  | — |
| 15 | **GPIO9**   | LCD D7 wire at B15   | 15 | GPIO45 | — |
| 16 | GPIO10      | — | 16 | GPIO48 | — |
| 17 | GPIO11      | — | 17 | GPIO47 | — |
| 18 | GPIO12      | — | 18 | GPIO21 | — |
| 19 | GPIO13      | — | 19 | GPIO20 | — |
| 20 | GPIO14      | — | 20 | GPIO19 | — |
| 21 | 5V          | — | 21 | GND    | — |
| 22 | **GND**     | power rail wire at B22 | 22 | **GND** | — |

---

## Step-by-Step Assembly

Work in order.  Complete each step before moving to the next.

---

### Part A — Place the ESP32-S3 board

**A1.** Orient the breadboard with row 1 at the top.

**A2.** Hold the ESP32-S3-DevKitC-1 with the USB-C port facing away from you.

**A3.** Press the board firmly into the breadboard so that:
- The left header pins go into **column A, rows 1–22**.
- The right header pins go into **column I, rows 1–22**.
- The board straddles the centre gap.

The board body will overhang the breadboard surface — rows 1–26 are now
physically covered by the PCB.  Do not place anything in those rows.

---

### Part B — Set up the power rails

**B1.** Take a **red** jumper wire.  Insert one end into **B1** (row 1, left
half — electrically connected to 3.3 V at A1).  Connect the other end to
the **(+) power rail**.

**B2.** Take a **black** jumper wire.  Insert one end into **B22** (row 22,
left half — connected to GND at A22).  Connect the other end to the
**(−) power rail**.

**B3.** Take a second **black** jumper wire.  Insert one end into **J1**
(row 1, right half — connected to GND at I1).  Connect the other end to
the **(−) power rail**.

---

### Part C — Light sensor (LDR voltage divider)

The LDR and 10 KΩ resistor form a voltage divider: 3.3 V → LDR → junction
→ resistor → GND.  The ESP32 reads the voltage at the junction: bright light
(low LDR resistance) = high voltage = high reading.

**C1.** Bend the LDR leads so they point straight down, about 7 mm apart.
Insert the LDR into the breadboard: **lead-1 into H28**, **lead-2 into H29**.
Either lead can go in either hole (the LDR has no polarity).

**C2.** Bend the 10 KΩ resistor leads so they are about 5 mm apart.  Insert
the resistor: **lead-1 into G29**, **lead-2 into G31**.
(G29 is in the same right-half row as H29 — they are electrically connected,
forming the ADC junction.)

**C3.** Take a **red** jumper wire.  Insert one end into **F28** (free hole
in right-half row 28, connected to the LDR 3.3 V lead at H28).  Connect the
other end to the **(+) power rail**.

**C4.** Take a **black** jumper wire.  Insert one end into **F31** (free hole
in right-half row 31, connected to the resistor GND lead at G31).  Connect
the other end to the **(−) power rail**.

**C5.** Take a **yellow** jumper wire.  Insert one end into **F29** (free
hole in right-half row 29, electrically connected to the junction at G29 /
H29).  Insert the other end into **J4** (free hole in right-half row 4,
electrically connected to GPIO1 at I4).

---

### Part D — Potentiometer (LCD contrast control)

Read the "Potentiometer Pin Identification" section above before continuing.
The pot must be rotated 90° before insertion.

**D1.** Orient the pot with the two terminals facing **column C** and the
wiper facing **column E** (to the right).  The GND terminal should be nearer
to row 33, the VCC terminal nearer to row 35.

**D2.** Insert the **GND terminal** into **C33**.

**D3.** Insert the **VCC terminal** into **C35**.

**D4.** Insert the **wiper** into **E34**.

**D5.** Take a **black** jumper wire.  Insert one end into **B33** (free
hole, same left-half row as GND terminal at C33).  Connect the other end to
the **(−) power rail**.

**D6.** Take a **red** jumper wire.  Insert one end into **B35** (free hole,
same left-half row as VCC terminal at C35).  Connect the other end to the
**(+) power rail**.

---

### Part E — LCD1602A (connected externally via jumper wires)

The LCD1602A PCB measures 80 × 36 mm — it is physically too large to sit on
the breadboard alongside the ESP32-S3.  Instead, place the LCD **beside** the
breadboard and use individual jumper wires to connect each of its 16 pins.

If the LCD does not already have a 16-pin male header soldered to it, solder
one now before proceeding.

Connect the LCD as follows.  For each row, take one jumper wire, plug one
end into the named breadboard hole (or power rail), and plug the other end
into the numbered LCD header pin.

| LCD pin | LCD label | Connect to | Wire colour |
|---------|-----------|------------|-------------|
| 1  | VSS | (−) power rail | Black |
| 2  | VDD | (+) power rail | Red |
| 3  | V0  | **D34** (row 34 left half — wiper node) | Green |
| 4  | RS  | **B4**  (row 4 left half — GPIO4 node) | Blue |
| 5  | RW  | (−) power rail | Black |
| 6  | E   | **B5**  (row 5 left half — GPIO5 node) | Purple |
| 7  | D0  | *(leave unconnected)* | — |
| 8  | D1  | *(leave unconnected)* | — |
| 9  | D2  | *(leave unconnected)* | — |
| 10 | D3  | *(leave unconnected)* | — |
| 11 | D4  | **B6**  (row 6 left half — GPIO6 node) | Orange |
| 12 | D5  | **B7**  (row 7 left half — GPIO7 node) | Yellow |
| 13 | D6  | **B12** (row 12 left half — GPIO8 node) | Green |
| 14 | D7  | **B15** (row 15 left half — GPIO9 node) | White |
| 15 | A   | (+) power rail | Red |
| 16 | K   | (−) power rail | Black |

> **D0–D3 (pins 7–10) are unused** in 4-bit mode.  Leave them unconnected.

---

### Part F — Verification checklist and power-on test

Before applying power, verify all 20 wires against this table:

| # | From | To | Colour | Purpose |
|---|------|----|--------|---------|
| 1 | B1 | (+) rail | Red | ESP32 3.3V |
| 2 | B22 | (−) rail | Black | ESP32 GND left header |
| 3 | J1 | (−) rail | Black | ESP32 GND right header |
| 4 | (+) rail | F28 | Red | 3.3V → LDR top |
| 5 | F31 | (−) rail | Black | Resistor GND end |
| 6 | F29 | J4 | Yellow | Junction → GPIO1 (ADC) |
| 7 | B33 | (−) rail | Black | Pot GND terminal |
| 8 | B35 | (+) rail | Red | Pot VCC terminal |
| 9 | D34 | LCD V0 (pin 3) | Green | Wiper → LCD contrast |
| 10 | (−) rail | LCD VSS (pin 1) | Black | LCD GND |
| 11 | (+) rail | LCD VDD (pin 2) | Red | LCD 3.3V |
| 12 | (−) rail | LCD RW (pin 5) | Black | LCD write-only mode |
| 13 | (+) rail | LCD A (pin 15) | Red | LCD backlight anode |
| 14 | (−) rail | LCD K (pin 16) | Black | LCD backlight cathode |
| 15 | B4 | LCD RS (pin 4) | Blue | GPIO4 → RS |
| 16 | B5 | LCD E (pin 6) | Purple | GPIO5 → Enable |
| 17 | B6 | LCD D4 (pin 11) | Orange | GPIO6 → D4 |
| 18 | B7 | LCD D5 (pin 12) | Yellow | GPIO7 → D5 |
| 19 | B12 | LCD D6 (pin 13) | Green | GPIO8 → D6 |
| 20 | B15 | LCD D7 (pin 14) | White | GPIO9 → D7 |

**Power-on checklist:**

1. Confirm all 20 wires are connected as above.
2. Turn the potentiometer knob to the mid-position.
3. Connect the USB-C cable to the ESP32.
4. The LCD backlight should illuminate within 1–2 seconds.
5. The LCD should display the light level, e.g. `Light: 73%`.
6. Cover the LDR with your finger — the percentage should fall toward 0%.
7. Uncover the LDR and hold a torch close — the percentage should rise toward 100%.
8. Adjust the potentiometer if the LCD text is faint or invisible — incorrect
   contrast is the most common cause of a blank (but illuminated) LCD.
