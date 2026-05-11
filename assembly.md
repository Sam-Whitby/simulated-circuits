# Assembly Instructions: Ambient Light Sensor with LCD Display

This guide walks you through building the circuit on a breadboard from scratch. You do not need any prior electronics experience. Read each step carefully, carry it out, then move to the next. Do not skip steps or work ahead.

Before you touch any component, read through the whole document once so you know what to expect.

---

## What You Are Building

An ambient light sensor that:
- Reads the brightness in the room using a photoresistor (a small disc-shaped component that changes resistance depending on how much light hits it)
- Displays the current light level as a percentage on a small character display (0% = very dark, 100% = very bright)
- Updates the reading once per second

---

## Parts List

Gather every item below and lay it on your desk before you start. Do not substitute components.

| # | Component | Quantity | What it looks like |
|---|-----------|----------|--------------------|
| 1 | ESP32-S3 DevKitC-1 (N16R8) development board | 1 | Rectangular black PCB with a USB-C port, two rows of metal pins on the long sides |
| 2 | LCD1602 display module — 16×2 characters, 16-pin single-row header | 1 | Rectangular green or blue PCB with a rectangular window showing two rows of character cells |
| 3 | Breadboard-compatible potentiometer, 10K ohm | 1 | A small component with a rotatable shaft and three pins underneath |
| 4 | Photoresistor (LDR — Light Dependent Resistor) | 1 | A small disc with a wavy line pattern on its face, two flexible metal leads |
| 5 | Resistor, 10K ohm — colour bands: brown, black, orange, gold | 1 | A small cylinder with wire leads and coloured stripes |
| 6 | Full-size solderless breadboard — 830 points | 1 | Rectangular plastic board covered in small holes, with red/blue rails along the edges |
| 7 | Jumper wires (male-to-male, pre-cut) — assorted colours | ≈ 20 | Short wires with a pin at each end. Red, black, blue, green, yellow, white, purple, orange |
| 8 | USB-C cable | 1 | To connect the ESP32 to your computer |
| 9 | Computer with the firmware already loaded onto the ESP32 | 1 | See WORKFLOW.md for instructions |

> ⚠️ **Voltage warning:** The ESP32-S3 uses 3.3 V logic. Never connect any 5 V signal to its GPIO pins — this will permanently damage the chip. All signals in this circuit are 3.3 V.

---

## Understanding the Breadboard

A full-size breadboard is a grid of small holes (sockets) arranged so that you can connect components and wires without soldering. Before assembling anything, understand how electricity flows through it.

### Columns and Rows

The main grid has:
- **63 numbered rows** — labelled 1 (top) to 63 (bottom) along the side.
- **10 lettered columns** — A, B, C, D, E on the LEFT side of a centre gap, and F, G, H, I, J on the RIGHT side of that gap.

A hole is identified by its column letter followed by its row number. Examples: **A1** (column A, row 1), **J22** (column J, row 22), **D35** (column D, row 35).

### Which holes are connected?

**Key rule:** All five holes in the same row-half are electrically connected to each other.
- A5, B5, C5, D5, E5 are ALL connected — pushing a wire into any of them reaches the others.
- F5, G5, H5, I5, J5 are ALL connected — but NOT connected to A5–E5.
- The centre gap separates the two halves. Holes on opposite sides of the gap in the same row are NOT connected unless you run a wire between them.

### Power Rails

The top and bottom edges each have two long horizontal strips of holes labelled **(+)** and **(−)**. Every hole in the (+) strip is connected to every other hole in the (+) strip. Same for (−). We will use these to distribute 3.3 V (positive) and Ground (negative) to all the components without running individual wires to each one.

In this build:
- **(+) top rail = 3.3 V**
- **(−) top rail = Ground (0 V)**

---

## ESP32-S3 Pin Reference

The ESP32-S3 DevKitC-1 board has two rows of 22 header pins — one row on each long side. When the board is seated on the breadboard (USB-C connector at the top), the left header occupies **column A** and the right header occupies **column I**, rows 1–22.

> ⚠️ **Important:** The GPIO numbers printed on the board do NOT correspond to row numbers. For example, GPIO 8 is at row 12, and GPIO 9 is at row 15. Always use the table below — do not guess from the GPIO number.

### Left header — column A, rows 1–22

