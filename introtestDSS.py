
# ##############################################################################
#
# Author: Keith Moffat
# Last edited: Jan 12 2021
#
# License:
# This code may be shared only with written permission from the author.
# This code may be used for academic research purposes.
# This code may not be used for commercial purposes without the author's permission.
#
# ##############################################################################

import numpy as np
from scipy.sparse import csc_matrix
import opendssdirect as dss

import sys

'''
5/6/20:
Have to come back to this and provide a clear explanation of:
- basekv=1.732
- That kV is in the load commands
- How kV and basekv relate to Vminpu and Vmaxpu
'''

dss.run_command('clear')
dss.run_command(
    "new circuit.currentckt basekv=1.732 pu=1.0000 phases=3 bus1=bus_1"
    " Angle=0 MVAsc3=200000 MVASC1=200000"
)
dss.run_command(
    "New Line.1 Bus1=bus_1.1.2.3 Bus2=bus_2.1.2.3 BaseFreq=60 Phases=3 Length=1"
    " rmatrix = (.02 | .01 .02 | .01 .01 .02)"
    " xmatrix = (0 | 0 0 | 0 0 0)"
)


#kV = 1: results as expected. Votlages within bounds so the powers are equal to the assigned powers
dss.run_command("New Load.load2aCP Bus1=bus_2.1 Phases=1 Conn=Wye Model=1 kV=1 kW=1e3 kvar=0 Vminpu=0.8 Vmaxpu=1.2")
dss.run_command("New Load.load2bCP Bus1=bus_2.2 Phases=1 Conn=Wye Model=1 kV=1 kW=1e3 kvar=0 Vminpu=0.8 Vmaxpu=1.2")
dss.run_command("New Load.load2cCP Bus1=bus_2.3 Phases=1 Conn=Wye Model=1 kV=1 kW=1e3 kvar=0 Vminpu=0.8 Vmaxpu=1.2")

#kV = 1.4: results in a bus 2 voltage that is below Vminpu (.8*1.4=1.1)
#openDSS does a ridiculous thing when voltages are outside of the specified ranges, DSS switches the constant power commands to constant impedance equivalents. (I have NO idea why.)
#so you will notice that when this code (with the base kV = 1.4) is used, the power calculation in TEST 2 is LESS than the assigned 1e3 kW.
# dss.run_command("New Load.load2aCP Bus1=bus_2.1 Phases=1 Conn=Wye Model=1 kV=1.4 kW=1e3 kvar=0 Vminpu=0.8 Vmaxpu=1.2")
# dss.run_command("New Load.load2bCP Bus1=bus_2.2 Phases=1 Conn=Wye Model=1 kV=1.4 kW=1e3 kvar=0 Vminpu=0.8 Vmaxpu=1.2")
# dss.run_command("New Load.load2cCP Bus1=bus_2.3 Phases=1 Conn=Wye Model=1 kV=1.4 kW=1e3 kvar=0 Vminpu=0.8 Vmaxpu=1.2")

#kV = .8: results in a bus 2 voltage that is above Vmaxpu (1.2*.8=.96), at which point the loads switch to constant Z
#so you will notice that when this code is used (with the base kV = .8), the power calculation in TEST 2 is MORE than the assigned 1e3 kW.
# dss.run_command("New Load.load2aCP Bus1=bus_2.1 Phases=1 Conn=Wye Model=1 kV=.8 kW=1e3 kvar=0 Vminpu=0.8 Vmaxpu=1.2")
# dss.run_command("New Load.load2bCP Bus1=bus_2.2 Phases=1 Conn=Wye Model=1 kV=.8 kW=1e3 kvar=0 Vminpu=0.8 Vmaxpu=1.2")
# dss.run_command("New Load.load2cCP Bus1=bus_2.3 Phases=1 Conn=Wye Model=1 kV=.8 kW=1e3 kvar=0 Vminpu=0.8 Vmaxpu=1.2")


