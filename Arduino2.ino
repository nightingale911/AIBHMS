#include <Arduino.h>
#include <Wire.h>
#include "HX711.h"
#include <Servo.h>


Servo myServo;
int count;
// HX711 Pins
const int LOADCELL_DOUT_PIN = 5;
const int LOADCELL_SCK_PIN = 6;

// HX711 Object
HX711 scale;

// LED/Buzzer Pin
const int led = 13;

void setup() {
  // Serial setup
  Serial.begin(57600);
  //Serial.println("Initializing HX711 scale...");
  scale.begin(LOADCELL_DOUT_PIN, LOADCELL_SCK_PIN);
  scale.set_scale(-104.653465); // Set calibration scale //-104.653465
  scale.tare();                // Reset scale to 0
  myServo.attach(9);
  // Configure LED/Buzzer as output
  myServo.write(90);
  pinMode(led, OUTPUT);
  digitalWrite(led, LOW); // Ensure it's initially off

  //Serial.println("System initialized.");
}

void loop() {
  
  
  // HX711: Get weight
  float weight = scale.get_units(10); // Average over 10 readings


  

  
  Serial.println(weight);
 
  // LED/Buzzer Logic
  if (weight > 100) {
    digitalWrite(led, HIGH);
    count=1;
    myServo.write(0);
    delay(500);
    digitalWrite(led, LOW);
  } else {
    if(count==1){
      myServo.write(90);
      count=0;
    }
    digitalWrite(led, LOW);  // Turn off LED/Buzzer if weight <= 100
  }

  delay(1000); // Wait 1 second before next reading
}
