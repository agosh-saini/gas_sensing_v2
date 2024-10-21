###########################
# Author: Agosh Saini - using GPT-1o-preview model
# Contact: contact@agoshsaini.com
# Date: 2024-OCT-17
###########################

####################### IMPORTS #######################

import serial
import time
import threading

####################### CLASS DEFINITION #######################
class RelayController:
    def __init__(self, port='COM7', baudrate=9600, timeout=1):
        """
        Initialize the serial connection to the Arduino.

        Parameters:
        - port: The serial port name (e.g., 'COM7' on Windows or '/dev/ttyACM0' on Linux).
        - baudrate: The baud rate matching the Arduino code (default is 9600).
        - timeout: Read timeout in seconds.
        """
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial_conn = None
        self.last_message = ''
        self.last_switch_time = 0.0  # Time taken to switch the relay
        self.cycle_thread = None  # Thread for continuous cycling
        self.stop_event = threading.Event()  # Event to signal the cycling thread to stop
        self.connect()

    def connect(self):
        """Establish the serial connection."""
        try:
            self.serial_conn = serial.Serial(self.port, self.baudrate, timeout=self.timeout)
            # Wait for Arduino to reset after establishing serial connection
            time.sleep(2)
            # Clear any initial messages from Arduino
            self.serial_conn.flushInput()
            print(f"Connected to Arduino on port {self.port}")
        except serial.SerialException as e:
            print(f"Error connecting to Arduino: {e}")

    def send_relay_command(self, relay_number):
        """
        Send a relay number to the Arduino to turn on/off relays.

        Parameters:
        - relay_number: Integer from 0 to 8 (0 turns off all relays).
        """
        if not self.serial_conn or not self.serial_conn.is_open:
            print("Serial connection not open.")
            return

        if not isinstance(relay_number, int) or not (0 <= relay_number <= 8):
            print("Invalid relay number. Must be an integer between 0 and 8.")
            return

        # Record the time before sending the command
        start_time = time.time()

        # Send the relay number followed by a newline character
        command = f"{relay_number}\n"
        self.serial_conn.write(command.encode('utf-8'))
        print(f"Sent command: {command.strip()}")

        # Read the response from Arduino
        self.read_messages()

        # Record the time after receiving the response
        end_time = time.time()

        # Calculate the time taken to switch the relay
        self.last_switch_time = end_time - start_time
        print(f"Time taken to switch relay {relay_number}: {self.last_switch_time:.6f} seconds")

    def read_messages(self):
        """Read messages from the Arduino and save the one prefixed with 'SAVE_MESSAGE:'."""
        start_time = time.time()
        while True:
            if self.serial_conn.in_waiting > 0:
                line = self.serial_conn.readline().decode('utf-8', errors='ignore').strip()
                if line:
                    print(f"Received: {line}")
                    # Check if the line contains the save message
                    if line.startswith("SAVE_MESSAGE:"):
                        self.last_message = line.replace("SAVE_MESSAGE:", "").strip()
                        print(f"Saved message: {self.last_message}")
                        break
            # Timeout after 2 seconds
            if time.time() - start_time > 2:
                print("No response from Arduino.")
                break

    def get_last_message(self):
        """Return the last saved message."""
        return self.last_message

    def get_last_switch_time(self):
        """Return the time taken for the last relay switch."""
        return self.last_switch_time

    def close(self):
        """Close the serial connection and stop any running cycles."""
        self.stop_cycle()  # Ensure cycling is stopped
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
            print("Serial connection closed.")

    def start_continuous_cycle(self, delay=0.1, message_handler=None):
        """
        Start continuously cycling through relays 1 to 8 until stopped.

        Parameters:
        - delay: Time in seconds to wait between switching relays.
        - message_handler: A callback function to handle the saved messages and timing information.
        """
        # Reset the stop event in case it was set previously
        self.stop_event.clear()

        # Define the cycling function to run in a separate thread
        def cycle_relays():
            while not self.stop_event.is_set():
                for relay in range(1, 9):
                    if self.stop_event.is_set():
                        break  # Exit inner loop if stop event is set
                    # Turn on the current relay
                    self.send_relay_command(relay)
                    # Get the saved message and switching time
                    message = self.get_last_message()
                    switch_time = self.get_last_switch_time()
                    print(f"Message to output to another function: {message}")
                    print(f"Switching time for relay {relay}: {switch_time:.6f} seconds")

                    # Pass the message and timing to the handler if provided
                    if message_handler:
                        message_handler(message, switch_time)

                    time.sleep(delay)  # Wait for the specified delay

            # After stopping, turn off all relays
            self.send_relay_command(0)
            message = self.get_last_message()
            switch_time = self.get_last_switch_time()
            print(f"Message to output to another function: {message}")
            print(f"Switching time for relay 0: {switch_time:.6f} seconds")
            if message_handler:
                message_handler(message, switch_time)

        # Start the cycling function in a new thread
        self.cycle_thread = threading.Thread(target=cycle_relays)
        self.cycle_thread.start()
        print("Started continuous cycling of relays.")

    def stop_cycle(self):
        """Stop the continuous cycling of relays."""
        if self.cycle_thread and self.cycle_thread.is_alive():
            self.stop_event.set()  # Signal the thread to stop
            self.cycle_thread.join()  # Wait for the thread to finish
            print("Stopped continuous cycling of relays.")

    def is_cycling(self):
        """Check if the relay controller is currently cycling."""
        return self.cycle_thread and self.cycle_thread.is_alive()

## Class to control the relay ##
class RelayManager:
    def __init__(self, controller):
        """
        Initialize the RelayManager with a RelayController instance.

        Parameters:
        - controller: An instance of RelayController.
        """
        self.controller = controller

    def start_relay_cycle(self, delay=0.1):
        """
        Start the relay cycling process.

        Parameters:
        - delay: Time in seconds to wait between switching relays.
        """
        if not self.controller.is_cycling():
            self.controller.start_continuous_cycle(delay=delay, message_handler=self.process_message)
            print("Relay cycling started.")
        else:
            print("Relay cycling is already running.")

    def stop_relay_cycle(self):
        """
        Stop the relay cycling process.
        """
        if self.controller.is_cycling():
            self.controller.stop_cycle()
            print("Relay cycling stopped.")
        else:
            print("Relay cycling is not running.")

    def process_message(self, message, switch_time):
        """
        Process the messages received from the RelayController along with timing information.

        Parameters:
        - message: The message string to process.
        - switch_time: The time taken to switch the relay.
        """
        # Implement any processing logic needed
        print(f"Processed message in RelayManager: {message}")
        print(f"Time taken for switch: {switch_time:.6f} seconds")

        # Example: You can log the timing data, send it to another program, or perform calculations
        # For demonstration, let's suppose we store it in a list
        # self.switch_times.append((message, switch_time))

####################### MAIN #######################

if __name__ == "__main__":
    # Replace 'COM7' with your Arduino's serial port
    controller = RelayController(port='COM7')

    # Create an instance of RelayManager
    relay_manager = RelayManager(controller=controller)

    try:
        # Start the relay cycling process
        relay_manager.start_relay_cycle(delay=0.05)

        # Simulate other operations in the main thread
        print("Main thread is running other tasks.")
        time.sleep(5)  # Wait for 5 seconds

        # At some point, decide to stop the relay cycling
        relay_manager.stop_relay_cycle()

        # Continue with other tasks or exit
        print("Relay cycling has been stopped from RelayManager.")

    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        # Ensure the relay cycling is stopped and the serial connection is closed
        controller.close()