| Hole | Signal | Used? |
|------|--------|-------|
| A1  | 3.3 V | ✅ → (+) power rail |
| A2  | 3.3 V | — |
| A3  | RST (Reset) | — |
| **A4**  | **GPIO 4** | ✅ → LCD RS (pin 4) |
| **A5**  | **GPIO 5** | ✅ → LCD Enable (pin 6) |
| **A6**  | **GPIO 6** | ✅ → LCD D4 (pin 11) |
| **A7**  | **GPIO 7** | ✅ → LCD D5 (pin 12) |
| A8  | GPIO 15 | — |
| A9  | GPIO 16 | — |
| A10 | GPIO 17 | — |
| A11 | GPIO 18 | — |
| **A12** | **GPIO 8** | ✅ → LCD D6 (pin 13) — note: row 12, not row 8 |
| A13 | GPIO 3 | — |
| A14 | GPIO 46 | — |
| **A15** | **GPIO 9** | ✅ → LCD D7 (pin 14) — note: row 15, not row 9 |
| A16 | GPIO 10 | — |
| A17 | GPIO 11 | — |
| A18 | GPIO 12 | — |
| A19 | GPIO 13 | — |
| A20 | GPIO 14 | — |
| A21 | 5 V | — |
| A22 | GND | ✅ → (−) power rail |

### Right header — column I, rows 1–22

| Hole | Signal | Used? |
|------|--------|-------|
| **I1**  | **GND** | ✅ → (−) power rail |
| I2  | TX (GPIO 43) | — |
| I3  | RX (GPIO 44) | — |
| **I4**  | **GPIO 1** | ✅ → LDR junction (analogue input) |
| I5  | GPIO 2 | — |
| I6  | GPIO 42 | — |
| I7  | GPIO 41 | — |
| I8  | GPIO 40 | — |
| I9  | GPIO 39 | — |
| I10 | GPIO 38 | — |
| I11 | GPIO 37 | — |
| I12 | GPIO 36 | — |
| I13 | GPIO 35 | — |
| I14 | GPIO 0 (BOOT) | — |
| I15 | GPIO 45 | — |
| I16 | GPIO 48 | — |
| I17 | GPIO 47 | — |
| I18 | GPIO 21 | — |
| I19 | GPIO 20 | — |
| I20 | GPIO 19 | — |
| I21 | GND | — |
| I22 | GND | — |

---

## Breadboard Layout Overview

Here is where every component will sit before you start wiring:

```
Top power rail ──────────────────────  (+) = 3.3 V   (−) = GND

Rows  1–22    ESP32-S3 DevKitC-1
              Left header  → column A, rows 1–22
              Right header → column I, rows 1–22

Rows 24–26    LDR + 10K resistor voltage divider (right half, column H)
              H24 = LDR top lead  →  H25 = junction  →  H26 = resistor bottom lead

Rows 29–31    Potentiometer (left half, column C)
              C29 = GND pin   C30 = wiper   C31 = VCC pin

Rows 33–48    LCD1602 display (left half, column E)
              E33 = LCD pin 1 (VSS)   …   E48 = LCD pin 16 (K)
```

---

## Step-by-Step Assembly

Work through each lettered part in order. Do not connect the USB-C cable until **Step F2**.

---

### Part A — Place the ESP32 Board

*Goal: Seat the microcontroller so all its pins are accessible in the breadboard grid.*

**Step A1.** Orient the breadboard with row 1 at the top and the power rails running along the top and bottom edges.

**Step A2.** Pick up the ESP32-S3 DevKitC-1 board. Rotate it so the USB-C connector is at the top (pointing upward, away from the breadboard body).

**Step A3.** Hold the board over the breadboard and align the left-side pins over **column A** and the right-side pins over **column I**. Both sets of pins should start at **row 1**.

**Step A4.** Press the board steadily and evenly downward until all pins click firmly into the holes. The board body will bridge the centre gap.

> **Check:** Look at the left side. The top pin should be in **A1** and the bottom pin in **A22**. Count them — you should count 22 pins. Do the same for the right side: **I1** at the top, **I22** at the bottom, 22 pins. If the count is off, the board may be shifted — pull it out and reseat it.

---

### Part B — Set Up the Power Rails

*Goal: Create a shared 3.3 V bus and Ground bus that every other component will connect to. This avoids running individual power wires to each component from the ESP32.*

