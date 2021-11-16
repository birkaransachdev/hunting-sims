
# ##############################################################################
#
# Author: Keith Moffat
# Last edited: Nov 15 2021
# 
# Revised by: Birks Sachdev
# 
# License:
# This code may be shared only with written permission from the author.
# This code may be used for academic research purposes with permission from the author.
# This code may not be used for commercial purposes without the author's written permission.
#
# ##############################################################################

import numpy as np
from pprint import pprint
import matplotlib.pyplot as plt
import sys
import os
import re 

from src.setup import *
import opendssdirect as dss
from src.dss_functions import *
# from Ycalcs import * # We don't need this ye

######################## Params #######################
def run(feeder_name, hi_node, lo_node, high_nodes, low_nodes):
    # Create an dictionary to record Hunting Results
    results = {}
    results[f'bus_{hi_node}'] = {}
    results[f'bus_{lo_node}'] = {}
    #Plotting flag
    plot = 1
    #Power flow params
    alarm = 0
    #print things while running?
    loud = 0

    testcase = feeder_name; timesteps = 1; interval = 1

    #######################################################

    #Its possible that os.getcwd() might not work on non-macs, in which case an alternative method for getting the path to the current working directory must be used
    if testcase == '13unb':
        loadfolder = os.getcwd() + "/IEEE13unb/"
        modelpath = loadfolder + "001_phasor08_IEEE13.xls"
        loadpath = loadfolder + "001_phasor08_IEEE13_norm03_HIL_7_1.xlsx"
        # Specify substation kV and kVA bases of the load data
        subkVbase_phg = 4.16/np.sqrt(3)
        subkVAbase = 5000
    elif testcase == '13bal':
        loadfolder = os.getcwd() + "/IEEE13bal/"
        modelpath = loadfolder + "016_GB_IEEE13_balance_all_ver2.xls"
        loadpath = loadfolder + "016_GB_IEEE13_balance_sigBuilder_Q_12_13_norm03_3_1.xlsx"
        # Specify substation kV and kVA bases of the load data
        subkVbase_phg = 4.16/np.sqrt(3)
        subkVAbase = 5000
    elif testcase == '123':
        loadfolder = os.getcwd() + "/src/IEEE123/"
        modelpath = loadfolder + "004_GB_IEEE123_OPAL.xls"
        loadpath = loadfolder + "004_GB_IEEE123_netload.xlsx"
        # Specify substation kV and kVA bases of the load data
        subkVbase_phg = 4.16/np.sqrt(3)
        subkVAbase = 5000
    else:
        os.error('error loading model')

    subkVAbase = subkVAbase/3
    modeldata = pd.ExcelFile(modelpath)
    actpath = loadpath

    # Create feeder object
    refphasor = np.ones((3,2))
    refphasor[:,0]=1
    refphasor[:,1]=[0,4*np.pi/3,2*np.pi/3]

    actpath = loadpath

    # set dummy values for undefined variables 
    timestepcur = 0
    Psat_nodes = []
    Qsat_nodes = []
    PVforecast = 0
    depth_dict = {}
    leaf_list = []

    myfeeder = feeder(modelpath,loadfolder,loadpath,actpath,timesteps,timestepcur,subkVbase_phg,subkVAbase,refphasor,Psat_nodes,Qsat_nodes,PVforecast, depth_dict, leaf_list)

    ################################################################################

    common_nodes = list(set(high_nodes).intersection(low_nodes))
    voltage_output_df = pd.DataFrame()
    
    common_voltage_mag_dict = {}
    common_voltage_ang_dict = {}

    low_voltage_mag_dict = {}
    low_voltage_ang_dict = {}

    high_voltage_mag_dict = {}
    high_voltage_ang_dict = {}

    for ts in range(0,timesteps):
        DSS_run3phasePF(myfeeder,ts, loud)
        savePFresults(myfeeder,ts,alarm)  

        for key,bus in myfeeder.busdict.items():
            bus_no = re.findall(r'\d+', bus.name)[0]
            if (int(bus_no) in high_nodes):
                high_voltage_mag_dict[bus_no] = bus.Vmag_NL[:,ts]/(bus.kVbase_phg*1000)
                high_voltage_ang_dict[bus_no] = bus.Vang_NL[:,ts]

            if (int(bus_no) in low_nodes):
                low_voltage_mag_dict[bus_no] = bus.Vmag_NL[:,ts]/(bus.kVbase_phg*1000)
                low_voltage_ang_dict[bus_no] = bus.Vang_NL[:,ts]

            if (int(bus_no) in common_nodes):
                common_voltage_mag_dict[bus_no] = bus.Vmag_NL[:,ts]/(bus.kVbase_phg*1000)
                common_voltage_ang_dict[bus_no] = bus.Vang_NL[:,ts]

            if (bus.name == f"bus_{hi_node}" or bus.name == f"bus_{lo_node}"):
                # Save results of hunting
                results[bus.name]["V_mag"] = bus.Vmag_NL[:,ts]/(bus.kVbase_phg*1000)
                results[bus.name]["V_angle"] = bus.Vang_NL[:,ts]

            Ibase = bus.kVAbase/bus.kVbase_phg #phg stands for phase to ground (rather than phase to phase)
            SinjCalc = bus.Vcomp[:,ts]/(bus.kVbase_phg*1000) * np.conjugate(bus.Icomp[:,ts]/Ibase) * bus.kVAbase #power in kVARs

    len_common = len(list(common_voltage_mag_dict.keys()))
    len_high = len(list(high_voltage_mag_dict.keys()))
    len_low = len(list(low_voltage_mag_dict.keys()))

    max_len = max(max(len_low, len_high), len_common)
    voltage_output_df["index"] = pd.Series(np.arange(0, max_len))
    voltage_output_df["common_nodes"] = pd.Series(list(common_voltage_mag_dict.keys()))
    voltage_output_df["common_Vmag"] = pd.Series(list(common_voltage_mag_dict.values()))
    voltage_output_df["common_Vang"] = pd.Series(list(common_voltage_ang_dict.values()))

    voltage_output_df["low_nodes"] = pd.Series(list(low_voltage_mag_dict.keys()))
    voltage_output_df["low_Vmag"] = pd.Series(list(low_voltage_mag_dict.values()))
    voltage_output_df["low_Vang"] = pd.Series(list(low_voltage_ang_dict.values()))

    voltage_output_df["high_nodes"] = pd.Series(list(high_voltage_mag_dict.keys()))
    voltage_output_df["high_Vmag"] = pd.Series(list(high_voltage_mag_dict.values()))
    voltage_output_df["high_Vang"] = pd.Series(list(high_voltage_ang_dict.values()))

    voltage_output_df.to_csv('voltage_output.csv', index=False)
    return results
        
   
if __name__ == "__main__":
    run()
