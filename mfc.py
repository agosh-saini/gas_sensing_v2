###########################
# Author: Agosh Saini - using using GPT-1o-preview model
# Contact: contact@agoshsaini.com
# Date: 2024-OCT-01
###########################

########################### IMPORTS ###########################
import time
from sprotocol import device

########################### CLASS DEFINITION ###########################
class MFCDevice:
    """
    A class to represent and control a Mass Flow Controller (MFC) device using the s-protocol.

    Attributes:
        mfc (device.mfc): The MFC device object from the sprotocol library.
    """

    def __init__(self, com_port, baudrate=19200, timeout=0.1):
        """
        Initialize the MFC device by establishing a connection and retrieving the device address.

        Parameters:
            com_port (str): The COM port to which the MFC is connected (e.g., 'COM3').
            baudrate (int, optional): The baud rate for serial communication. Default is 19200.
            timeout (float, optional): The timeout for serial communication in seconds. Default is 0.1.
        """
        try:
            # Initialize the MFC device from the sprotocol library
            self.mfc = device.mfc(com_port, baudrate, timeout)
            # Get the device address to enable communication
            self.mfc.get_address()
        except Exception as e:
            print(f"Error initializing device on {com_port}: {e}")
            # Perform emergency stop as a backup
            self.emergency_stop()
            raise

    def write_setpoint(self, setpoint_value, units=57):
        """
        Write the setpoint value to the MFC.

        Parameters:
            setpoint_value (float): The desired setpoint value.
            units (int, optional): The units code. Default is 57 (percent of flow range).

        Returns:
            tuple: Contains the percent setpoint, setpoint float value, and setpoint units.
        """
        try:
            return self.mfc.write_setpoint(setpoint_value, units)
        except Exception as e:
            print(f"Error writing setpoint: {e}")
            # Perform emergency stop as a backup
            self.emergency_stop()
            raise

    def read_setpoint(self):
        """
        Read the current setpoint from the MFC.

        Returns:
            tuple: Contains the percent setpoint, setpoint float value, and setpoint units.
        """
        try:
            return self.mfc.read_setpoint()
        except Exception as e:
            print(f"Error reading setpoint: {e}")
            # Perform emergency stop as a backup
            self.emergency_stop()
            raise

    def write_flow_unit(self, flow_ref, flow_unit):
        """
        Set the flow units and flow reference of the MFC.

        Parameters:
            flow_ref (int): The flow reference code (e.g., 0 for Normal, 1 for Standard).
            flow_unit (int): The flow unit code (e.g., 17 for Litres/minute).

        Returns:
            tuple: Contains the flow reference string and flow unit string.
        """
        try:
            return self.mfc.write_flow_unit(flow_ref, flow_unit)
        except Exception as e:
            print(f"Error writing flow unit: {e}")
            # Perform emergency stop as a backup
            self.emergency_stop()
            raise

    def read_flow_unit(self):
        """
        Read the current flow units and flow reference of the MFC.

        Returns:
            tuple: Contains the flow reference string and flow unit string.
        """
        try:
            # Command 196 without data reads the current flow units and reference
            self.mfc.write_command(196)
            time.sleep(0.2)
            response = self.mfc.read_command()
            data_bytes = response[3]
            flow_ref_code = data_bytes[0]
            flow_unit_code = data_bytes[1]
            flow_ref_str = self.mfc.units_from_flow_ref(flow_ref_code)
            flow_unit_str = self.mfc.units_from_int_flow(flow_unit_code)
            return flow_ref_str, flow_unit_str
        except Exception as e:
            print(f"Error reading flow unit: {e}")
            # Perform emergency stop as a backup
            self.emergency_stop()
            raise

    def read_flow_reference(self):
        """
        Read the flow reference from the device.

        Returns:
            str: The flow reference as a string (e.g., 'Normal', 'Standard').
        """
        try:
            flow_ref_str, _ = self.read_flow_unit()
            return flow_ref_str
        except Exception as e:
            print(f"Error reading flow reference: {e}")
            # Perform emergency stop as a backup
            self.emergency_stop()
            raise

    def write_flow_reference(self, flow_ref):
        """
        Write the flow reference to the device.

        Parameters:
            flow_ref (int): The flow reference code (e.g., 0 for Normal, 1 for Standard).

        Returns:
            str: The updated flow reference as a string.
        """
        try:
            # Read current flow unit to avoid changing it
            _, flow_unit_str = self.read_flow_unit()
            flow_unit_code = None
            # Find the unit code from the unit string
            for code, unit in self.mfc.flow_units_table.items():
                if unit == flow_unit_str:
                    flow_unit_code = code
                    break
            if flow_unit_code is None:
                raise ValueError("Current flow unit not recognized.")
            # Write the new flow reference with the existing flow unit
            self.write_flow_unit(flow_ref, flow_unit_code)
            flow_ref_str = self.mfc.units_from_flow_ref(flow_ref)
            return flow_ref_str
        except Exception as e:
            print(f"Error writing flow reference: {e}")
            # Perform emergency stop as a backup
            self.emergency_stop()
            raise

    def emergency_stop(self):
        """
        Emergency stop function that sets the setpoint to zero.
        """
        try:
            self.mfc.write_setpoint(0.0)
            print("Emergency stop activated: Setpoint set to zero.")
        except Exception as e:
            print(f"Error during emergency stop: {e}")

    def close(self):
        """
        Close the serial connection to the device.
        """
        if self.mfc.ser and self.mfc.ser.is_open:
            self.mfc.ser.close()
            print("Serial connection closed.")

