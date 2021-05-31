#include "SparkFun_AS7265X.h" //Click here to get the library: http://librarymanager/All#SparkFun_AS7265X
AS7265X sensor;
#include <Wire.h>

void setup() {
  
  Serial.begin(115200);
  while(!Serial); //We must wait for Teensy to come online
  
  if(sensor.begin() == false)
  {
    Serial.println("Sensor does not appear to be connected. Please check wiring. Freezing...");
    while(1);
  }
  Wire.setClock(400000);
  
  sensor.setGain(AS7265X_GAIN_64X);
  
  sensor.setMeasurementMode(AS7265X_MEASUREMENT_MODE_6CHAN_CONTINUOUS); //All 6 channels on all devices
  sensor.setIntegrationCycles(30); 
  //0 seems to cause the sensors to read very slowly
  //7*2.8ms = 19.6ms per reading = 51 Hz 
  
  sensor.setBulbCurrent(AS7265X_LED_CURRENT_LIMIT_100MA, AS7265x_LED_WHITE);
  sensor.setBulbCurrent(AS7265X_LED_CURRENT_LIMIT_12_5MA, AS7265x_LED_IR);

  sensor.enableInterrupt();
  sensor.disableIndicator();
  sensor.enableBulb(AS7265x_LED_WHITE);
  sensor.enableBulb(AS7265x_LED_IR);

}

void loop() {

  while(sensor.dataAvailable() == false) {} 
  
  Serial.print(micros());
  Serial.print(",");
  Serial.print(sensor.getCalibratedI(),16);
  Serial.print(",");
  Serial.print(sensor.getCalibratedS(),16);
  Serial.print(",");
  Serial.print(sensor.getCalibratedL(),16);
  
  Serial.println();
}