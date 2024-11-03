###########################
# Author: Agosh Saini
# Date: 2024-11-03
###########################

#### Environment Variables ####

class env:

    # Default COM PORT
    MFC_COM_PORTS = {
        'MFC 1': 'COM3',
        'MFC 2': 'COM4',
        'MFC 3': 'COM5',
    }

    # Relay COM PORT
    RELAY_COM_PORT = 'COM6'
    RELAY_DELAY = 0

    # Keithey Address
    KEITHLEY = 'USB0::0x05E6::0x2450::04502549::INSTR'


class default:

    # Default Cycling Values
    REPEAT_VALUES = {
        'repeats': 1,
        'MFC 1': 0,
        'MFC 2': 0,
        'MFC 3': 0
    }

    # Default Cycling Values
    MFC_DEFAULT_VALUES = {
        'Pre-Cycle': {
            'time': 300,
            'MFC 1': 0,
            'MFC 2': 0,
            'MFC 3': 0
        },

        'Run-On Cycle': {
            'time': 60,
            'MFC 1': 0,
            'MFC 2': 0,
            'MFC 3': 0
        },

        'Off Cycle': {
            'time': 180,
            'MFC 1': 0,
            'MFC 2': 0,
            'MFC 3': 0
        }
    }
