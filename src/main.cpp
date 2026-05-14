#include <Arduino.h>
#include <LiquidCrystal.h>

static const int LDR_PIN = 1;    // ADC1_CH0 — right header I4, tapped at J4
static const int LCD_RS  = 2;    // right header I5,  tapped at J5
static const int LCD_EN  = 42;   // right header I6,  tapped at J6
static const int LCD_D4  = 41;   // right header I7,  tapped at J7
static const int LCD_D5  = 40;   // right header I8,  tapped at J8
static const int LCD_D6  = 39;   // right header I9,  tapped at J9
static const int LCD_D7  = 38;   // right header I10, tapped at J10

static const unsigned long UPDATE_MS = 1000;

LiquidCrystal lcd(LCD_RS, LCD_EN, LCD_D4, LCD_D5, LCD_D6, LCD_D7);

void setup() {
  Serial.begin(115200);
  Serial.println("BOOT");
  Serial.flush();

  analogReadResolution(12);

  lcd.begin(16, 2);
  lcd.print("Light Sensor");
}

void loop() {
  static unsigned long lastUpdate = 0;
  unsigned long now = millis();

  if (now - lastUpdate >= UPDATE_MS) {
    lastUpdate = now;

    int raw = analogRead(LDR_PIN);
    int pct = map(raw, 0, 4095, 0, 100);

    lcd.setCursor(0, 1);
    lcd.print("Level: ");
    lcd.print(pct);
    lcd.print("%   ");

    Serial.printf("{\"raw\":%d,\"pct\":%d}\n", raw, pct);
    Serial.flush();
  }
}
