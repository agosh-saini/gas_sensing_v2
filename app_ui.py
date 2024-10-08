###########################
# Author: Agosh Saini - with ChatGPT
# Date: 2024-10-02
###########################

########################### IMPORTS ###########################
import tkinter as tk
from tkinter import ttk
import threading
import time
import csv
import datetime
import os
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import queue

# Import the Keithley and MFC classes
from ampmeter import Keithley2450
from mfc import MFCDevice

# Use Agg backend for Matplotlib
matplotlib.use("TkAgg")

########################### INITIALIZE ###########################
# Create the main application window
root = tk.Tk()
root.title("Keithley Data Recorder and MFC Control")
root.geometry("1200x900")

# Initialize cycle parameters
cycle_vars = {
    'Pre-Cycle': {
        'duration': tk.StringVar(value='10'),
        'mfc_rates': {
            'MFC 1': tk.StringVar(value='10'),
            'MFC 2': tk.StringVar(value='20'),
            'MFC 3': tk.StringVar(value='30'),
        },
    },
    'Run-On Cycle': {
        'duration': tk.StringVar(value='20'),
        'mfc_rates': {
            'MFC 1': tk.StringVar(value='40'),
            'MFC 2': tk.StringVar(value='50'),
            'MFC 3': tk.StringVar(value='60'),
        },
    },
    'Off Cycle': {
        'duration': tk.StringVar(value='10'),
        'mfc_rates': {
            'MFC 1': tk.StringVar(value='0'),
            'MFC 2': tk.StringVar(value='0'),
            'MFC 3': tk.StringVar(value='0'),
        },
    },
}

# User-defined parameters
num_repeats_var = tk.StringVar(value='1')  # Number of repeats
mfc_adjustments = {
    'MFC 1': tk.StringVar(value='0'),
    'MFC 2': tk.StringVar(value='0'),
    'MFC 3': tk.StringVar(value='0'),
}

# Initialize the Keithley Ammeter
resource_address = 'USB0::0x05E6::0x2450::04502549::INSTR'
keithley = Keithley2450(resource_address)

# Initialize MFC Devices
# We'll store them in a dictionary for easy access
mfc_devices = {
    'MFC 1': MFCDevice('COM3'),
    'MFC 2': MFCDevice('COM4'),
    'MFC 3': MFCDevice('COM5'),
}

# Variables to control the recording thread
recording = False
stop_time = None

# Data lists for logging
data_records = []
data_queue = queue.Queue()  # Thread-safe queue for data communication
cycle_plot_data = {}        # Data for plotting

