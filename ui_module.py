###########################
# Author: Agosh Saini - using GPT-10-preview model
# Contact: contact@agoshsaini.com
# Date: 2024-10-02
###########################

########################### IMPORTS ###########################
import tkinter as tk
from tkinter import ttk
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import serial.tools.list_ports
import queue
import logging  

# Use Agg backend for Matplotlib
matplotlib.use("TkAgg")

# Configure logging
logging.basicConfig(level=logging.INFO)

########################### UI FUNCTIONS ###########################
def create_ui(
    root, keithley, mfc_devices, relay_controller,
    start_recording_callback, stop_recording_callback,
    update_relay_com_callback, update_mfc_com_callback,
    reset_mfcs_callback, set_mfc_rates_callback,
    set_mfc_flow_callback,
    close_connections_callback
):
    """
    Creates the user interface for the application.

    Parameters:
        root (tk.Tk): The main Tkinter window.
        keithley: The Keithley device instance.
        mfc_devices (dict): Dictionary of MFC devices.
        relay_controller: The relay controller instance.
        start_recording_callback (function): Function to call when starting recording.
        stop_recording_callback (function): Function to call when stopping recording.
        update_relay_com_callback (function): Function to update relay COM port.
        update_mfc_com_callback (function): Function to update MFC COM ports.
        reset_mfcs_callback (function): Function to reset MFCs.
        set_mfc_rates_callback (function): Function to set MFC rates.
        set_mfc_flow_callback (function): Function to set MFC flow.
        close_connections_callback (function): Function to close device connections.

    Returns:
        dict: A dictionary containing UI elements and variables.
    """
    # Initialize variables
    data_queue = queue.Queue()
    data_label = ttk.Label(root)
    # Initialize relay_plot_data
    relay_plot_data = {
        relay_num: {'times': [], 'values': []}
        for relay_num in range(1, 9)
    }
    # Initialize StringVars and other variables
    cycle_vars = {}
    num_repeats_var = tk.StringVar(root, value='1')
    mfc_adjustments = {}
    relay_delay_var = tk.StringVar(root, value='0.1')
    flow_vars = {}
    status_labels = {}
    mfc_com_vars = {}
    relay_com_var = tk.StringVar(root)
    relay_status_label = ttk.Label(root)

    # Variables for experiment status
    experiment_duration_var = tk.StringVar(root, value='Total Duration: N/A')
    remaining_time_var = tk.StringVar(root, value='Time Remaining: N/A')
    current_cycle_var = tk.StringVar(root, value='Current Cycle: N/A')

    # Create a main frame
    main_frame = ttk.Frame(root)
    main_frame.pack(fill="both", expand=True)

    # Create top frame for controls
    top_frame = ttk.Frame(main_frame)
    top_frame.pack(side="top", fill="both", expand=False)

    # Create bottom frame for the graph
    bottom_frame = ttk.Frame(main_frame)
    bottom_frame.pack(side="bottom", fill="both", expand=True)

    # Divide the top frame into three sections
    left_frame = ttk.Frame(top_frame)
    center_frame = ttk.Frame(top_frame)
    right_frame = ttk.Frame(top_frame)
    left_frame.pack(side="left", fill="both", expand=True)
    center_frame.pack(side="left", fill="both", expand=True)
    right_frame.pack(side="left", fill="both", expand=True)

    # Create labeled sections in left_frame
    create_repeats_and_adjustments_section(left_frame, num_repeats_var, mfc_adjustments)
    create_mfc_control_section(left_frame, mfc_devices, mfc_com_vars, flow_vars, status_labels, update_mfc_com_callback, set_mfc_flow_callback)

    # Create labeled sections in center_frame
    create_cycle_configuration_section(center_frame, cycle_vars)

    # Prepare ui_elements dictionary before creating buttons
    ui_elements = {}  # Initialize empty and fill later

    # Create labeled sections in right_frame
    create_relay_control_section(right_frame, relay_com_var, relay_delay_var, relay_status_label, update_relay_com_callback, ui_elements)

    # Create the plot in bottom_frame
    fig, ax = create_plot_section(bottom_frame)

    # Create data label and start/stop buttons
    data_frame = ttk.Frame(root)
    data_frame.pack(pady=10)

    data_label = ttk.Label(data_frame, text="Resistance Data: N/A")
    data_label.pack(side="left", padx=5)

    start_button = ttk.Button(data_frame, text="Start", command=lambda: start_recording_callback(ui_elements))
    start_button.pack(side="left", padx=5)

    stop_button = ttk.Button(data_frame, text="Stop", command=lambda: stop_recording_callback(ui_elements), state='disabled')
    stop_button.pack(side="left", padx=5)

    # Add experiment status labels
    status_frame = ttk.Frame(root)
    status_frame.pack(pady=5)

    ttk.Label(status_frame, textvariable=experiment_duration_var).pack(side="left", padx=5)
    ttk.Label(status_frame, textvariable=remaining_time_var).pack(side="left", padx=5)
    ttk.Label(status_frame, textvariable=current_cycle_var).pack(side="left", padx=5)

    # Now fill the ui_elements dictionary
    ui_elements.update({
        'data_label': data_label,
        'start_button': start_button,
        'stop_button': stop_button,
        'cycle_vars': cycle_vars,
        'num_repeats_var': num_repeats_var,
        'mfc_adjustments': mfc_adjustments,
        'relay_delay_var': relay_delay_var,
        'relay_controller': relay_controller,
        'mfc_devices': mfc_devices,
        'reset_mfcs': reset_mfcs_callback,
        'set_mfc_rates': set_mfc_rates_callback,
        'set_mfc_flow': set_mfc_flow_callback,
        'data_queue': data_queue,
        'relay_plot_data': relay_plot_data,
        'keithley': keithley,
        'relay_status_label': relay_status_label,
        'flow_vars': flow_vars,
        'status_labels': status_labels,
        'mfc_com_vars': mfc_com_vars,
        'relay_com_var': relay_com_var,
        'fig': fig,
        'ax': ax,
        'root': root,
        'experiment_duration_var': experiment_duration_var,
        'remaining_time_var': remaining_time_var,
        'current_cycle_var': current_cycle_var
    })

    return ui_elements

