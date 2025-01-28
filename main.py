###########################
# Author: Agosh Saini
# Date: 2024-10-02
###########################

########################### IMPORTS ###########################
import threading
import time
import csv
import datetime
import os
import queue
import tkinter as tk
import signal

# Import the instrument classes
from ampmeter import Keithley2450
from mfc import MFCDevice
from relay_controller import RelayController

# Import environment variables
from env import env

# Import the UI module
import ui_module

########################### GLOBAL VARIABLES ###########################
recording = False  # Recording state
lock = threading.Lock()  # Thread lock for shared resources
exit_event = threading.Event()  # Event for graceful shutdown

########################### MAIN APPLICATION ###########################
def main():
    """
    The main function initializes the GUI application, devices, and starts the Tkinter event loop.
    It also sets up signal handlers for graceful shutdown.
    """
    global recording  # Declare global recording variable
    global ui_elements  # Make ui_elements accessible in on_closing()
    global root  # Make root accessible in on_closing()

    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, lambda sig, frame: exit_event.set())
    signal.signal(signal.SIGTERM, lambda sig, frame: exit_event.set())

    # Create the main application window
    root = tk.Tk()
    root.title("Keithley Data Recorder, MFC Control, and Relay System")
    root.state('zoomed')  # Maximize the window

    # Initialize the Keithley Ammeter
    resource_address = env.KEITHLEY
    try:
        with lock:
            keithley = Keithley2450(resource_address)
            print("Keithley device initialized successfully.")
    except Exception as e:
        print(f"Failed to initialize Keithley device: {e}")
        keithley = None  # Proceed without the device

    # Initialize MFC Devices (will be set in the UI)
    mfc_devices = {
        'MFC 1': None,
        'MFC 2': None,
        'MFC 3': None,
    }

    # Initialize relay_controller as None
    relay_controller = None

    # Data structures for logging
    data_records = []
    data_queue = queue.Queue()  # Thread-safe queue for data communication

    # Initialize the UI and get UI elements 
    ui_elements = ui_module.create_ui(
        root, keithley, mfc_devices, relay_controller,
        start_recording_callback=start_recording,
        stop_recording_callback=stop_recording,
        update_relay_com_callback=update_relay_com,
        update_mfc_com_callback=update_mfc_com,
        reset_mfcs_callback=reset_mfcs,
        set_mfc_rates_callback=set_mfc_rates,
        set_mfc_flow_callback=set_mfc_flow,
        close_connections_callback=close_connections
    )

    # Handle window close event
    def on_closing():
        """
        Handles the event when the user closes the main window.
        """
        # Set the exit event
        exit_event.set()
        # Stop recording if it's running
        if recording:
            stop_recording(ui_elements)
        # Destroy the root window
        root.destroy()
        print("Application closed by user.")

    root.protocol("WM_DELETE_WINDOW", on_closing)

    # Start the Tkinter main loop
    try:
        root.mainloop()
    except KeyboardInterrupt:
        pass
    finally:
        # Ensure devices are closed when the application exits
        close_connections(ui_elements)
        print("Application closed.")

########################### CALLBACK FUNCTIONS ###########################
def start_recording(ui_elements):
    """
    Starts the data recording process in a separate thread and updates UI elements.
    """
    global recording, data_records
    if not recording:
        recording = True
        data_records = []  # Clear previous data
        ui_elements['start_button'].config(state='disabled')
        ui_elements['stop_button'].config(state='normal')
        print("Recording started.")

        # Start the recording thread
        threading.Thread(target=record_data, args=(ui_elements,), daemon=True).start()
        # Start the plot updating
        ui_elements['root'].after(1000, lambda: update_plot(ui_elements))

def stop_recording(ui_elements):
    """
    Stops the data recording process and updates UI elements.
    """
    global recording
    if recording:
        recording = False
        ui_elements['start_button'].config(state='normal')
        ui_elements['stop_button'].config(state='disabled')
        print("Recording stopped.")