########################### FUNCTIONS ###########################
# Function to handle data recording from Keithley
def record_data():
    global recording, stop_time, cycle_plot_data
    start_time = time.time()

    # Build cycles from user input
    base_cycles = []
    for cycle_name in ['Pre-Cycle', 'Run-On Cycle', 'Off Cycle']:
        duration_str = cycle_vars[cycle_name]['duration'].get()
        try:
            duration = float(duration_str)
        except ValueError:
            data_label.config(text=f"Invalid duration for {cycle_name}. Using default value of 0.")
            duration = 0
        mfc_rates = {}
        for mfc_name in ['MFC 1', 'MFC 2', 'MFC 3']:
            rate_str = cycle_vars[cycle_name]['mfc_rates'][mfc_name].get()
            try:
                rate = float(rate_str)
            except ValueError:
                data_label.config(text=f"Invalid rate for {mfc_name} in {cycle_name}. Using default value of 0.")
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
    except ValueError:
        data_label.config(text=f"Invalid number of repeats. Using default value of 1.")
        num_repeats = 1

    # Get MFC adjustment values
    try:
        mfc_adjustment_values = {mfc_name: float(adj_var.get()) for mfc_name, adj_var in mfc_adjustments.items()}
    except ValueError:
        data_label.config(text="Invalid MFC adjustment values. Using default value of 0.")
        mfc_adjustment_values = {mfc_name: 0 for mfc_name in mfc_devices.keys()}

    # Build full cycle list with repeats and adjustments
    cycles = []

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
            adjustment = mfc_adjustment_values[mfc_name] * adjustment_multiplier
            adjusted_rate = base_rate + adjustment
            adjusted_mfc_rates[mfc_name] = adjusted_rate
        adjusted_cycle = {
            'name': f"{on_cycle['name']} (Repeat {repeat + 1})",
            'duration': on_cycle['duration'],
            'mfc_rates': adjusted_mfc_rates,
        }
        cycles.append(adjusted_cycle)

        # Off Cycle (no adjustments)
        cycles.append({
            'name': f"{off_cycle['name']} (Repeat {repeat + 1})",
            'duration': off_cycle['duration'],
            'mfc_rates': off_cycle['mfc_rates'],
        })

    current_cycle_index = 0
    cycle_start_time = start_time
    current_cycle = cycles[current_cycle_index]
    set_mfc_rates(current_cycle['mfc_rates'])  # Set initial MFC rates

    # Initialize cycle plotting data
    cycle_plot_data = {}
    last_cycle_type = ''
    # Define colors for cycles
    cycle_colors = {
        'Pre-Cycle': 'blue',
        'Run-On Cycle': 'red',
        'Off Cycle': 'green'
    }

    try:
        while recording:
            current_time = time.time()
            elapsed_time = current_time - start_time
            cycle_elapsed_time = current_time - cycle_start_time

            # Check if we need to move to the next cycle
            if cycle_elapsed_time >= current_cycle['duration']:
                current_cycle_index += 1
                if current_cycle_index >= len(cycles):
                    # All cycles completed
                    recording = False
                    start_button.config(state='normal')
                    stop_button.config(state='disabled')
                    break
                else:
                    # Move to the next cycle
                    current_cycle = cycles[current_cycle_index]
                    cycle_start_time = current_time
                    set_mfc_rates(current_cycle['mfc_rates'])  # Set new MFC rates

            # Determine cycle type without repeat number
            cycle_type = current_cycle['name'].split(' (Repeat')[0]

            # If the cycle has changed, initialize plotting data if necessary
            if cycle_type != last_cycle_type:
                last_cycle_type = cycle_type
                # Initialize plotting data for the new cycle type
                if cycle_type not in cycle_plot_data:
                    cycle_plot_data[cycle_type] = {'times': [], 'values': [], 'color': cycle_colors.get(cycle_type, 'black')}

            try:
                # Measure current from the Keithley device
                current_measurement, voltage_measurement, resistance_measurement = keithley.measure_all()

                # Get flow rates from MFCs sequentially
                flow_rates = {}
                for mfc_name, mfc in mfc_devices.items():
                    # Read setpoint with retries
                    for attempt in range(3):
                        try:
                            percent_sp, setpoint_value, units = mfc.read_setpoint()
                            flow_rates[mfc_name] = setpoint_value
                            break  # Exit the retry loop if successful
                        except Exception as e:
                            if attempt < 2:
                                time.sleep(0.5)
                            else:
                                raise Exception(f"Failed to read from {mfc_name}: {e}")
                    # Wait before moving to the next MFC
                    time.sleep(0.05)

                # Get timestamp
                timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]  # Include milliseconds
                # Prepare data record
                record = {
                    'Time': timestamp,
                    'Elapsed Time (s)': round(elapsed_time, 3),
                    'Current (A)': current_measurement,
                    'Voltage (V)': voltage_measurement,
                    'Resistance (Ohms)': resistance_measurement,
                    'MFC 1 Flow Rate': flow_rates.get('MFC 1', 'N/A'),
                    'MFC 2 Flow Rate': flow_rates.get('MFC 2', 'N/A'),
                    'MFC 3 Flow Rate': flow_rates.get('MFC 3', 'N/A'),
                    'Cycle': current_cycle['name'],
                }
                data_records.append(record)
                # Put data into the queue for the UI thread
                data_queue.put({'elapsed_time': elapsed_time, 'resistance': resistance_measurement, 'cycle_type': cycle_type})
                # Add data to cycle_plot_data
                cycle_plot_data[cycle_type]['times'].append(elapsed_time)
                cycle_plot_data[cycle_type]['values'].append(resistance_measurement)
            except Exception as e:
                data_label.config(text=f"Error reading data: {e}")
            time.sleep(0.1)  # Data resolution of 0.1 seconds

    finally:
        # Turn off the Keithley output after measurements are done
        keithley.instrument.write('OUTP OFF')
        # Set MFC flow rates to 0
        reset_mfcs()
        # After recording stops, save data to CSV
        save_data_to_csv()
        # Do not close connections here to allow further experiments

