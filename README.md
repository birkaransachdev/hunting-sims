# Hunting Simulator
## Summary of Tool
Hunting Simulations using OpenDSS code

This repository provides the setup required to run Over & Undervoltage scenarios on various distribution feeders.

Users can select which feeder they would like to simulate Over/Undervoltage conditions on.

## Installation

- networkx
- pandas
- re 
- opendssdirect
- matplotlib
- numpy

## Using the Tool
Run 'python create_hunting.py'

The program will walked through a series of commands for how to run your desired Hunting scenario. 
1. "Please enter your feeder name:" -> e.g. enter `123` or `13bal` (for 123 node feeder and 13 node feeder respectively)
2. "Please choose your 1st hunting node:" -> e.g. enter `48` (can be any node number on the feeder you choose)
3. "Please choose your 2nd hunting node:" -> e.g. enter `83` (any other node on the feeder, distinct from 1st hunting node)
4. "Do you want an overvoltage, undervoltage, or both?" -> e.g. (type o for overvoltage, u for undervoltage, b for both)
5. "Do you want to keep previous output (type y to save, n to clear)" -> Tell the program if you'd like to Hunting results from previous simulations