class MFCController:
    """
    A controller class to manage multiple MFC devices.

    Attributes:
        devices (list): A list of MFCDevice instances.
    """

    def __init__(self):
        """
        Initialize the MFCController with an empty list of devices.
        """
        self.devices = []

    def add_device(self, com_port, baudrate=19200, timeout=0.1):
        """
        Add an MFC device to the controller.

        Parameters:
            com_port (str): The COM port of the MFC device (e.g., 'COM3').
            baudrate (int, optional): The baud rate for serial communication. Default is 19200.
            timeout (float, optional): The timeout for serial communication in seconds. Default is 0.1.

        Returns:
            MFCDevice: The added MFC device instance.
        """
        try:
            mfc_device = MFCDevice(com_port, baudrate, timeout)
            self.devices.append(mfc_device)
            print(f"Device added on {com_port}")
            return mfc_device
        except Exception as e:
            print(f"Error adding device on {com_port}: {e}")
            # Perform emergency stop as a backup
            self.emergency_stop_all()
            raise

    def emergency_stop_all(self):
        """
        Emergency stop all connected MFC devices by setting their setpoints to zero.
        """
        print("Performing emergency stop on all devices.")
        for device in self.devices:
            device.emergency_stop()

    def close_all(self):
        """
        Close all serial connections to the MFC devices.
        """
        for device in self.devices:
            device.close()
        print("All devices have been disconnected.")

########################### MAIN FUNCTION ###########################
if __name__ == "__main__":
    """
    Example main function demonstrating how to use the MFCDevice and MFCController classes.
    """
    try:
        # Create an MFCController instance
        controller = MFCController()

        # Add MFC devices (replace 'COM3' and 'COM4' with your actual COM ports)
        mfc1 = controller.add_device('COM3')
        mfc2 = controller.add_device('COM4')

        # Write setpoint to MFC1 (e.g., set to 50% of full scale)
        percent_sp, setpoint_value, units = mfc1.write_setpoint(50.0)
        print(f"MFC1 Setpoint set to {percent_sp}% ({setpoint_value} {units})")

        # Read setpoint from MFC2
        percent_sp, setpoint_value, units = mfc2.read_setpoint()
        print(f"MFC2 Current Setpoint: {percent_sp}% ({setpoint_value} {units})")

        # Change flow units and reference of MFC1 (e.g., set to Standard Litres/minute)
        flow_ref_str, flow_unit_str = mfc1.write_flow_unit(flow_ref=1, flow_unit=17)
        print(f"MFC1 Units set to {flow_ref_str} {flow_unit_str}")

        # Read flow units and reference of MFC1
        flow_ref_str, flow_unit_str = mfc1.read_flow_unit()
        print(f"MFC1 Current Units: {flow_ref_str} {flow_unit_str}")

        # Read flow reference of MFC1
        flow_ref = mfc1.read_flow_reference()
        print(f"MFC1 Flow Reference: {flow_ref}")

        # Write new flow reference to MFC1 (e.g., set to Normal)
        flow_ref_str = mfc1.write_flow_reference(flow_ref=0)
        print(f"MFC1 Flow Reference updated to: {flow_ref_str}")

        # Emergency stop all devices
        controller.emergency_stop_all()
        print("Emergency stop activated for all devices.")

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        # Perform emergency stop as a backup
        controller.emergency_stop_all()
    finally:
        # Close all connections when done
        controller.close_all()
        print("All devices have been disconnected.")