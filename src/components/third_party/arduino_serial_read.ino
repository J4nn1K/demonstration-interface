void setup() {
  Serial.begin(9600);
}

void loop() {
  Serial.println(analogRead(A7));
  delay(1); // 100 Hz read
}
