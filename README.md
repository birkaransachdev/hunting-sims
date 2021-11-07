# Hunting Simulator
## Summary of Tool
This repository provides the codes and setup required to run power-voltage scenarios that result in overvoltages and undervoltages on various sizes of power distribution grids. The voltage scenarios can enable hunting between grid devices, which can result in voltage oscillations.

## Installation
Using pip/pip3, you should first install the following libraries:
- networkx (run `pip install networkx`)
- pandas (run `pip install pandas`)
- re (run `pip install re`)
- opendssdirect (`pip install OpenDSSDirect.py`)
- matplotlib (`pip install matplotlib`)
- numpy (`pip install numpy`)

## Using the Tool

Step 1)  Navigate into the src directory by running: `cd introDSSsim` in the Command Prompt/Terminal, once you have cloned the 
`hunting-sims` repository.

Step 2) Run the command `python create_hunting.py` in your terminal.
This is the file responsible for creating various Hunting scenarios.

Step 3) Now the program will walked through a series of commands for how to run your desired Hunting scenario, on the feeder of your choice. 
1. "Please enter your feeder name:" -> e.g. enter `123` or `13bal` (for 123 node feeder and 13 node feeder respectively).
2. "Please choose your 1st hunting node:" -> e.g. enter `48` (can be any node number on the feeder you choose).
3. "Please choose your 2nd hunting node:" -> e.g. enter `83` (any other node on the feeder, distinct from 1st hunting node).
4. "Do you want an overvoltage, undervoltage, or both?" -> e.g. (type o for overvoltage, u for undervoltage).
5. "Do you want to keep previous output (type y to save, n to clear)" -> Tell the program whether you'd like to save or clear Hunting results from previous simulations.

Step 4) The simulation will run to convergence and display the output of the successful over/undervoltage values in the command line. 
Access the results of simulation the file `hunting_results.csv`.