# Function to save data to a CSV file
def save_data_to_csv():
    # Create a directory for data logs if it doesn't exist
    if not os.path.exists('data_logs'):
        os.makedirs('data_logs')
    # Generate filename with timestamp
    filename = datetime.datetime.now().strftime('data_logs/data_log_%Y%m%d_%H%M%S.csv')
    fieldnames = ['Time', 'Elapsed Time (s)', 'Current (A)', 'Voltage (V)', 'Resistance (Ohms)',
                  'MFC 1 Flow Rate', 'MFC 2 Flow Rate', 'MFC 3 Flow Rate', 'Cycle']
    try:
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for record in data_records:
                writer.writerow(record)
        data_label.config(text=f"Data saved to {filename}")
    except Exception as e:
        data_label.config(text=f"Error saving data: {e}")

# Function to start recording
def start_recording():
    global recording, data_records, cycle_plot_data
    if not recording:
        recording = True
        data_records = []  # Clear previous data
        cycle_plot_data = {}  # Initialize cycle plot data
        ax.clear()
        ax.set_xlabel('Elapsed Time (s)')
        ax.set_ylabel('Resistance (Ohms)')
        ax.set_title('Real-Time Resistance Measurement')
        start_button.config(state='disabled')
        stop_button.config(state='normal')
        threading.Thread(target=record_data, daemon=True).start()
        update_plot()

# Function to stop recording
def stop_recording():
    global recording
    if recording:
        recording = False
        start_button.config(state='normal')
        stop_button.config(state='disabled')
        # The output will be turned off, MFCs reset, and data saved in record_data()

# Function to set MFC rates for a given cycle
def set_mfc_rates(mfc_rates):
    for mfc_name, rate in mfc_rates.items():
        flow_var = flow_vars[mfc_name]
        flow_var.set(rate)
        set_mfc_flow(mfc_name, flow_var)

# Function to reset MFCs (set flow rates to 0)
def reset_mfcs():
    for mfc_name, mfc in mfc_devices.items():
        try:
            mfc.write_setpoint(0, units=57)  # Set flow rate to 0%
            status_labels[mfc_name].config(text=f"Flow Rate Set to: 0%")
        except Exception as e:
            status_labels[mfc_name].config(text=f"Error resetting {mfc_name}: {e}")

# Function to set gas flow for each MFC
def set_mfc_flow(mfc_name, flow_var):
    try:
        mfc = mfc_devices[mfc_name]
        flow_rate = float(flow_var.get())
        # Set the flow rate with retries
        for attempt in range(3):
            try:
                # Set the flow rate (assuming units code 57 for percent)
                mfc.write_setpoint(flow_rate, units=57)
                # Update status label
                status_labels[mfc_name].config(text=f"Flow Rate Set to: {flow_rate}%")
                break  # Exit the retry loop if successful
            except Exception as e:
                if attempt < 2:
                    time.sleep(0.5)
                else:
                    status_labels[mfc_name].config(text=f"Error: {e}")
                    raise e
        # Wait before moving to the next MFC
        time.sleep(0.05)
    except Exception as e:
        status_labels[mfc_name].config(text=f"Error: {e}")