def update_relay_com(com_var, ui_elements, relay_status_label):
    """
    Updates the COM port for the relay controller and reinitializes the connection.
    """
    com_port = com_var.get()
    try:
        # Close the current connection if it exists
        if ui_elements['relay_controller']:
            with lock:
                ui_elements['relay_controller'].close()
            print("Previous relay controller connection closed.")

        # Initialize a new RelayController
        with lock:
            relay_controller = RelayController(port=com_port)
        ui_elements['relay_controller'] = relay_controller
        relay_status_label.config(text=f"Connected to Arduino on port {com_port}")
        print(f"Connected to Arduino on port {com_port}")
    except Exception as e:
        relay_status_label.config(text=f"Error connecting to Arduino: {e}")
        print(f"Error connecting to Arduino: {e}")

def update_mfc_com(mfc_name, com_var, status_labels, mfc_devices):
    """
    Updates the COM port for a specified MFC device and reinitializes the connection.
    """
    com_port = com_var.get()
    try:
        # Close the current connection
        if mfc_devices[mfc_name]:
            with lock:
                mfc_devices[mfc_name].close()
            print(f"Previous connection for {mfc_name} closed.")

        # Re-initialize the MFCDevice with the new COM port
        with lock:
            mfc_devices[mfc_name] = MFCDevice(com_port)
        status_labels[mfc_name].config(text=f"Using COM Port: {com_port}")
        print(f"{mfc_name} connected on {com_port}.")
    except Exception as e:
        status_labels[mfc_name].config(text=f"Error: {e}")
        print(f"Error connecting {mfc_name} on {com_port}: {e}")
        mfc_devices[mfc_name] = None  # Ensure the device is set to None on failure

def reset_mfcs(mfc_devices, status_labels):
    """
    Resets all connected MFC devices to a flow rate of 0%.
    """
    for mfc_name, mfc in mfc_devices.items():
        try:
            if mfc:
                with lock:
                    mfc.write_setpoint(0, units=57)  # Set flow rate to 0%
                status_labels[mfc_name].config(text=f"Flow Rate Set to: 0%")
                print(f"{mfc_name} flow rate reset to 0%.")
        except Exception as e:
            status_labels[mfc_name].config(text=f"Error resetting {mfc_name}: {e}")
            print(f"Error resetting {mfc_name}: {e}")

def set_mfc_rates(mfc_rates, flow_vars, mfc_devices, status_labels):
    """
    Sets the flow rates for all MFC devices based on the provided rates.
    """
    for mfc_name, rate in mfc_rates.items():
        flow_var = flow_vars[mfc_name]
        flow_var.set(rate)
        set_mfc_flow(mfc_name, flow_var, mfc_devices, status_labels)

def set_mfc_flow(mfc_name, flow_var, mfc_devices, status_labels):
    """
    Sets the flow rate for a specific MFC device based on user input.
    """
    try:
        mfc = mfc_devices[mfc_name]
        if not mfc:
            status_labels[mfc_name].config(text=f"{mfc_name} not connected.")
            print(f"{mfc_name} not connected.")
            return
        flow_rate = float(flow_var.get())
        with lock:
            mfc.write_setpoint(flow_rate, units=57)
        status_labels[mfc_name].config(text=f"Flow Rate Set to: {flow_rate}%")
        print(f"{mfc_name} flow rate set to {flow_rate}%.")
    except Exception as e:
        status_labels[mfc_name].config(text=f"Error: {e}")
        print(f"Error setting flow rate for {mfc_name}: {e}")

def close_connections(ui_elements):
    """
    Closes all open connections to hardware devices when the application exits.
    """
    # Unpack UI elements
    keithley = ui_elements['keithley']
    mfc_devices = ui_elements['mfc_devices']
    relay_controller = ui_elements['relay_controller']
    try:
        if keithley:
            with lock:
                keithley.instrument.write('OUTP OFF')
                keithley.close()
            print("Keithley device closed.")
    except Exception as e:
        print(f"Error closing Keithley device: {e}")
    for mfc in mfc_devices.values():
        try:
            if mfc:
                with lock:
                    mfc.close()
                print(f"MFC device {mfc} closed.")
        except Exception as e:
            print(f"Error closing MFC device {mfc}: {e}")
    try:
        if relay_controller:
            with lock:
                relay_controller.close()
            print("Relay controller connection closed.")
    except Exception as e:
        print(f"Error closing relay controller: {e}")

