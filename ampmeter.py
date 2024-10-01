import pyvisa

class Keithley2450:
    def __init__(self, resource_address: str):
        self.rm = pyvisa.ResourceManager()
        self.instrument = self.rm.open_resource(resource_address)
        self.instrument.write_termination = '\n'
        self.instrument.read_termination = '\n'
        self.configure_measurement()

    def configure_measurement(self) -> None:
        self.instrument.write('*RST')
        self.instrument.write('*CLS')
        self.instrument.write('SOUR:FUNC VOLT')
        self.instrument.write('SOUR:VOLT 1')  # Set source voltage to 1V
        self.instrument.write('SENS:CURR:PROT 0.1')  # Compliance limit at 100 mA
        self.instrument.write('SENS:FUNC "CURR","VOLT"')
        self.instrument.write('SENS:CURR:RANG:AUTO ON')
        self.instrument.write('SENS:VOLT:RANG:AUTO ON')
        self.instrument.write('SENS:CURR:NPLC 1')
        self.instrument.write('SENS:VOLT:NPLC 1')
        self.instrument.write('FORM:ELEM CURR,VOLT')
        self.instrument.write('OUTP ON')

    def measure_all(self):
        self.instrument.write('INIT')
        self.instrument.write('FETCH?')
        response = self.instrument.read()
        values = [float(v) for v in response.strip().split(',')]
        current = values[0]
        voltage = values[1]
        resistance = voltage / current if current != 0 else float('inf')
        return current, voltage, resistance

    def close(self) -> None:
        self.instrument.write('OUTP OFF')
        self.instrument.close()
        self.rm.close()



# Initialize the instrument
resource_address = 'USB0::0x05E6::0x2450::04502549::INSTR'
keithley = Keithley2450(resource_address)

try:
    # Measure current, voltage, and calculate resistance at 1V
    current, voltage, resistance = keithley.measure_all()
    print(f"Measured Current: {current} A")
    print(f"Measured Voltage: {voltage} V")
    print(f"Calculated Resistance: {resistance} Ohms")
except Exception as e:
    print(f"An error occurred: {e}")
finally:
    # Close the connection when done
    keithley.close()
