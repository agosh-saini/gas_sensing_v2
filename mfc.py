###########################
# Author: Agosh Saini - using GPT-1o-preview model
# Contact: contact@agoshsaini.com
# Date: 2024-SPET-12
###########################

########################### IMPORTS ###########################
import serial
import struct
from typing import Optional


########################### CLASS DEFINITION ###########################
class MassFlowController:
    """
    A class to control a mass flow controller (MFC) via RS485 communication interface.

    Attributes:
        port (str): Serial port to which the MFC is connected.
        address (int): Device address on the RS485 bus.
        max_sccm (float): Maximum flow rate in SCCM.
        ser (Optional[serial.Serial]): Serial connection object.
    """

    def __init__(self, port: str, address: int = 1, max_sccm: Optional[float] = None):
        """
        Initialize the MassFlowController.

        Args:
            port (str): Serial port (e.g., 'COM3', '/dev/ttyUSB0').
            address (int): Device address on the RS485 bus (default is 1).
            max_sccm (float, optional): Maximum flow rate in SCCM. If None, it will be read from the device.
        """
        self.port = port
        self.address = address
        self.max_sccm = max_sccm
        self.ser: Optional[serial.Serial] = None

    def connect(self) -> None:
        """
        Open the serial connection to the MFC and read the maximum flow rate if not provided.
        """
        self.ser = serial.Serial(port=self.port, baudrate=19200, timeout=1)
        print(f"Connected to {self.port} at 19200 baud.")
        if self.max_sccm is None:
            self.max_sccm = self.read_full_scale()
            print(f"Max flow rate read from device: {self.max_sccm} SCCM")

    def disconnect(self) -> None:
        """
        Close the serial connection.
        """
        if self.ser and self.ser.is_open:
            self.ser.close()
            print("Serial connection closed.")
            self.ser = None

    def set_flow_rate(self, flow_rate: float) -> None:
        """
        Set the flow rate in SCCM.

        Args:
            flow_rate (float): Desired flow rate in SCCM.

        Raises:
            ValueError: If flow_rate is out of range.
            IOError: If communication fails.
        """
        if not 0 <= flow_rate <= self.max_sccm:
            raise ValueError(f"Flow rate must be between 0 and {self.max_sccm} SCCM.")

        # Convert flow rate to percentage of full scale
        flow_percentage = (flow_rate / self.max_sccm) * 100.0

        # Encode flow_percentage as 32-bit IEEE 754 float in big-endian
        data_bytes = struct.pack('>f', flow_percentage)

        command_number = 236  # Command to set flow rate

        # Send command
        self._send_command(command_number, data_bytes)
        print(f"Flow rate set to {flow_rate} SCCM ({flow_percentage:.2f}% of full scale).")

    def close(self) -> None:
        """
        Set the flow rate to 0 SCCM (close the flow).
        """
        self.set_flow_rate(0.0)
        print("Flow closed (set to 0 SCCM).")

    def read_flow_rate(self) -> float:
        """
        Read the current flow rate from the MFC.

        Returns:
            float: Current flow rate in SCCM.

        Raises:
            IOError: If communication fails or invalid response.
        """
        command_number = 1
        data_bytes = self._send_command(command_number)
        if len(data_bytes) != 4:
            raise IOError("Invalid data length in flow rate response.")

        # Data bytes are a 32-bit IEEE 754 float representing percentage
        flow_percentage = struct.unpack('>f', data_bytes)[0]
        # Convert percentage to SCCM
        flow_rate = (flow_percentage / 100.0) * self.max_sccm
        print(f"Current flow rate: {flow_rate:.2f} SCCM ({flow_percentage:.2f}% of full scale).")
        return flow_rate

    def read_full_scale(self) -> float:
        """
        Read the full-scale flow rate from the MFC.

        Returns:
            float: Full-scale flow rate in SCCM.

        Raises:
            IOError: If communication fails or invalid response.
        """
        command_number = 152
        data_bytes = self._send_command(command_number)
        if len(data_bytes) != 4:
            raise IOError("Invalid data length in full-scale response.")

        # Data bytes are a 32-bit IEEE 754 float
        full_scale_value = struct.unpack('>f', data_bytes)[0]
        return full_scale_value

    def _calculate_checksum(self, data: bytes) -> int:
        """
        Calculate the checksum for a given data sequence.

        Args:
            data (bytes): Data sequence to calculate checksum.

        Returns:
            int: Calculated checksum.
        """
        checksum = 0
        for b in data:
            checksum ^= b
        return checksum

    def _send_command(self, command: int, data: Optional[bytes] = None) -> bytes:
        """
        Send a command to the MFC and read the response.

        Args:
            command (int): Command number.
            data (bytes, optional): Data bytes to send with the command.

        Returns:
            bytes: Data bytes from the response.

        Raises:
            IOError: If communication fails or checksum is invalid.
        """
        if not self.ser or not self.ser.is_open:
            raise IOError("Serial port is not open.")

        # Construct the command frame
        frame = bytearray()
        # Preamble: 5 bytes of 0xFF
        frame.extend([0xFF] * 5)
        # Start character: 0x02 (master to slave)
        frame.append(0x02)
        # Address: single byte
        frame.append(self.address & 0xFF)
        # Command byte
        frame.append(command & 0xFF)
        # Data bytes
        if data:
            frame.extend(data)
        # Calculate checksum
        checksum_data = frame[5:]  # From start character onwards
        checksum = self._calculate_checksum(checksum_data)
        # Append checksum
        frame.append(checksum & 0xFF)

        # Send the command
        self.ser.write(frame)
        print(f"Command {command} sent to device at address {self.address}.")

        # Read response
        response = self.ser.read(256)  # Read up to 256 bytes or until timeout
        if not response:
            raise IOError("No response received from device.")

        # Find the start of the response frame (0x06 for slave-to-master message)
        start_index = response.find(b'\x06')
        if start_index == -1:
            raise IOError("Invalid response: start character not found.")

        # Response frame starts from start_index
        response_frame = response[start_index:]

        # Extract address, status, data, checksum
        if len(response_frame) < 5:
            raise IOError("Invalid response: too short.")

        # Extract fields
        start_char = response_frame[0]
        address = response_frame[1]
        status = response_frame[2]
        data_bytes = response_frame[3:-1]
        checksum_received = response_frame[-1]

        # Calculate checksum
        checksum_data = response_frame[:-1]
        checksum_calculated = self._calculate_checksum(checksum_data)

        if checksum_received != (checksum_calculated & 0xFF):
            raise IOError("Invalid checksum in response.")

        if status != 0x00:
            raise IOError(f"Device returned error status: {status}")

        print(f"Response received for command {command}.")

        return data_bytes


########################### MAIN ###########################
if __name__ == "__main__":
    # Replace 'COM3' with your serial port
    mfc = MassFlowController(port='COM3')
    try:
        mfc.connect()
        mfc.set_flow_rate(500.0)  # Set flow rate to 500 SCCM
        current_flow = mfc.read_flow_rate()
        mfc.close()  # Close the flow
    except Exception as e:
        print(f"Error: {e}")
    finally:
        mfc.disconnect()