def create_repeats_and_adjustments_section(parent_frame, num_repeats_var, mfc_adjustments):
    """
    Creates the repeats and adjustments section in the UI.

    Parameters:
        parent_frame (ttk.Frame): The parent frame to place this section in.
        num_repeats_var (tk.StringVar): Variable for the number of repeats.
        mfc_adjustments (dict): Dictionary to store MFC adjustment variables.
    """
    repeats_frame = ttk.LabelFrame(parent_frame, text="Cycle Repeats and MFC Adjustments")
    repeats_frame.pack(fill="both", expand=True, padx=5, pady=5)
    # Add widgets to repeats_frame

    # Number of Repeats
    repeats_label = ttk.Label(repeats_frame, text="Number of Repeats:")
    repeats_label.grid(row=0, column=0, padx=5, pady=2, sticky='e')
    repeats_entry = ttk.Entry(repeats_frame, textvariable=num_repeats_var, width=10)
    repeats_entry.grid(row=0, column=1, padx=5, pady=2, sticky='w')

    # MFC Adjustments
    for idx, mfc_name in enumerate(['MFC 1', 'MFC 2', 'MFC 3']):
        mfc_adjustments[mfc_name] = tk.StringVar(value='0')
        adj_label = ttk.Label(repeats_frame, text=f"{mfc_name} Adjustment per Repeat (%):")
        adj_label.grid(row=idx+1, column=0, padx=5, pady=2, sticky='e')
        adj_entry = ttk.Entry(repeats_frame, textvariable=mfc_adjustments[mfc_name], width=10)
        adj_entry.grid(row=idx+1, column=1, padx=5, pady=2, sticky='w')