#Test 3:
#the first version wont work and DSS's error message doesnt make it through to python
# Pload = 1e3
# Qload = 0
# dss.run_command("New Load.load2aCP Bus1=bus_2.1 Phases=1 Conn=Wye Model=1 kV=1 kW=Pload kvar=Qload Vminpu=0.8 Vmaxpu=1.2")
# dss.run_command("New Load.load2bCP Bus1=bus_2.2 Phases=1 Conn=Wye Model=1 kV=1 kW=Pload kvar=Qload Vminpu=0.8 Vmaxpu=1.2")
# dss.run_command("New Load.load2cCP Bus1=bus_2.3 Phases=1 Conn=Wye Model=1 kV=1 kW=Pload kvar=Qload Vminpu=0.8 Vmaxpu=1.2")
# dss.run_command("New Load.load2aCP Bus1=bus_2.1 Phases=1 Conn=Wye Model=1 kV=1 kW=" + str(Pload) + " kvar=" + str(Qload) + " Vminpu=0.8 Vmaxpu=1.2")
# dss.run_command("New Load.load2bCP Bus1=bus_2.2 Phases=1 Conn=Wye Model=1 kV=1 kW=" + str(Pload) + " kvar=" + str(Qload) + " Vminpu=0.8 Vmaxpu=1.2")
# dss.run_command("New Load.load2cCP Bus1=bus_2.3 Phases=1 Conn=Wye Model=1 kV=1 kW=" + str(Pload) + " kvar=" + str(Qload) + " Vminpu=0.8 Vmaxpu=1.2")

'''
LESSON:
You have to manually check that the powers you are assigned were actaully actuated by DSS.
(I wrote this functionality into savePFResults of introtestDSS. It requires alarm=1)
'''

dss.run_command("set tolerance=0.0000000001")
dss.run_command("calcv")

dss.run_command("Solve")



dss.Circuit.SetActiveBus('bus_2')
bus2V = np.asarray(dss.Bus.Voltages()).view(dtype=complex)
print(f'bus2V {bus2V}')

dss.Circuit.SetActiveBus('bus_1')
bus1V = np.asarray(dss.Bus.Voltages()).view(dtype=complex)
print(f'bus1V {bus1V}')

#load convention is used in the commands, so power is positive into the load
dV = bus1V - bus2V
print(f'dV {dV}')

dss.Circuit.SetActiveElement('Line.1')
lineI = -np.asarray(dss.CktElement.Currents()).view(dtype=complex)[3:6]
#for some reason the current that is returned is positive into the network?

(Ysparse, indices, indptr) = dss.YMatrix.getYsparse(factor=False)
Ydss = csc_matrix((Ysparse, indices, indptr))
Yline = -Ydss[0:3, 3:6].toarray()
Zline = np.linalg.inv(Yline)

print('Zline ', Zline)

# TEST 1: The voltage differences from the DSS output and the voltages differences from Ohms law should be equal
#       (The currents from DSS and the currents calculated from Ohms law should also be equal)
Icalc = np.dot(Yline, dV)
# dVcalc = np.dot(Zline, lineI) #this is useless, its just dVcalc = Z*Y*dV
# print(f'dVcalc {dVcalc}')
# print(f'dV {dV}')
print(f'Icalc {Icalc}')
print(f'lineI {lineI}')

# TEST 2: The power at the load bus should be equal to the specified power kW=1e3 (as long as the voltages are within the specified range)
S2calc = bus2V*np.conjugate(lineI)/(1e3) #divided by 1e3 to get powers in terms of kW
print(f'S2calc: {S2calc}')




# Output:
# dVcalc [-10.10239179+1.48571346e-04j   5.05132456+8.74885364e+00j   5.05106722-8.74900222e+00j]
# dV [-10.10239179+1.42227453e-04j   5.05131907+8.74885681e+00j   5.05107272-8.74899904e+00j]
# Icalc [1010.23917873-1.42229161e-02j  -505.13190687-8.74885681e+02j  -505.10727176+8.74899904e+02j]
# lineI [1010.23917872-1.48573054e-02j  -505.13245626-8.74885364e+02j  -505.10672236+8.74900221e+02j]
# |Icalc| [1010.23917883 1010.23917883 1010.23917883]
# |lineI| [1010.23917883 1010.23917883 1010.23917883]