########################### DATA RECORDING FUNCTION ###########################
def record_data(ui_elements):
    """
    The core function that handles the data recording loop.
    It cycles through predefined phases, adjusts MFC flow rates,
    switches relays, measures resistance, and records data.
    """
    global recording, data_records
    start_time = time.time()

    # Unpack UI elements
    data_label = ui_elements['data_label']
    start_button = ui_elements['start_button']
    stop_button = ui_elements['stop_button']
    cycle_vars = ui_elements['cycle_vars']
    num_repeats_var = ui_elements['num_repeats_var']
    mfc_adjustments = ui_elements['mfc_adjustments']
    relay_delay_var = ui_elements['relay_delay_var']
    relay_controller = ui_elements['relay_controller']
    mfc_devices = ui_elements['mfc_devices']
    reset_mfcs = ui_elements['reset_mfcs']
    set_mfc_rates = ui_elements['set_mfc_rates']
    data_queue = ui_elements['data_queue']
    relay_plot_data = ui_elements['relay_plot_data']
    keithley = ui_elements['keithley']
    relay_status_label = ui_elements['relay_status_label']
    flow_vars = ui_elements['flow_vars']
    status_labels = ui_elements['status_labels']
    experiment_duration_var = ui_elements['experiment_duration_var']
    remaining_time_var = ui_elements['remaining_time_var']
    current_cycle_var = ui_elements['current_cycle_var']

    # Retrieve selected relays
    selected_relays = [
        relay_num for relay_num, var in ui_elements['relay_vars'].items() if var.get()
    ]

    if not selected_relays:
        data_label.config(text="No relays selected. Please select at least one relay.")
        print("No relays selected. Please select at least one relay.")
        recording = False
        start_button.config(state='normal')
        stop_button.config(state='disabled')
        return

    if not relay_controller:
        data_label.config(text="Relay controller not connected.")
        print("Relay controller not connected.")
        return

    if not keithley:
        data_label.config(text="Keithley device not connected.")
        print("Keithley device not connected.")
        return

    try:
        # Build cycles from user input
        cycles, total_experiment_duration = build_cycles(ui_elements)
        experiment_duration_var.set(f"Total Duration: {int(total_experiment_duration)} s")
        current_cycle_index = 0
        cycle_start_time = start_time
        current_cycle = cycles[current_cycle_index]
        set_mfc_rates(current_cycle['mfc_rates'], flow_vars, mfc_devices, status_labels)  # Set initial MFC rates
        current_cycle_var.set(f"Current Cycle: {current_cycle['name']}")

        # Initialize relay_plot_data
        for relay_num in selected_relays:
            ui_elements['relay_plot_data'][relay_num]['times'] = []
            ui_elements['relay_plot_data'][relay_num]['values'] = []

        while recording and not exit_event.is_set():
            current_time = time.time()
            elapsed_time = current_time - start_time
            cycle_elapsed_time = current_time - cycle_start_time
            remaining_time = max(0, total_experiment_duration - elapsed_time)
            remaining_time_var.set(f"Time Remaining: {int(remaining_time)} s")

            # Check if we need to move to the next cycle
            if cycle_elapsed_time >= current_cycle['duration']:
                current_cycle_index += 1
                if current_cycle_index >= len(cycles):
                    # All cycles completed
                    recording = False
                    start_button.config(state='normal')
                    stop_button.config(state='disabled')
                    print("All cycles completed.")
                    break
                else:
                    # Move to the next cycle
                    current_cycle = cycles[current_cycle_index]
                    cycle_start_time = current_time
                    set_mfc_rates(current_cycle['mfc_rates'], flow_vars, mfc_devices, status_labels)  # Set new MFC rates
                    current_cycle_var.set(f"Current Cycle: {current_cycle['name']}")
                    print(f"Starting new cycle: {current_cycle['name']}")

            # Perform measurements
            measure_and_record(
                elapsed_time,
                relay_controller,
                keithley,
                mfc_devices,
                data_records,
                data_queue,
                data_label,
                ui_elements  # Pass ui_elements here
            )
            time.sleep(0.1)  # Data resolution of 0.1 seconds

    except Exception as e:
        print(f"Unexpected error during data recording: {e}")
    finally:
        # Turn off the Keithley output after measurements are done
        if keithley:
            with lock:
                keithley.instrument.write('OUTP OFF')
            print("Keithley output turned off.")

        # Set MFC flow rates to 0
        reset_mfcs(mfc_devices, status_labels)

        # Turn off all relays
        if relay_controller:
            with lock:
                relay_controller.send_relay_command(0)
            print("All relays turned off.")

        # After recording stops, save data to CSV
        save_data_to_csv(data_records, data_label, ui_elements)
        print("Data recording completed.")

