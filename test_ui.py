# gas_ammeter_ui.py

import tkinter as tk
from tkinter import messagebox
from tkinter import ttk

# Import the mfc and ampmeter modules
import mfc
import ampmeter

class GasAmmeterControlUI:
    def __init__(self, master):
        self.master = master
        master.title("Gas Flow Meter and Ammeter Control")

        # Create the main frame
        self.main_frame = ttk.Frame(master, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Gas Flow Meter Section
        self.create_gas_flow_meter_section()

        # Ammeter Section
        self.create_ammeter_section()

        # Status Message Section
        self.create_status_section()

    def create_gas_flow_meter_section(self):
        # Section Label
        gas_label = ttk.Label(self.main_frame, text="Gas Flow Meter Control", font=('Helvetica', 14, 'bold'))
        gas_label.grid(row=0, column=0, columnspan=3, pady=(0, 10), sticky=tk.W)

        # Flow Rate Input
        flow_rate_label = ttk.Label(self.main_frame, text="Set Flow Rate (sccm):")
        flow_rate_label.grid(row=1, column=0, sticky=tk.E)
        self.flow_rate_entry = ttk.Entry(self.main_frame, width=15)
        self.flow_rate_entry.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)

        # Set Flow Rate Button
        set_flow_button = ttk.Button(self.main_frame, text="Set Flow Rate", command=self.set_flow_rate)
        set_flow_button.grid(row=1, column=2, padx=5, pady=5, sticky=tk.W)

        # Stop Gas Flow Button
        stop_flow_button = ttk.Button(self.main_frame, text="Stop Gas Flow", command=self.stop_gas_flow)
        stop_flow_button.grid(row=1, column=3, padx=5, pady=5, sticky=tk.W)

    def create_ammeter_section(self):
        # Section Label
        ammeter_label = ttk.Label(self.main_frame, text="Ammeter Control", font=('Helvetica', 14, 'bold'))
        ammeter_label.grid(row=2, column=0, columnspan=3, pady=(20, 10), sticky=tk.W)

        # Current Value Input
        current_label = ttk.Label(self.main_frame, text="Set Amp Value (A):")
        current_label.grid(row=3, column=0, sticky=tk.E)
        self.current_entry = ttk.Entry(self.main_frame, width=15)
        self.current_entry.grid(row=3, column=1, padx=5, pady=5, sticky=tk.W)

        # Set Current Button
        set_current_button = ttk.Button(self.main_frame, text="Set Amp Value", command=self.set_current)
        set_current_button.grid(row=3, column=2, padx=5, pady=5, sticky=tk.W)

        # Stop Current Flow Button
        stop_current_button = ttk.Button(self.main_frame, text="Stop Current", command=self.stop_current_flow)
        stop_current_button.grid(row=3, column=3, padx=5, pady=5, sticky=tk.W)

    def create_status_section(self):
        # Status Label
        self.status_label = ttk.Label(self.main_frame, text="", font=('Helvetica', 10))
        self.status_label.grid(row=4, column=0, columnspan=4, pady=(20, 0), sticky=tk.W)

    def set_flow_rate(self):
        try:
            flow_rate_str = self.flow_rate_entry.get()
            if not flow_rate_str:
                raise ValueError("Flow rate cannot be empty.")
            flow_rate = float(flow_rate_str)
            if flow_rate < 0:
                raise ValueError("Flow rate must be a positive number.")

            # Set the flow rate using the mfc module
            mfc.set_flow_rate(flow_rate)

            # Update status message
            self.status_label.config(text="Flow rate set successfully.", foreground='green')
        except ValueError as ve:
            self.status_label.config(text=f"Error: {ve}", foreground='red')
        except ConnectionError as ce:
            self.status_label.config(text=f"Error: {ce}", foreground='red')
            messagebox.showerror("Device Communication Error", f"Failed to communicate with the gas flow meter.\n\n{ce}")
        except Exception as e:
            self.status_label.config(text=f"Unexpected Error: {e}", foreground='red')
            messagebox.showerror("Unexpected Error", f"An unexpected error occurred:\n\n{e}")

    def set_current(self):
        try:
            current_str = self.current_entry.get()
            if not current_str:
                raise ValueError("Current value cannot be empty.")
            current_value = float(current_str)
            if current_value < 0:
                raise ValueError("Current value must be a positive number.")

            # Set the current using the ampmeter module
            ampmeter.set_current(current_value)

            # Update status message
            self.status_label.config(text="Current set successfully.", foreground='green')
        except ValueError as ve:
            self.status_label.config(text=f"Error: {ve}", foreground='red')
        except ConnectionError as ce:
            self.status_label.config(text=f"Error: {ce}", foreground='red')
            messagebox.showerror("Device Communication Error", f"Failed to communicate with the ammeter.\n\n{ce}")
        except Exception as e:
            self.status_label.config(text=f"Unexpected Error: {e}", foreground='red')
            messagebox.showerror("Unexpected Error", f"An unexpected error occurred:\n\n{e}")

    def stop_gas_flow(self):
        try:
            # Set the flow rate to zero
            mfc.set_flow_rate(0.0)

            # Update status message
            self.status_label.config(text="Gas flow stopped successfully.", foreground='green')
        except ConnectionError as ce:
            self.status_label.config(text=f"Error: {ce}", foreground='red')
            messagebox.showerror("Device Communication Error", f"Failed to communicate with the gas flow meter.\n\n{ce}")
        except Exception as e:
            self.status_label.config(text=f"Unexpected Error: {e}", foreground='red')
            messagebox.showerror("Unexpected Error", f"An unexpected error occurred:\n\n{e}")

    def stop_current_flow(self):
        try:
            # Set the current to zero
            ampmeter.set_current(0.0)

            # Update status message
            self.status_label.config(text="Current stopped successfully.", foreground='green')
        except ConnectionError as ce:
            self.status_label.config(text=f"Error: {ce}", foreground='red')
            messagebox.showerror("Device Communication Error", f"Failed to communicate with the ammeter.\n\n{ce}")
        except Exception as e:
            self.status_label.config(text=f"Unexpected Error: {e}", foreground='red')
            messagebox.showerror("Unexpected Error", f"An unexpected error occurred:\n\n{e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = GasAmmeterControlUI(root)
    root.mainloop()