**Step B1.** Take a **red** jumper wire. Insert one end into **A1** (ESP32 3.3 V, left header pin 1) and the other end into any hole in the **(+)** row of the top power rail.

**Step B2.** Take a **black** jumper wire. Insert one end into **A22** (ESP32 GND, left header pin 22) and the other end into any hole in the **(−)** row of the top power rail.

**Step B3.** Take a second **black** jumper wire. Insert one end into **I1** (ESP32 GND, right header pin 1) and the other end into any hole in the **(−)** row of the top power rail.

> After these three steps, every hole in the (+) rail carries 3.3 V, and every hole in the (−) rail is Ground. All future power and ground connections go to these rails.

---

### Part C — Light Sensor (LDR Voltage Divider)

*Goal: Create a circuit whose output voltage rises when light is bright and falls when it is dark. The ESP32 reads this voltage on its analogue input (GPIO 1, hole I4) and converts it to a 0–100% reading.*

**How it works:** A photoresistor (LDR) is paired with a fixed 10K resistor to form a voltage divider:

```
  3.3 V ──[LDR]──┬──[10K resistor]── GND
                 │
               GPIO 1
              (reads voltage here)
```

When bright, the LDR's resistance drops, and the junction voltage rises toward 3.3 V → higher reading → higher percentage. When dark, the LDR's resistance rises → junction voltage falls → lower percentage.

The three holes H24, H25, H26 will carry these voltages:
- **H24** — 3.3 V (top of LDR)
- **H25** — junction voltage (bottom of LDR / top of resistor) — the reading point
- **H26** — Ground (bottom of resistor)

**Step C1.** Take the **photoresistor (LDR)**. Insert one lead into hole **H24** and the other lead into hole **H25**. The LDR has no polarity — either lead can go into either hole.

**Step C2.** Take the **10K ohm resistor** (brown-black-orange-gold bands). Insert one lead into hole **H25** and the other lead into hole **H26**. The resistor has no polarity.

> **Check:** Holes H24, H25, and H26 should now each contain one component lead. H25 contains two leads — one from the LDR and one from the resistor. This shared point (H25) is the junction that the ESP32 will measure.

