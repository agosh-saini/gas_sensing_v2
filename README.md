# Brooks MFC Control and UI with Keithley Sourcemeter

  

This project is designed to control Brooks Mass Flow Controllers (MFCs) via a serial (COM) interface using Python. It includes several key modules for reading data from an ammeter, creating a graphical user interface (GUI), and controlling the MFC devices.

  

## Table of Contents

  

- [Installation](#installation)

- [Usage](#usage)

- [Files Overview](#files-overview)

- [Dependencies](#dependencies)

- [License](#license)

  

## Installation

  

1. Clone the repository to your local machine:

```bash

git clone <repository-url>

cd <repository-directory>

  ```

2. Upload the Arduino Uno Sketch file (.ino) to the Arduino device using the [Arduino IDE](https://www.arduino.cc/en/software).

3. Install the required Python packages using ```pip```

```bash

pip install -r requirements.txt

 ```

## Usage

1.  **Running the GUI**: To start the application, use the following command:

```bash

python main.py

``` 

2.  **Ampmeter Control**: To read data from the ampmeter, you can run the following script:

```bash

python ampmeter.py

```  

3.  **Mass Flow Controller (MFC) Control**: The MFC can be controlled using the mfc.py script:

```bash

python mfc.py
```
  
4.  **Relay Control**: The relay can be controlled using the following script

```bash

python relay_controller.py
```

Make sure your MFC devices and Arduino Uno are properly connected to the COM port before running the scripts.

  

## Files Overview

- ```ampmeter.py```: A script to interact with and read data from an ammeter device connected via COM.

- ```app_ui.py```: This file contains the code for the graphical user interface (GUI) for controlling the MFC and visualizing data.

- ```mfc.py```: A script designed to send control commands to the Brooks MFC via serial communication.

- ```relay_controller.py```: A script to control relay switches connected to the system.

- ```main.py```: The main entry point for the application, initializing the GUI and setting up necessary configurations.

- ```requirements.txt```: Lists all Python dependencies required for the project.

- ```Arduino_Uno_Sketch.ino```: This file contains the Arduino sketch code for interfacing with the Brooks MFC and other hardware components. It should be uploaded to the Arduino Uno to enable communication and control via the serial interface.

- ```Relay_controller_Schematic.pdf```: The schematic to connect 2 4Relay Arduino Sheild and Arduino uno is provided in this file.

  

## Dependencies

  

This project uses several external libraries. Please install them via the ```requirements.txt``` file as mentioned above. Some notable dependencies include:

  

- ```sprotocol``` (0.0.3): A protocol for serial communication with the Brooks MFC.

- ```pyserial``` (3.5): Provides support for serial communication in Python.

- ```PyVISA``` (1.14.1): Used for controlling instruments via VISA.

- ```matplotlib``` (3.9.2): Used for data visualization.

  

See ```requirements.txt``` for the complete list of dependencies.

  

## License

This project is licensed under the ```Apache License 2.0```.. You may use, distribute, and modify this code under the terms of the license. Significant portions of the code were generated using ChatGPT-1o-preview model, however, the prompting, stucture, testing, and project management was done by ```agosh-saini```