# Function to update COM port for each MFC
def update_mfc_com(mfc_name, com_var):
    try:
        com_port = com_var.get()
        # Close the current connection
        mfc_devices[mfc_name].close()
        # Re-initialize the MFCDevice with the new COM port
        for attempt in range(3):
            try:
                mfc_devices[mfc_name] = MFCDevice(com_port)
                # Update status label
                status_labels[mfc_name].config(text=f"Using COM Port: {com_port}")
                break  # Exit the retry loop if successful
            except Exception as e:
                if attempt < 2:
                    time.sleep(0.5)
                else:
                    status_labels[mfc_name].config(text=f"Error: {e}")
                    raise e
        # Wait before moving to the next MFC
        time.sleep(0.05)
    except Exception as e:
        status_labels[mfc_name].config(text=f"Error: {e}")

# Function to update the plot in real-time
def update_plot():
    if not recording and data_queue.empty():
        return
    try:
        # Clear axes
        ax.clear()
        ax.set_xlabel('Elapsed Time (s)')
        ax.set_ylabel('Resistance (Ohms)')
        ax.set_title('Real-Time Resistance Measurement')
        # Plot each cycle's data
        for cycle_type, data in cycle_plot_data.items():
            ax.scatter(data['times'], data['values'], color=data['color'], label=cycle_type)
        ax.legend()
        canvas.draw()
    except Exception as e:
        print(f"Error updating plot: {e}")
    root.after(100, update_plot)

# Function to close connections
def close_connections():
    try:
        keithley.instrument.write('OUTP OFF')  # Ensure output is off
        keithley.close()
    except:
        pass
    for mfc in mfc_devices.values():
        try:
            mfc.close()
        except:
            pass

# Function to handle closing the application
def on_closing():
    global recording
    if recording:
        recording = False
        time.sleep(0.2)  # Wait for recording thread to finish
    # Turn off devices
    try:
        keithley.instrument.write('OUTP OFF')
    except:
        pass
    reset_mfcs()
    # Close connections
    close_connections()
    # Destroy the window
    root.destroy()

# Bind the on_closing function to the window close event
root.protocol("WM_DELETE_WINDOW", on_closing)

########################### UI SETUP ###########################
# Keithley Data Section
data_frame = ttk.Frame(root)
data_frame.pack(pady=10)

data_label = ttk.Label(data_frame, text="Resistance Data: N/A")
data_label.pack(side="left", padx=5)

start_button = ttk.Button(data_frame, text="Start", command=start_recording)
start_button.pack(side="left", padx=5)

stop_button = ttk.Button(data_frame, text="Stop", command=stop_recording, state='disabled')
stop_button.pack(side="left", padx=5)

# Repeats and Adjustments Section
repeats_frame = ttk.LabelFrame(root, text="Cycle Repeats and MFC Adjustments")
repeats_frame.pack(fill="x", padx=5, pady=5)

# Number of Repeats
repeats_label = ttk.Label(repeats_frame, text="Number of Repeats:")
repeats_label.grid(row=0, column=0, padx=5, pady=2, sticky='e')
repeats_entry = ttk.Entry(repeats_frame, textvariable=num_repeats_var, width=10)
repeats_entry.grid(row=0, column=1, padx=5, pady=2, sticky='w')

# MFC Adjustments
for idx, mfc_name in enumerate(['MFC 1', 'MFC 2', 'MFC 3']):
    adj_label = ttk.Label(repeats_frame, text=f"{mfc_name} Adjustment per Repeat (%):")
    adj_label.grid(row=idx+1, column=0, padx=5, pady=2, sticky='e')
    adj_entry = ttk.Entry(repeats_frame, textvariable=mfc_adjustments[mfc_name], width=10)
    adj_entry.grid(row=idx+1, column=1, padx=5, pady=2, sticky='w')