**Step C3.** Take a **red** jumper wire. Insert one end into **G24** (same row as H24, same electrical node as the LDR's top lead) and the other end into the **(+)** rail. This supplies 3.3 V to the top of the voltage divider.

**Step C4.** Take a **black** jumper wire. Insert one end into **G26** (same row as H26, same electrical node as the resistor's bottom lead) and the other end into the **(−)** rail. This connects the bottom of the divider to Ground.

**Step C5.** Take a **yellow** jumper wire. Insert one end into **J25** (same row as H25 — the junction) and the other end into **I4** (ESP32 GPIO 1, analogue input). This carries the light-level voltage to the chip.

---

### Part D — Potentiometer (LCD Contrast Adjustment)

*Goal: Wire a variable resistor so you can turn a knob to adjust the display contrast. Without this, characters may be invisible even if the display is powered.*

A potentiometer has three pins. The two outer pins connect to GND and 3.3 V. The middle pin (the wiper) outputs a variable voltage between those two extremes — turning the knob changes the voltage.

**Step D1.** Take the **potentiometer**. Identify its three pins. The centre pin is the wiper; the outer two pins are the GND and VCC ends. Insert the three pins into holes **C29** (GND end), **C30** (wiper), and **C31** (VCC end). The potentiometer body sits above the breadboard.

> If your potentiometer has a rotary shaft on top, the wiper is the centre pin when viewed from the front.

**Step D2.** Take a **black** jumper wire. Insert one end into **B29** (same row as C29, the GND end of the potentiometer) and the other end into the **(−)** rail.

**Step D3.** Take a **red** jumper wire. Insert one end into **B31** (same row as C31, the VCC end) and the other end into the **(+)** rail.

**Step D4.** Take a **green** jumper wire. Insert one end into **C30** (the wiper) and the other end into **D35**. Hole D35 is in the same row as E35, which will be LCD contrast input (pin 3) once the display is inserted in the next step.

---

### Part E — LCD1602 Display

*Goal: Seat the 16×2 display and wire all its control, data, and power pins to the ESP32 and power rails.*

The LCD1602 uses 4-bit mode, which means:
- Pins 1–6 handle power, ground, contrast, and control signals.
- Pins 7–10 (D0–D3) are unused — leave them empty.
- Pins 11–14 (D4–D7) carry the 4 data bits.
- Pins 15–16 control the backlight.

**Step E1.** Pick up the LCD1602 display. Identify the 16-pin header along one long edge.

**Step E2.** Orient the display so pin 1 is at the top and the display screen faces you. Align pin 1 over hole **E33** and pin 16 over hole **E48**. Press the display firmly downward until all 16 pins are seated. The display body will extend to the left.

> **Check:** Count from E33 to E48 — exactly 16 holes. Pin 1 is labelled VSS (Ground) and pin 16 is labelled K (backlight negative). If your LCD has a label or the pins are numbered on the PCB, verify pin 1 is in E33.

Once the LCD is seated, the pin-to-hole mapping is:

| LCD Pin | Name | Hole | Connect to |
|---------|------|------|------------|
| 1 | VSS (GND) | E33 | (−) rail |
| 2 | VDD (3.3 V) | E34 | (+) rail |
| 3 | V0 (contrast) | E35 | Potentiometer wiper — already wired in Step D4 |
| 4 | RS | E36 | GPIO 4 (A4) |
| 5 | RW | E37 | (−) rail |
| 6 | E (Enable) | E38 | GPIO 5 (A5) |
| 7–10 | D0–D3 | E39–E42 | **Leave empty — not used in 4-bit mode** |
| 11 | D4 | E43 | GPIO 6 (A6) |
| 12 | D5 | E44 | GPIO 7 (A7) |
| 13 | D6 | E45 | GPIO 8 (A12) |
| 14 | D7 | E46 | GPIO 9 (A15) |
| 15 | A (backlight +) | E47 | (+) rail |
| 16 | K (backlight −) | E48 | (−) rail |

Now connect each pin in order:

**Step E3.** LCD GND — take a **black** wire, one end into **D33**, other end into **(−)** rail.

**Step E4.** LCD 3.3 V — take a **red** wire, one end into **D34**, other end into **(+)** rail.

*(LCD contrast — E35 — is already connected via the wire you placed in Step D4.)*

**Step E5.** LCD RW to GND — take a **black** wire, one end into **D37**, other end into **(−)** rail. This puts the display permanently in write-only mode (it only receives data, never sends it).

**Step E6.** LCD backlight positive — take a **red** wire, one end into **D47**, other end into **(+)** rail.

> **Note:** The backlight is connected directly to 3.3 V without a current-limiting resistor. This is safe for prototyping — most 3.3 V LCD backlights have a forward voltage close to 3.3 V that limits current naturally. For a permanent build, place a 33 Ω resistor in series.

**Step E7.** LCD backlight negative — take a **black** wire, one end into **D48**, other end into **(−)** rail.

**Step E8.** RS — data/command select (GPIO 4):
Take a **blue** wire, one end into **B4** (same row as **A4** = GPIO 4), other end into **D36** (same row as **E36** = LCD RS).

**Step E9.** Enable — clock signal (GPIO 5):
Take a **purple** wire, one end into **B5** (same row as **A5** = GPIO 5), other end into **D38** (same row as **E38** = LCD Enable).

**Step E10.** D4 — data bit 4 (GPIO 6):
Take an **orange** wire, one end into **B6** (same row as **A6** = GPIO 6), other end into **D43** (same row as **E43** = LCD D4).

**Step E11.** D5 — data bit 5 (GPIO 7):
Take a **yellow** wire, one end into **B7** (same row as **A7** = GPIO 7), other end into **D44** (same row as **E44** = LCD D5).

**Step E12.** D6 — data bit 6 (GPIO 8):
Take a **green** wire, one end into **B12** (same row as **A12** = GPIO 8), other end into **D45** (same row as **E45** = LCD D6).

> ⚠️ **Important:** GPIO 8 is at **row 12** of the left header (**A12**), NOT row 8 (**A8**). The ESP32 pin order is not sequential by GPIO number. Always follow the pin table.

**Step E13.** D7 — data bit 7 (GPIO 9):
Take a **white** wire, one end into **B15** (same row as **A15** = GPIO 9), other end into **D46** (same row as **E46** = LCD D7).

> ⚠️ **Important:** GPIO 9 is at **row 15** (**A15**), not row 9.

---

### Part F — Final Check and Power-On

*Goal: Verify every connection before applying power, then confirm the circuit works.*

**Step F1.** Before connecting the USB cable, go through the complete wiring table below and tick off every wire:

| # | From | To | Wire colour | Purpose |
|---|------|----|-------------|---------|
| 1 | A1 | (+) rail | Red | ESP32 3.3 V → power bus |
| 2 | A22 | (−) rail | Black | ESP32 GND (left) → ground bus |
| 3 | I1 | (−) rail | Black | ESP32 GND (right) → ground bus |
| 4 | (+) rail | G24 | Red | 3.3 V → top of LDR |
| 5 | G26 | (−) rail | Black | Bottom of 10K resistor → GND |
| 6 | J25 | I4 | Yellow | LDR junction → GPIO 1 (ADC) |
| 7 | B29 | (−) rail | Black | Potentiometer GND end |
| 8 | B31 | (+) rail | Red | Potentiometer 3.3 V end |
| 9 | C30 | D35 | Green | Potentiometer wiper → LCD contrast |
| 10 | D33 | (−) rail | Black | LCD VSS → GND |
| 11 | D34 | (+) rail | Red | LCD VDD → 3.3 V |
| 12 | D37 | (−) rail | Black | LCD RW → GND (write-only) |
| 13 | D47 | (+) rail | Red | LCD backlight + |
| 14 | D48 | (−) rail | Black | LCD backlight − |
| 15 | B4 | D36 | Blue | GPIO 4 → LCD RS |
| 16 | B5 | D38 | Purple | GPIO 5 → LCD Enable |
| 17 | B6 | D43 | Orange | GPIO 6 → LCD D4 |
| 18 | B7 | D44 | Yellow | GPIO 7 → LCD D5 |
| 19 | B12 | D45 | Green | GPIO 8 → LCD D6 |
| 20 | B15 | D46 | White | GPIO 9 → LCD D7 |

Also verify:
- [ ] LDR leads: one in **H24**, one in **H25**
- [ ] 10K resistor leads: one in **H25**, one in **H26**
- [ ] Potentiometer pins: **C29**, **C30**, **C31**
- [ ] LCD 16-pin header: **E33** through **E48**
- [ ] Holes **E39–E42** (LCD D0–D3) are empty

**Step F2.** Connect the USB-C cable to the ESP32 board. Connect the other end to your computer. Do not press any buttons on the ESP32.

**Step F3.** Watch the display. Within 3 seconds, the backlight should illuminate and you should see:

```
Light Sensor
Level: XX%
```

The percentage will update once per second.

**Step F4.** If the backlight is on but the display shows only solid black rectangles or is blank, slowly turn the potentiometer knob. The contrast will change as you turn it. Rotate until you see clear black text on a light background.

**Step F5.** Test the sensor. Cover the photoresistor fully with your hand — the percentage should drop toward 0%. Remove your hand and shine a torch directly at the LDR — the percentage should rise toward 100%.

---

## Troubleshooting

| Symptom | Most likely cause | What to do |
|---------|-------------------|------------|
| No backlight, display completely dark | Power wires missing or wrong | Recheck Steps B1–B3, E6, E7. Confirm A1→(+) rail and A22→(−) rail are seated. |
| Backlight on, display blank/solid blocks | Contrast not adjusted | Turn potentiometer slowly through its full range. Also check Step D4 (C30 → D35). |
| Display shows text but percentage stuck at 0% | LDR circuit not connected | Recheck Steps C1–C5. Confirm H25 has two leads in it. Confirm J25 → I4. |
| Percentage always shows 100% | Junction shorted to 3.3 V, or GND wire missing | Recheck G26 → (−) rail (Step C4). Make sure nothing bridges H24 and H26. |
| Percentage goes DOWN when you shine a light | LDR leads are reversed | Remove the LDR and swap which lead goes into H24 and which into H25. |
| Firmware boots (serial output) but display shows nothing | Data wires wrong | Recheck Steps E8–E13 against the pin table. Pay attention to GPIO 8 at A12 and GPIO 9 at A15. |
| Display shows garbled characters | RS or Enable wiring wrong | Recheck E8 (B4 → D36) and E9 (B5 → D38). |
