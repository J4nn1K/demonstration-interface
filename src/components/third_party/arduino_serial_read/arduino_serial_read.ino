void setup() {
  Serial.begin(115200);
}

void loop() {
  Serial.println(analogRead(A7));
  delay(1); // 1000 Hz read
}