# Cycle Configuration Section
cycle_frame = ttk.Frame(root)
cycle_frame.pack(fill="x", padx=5, pady=5)

for cycle_name in ['Pre-Cycle', 'Run-On Cycle', 'Off Cycle']:
    frame = ttk.LabelFrame(cycle_frame, text=cycle_name)
    frame.pack(fill="x", padx=5, pady=5)

    # Duration
    duration_label = ttk.Label(frame, text="Duration (s):")
    duration_label.grid(row=0, column=0, padx=5, pady=2, sticky='e')
    duration_entry = ttk.Entry(frame, textvariable=cycle_vars[cycle_name]['duration'], width=10)
    duration_entry.grid(row=0, column=1, padx=5, pady=2, sticky='w')

    # MFC Rates
    for idx, mfc_name in enumerate(['MFC 1', 'MFC 2', 'MFC 3']):
        mfc_label = ttk.Label(frame, text=f"{mfc_name} Flow Rate (%):")
        mfc_label.grid(row=idx+1, column=0, padx=5, pady=2, sticky='e')
        mfc_entry = ttk.Entry(frame, textvariable=cycle_vars[cycle_name]['mfc_rates'][mfc_name], width=10)
        mfc_entry.grid(row=idx+1, column=1, padx=5, pady=2, sticky='w')

# MFC Control Section
status_labels = {}
flow_vars = {}  # To keep track of flow variables for each MFC

for i, mfc_name in enumerate(['MFC 1', 'MFC 2', 'MFC 3'], start=1):
    frame = ttk.LabelFrame(root, text=mfc_name)
    frame.pack(fill="x", padx=5, pady=5)

    # Manual Flow Rate Entry
    flow_label = ttk.Label(frame, text="Set Flow Rate (%):")
    flow_label.pack(side="left", padx=5)
    flow_var = tk.StringVar(value='0')
    flow_vars[mfc_name] = flow_var  # Store the variable
    flow_entry = ttk.Entry(frame, textvariable=flow_var, width=10)
    flow_entry.pack(side="left", padx=5)
    flow_button = ttk.Button(frame, text="Set", command=lambda mfc_name=mfc_name, flow_var=flow_var: set_mfc_flow(mfc_name, flow_var))
    flow_button.pack(side="left", padx=5)

    # COM Port Selection
    com_label = ttk.Label(frame, text="COM Port:")
    com_label.pack(side="left", padx=5)

    com_var = tk.StringVar(value=f'COM{3 + i - 1}')  # Default COM ports COM3, COM4, COM5
    com_dropdown = ttk.Combobox(frame, textvariable=com_var, values=['COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9'], width=10)
    com_dropdown.pack(side="left", padx=5)

    com_button = ttk.Button(frame, text="Update COM", command=lambda mfc_name=mfc_name, com_var=com_var: update_mfc_com(mfc_name, com_var))
    com_button.pack(side="left", padx=5)

    status_label = ttk.Label(frame, text=f"Using COM Port: {com_var.get()}, Flow Rate: N/A")
    status_label.pack(side="left", padx=5)

    status_labels[mfc_name] = status_label

# Real-Time Plot Section
plot_frame = ttk.Frame(root)
plot_frame.pack(fill="both", expand=True)

fig, ax = plt.subplots(figsize=(8, 4))
ax.set_xlabel('Elapsed Time (s)')
ax.set_ylabel('Resistance (Ohms)')
ax.set_title('Real-Time Resistance Measurement')

canvas = FigureCanvasTkAgg(fig, master=plot_frame)
canvas.draw()
canvas.get_tk_widget().pack(side="top", fill="both", expand=True)

########################## MAIN LOOP ##########################
try:
    root.mainloop()
except KeyboardInterrupt:
    pass
finally:
    # Ensure devices are closed when the application exits
    on_closing()
