// Arduino Uno with two relay shields controlling 8 relays

// Define the pins connected to the relays
const int relayPins[] = {4,7,8,12,5,6,9,11}; // Adjust these pin numbers as needed

// Number of relays
const int numRelays = sizeof(relayPins) / sizeof(relayPins[0]);

// Relay logic levels for active HIGH relays
#define RELAY_ON  HIGH  // Define relay ON state as HIGH
#define RELAY_OFF LOW   // Define relay OFF state as LOW

void setup() {
  // Initialize serial communication for debugging or setting the interval
  Serial.begin(9600);

  // Initialize relay pins as outputs and turn them OFF
  for (int i = 0; i < numRelays; i++) {
    pinMode(relayPins[i], OUTPUT); // Set the relay pin as output
    digitalWrite(relayPins[i], RELAY_OFF); // Set to LOW to turn relay OFF initially
  }

  // Prompt the user to enter a relay number to turn ON or OFF
  Serial.println("Enter the relay number to turn ON (1 to 8) or 0 to turn OFF all relays:");
}

void loop() {
  // Check if there is user input
  if (Serial.available() > 0) {
    // Read the relay number from the serial input
    int relayNumber = Serial.parseInt();

    // Validate the input
    if (relayNumber == 0) {
      // Turn OFF all relays if the user enters 0
      for (int i = 0; i < numRelays; i++) {
        digitalWrite(relayPins[i], RELAY_OFF); // Set to LOW to turn relay OFF
      }
      // Inform the user that all relays are OFF
      Serial.print("SAVE_MESSAGE:");
      Serial.println("All relays OFF");
    } else if (relayNumber >= 1 && relayNumber <= numRelays) {
      // If a valid relay number is entered, turn OFF all relays first
      for (int i = 0; i < numRelays; i++) {
        digitalWrite(relayPins[i], RELAY_OFF); // Set to LOW to turn relay OFF
      }

      // Turn ON the selected relay
      int relayIndex = relayNumber - 1; // Convert relay number to array index (0-based)
      digitalWrite(relayPins[relayIndex], RELAY_ON); // Set to HIGH to turn relay ON

      // Inform the user which relay is turned ON
      String message = "Relay " + String(relayNumber) + " ON (Pin " + String(relayPins[relayIndex]) + ")";
      Serial.println(message);

      // Save the message to a variable to be used by Python
      Serial.print("SAVE_MESSAGE:");
      Serial.println(message);
    } else {
      // If an invalid relay number is entered, inform the user
      Serial.println("Invalid relay number. Enter a number between 1 and 8.");
    }

    // Clear the serial buffer to remove any remaining input data
    while (Serial.available() > 0) {
      Serial.read(); // Read and discard any remaining bytes in the buffer
    }
  }
}
