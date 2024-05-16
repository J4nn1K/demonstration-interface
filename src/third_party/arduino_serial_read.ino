void setup() {
  Serial.begin(9600);
}

void loop() {
  Serial.println(analogRead(A7));
  delay(10); // 100 Hz read
}
