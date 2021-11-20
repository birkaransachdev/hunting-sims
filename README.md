# Hunting Simulator
## Summary of Tool
This repository provides the codes and setup required to run power-voltage scenarios that result in overvoltages and undervoltages on various sizes of power distribution grids. The voltage scenarios can enable hunting between grid devices, which can result in voltage oscillations. As prerequisites to run the code, you will need Python 3 and the power flow program OpenDSS installed.

## Installation
Using pip/pip3, you should install the following libraries:
- networkx (run `pip install networkx`)
- pandas (run `pip install pandas`)
- re (run `pip install re`)
- opendssdirect (`pip install OpenDSSDirect.py`)
- matplotlib (`pip install matplotlib`)
- numpy (`pip install numpy`)
- UliPlot (`pip install UliPlot`)

## Using the Tool

Step 1)  Clone this `hunting-sims` repository. Navigate into the src directory by running: `cd introDSSsim` in the Command Prompt/Terminal.

Step 2) Run the command `python create_hunting.py` in your terminal.
This is the file responsible for creating various hunting scenarios.

Step 3) Now the program will walk through a series of user input requests to setup your desired hunting scenario: 
1. "Please enter your feeder name:" -> e.g. enter `123` or `13bal` (for 123 node feeder and 13 node feeder respectively).
2. "Please choose your 1st hunting node:" -> e.g. enter `48` (can be any node number on the feeder you choose).
3. "Please choose your 2nd hunting node:" -> e.g. enter `83` (any other node on the feeder, distinct from 1st hunting node).
4. "Do you want an overvoltage, undervoltage, or both?" -> e.g. (type o for overvoltage, u for undervoltage, or 'b' for both of these voltage issues).
5. "Do you want to keep previous output (type y to save, n to clear)" -> Tell the program whether you'd like to write the results under previous results (save) or to overwrite them with the latest results (clear).

Step 4) The simulation will run to convergence and display the output of the successful over/undervoltage values in the command line. 
Access the code outputted results with the file `hunting_results.csv`.