def create_mfc_control_section(parent_frame, mfc_devices, mfc_com_vars, flow_vars, status_labels, update_mfc_com_callback, set_mfc_flow_callback):
    """
    Creates the MFC control section in the UI.

    Parameters:
        parent_frame (ttk.Frame): The parent frame to place this section in.
        mfc_devices (dict): Dictionary of MFC devices.
        mfc_com_vars (dict): Dictionary to store MFC COM port variables.
        flow_vars (dict): Dictionary to store flow rate variables.
        status_labels (dict): Dictionary to store status labels for MFCs.
        update_mfc_com_callback (function): Callback function to update MFC COM ports.
        set_mfc_flow_callback (function): Callback function to set MFC flow rates.
    """
    mfc_frame = ttk.LabelFrame(parent_frame, text="MFC Control")
    mfc_frame.pack(fill="both", expand=True, padx=5, pady=5)

    # Get available COM ports
    ports = serial.tools.list_ports.comports()
    available_ports = [port.device for port in ports]
    if not available_ports:
        available_ports = ['COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9']

    for i, mfc_name in enumerate(['MFC 1', 'MFC 2', 'MFC 3'], start=1):
        frame = ttk.LabelFrame(mfc_frame, text=mfc_name)
        frame.pack(fill="x", padx=5, pady=5)

        # Manual Flow Rate Entry
        flow_label = ttk.Label(frame, text="Set Flow Rate (%):")
        flow_label.pack(side="left", padx=5)
        flow_vars[mfc_name] = tk.StringVar(value='0')
        flow_entry = ttk.Entry(frame, textvariable=flow_vars[mfc_name], width=10)
        flow_entry.pack(side="left", padx=5)
        # Set up the set_mfc_flow function
        flow_button = ttk.Button(frame, text="Set", command=lambda mfc_name=mfc_name: set_mfc_flow_callback(mfc_name, flow_vars[mfc_name], mfc_devices, status_labels))
        flow_button.pack(side="left", padx=5)

        # COM Port Selection
        com_label = ttk.Label(frame, text="COM Port:")
        com_label.pack(side="left", padx=5)

        mfc_com_vars[mfc_name] = tk.StringVar(value=f'COM{3 + i - 1}')  # Default COM ports COM3, COM4, COM5
        com_dropdown = ttk.Combobox(frame, textvariable=mfc_com_vars[mfc_name], values=available_ports, width=10)
        com_dropdown.pack(side="left", padx=5)

        com_button = ttk.Button(frame, text="Update COM", command=lambda mfc_name=mfc_name: update_mfc_com_callback(mfc_name, mfc_com_vars[mfc_name], status_labels, mfc_devices))
        com_button.pack(side="left", padx=5)

        status_labels[mfc_name] = ttk.Label(frame, text=f"Using COM Port: {mfc_com_vars[mfc_name].get()}, Flow Rate: N/A")
        status_labels[mfc_name].pack(side="left", padx=5)

