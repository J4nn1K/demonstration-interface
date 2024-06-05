const int redLEDPin = 2;
const int greenLEDPin = 3;
const int buttonPin = 13;
const int potPin = A7;

int buttonState = 0;

int minPotValue = 1023;
int maxPotValue = 0;

int potValue = 0;
float filteredPotValue = 0.0; 
const float alpha = 0.9; // Smoothing factor 

void setup() {
  pinMode(buttonPin, INPUT);
  pinMode(redLEDPin, OUTPUT);
  pinMode(greenLEDPin, INPUT);
  
  Serial.begin(115200);

  filteredPotValue = analogRead(potPin);
}

void loop() {

  // Read potentiometer state and auto-calibrate
  potValue = analogRead(potPin);
  if (potValue < minPotValue) {
    minPotValue = potValue;
  } else if (potValue > maxPotValue) {
    maxPotValue = potValue;
  }
  // Apply a lag filter
  filteredPotValue = alpha * potValue + (1 - alpha) * filteredPotValue;

  // Read button state
  buttonState = digitalRead(buttonPin);
  
  // Send data via serial port
  String dataString = String(map(filteredPotValue, minPotValue, maxPotValue, 0, 100)) + "," + String(buttonState);
  Serial.println(dataString);
  
  delay(10); // 100 Hz read
}
