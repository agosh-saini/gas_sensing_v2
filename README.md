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

2. nstall the required Python packages using ```pip```

```bash

pip install -r requirements.txt

 ```

## Usage

1.  **Running the GUI**: To start the application, use the following command:

```bash

python app_ui.py

``` 

2.  **Ammeter Control**: To read data from the ammeter, you can run the following script:

```bash

python ampmeter.py

```  

3.  **Mass Flow Controller (MFC) Control**: The MFC can be controlled using the mfc.py script:

```bash

python mfc.py
```
  

Make sure your MFC devices are properly connected to the COM port before running the scripts.

  

## Files Overview

- ```ampmeter.py```: A script to interact with and read data from an ammeter device connected via COM.

- ```app_ui.py```: This file contains the code for the graphical user interface (GUI) for controlling the MFC and visualizing data.

- ```mfc.py```: A script designed to send control commands to the Brooks MFC via serial communication.

- ```requirements.txt```: Lists all Python dependencies required for the project.

  

## Dependencies

  

This project uses several external libraries. Please install them via the ```requirements.txt``` file as mentioned above. Some notable dependencies include:

  

- ```sprotocol``` (0.0.3): A protocol for serial communication with the Brooks MFC.

- ```pyserial``` (3.5): Provides support for serial communication in Python.

- ```PyVISA``` (1.14.1): Used for controlling instruments via VISA.

- ```matplotlib``` (3.9.2): Used for data visualization.

  

See ```requirements.txt``` for the complete list of dependencies.

  

## License

This project is licensed under the ```Apache License 2.0```.. You may use, distribute, and modify this code under the terms of the license. Significant portions of the code were generated using ChatGPT-1o-preview model, however, the prompting, stucture, testing, and project management was done by ```agosh-saini```