def build_cycles(ui_elements):
    """
    Builds the cycles from user input and calculates the total experiment duration.
    """
    cycle_vars = ui_elements['cycle_vars']
    num_repeats_var = ui_elements['num_repeats_var']
    mfc_adjustments = ui_elements['mfc_adjustments']
    data_label = ui_elements['data_label']
    mfc_devices = ui_elements['mfc_devices']  # Added this line

    # Initialize cycles
    base_cycles = []
    total_experiment_duration = 0
    for cycle_name in ['Pre-Cycle', 'Run-On Cycle', 'Off Cycle']:
        duration_str = cycle_vars[cycle_name]['duration'].get()
        try:
            duration = float(duration_str)
            print(f"{cycle_name} duration: {duration} seconds")
        except ValueError:
            data_label.config(text=f"Invalid duration for {cycle_name}. Using default value of 0.")
            print(f"Invalid duration for {cycle_name}. Using default value of 0.")
            duration = 0
        mfc_rates = {}
        for mfc_name in ['MFC 1', 'MFC 2', 'MFC 3']:
            rate_str = cycle_vars[cycle_name]['mfc_rates'][mfc_name].get()
            try:
                rate = float(rate_str)
                print(f"{cycle_name} - {mfc_name} flow rate: {rate}%")
            except ValueError:
                data_label.config(text=f"Invalid rate for {mfc_name} in {cycle_name}. Using default value of 0.")
                print(f"Invalid rate for {mfc_name} in {cycle_name}. Using default value of 0.")
                rate = 0
            mfc_rates[mfc_name] = rate
        base_cycles.append({
            'name': cycle_name,
            'duration': duration,
            'mfc_rates': mfc_rates,
        })

    # Get number of repeats
    try:
        num_repeats = int(num_repeats_var.get())
        if num_repeats < 1:
            raise ValueError
        print(f"Number of repeats: {num_repeats}")
    except ValueError:
        data_label.config(text=f"Invalid number of repeats. Using default value of 1.")
        print(f"Invalid number of repeats. Using default value of 1.")
        num_repeats = 1

    # Get MFC adjustment values
    try:
        mfc_adjustment_values = {mfc_name: float(adj_var.get()) for mfc_name, adj_var in mfc_adjustments.items()}
        print(f"MFC adjustment values per repeat: {mfc_adjustment_values}")
    except ValueError:
        data_label.config(text="Invalid MFC adjustment values. Using default value of 0.")
        print("Invalid MFC adjustment values. Using default value of 0.")
        mfc_adjustment_values = {mfc_name: 0 for mfc_name in mfc_devices.keys()}

    # Build full cycle list with repeats and adjustments
    cycles = []
    total_experiment_duration += base_cycles[0]['duration']

    # Add Pre-Cycle once
    pre_cycle = base_cycles[0]
    cycles.append({
        'name': pre_cycle['name'],
        'duration': pre_cycle['duration'],
        'mfc_rates': pre_cycle['mfc_rates'],
    })

    # Get the Run-On and Off cycles
    on_cycle = base_cycles[1]
    off_cycle = base_cycles[2]

    for repeat in range(num_repeats):
        adjustment_multiplier = repeat  # Adjustments increase each repeat

        # Adjusted Run-On Cycle
        adjusted_mfc_rates = on_cycle['mfc_rates'].copy()
        for mfc_name in ['MFC 1', 'MFC 2', 'MFC 3']:
            base_rate = on_cycle['mfc_rates'][mfc_name]
            adjustment = mfc_adjustment_values.get(mfc_name, 0) * adjustment_multiplier
            adjusted_rate = base_rate + adjustment
            adjusted_mfc_rates[mfc_name] = adjusted_rate
        adjusted_cycle = {
            'name': f"{on_cycle['name']} (Repeat {repeat + 1})",
            'duration': on_cycle['duration'],
            'mfc_rates': adjusted_mfc_rates,
        }
        cycles.append(adjusted_cycle)
        total_experiment_duration += on_cycle['duration']

        # Off Cycle (no adjustments)
        cycles.append({
            'name': f"{off_cycle['name']} (Repeat {repeat + 1})",
            'duration': off_cycle['duration'],
            'mfc_rates': off_cycle['mfc_rates'],
        })
        total_experiment_duration += off_cycle['duration']

    return cycles, total_experiment_duration

