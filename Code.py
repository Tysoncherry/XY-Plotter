#include <stdio.h>
#include <Arduino.h>
#include <Wire.h>
#include <BluetoothSerial.h>
#include <SCMD.h>
#include "SCMD_config.h"

#define LEFT_MOTOR 1
#define RIGHT_MOTOR 0

const int LeftLimit = 15;
const int UpLimit = 12;
const int Emergency = 21;

bool LeftLimitState = false;
bool UpLimitState = false;
bool EmergencyState = false;
bool EmergencyStop = false;
bool InsideHouse = false;
bool reset = false;

BluetoothSerial bluetooth;
SCMD qwiicMotorDriver;

void setup() {
  bluetooth.begin("Esp32 Bluetooth Interface");
  Serial.begin(9600);
  Serial.println("Starting sketch.");
  configureMotorDriver();
  pinMode(LeftLimit, INPUT_PULLUP);
  pinMode(UpLimit, INPUT_PULLUP);
  pinMode(Emergency, INPUT_PULLUP);
}

void configureMotorDriver() {
  qwiicMotorDriver.settings.commInterface = I2C_MODE;
  qwiicMotorDriver.settings.I2CAddress = 0x5D;
  qwiicMotorDriver.settings.chipSelectPin = 10;

  while (qwiicMotorDriver.begin() != 0xA9) {
    Serial.println("ID mismatch, trying again");
    delay(500);
  }
  Serial.println("ID matches 0xA9");

  Serial.print("Waiting for enumeration...");
  while (!qwiicMotorDriver.ready());
  Serial.println("Done.");

  configureMotors();
  qwiicMotorDriver.enable();
}

void configureMotors() {
  while ( qwiicMotorDriver.busy() ); //Waits until the SCMD is available.
  qwiicMotorDriver.inversionMode(1, 1); //invert motor 1
  while ( qwiicMotorDriver.busy() );
  qwiicMotorDriver.enable(); //Enables the output driver hardware
}

void move(char* direction, int speed, int duration) {
  if (reset == false){
    if (direction == "Right"){
      qwiicMotorDriver.setDrive( LEFT_MOTOR, 0, speed); 
      qwiicMotorDriver.setDrive( RIGHT_MOTOR, 0, speed);
      delay(duration);
    } else if (direction == "Left"){
      qwiicMotorDriver.setDrive( LEFT_MOTOR, 1, speed); 
      qwiicMotorDriver.setDrive( RIGHT_MOTOR, 1, speed);
      delay(duration);
    } else if (direction == "Down"){
      qwiicMotorDriver.setDrive( LEFT_MOTOR, 0, speed); 
      qwiicMotorDriver.setDrive( RIGHT_MOTOR, 1, speed);
      delay(duration);
    } else if (direction == "Up"){
      qwiicMotorDriver.setDrive( LEFT_MOTOR, 1, speed); 
      qwiicMotorDriver.setDrive( RIGHT_MOTOR, 0, speed);
      delay(duration);
    } else if (direction == "Bottom Left"){
      qwiicMotorDriver.setDrive( LEFT_MOTOR, 0, (speed/10)); 
      qwiicMotorDriver.setDrive( RIGHT_MOTOR, 1, speed);
      delay(duration);;
    } else if (direction == "Top Right"){
      qwiicMotorDriver.setDrive( LEFT_MOTOR, 0, (speed/10)); 
      qwiicMotorDriver.setDrive( RIGHT_MOTOR, 0, speed);
      delay(duration);;
    } else if (direction == "Top Left"){
      qwiicMotorDriver.setDrive( LEFT_MOTOR, 1, speed); 
      qwiicMotorDriver.setDrive( RIGHT_MOTOR, 0, (speed/10));
      delay(duration);
    } else if (direction == "Bottom Right"){
      qwiicMotorDriver.setDrive( LEFT_MOTOR, 0, speed); 
      qwiicMotorDriver.setDrive( RIGHT_MOTOR, 0, (speed/10));
      delay(duration);
    }
  } else{
    stopMotors(0);
  }
}

void stopMotors(int duration) {
  qwiicMotorDriver.setDrive(LEFT_MOTOR, 0, 0);
  qwiicMotorDriver.setDrive(RIGHT_MOTOR, 0, 0);
  delay(duration);
}

void readSwitches() {
  LeftLimitState = digitalRead(LeftLimit);
  UpLimitState = digitalRead(UpLimit);
  EmergencyState = digitalRead(Emergency);
}

void checkLimits() {
  readSwitches();
  Serial.println("Checking Limits");
  if(LeftLimitState == HIGH || UpLimitState == HIGH ){
    moveToHome();
  }  
  if(EmergencyState == HIGH){
    EmergencyStop = true;
  }
}

void moveToHome() {
  Serial.println("Moving To Home Position");
  readSwitches();
  while (LeftLimitState == LOW)
  {
    move("Left", 175, 500);
    readSwitches();
  }
  while (UpLimitState == LOW)
  {
    move("Up", 175, 500);
    readSwitches();
  }
  move("Down", 200, 1750);
  stopMotors(500);
  move("Right", 200, 1750);
  stopMotors(500);

  if (InsideHouse == true)
  {
    reset = true;
  }
}

void draw(char* direction, int speed, int duration, int stopDuration){
  checkLimits();
  move(direction, speed, duration);
  stopMotors(stopDuration);
}

void drawNicolasHouse() {
  checkLimits();
  Serial.println("Nicolas' House loading...");
  InsideHouse = true;
  
  if(EmergencyStop){stopMotors(0); return;}
  draw("Up", 175, 600, 500);
  if(EmergencyStop){stopMotors(0); return;}
  draw("Left", 175, 650, 500);
  if(EmergencyStop){stopMotors(0); return;}
  draw("Down", 175, 600, 500);
  if(EmergencyStop){stopMotors(0); return;}
  draw("Right", 175, 625, 750);
  if(EmergencyStop){stopMotors(0); return;}
  draw("Top Left", 200, 1000, 750);
  if(EmergencyStop){stopMotors(0); return;}
  draw("Top Right", 200, 600, 750);
  if(EmergencyStop){stopMotors(0); return;}
  draw("Bottom Right", 200, 490, 750);
  if(EmergencyStop){stopMotors(0); return;}
  draw("Bottom Left", 200, 1300, 500);
  if(EmergencyStop){stopMotors(0); return;}

}

void loop() {

  if (bluetooth.available()) {
    checkLimits();
    char cmd = bluetooth.read();
    if (cmd == '1') {
      moveToHome();
      while (cmd != '0') {
        cmd = bluetooth.read();
        reset = false;
        if (cmd == '0') {
          Serial.println("STOP command received in Bluetooth Terminal");
          break;
        }
        drawNicolasHouse();
      }
    }else if (cmd == '2') {
      moveToHome();
    }
  } else {
    if (!EmergencyStop) {
      Serial.println("Select Input");
    } else {
      Serial.println("Emergency STOP activated. Reset to start drawing.");
    }
  }
}

