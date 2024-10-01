###########################
# Author: Agosh Saini - using using GPT-1o-preview model
# Contact: contact@agoshsaini.com
# Date: 2024-OCT-01
###########################

########################### IMPORTS ###########################
import tkinter as tk
from tkinter import ttk
import threading
import time
import csv
import datetime
import os

# Import the Keithley and MFC classes
from ampmeter import Keithley2450
from mfc import MFCDevice

########################### INITIALIZE ###########################
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

########################### FUNCTIONS ###########################
# Function to handle data recording from Keithley
def record_data():
    global recording, stop_time
    start_time = time.time()
    while recording:
        current_time = time.time()
        elapsed_time = current_time - start_time
        # Check if we have reached the stop time
        if stop_time is not None and elapsed_time >= stop_time:
            recording = False
            start_button.config(text="Start")
            break
        try:
            # Measure current from the Keithley device
            current = keithley.measure_current()
            # Get flow rates from MFCs
            flow_rates = {}
            for mfc_name, mfc in mfc_devices.items():
                percent_sp, setpoint_value, units = mfc.read_setpoint()
                flow_rates[mfc_name] = setpoint_value
            # Get timestamp
            timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            # Update the data label in the UI
            data_label.config(text=f"Current Data: {current} A")
            # Save data to records
            record = {
                'Time': timestamp,
                'Elapsed Time (s)': round(elapsed_time, 2),
                'Current (A)': current,
                'MFC 1 Flow Rate': flow_rates['MFC 1'],
                'MFC 2 Flow Rate': flow_rates['MFC 2'],
                'MFC 3 Flow Rate': flow_rates['MFC 3'],
            }
            data_records.append(record)
        except Exception as e:
            data_label.config(text=f"Error reading data: {e}")
        time.sleep(1)  # Adjust the interval as needed

    # After recording stops, save data to CSV
    save_data_to_csv()

# Function to save data to a CSV file
def save_data_to_csv():
    # Create a directory for data logs if it doesn't exist
    if not os.path.exists('data_logs'):
        os.makedirs('data_logs')
    # Generate filename with timestamp
    filename = datetime.datetime.now().strftime('data_logs/data_log_%Y%m%d_%H%M%S.csv')
    fieldnames = ['Time', 'Elapsed Time (s)', 'Current (A)', 'MFC 1 Flow Rate', 'MFC 2 Flow Rate', 'MFC 3 Flow Rate']
    try:
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for record in data_records:
                writer.writerow(record)
        data_label.config(text=f"Data saved to {filename}")
    except Exception as e:
        data_label.config(text=f"Error saving data: {e}")

# Function to start/stop recording
def toggle_recording():
    global recording, stop_time, data_records
    if not recording:
        recording = True
        data_records = []  # Clear previous data
        # Get the duration from the UI
        duration_str = duration_entry.get()
        if duration_str:
            try:
                duration = float(duration_str)
                stop_time = duration
            except ValueError:
                data_label.config(text="Invalid duration. Please enter a number.")
                return
        else:
            stop_time = None  # Run indefinitely until stopped
        start_button.config(text="Stop")
        threading.Thread(target=record_data, daemon=True).start()
    else:
        recording = False
        start_button.config(text="Start")
        save_data_to_csv()

# Function to set gas flow for each MFC
def set_mfc_flow(mfc_name, flow_var):
    try:
        mfc = mfc_devices[mfc_name]
        flow_rate = flow_var.get()
        # Set the flow rate (assuming units code 57 for percent)
        mfc.write_setpoint(flow_rate, units=57)
        # Update status label
        status_labels[mfc_name].config(text=f"Flow Rate Set to: {flow_rate}%")
    except Exception as e:
        status_labels[mfc_name].config(text=f"Error: {e}")

# Function to update COM port for each MFC
def update_mfc_com(mfc_name, com_var):
    try:
        com_port = com_var.get()
        # Close the current connection
        mfc_devices[mfc_name].close()
        # Re-initialize the MFCDevice with the new COM port
        mfc_devices[mfc_name] = MFCDevice(com_port)
        # Update status label
        status_labels[mfc_name].config(text=f"Using COM Port: {com_port}")
    except Exception as e:
        status_labels[mfc_name].config(text=f"Error: {e}")

########################### UI SETUP ###########################
# Create the main application window
root = tk.Tk()
root.title("Keithley Data Recorder and MFC Control")
root.geometry("800x600")

# Keithley Data Section
data_frame = ttk.Frame(root)
data_frame.pack(pady=10)

data_label = ttk.Label(data_frame, text="Current Data: N/A")
data_label.pack(side="left", padx=5)

start_button = ttk.Button(data_frame, text="Start", command=toggle_recording)
start_button.pack(side="left", padx=5)

duration_label = ttk.Label(data_frame, text="Duration (s):")
duration_label.pack(side="left", padx=5)

duration_entry = ttk.Entry(data_frame, width=10)
duration_entry.pack(side="left", padx=5)
duration_entry.insert(0, "60")  # Default duration

# MFC Control Section
status_labels = {}
flow_vars = {}  # To keep track of flow variables for each MFC

for i, mfc_name in enumerate(['MFC 1', 'MFC 2', 'MFC 3'], start=1):
    frame = ttk.LabelFrame(root, text=mfc_name)
    frame.pack(fill="x", padx=5, pady=5)
    
    flow_label = ttk.Label(frame, text="Set Flow Rate (%):")
    flow_label.pack(side="left", padx=5)
    
    flow_var = tk.DoubleVar(value=0)
    flow_vars[mfc_name] = flow_var  # Store the variable
    
    flow_slider = ttk.Scale(frame, from_=0, to=100, orient="horizontal", variable=flow_var)
    flow_slider.pack(side="left", padx=5)
    
    flow_button = ttk.Button(frame, text="Set", command=lambda mfc_name=mfc_name, flow_var=flow_var: set_mfc_flow(mfc_name, flow_var))
    flow_button.pack(side="left", padx=5)
    
    com_label = ttk.Label(frame, text="COM Port:")
    com_label.pack(side="left", padx=5)
    
    com_var = tk.StringVar(value=f'COM{6 + i - 1}')  # Default COM ports COM6, COM7, COM8
    com_dropdown = ttk.Combobox(frame, textvariable=com_var, values=['COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9'])
    com_dropdown.pack(side="left", padx=5)
    
    com_button = ttk.Button(frame, text="Update COM", command=lambda mfc_name=mfc_name, com_var=com_var: update_mfc_com(mfc_name, com_var))
    com_button.pack(side="left", padx=5)
    
    status_label = ttk.Label(frame, text=f"Using COM Port: {com_var.get()}, Flow Rate: N/A")
    status_label.pack(side="left", padx=5)
    
    status_labels[mfc_name] = status_label

########################## MAIN LOOP ##########################
try:
    root.mainloop()
except KeyboardInterrupt:
    pass
finally:
    # Ensure devices are closed when the application exits
    keithley.close()
    for mfc in mfc_devices.values():
        mfc.close()