def measure_and_record(
    elapsed_time,
    relay_controller,
    keithley,
    mfc_devices,
    data_records,
    data_queue,
    data_label,
    ui_elements
):
    """
    Measures resistance for each selected relay, reads MFC flow rates, and records the data.
    """
    try:
        relay_resistances = {}
        relay_delay = float(ui_elements['relay_delay_var'].get())

        # Retrieve selected relays from UI
        selected_relays = [
            relay_num for relay_num, var in ui_elements['relay_vars'].items() if var.get()
        ]

        # Check if exit_event is set before starting measurements
        if exit_event.is_set():
            return

        # Measure resistance for each selected relay
        for relay_number in selected_relays:
            # Check if exit_event is set to exit early
            if exit_event.is_set():
                return

            # Switch to the relay
            with lock:
                relay_controller.send_relay_command(relay_number)
            print(f"Switched to Relay {relay_number}")

            # Wait for the relay to switch
            time.sleep(relay_delay)

            # Measure resistance and voltage using the Keithley device
            try:
                with lock:
                    current_measurement, voltage_measurement, resistance_measurement = keithley.measure_all()
                print(
                    f"Measured Relay {relay_number}: Current={current_measurement} A, "
                    f"Voltage={voltage_measurement} V, Resistance={resistance_measurement} Ohms"
                )
                # Store the resistance value
                relay_resistances[f'Relay {relay_number} Resistance'] = resistance_measurement
            except Exception as e:
                data_label.config(text=f"Error measuring resistance on Relay {relay_number}: {e}")
                print(f"Error measuring resistance on Relay {relay_number}: {e}")
                relay_resistances[f'Relay {relay_number} Resistance'] = None

        # Turn off all relays
        with lock:
            relay_controller.send_relay_command(0)
        print("Turned off all relays")

        # Get flow rates from MFCs sequentially
        flow_rates = {}
        for mfc_name, mfc in mfc_devices.items():
            if not mfc:
                flow_rates[mfc_name] = 'N/A'
                continue
            # Read setpoint with retries
            for attempt in range(3):
                try:
                    with lock:
                        percent_sp, setpoint_value, units = mfc.read_setpoint()
                    flow_rates[mfc_name] = setpoint_value
                    print(f"{mfc_name} flow rate read as {setpoint_value}%")
                    break  # Exit the retry loop if successful
                except Exception as e:
                    if attempt < 2:
                        time.sleep(0.5)
                    else:
                        data_label.config(text=f"Failed to read from {mfc_name}: {e}")
                        print(f"Failed to read from {mfc_name}: {e}")
                        flow_rates[mfc_name] = 'N/A'
            # Wait before moving to the next MFC
            time.sleep(0.05)

        # Get timestamp
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]  # Include milliseconds

        # Prepare data record
        record = {
            'Time': timestamp,
            'Elapsed Time (s)': round(elapsed_time, 3),
            'Voltage (V)': voltage_measurement,
            'MFC A Flow Rate': flow_rates.get('MFC 1', 'N/A'),
            'MFC B Flow Rate': flow_rates.get('MFC 2', 'N/A'),
            'MFC C Flow Rate': flow_rates.get('MFC 3', 'N/A'),
            'Cycle': ui_elements['current_cycle_var'].get().replace("Current Cycle: ", ""),
        }
        # Add relay resistances to the record
        record.update(relay_resistances)
        data_records.append(record)
        print(f"Data recorded at {timestamp}")

        # Put data into the queue for the UI thread
        data_queue.put({'elapsed_time': elapsed_time, 'relay_resistances': relay_resistances})

    except Exception as e:
        data_label.config(text=f"Error reading data: {e}")
        print(f"Error reading data: {e}")

