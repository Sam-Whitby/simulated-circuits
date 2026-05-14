// MIDI Logger — ESP32-S3 + SD Card
//
// Captures USB MIDI from a Yamaha P-125 and logs every note (channel, note
// number, velocity, duration) as JSON lines to an SD card and serial.
//
// Physical chain (real hardware):
//   Yamaha P-125 USB-B port
//     → USB-B to USB-A cable
//     → Mepsies OTG adapter (USB-A female ↔ USB-C male)
//     → ESP32-S3 DevKitC-1 native USB port ("USB", not "COM")
//
// GPIO assignments (all right-header, tapped via column J on breadboard):
//   GPIO35 (I13, J13) — SD MOSI
//   GPIO36 (I12, J12) — SD SCK
//   GPIO37 (I11, J11) — SD MISO
//   GPIO38 (I10, J10) — SD CS
//
// Output format — one JSON line per completed note:
//   {"t":12345,"ch":0,"note":60,"vel":80,"dur":512}
//   t   : timestamp (ms since boot)
//   ch  : MIDI channel 0–15
//   note: MIDI note number 0–127 (middle C = 60)
//   vel : note-on velocity 1–127
//   dur : held duration in ms

#include <Arduino.h>
#include <SPI.h>
#include <SD.h>

// ── Pin constants ─────────────────────────────────────────────────────────────
static const int SD_CS   = 38;
static const int SD_MOSI = 35;
static const int SD_MISO = 37;
static const int SD_SCK  = 36;

// ── State ─────────────────────────────────────────────────────────────────────
struct NoteState { bool active = false; uint32_t startMs = 0; uint8_t vel = 0; };
static NoteState notes[16][128];
static File      logFile;
static bool      sdReady = false;

// ── I/O helpers ───────────────────────────────────────────────────────────────
static void logLine(const char *buf) {
    Serial.println(buf);
    if (sdReady && logFile) {
        logFile.println(buf);
        logFile.flush();
    }
}

// ── MIDI event handlers ───────────────────────────────────────────────────────
static void noteOff(uint8_t ch, uint8_t note, uint8_t) {
    NoteState &s = notes[ch & 15][note & 127];
    if (!s.active) return;
    char buf[80];
    snprintf(buf, sizeof(buf),
             "{\"t\":%lu,\"ch\":%u,\"note\":%u,\"vel\":%u,\"dur\":%lu}",
             (unsigned long)millis(), ch, note, s.vel,
             (unsigned long)(millis() - s.startMs));
    logLine(buf);
    s.active = false;
}

static void noteOn(uint8_t ch, uint8_t note, uint8_t vel) {
    if (vel == 0) { noteOff(ch, note, 0); return; }   // vel=0 means note-off
    NoteState &s = notes[ch & 15][note & 127];
    s.active  = true;
    s.startMs = millis();
    s.vel     = vel;
}

// ── WOKWI SIMULATION ─────────────────────────────────────────────────────────
#ifdef WOKWI_SIMULATION

// Plays a C-major arpeggio: C4, E4, G4, C5, A4, F4, D4, G3
static const uint8_t ARPEGGIO[] = {60, 64, 67, 72, 69, 65, 62, 55};
static uint8_t  arpIdx   = 0;
static uint8_t  heldNote = 0;
static bool     noteHeld = false;
static uint32_t nextEvtMs = 0;

static void tickSim() {
    uint32_t now = millis();
    if (now < nextEvtMs) return;
    if (!noteHeld) {
        heldNote = ARPEGGIO[arpIdx++ % (sizeof ARPEGGIO / sizeof *ARPEGGIO)];
        noteOn(0, heldNote, 80);
        nextEvtMs = now + 500;   // hold for 500 ms
        noteHeld  = true;
    } else {
        noteOff(0, heldNote, 64);
        nextEvtMs = now + 700;   // gap before next note
        noteHeld  = false;
    }
}

// ── REAL HARDWARE: USB MIDI HOST ──────────────────────────────────────────────
#else

// The ESP32-S3's built-in USB OTG (native USB port on DevKitC-1) enumerates
// the P-125 as a USB MIDI class device and reads bulk-in packets.
//
// Build flags required for real hardware:
//   -DARDUINO_USB_MODE=0          ; enable USB OTG (not CDC device)
//
// Implementation sketch using ESP-IDF USB host library:
//   See esp-idf/examples/peripherals/usb/host/usb_host_lib for the full pattern.
//
// USB MIDI packet format (4 bytes per event):
//   Byte 0: Code Index Number (CIN) | Cable Number  → top nibble = cable, low nibble = CIN
//   Byte 1: MIDI status byte        → 0x8n = Note Off ch n,  0x9n = Note On ch n
//   Byte 2: MIDI data byte 1        → note number (0–127)
//   Byte 3: MIDI data byte 2        → velocity (0–127)
//
// Key CIN values:
//   0x08 = Note Off    0x09 = Note On
//
// Minimal implementation steps:
//   1.  usb_host_install(&cfg);
//   2.  usb_host_client_register(&ccfg, &client);
//   3.  On USB_HOST_CLIENT_EVENT_NEW_DEV: open device, get descriptor.
//   4.  Find interface with bInterfaceClass=0x01 (Audio), bInterfaceSubClass=0x03 (MIDI).
//   5.  Find bulk-in endpoint (bmAttributes=0x02, bEndpointAddress & 0x80).
//   6.  usb_transfer_alloc(64, &xfer); set xfer->callback = midiCallback;
//   7.  usb_host_transfer_submit(xfer);  — re-submit in callback for continuous read.
//   8.  In midiCallback: iterate xfer->data_buffer in 4-byte steps, call noteOn/noteOff.

static void tickUsbMidi() {
    // Replace with: usb_host_lib_handle_events(0, NULL);
    //               usb_host_client_handle_events(client, 0);
}

#endif

// ── Setup & loop ──────────────────────────────────────────────────────────────
void setup() {
    Serial.begin(115200);
    while (!Serial && millis() < 2000) {}

    SPI.begin(SD_SCK, SD_MISO, SD_MOSI, SD_CS);
    if (SD.begin(SD_CS)) {
        logFile  = SD.open("/midi.jsonl", FILE_APPEND);
        sdReady  = logFile;
        logLine("{\"status\":\"SD_OK\"}");
    } else {
        logLine("{\"status\":\"SD_FAIL\"}");
    }

    logLine("{\"status\":\"BOOT\"}");

#ifdef WOKWI_SIMULATION
    nextEvtMs = millis() + 1500;   // first note 1.5 s after boot
#endif
}

void loop() {
#ifdef WOKWI_SIMULATION
    tickSim();
#else
    tickUsbMidi();
#endif
}
