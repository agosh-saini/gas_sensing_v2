###########################
# Author: Agosh Saini - using using GPT-1o-preview model
# Contact: contact@agoshsaini.com
# Date: 2024-OCT-01
###########################

########################### IMPORTS ###########################
import pyvisa


########################### CLASS DEFINITION ###########################
class Keithley2450:
    """
    A class to interface with the Keithley 2450 SourceMeter.

    This class provides methods to control and measure voltage, current, and resistance
    using SCPI commands over various interfaces like USB, LAN, or GPIB.
    """

    def __init__(self, resource_address: str):
        """
        Initialize the connection to the Keithley 2450 SourceMeter.

        Args:
            resource_address (str): The VISA resource address of the instrument.
                Examples:
                    - 'USB0::0x05E6::2450::INSTR'
                    - 'GPIB::24::INSTR'
                    - 'TCPIP0::192.168.1.100::INSTR'
        """
        # Create a Resource Manager
        self.rm = pyvisa.ResourceManager()
        # Open a session to the instrument
        self.instrument = self.rm.open_resource(resource_address)

    def reset(self) -> None:
        """
        Reset the instrument to its default state.

        This ensures that any previous configurations do not interfere with the current session.
        """
        self.instrument.write('*RST')

    def set_voltage(self, voltage: float) -> None:
        """
        Set the source voltage of the instrument.

        Args:
            voltage (float): The voltage level to set in volts.
        """
        # Set the source function to voltage
        self.instrument.write('SOUR:FUNC VOLT')
        # Set the voltage level
        self.instrument.write(f'SOUR:VOLT {voltage}')

    def set_current(self, current: float) -> None:
        """
        Set the source current of the instrument.

        Args:
            current (float): The current level to set in amperes.
        """
        # Set the source function to current
        self.instrument.write('SOUR:FUNC CURR')
        # Set the current level
        self.instrument.write(f'SOUR:CURR {current}')

    def measure_voltage(self) -> float:
        """
        Measure the voltage.

        Returns:
            float: The measured voltage in volts.
        """
        # Configure the measurement function to voltage
        self.instrument.write('MEAS:VOLT?')
        # Read and return the measurement
        response = self.instrument.read()
        return float(response)

    def measure_current(self) -> float:
        """
        Measure the current from the instrument.

        Returns:
            float: The measured current in amperes.
        """
        # Send the command to read the current
        self.instrument.write('READ?')
        # Read the response
        response = self.instrument.read()
        # Parse the response to extract the current value
        data = response.strip().split(',')
        # Extract the current value (adjust the index if necessary)
        # Assuming the current value is the second element in the response
        current = float(data[1])
        return current


    def measure_resistance(self) -> float:
        """
        Measure the resistance.

        Returns:
            float: The measured resistance in ohms.
        """
        # Configure the measurement function to resistance
        self.instrument.write('MEAS:RES?')
        # Read and return the measurement
        response = self.instrument.read()
        return float(response)

    def measure_at_voltage(self, voltage: float) -> float:
        """
        Set a specific voltage and measure the resulting current.

        Args:
            voltage (float): The voltage level to set in volts.

        Returns:
            float: The measured current in amperes at the specified voltage.
        """
        # Set the voltage level
        self.set_voltage(voltage)
        # Turn on the output
        self.instrument.write('OUTP ON')
        # Measure the current
        current = self.measure_current()
        # Turn off the output
        self.instrument.write('OUTP OFF')
        return current

    def close(self) -> None:
        """
        Close the connection to the instrument.

        This should be called when all operations are complete to free up system resources.
        """
        self.instrument.close()
        # Close the resource manager if no longer needed
        self.rm.close()


########################### MAIN FUNCTION ###########################
# Specify the resource address of your instrument
resource_address = 'USB0::0x05E6::0x2450::04502549::INSTR'

# Create an instance of the Keithley2450 class
keithley = Keithley2450(resource_address)

# Reset the instrument to its default state
keithley.reset()

# Measure current at a specified voltage
voltage_level = 1.0  # in volts
current = keithley.measure_at_voltage(voltage_level)
print(f"Measured current at {voltage_level} V: {current} A")

# Close the connection when done
keithley.close()