########################### DATA SAVING FUNCTION ###########################
def save_data_to_csv(data_records, data_label, ui_elements):
    """
    Saves the recorded data to a CSV file with a timestamped filename.
    """
    # Retrieve selected relays
    selected_relays = [
        relay_num for relay_num, var in ui_elements['relay_vars'].items() if var.get()
    ]

    # Create a directory for data logs if it doesn't exist
    if not os.path.exists('data_logs'):
        os.makedirs('data_logs')
    # Generate filename with timestamp
    filename = datetime.datetime.now().strftime('data_logs/data_log_%Y%m%d_%H%M%S.csv')
    # Prepare fieldnames
    fieldnames = ['Time', 'Elapsed Time (s)', 'Voltage (V)']
    # Add relay resistance columns for selected relays
    for relay_number in selected_relays:
        fieldnames.append(f'Relay {relay_number} Resistance')
    # Add MFC flow rate columns
    fieldnames.extend(['MFC A Flow Rate', 'MFC B Flow Rate', 'MFC C Flow Rate', 'Cycle'])
    try:
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for record in data_records:
                writer.writerow(record)
        data_label.config(text=f"Data saved to {filename}")
        print(f"Data saved to {filename}")
    except Exception as e:
        data_label.config(text=f"Error saving data: {e}")
        print(f"Error saving data: {e}")

########################### PLOT UPDATING FUNCTION ###########################
def update_plot(ui_elements):
    """
    Updates the matplotlib plot with the latest resistance measurements from selected relays.
    """
    data_queue = ui_elements['data_queue']
    relay_plot_data = ui_elements['relay_plot_data']
    ax = ui_elements['ax']
    fig = ui_elements['fig']
    root = ui_elements['root']
    try:
        # Process data from the queue
        while not data_queue.empty():
            data = data_queue.get()
            elapsed_time = data['elapsed_time']
            relay_resistances = data['relay_resistances']
            # Update relay_plot_data
            for key, resistance in relay_resistances.items():
                relay_num = int(key.split()[1])  # Extract relay number
                if resistance is not None and isinstance(resistance, (int, float)):
                    relay_plot_data[relay_num]['times'].append(elapsed_time)
                    relay_plot_data[relay_num]['values'].append(resistance)
        # Clear axes
        ax.clear()
        ax.set_xlabel('Elapsed Time (s)')
        ax.set_ylabel('Resistance (Ohms)')
        ax.set_title('Real-Time Resistance Measurement (Selected Relays)')
        # Retrieve selected relays
        selected_relays = [
            relay_num for relay_num, var in ui_elements['relay_vars'].items() if var.get()
        ]
        # Plot each selected relay's data
        colors = ['red', 'blue', 'green', 'orange', 'purple', 'brown', 'pink', 'gray']
        for idx, relay_num in enumerate(selected_relays):
            times = relay_plot_data[relay_num]['times']
            values = relay_plot_data[relay_num]['values']
            if times and values:
                ax.plot(times, values, label=f'Relay {relay_num}', color=colors[(relay_num - 1) % len(colors)])
        ax.legend()
        fig.canvas.draw()
    except Exception as e:
        print(f"Error updating plot: {e}")
    finally:
        if not exit_event.is_set():
            root.after(1000, lambda: update_plot(ui_elements))

if __name__ == "__main__":
    main()
