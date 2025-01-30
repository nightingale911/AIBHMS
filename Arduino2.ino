#include <Arduino.h>
#include <Wire.h>
#include "HX711.h"
#include <Servo.h>

Servo servo;

// HX711 Pins
const int LOADCELL_DOUT_PIN = 2;
const int LOADCELL_SCK_PIN = 3;

// HX711 Object
HX711 scale;

// FSR Constants
const int fsrPin = A0;          // FSR is connected to Analog pin A0
const float resistor = 10000.0; // Resistor in voltage divider circuit (ohms)
const float materialModulus = 193000000000.0; // Modulus of elasticity (Pa) for stainless steel
const float crossSectionArea = 0.0025; // Cross-sectional area of material (m^2)0.00010012294

// LED/Buzzer Pin
const int led = 13;

// Accelerometer Constants
const int ADXL345_ADDR = 0x53;  // I2C address of ADXL345
int16_t accX, accY, accZ;       // Raw accelerometer values
float x_avg, y_avg, z_avg;      // Averaged accelerometer values
int32_t x_sum, y_sum, z_sum;    // Summation for averaging
#define NUM_SAMPLES 10          // Number of samples for averaging

// Force Calculation Function for FSR
float calculateForceFromResistance(float resistance) {
  float k = 10000.0; // Calibration constant
  float intermediate= k / resistance; // Force calculation based on resistance
  return intermediate;
}

void setup() {
  // Serial setup
  Serial.begin(57600);
  Serial.println("Begin");

  // HX711 Setup
  Serial.println("Initializing HX711 scale...");
  scale.begin(LOADCELL_DOUT_PIN, LOADCELL_SCK_PIN);
  scale.set_scale(-104.653465); // Set calibration scale //-104.653465
  scale.tare();                // Reset scale to 0
  Serial.println("LoadCell Done");

  // Accelerometer Setup
  Serial.println("StartWire");
  Wire.begin();
  Wire.beginTransmission(ADXL345_ADDR);
  Wire.write(0x2D);            // Power control register
  Wire.write(0x08);            // Set to measurement mode
  Wire.endTransmission();
  Serial.println("StartWire DOne");

  // Configure LED/Buzzer as output
  pinMode(led, OUTPUT);
  digitalWrite(led, LOW); // Ensure it's initially off

  servo.attach(9);

  Serial.println("System initialized.");
}

void loop() {
  // HX711: Get weight
  float weight = scale.get_units(10); // Average over 10 readings

  // FSR: Get force, stress, and strain
  int fsrReading = analogRead(fsrPin);
  float fsrVoltage = (fsrReading / 1023.0) * 5.0;
  float fsrResistance = (5.0 - fsrVoltage) * resistor / fsrVoltage;
  float force = calculateForceFromResistance(fsrResistance);
  float stress = force;
  double strain = stress / materialModulus;
  double fsrmass = force / 9.8;

  // Accelerometer: Get averaged readings
  x_sum = y_sum = z_sum = 0;
  for (int i = 0; i < NUM_SAMPLES; i++) {
    // Request accelerometer data
    Wire.beginTransmission(ADXL345_ADDR);
    Wire.write(0x32); // Starting register for accelerometer data
    Wire.endTransmission(false);
    Wire.requestFrom(ADXL345_ADDR, 6, true);

    // Read accelerometer values
    accX = (Wire.read() | (Wire.read() << 8));
    accY = (Wire.read() | (Wire.read() << 8));
    accZ = (Wire.read() | (Wire.read() << 8));

    // Add to sums
    x_sum += accX;
    y_sum += accY;
    z_sum += accZ;

    delay(10); // Short delay between samples
  }

  // Calculate averages
  x_avg = x_sum / (float)NUM_SAMPLES;
  y_avg = y_sum / (float)NUM_SAMPLES;
  z_avg = z_sum / (float)NUM_SAMPLES;

  // Print output: strain, stress, x, y, z, weight
  //Serial.print("Strain:");
  Serial.print(strain * 1000, 7); // Convert strain to millistrain//
  Serial.print(",");
  //Serial.print("stress");
  Serial.print(stress, 3); // Stress in Pa
  Serial.print(",");
  //Serial.print("x_avg");
  Serial.print(x_avg, 2); // X-axis accelerometer reading
  Serial.print(",");
  //Serial.print("y_avg");
  Serial.print(y_avg, 2); // Y-axis accelerometer reading
  Serial.print(",");
  //Serial.print("z_avg");
  Serial.print(z_avg, 2); // Z-axis accelerometer reading
  Serial.print(",");
  Serial.print(weight);
  Serial.print(",");
  Serial.println(fsrmass, 2); 
 
  // LED/Buzzer Logic
  if (weight > 100) {
    digitalWrite(led, HIGH);
    delay(500);
    digitalWrite(led, LOW);
    servo.write(0);
  } else {
    servo.write(180);
    digitalWrite(led, LOW);  // Turn off LED/Buzzer if weight <= 100
  }

  delay(1000); // Wait 1 second before next reading
}