def create_cycle_configuration_section(parent_frame, cycle_vars):
    """
    Creates the cycle configuration section in the UI.

    Parameters:
        parent_frame (ttk.Frame): The parent frame to place this section in.
        cycle_vars (dict): Dictionary to store cycle configuration variables.
    """
    cycle_frame = ttk.LabelFrame(parent_frame, text="Cycle Configuration")
    cycle_frame.pack(fill="both", expand=True, padx=5, pady=5)

    for cycle_name in ['Pre-Cycle', 'Run-On Cycle', 'Off Cycle']:
        frame = ttk.LabelFrame(cycle_frame, text=cycle_name)
        frame.pack(fill="x", padx=5, pady=5)

        # Initialize variables
        cycle_vars[cycle_name] = {
            'duration': tk.StringVar(value='10'),
            'mfc_rates': {}
        }

        # Duration
        duration_label = ttk.Label(frame, text="Duration (s):")
        duration_label.grid(row=0, column=0, padx=5, pady=2, sticky='e')
        duration_entry = ttk.Entry(frame, textvariable=cycle_vars[cycle_name]['duration'], width=10)
        duration_entry.grid(row=0, column=1, padx=5, pady=2, sticky='w')

        # MFC Rates
        for idx, mfc_name in enumerate(['MFC 1', 'MFC 2', 'MFC 3']):
            cycle_vars[cycle_name]['mfc_rates'][mfc_name] = tk.StringVar(value='0')
            mfc_label = ttk.Label(frame, text=f"{mfc_name} Flow Rate (%):")
            mfc_label.grid(row=idx+1, column=0, padx=5, pady=2, sticky='e')
            mfc_entry = ttk.Entry(frame, textvariable=cycle_vars[cycle_name]['mfc_rates'][mfc_name], width=10)
            mfc_entry.grid(row=idx+1, column=1, padx=5, pady=2, sticky='w')

def create_relay_control_section(parent_frame, relay_com_var, relay_delay_var, relay_status_label, update_relay_com_callback, ui_elements):
    """
    Creates the relay control section in the UI.

    Parameters:
        parent_frame (ttk.Frame): The parent frame to place this section in.
        relay_com_var (tk.StringVar): Variable for the relay COM port.
        relay_delay_var (tk.StringVar): Variable for the relay delay.
        relay_status_label (ttk.Label): Label to display the relay status.
        update_relay_com_callback (function): Callback function to update relay COM port.
        ui_elements (dict): Dictionary of UI elements.
    """
    relay_frame = ttk.LabelFrame(parent_frame, text="Relay Control")
    relay_frame.pack(fill="both", expand=True, padx=5, pady=5)

    relay_delay_label = ttk.Label(relay_frame, text="Relay Delay (s):")
    relay_delay_label.pack(side="left", padx=5)
    relay_delay_entry = ttk.Entry(relay_frame, textvariable=relay_delay_var, width=10)
    relay_delay_entry.pack(side="left", padx=5)

    # Relay COM Port Selection
    relay_com_label = ttk.Label(relay_frame, text="Arduino COM Port:")
    relay_com_label.pack(side="left", padx=5)

    # Get a list of available COM ports
    ports = serial.tools.list_ports.comports()
    available_ports = [port.device for port in ports]
    if not available_ports:
        available_ports = ['COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9']

    relay_com_var.set(available_ports[0])  # Set default to first available port

    relay_com_dropdown = ttk.Combobox(relay_frame, textvariable=relay_com_var, values=available_ports, width=10)
    relay_com_dropdown.pack(side="left", padx=5)

    # Update the command to pass ui_elements
    relay_com_button = ttk.Button(relay_frame, text="Update COM", command=lambda: update_relay_com_callback(relay_com_var, ui_elements, relay_status_label))
    relay_com_button.pack(side="left", padx=5)

    relay_status_label.config(text="Arduino COM Port not set.")
    relay_status_label.pack(side="left", padx=5)

def create_plot_section(parent_frame):
    """
    Creates the plot section in the UI.

    Parameters:
        parent_frame (ttk.Frame): The parent frame to place the plot in.

    Returns:
        tuple: A tuple containing the figure and axes objects.
    """
    plot_frame = ttk.Frame(parent_frame)
    plot_frame.pack(fill="both", expand=True)
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.set_xlabel('Elapsed Time (s)')
    ax.set_ylabel('Resistance (Ohms)')
    ax.set_title('Real-Time Resistance Measurement (All Relays)')
    canvas = FigureCanvasTkAgg(fig, master=plot_frame)
    canvas.draw()
    canvas.get_tk_widget().pack(side="top", fill="both", expand=True)
    # Return the figure and axes if needed
    return (fig, ax)
