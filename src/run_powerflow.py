
# ##############################################################################
#
# Author: Keith Moffat
# Last edited: Nov 6 2021
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

from setup import *
import opendssdirect as dss
from dss_functions import *
# from Ycalcs import * # We don't need this ye

######################## Params #######################
def run(feeder_name, hi_node, lo_node):
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

    #Test Case
    #Its possible that os.getcwd() might not work on non-macs, in which case an alternative method for getting the path to the current working directory must be used
    if testcase == '37':
        loadfolder = os.getcwd() + "/IEEE37/"
        modelpath = loadfolder + "003_GB_IEEE37_OPAL_reform.xls"
        loadpath = loadfolder + "003_GB_IEEE37_time_sigBuilder_1300-1400_norm05.xlsx"
        # Specify substation kV and kVA bases of the load data
        subkVbase_phg = 4.8/np.sqrt(3)
        subkVAbase = 2500
        #shouldnt this come from the load file?
    elif testcase == '13unb':
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
        loadfolder = os.getcwd() + "/IEEE123/"
        # modelpath = loadfolder + "004_GB_IEEE123_OPAL_1.xls"
        modelpath = loadfolder + "004_GB_IEEE123_OPAL.xls"
        # loadpath = loadfolder + "004_123NF_PVpen100_nocloud_minutewise_whead.xlsx"
        loadpath = loadfolder + "004_GB_IEEE123_netload.xlsx"
        # loadpath = loadfolder + "10kwload.xlsx"
        # Specify substation kV and kVA bases of the load data
        subkVbase_phg = 4.16/np.sqrt(3)
        subkVAbase = 5000
    elif testcase == '13balFlatLoad':
        loadfolder = os.getcwd() + "/IEEE13balFlatLoad/"
        modelpath = loadfolder + "016_GB_IEEE13_balance_all_ver2.xls"
        loadpath = loadfolder + "016_GB_IEEE13_balance_sigBuilder_Q_12_13_norm03_3_1.xlsx"
        # Specify substation kV and kVA bases of the load data
        subkVbase_phg = 4.16/np.sqrt(3)
        subkVAbase = 5000
    elif testcase == '2':
        loadfolder = os.getcwd() + "/splitLine3Load/"
        # modelpath = loadfolder + "splitLine3LoadNetwork.xls"
        modelpath = loadfolder + "splitLine3LoadNetworkCrossZ.xls"
        loadpath = loadfolder + "threeLoad.xlsx"
        # Specify substation kV and kVA bases of the load data
        subkVbase_phg = 1
        subkVAbase = 3000
    elif testcase == '1':
        loadfolder = os.getcwd() + "/singleLine/"
        # modelpath = loadfolder + "singleSwitchNetwork.xls" #switch impedance set to a default in switchbuilder
        # modelpath = loadfolder + "singleTransformerNetwork.xls"
        modelpath = loadfolder + "singleLineNetwork.xls"
        # modelpath = loadfolder + "singleLineNetworkCrossZ.xls"
        loadpath = loadfolder + "singleLoad.xlsx"
        # Specify substation kV and kVA bases of the load data
        subkVbase_phg = 1
        subkVAbase = 3000
    else:
        os.error('error loading model')

    subkVAbase = subkVAbase/3
    modeldata = pd.ExcelFile(modelpath)
    actpath = loadpath
    # print(loadpath)
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
    # print(myfeeder)
    # pprint(vars(myfeeder))

    ################################################################################

    common_nodes = [150, 149, 1, 7, 8, 13]
    high_nodes = [18, 135, 35, 40, 42, 44, 47, 48]
    low_nodes = [152, 52, 53, 54, 57, 60, 160, 67, 72, 76, 77, 78, 80, 81, 82, 83]
    
    voltage_output_df = pd.DataFrame()
    
    common_voltage_mag_dict = {}
    common_voltage_ang_dict = {}

    low_voltage_mag_dict = {}
    low_voltage_ang_dict = {}

    high_voltage_mag_dict = {}
    high_voltage_ang_dict = {}

    for ts in range(0,timesteps):
        # print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
        #run power flow:
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
                # print('$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$')
                # print(f'bus.name {bus.name}')
                # print(f'Vmag: {bus.Vmag_NL[:,ts]/(bus.kVbase_phg*1000)}')
                # print(f'Vang: {bus.Vang_NL[:,ts]}')
                # Save results of hunting
                results[bus.name]["V_mag"] = bus.Vmag_NL[:,ts]/(bus.kVbase_phg*1000)
                results[bus.name]["V_angle"] = bus.Vang_NL[:,ts]

            Ibase = bus.kVAbase/bus.kVbase_phg #phg stands for phase to ground (rather than phase to phase)
            SinjCalc = bus.Vcomp[:,ts]/(bus.kVbase_phg*1000) * np.conjugate(bus.Icomp[:,ts]/Ibase) * bus.kVAbase #power in kVARs
            # print(f'PinjCalc: {np.real(SinjCalc)}')
            # print(f'QinjCalc: {np.imag(SinjCalc)}')

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

    # sys.exit()
    ################################################################################

    export_Measurements(myfeeder)

    # sys.exit() #comment this out if you want plots

    #Dictionary to store all results after a run
    look_all_dict = {}
    if plot:
        # phase = 0
        for key,bus in myfeeder.busdict.items():
            # print('bus ', key)
            # print('bus.Vmag_NL ', bus.Vmag_NL)
            # print('bus.phases ', bus.phases)
            for phase in bus.phases:
                # print('phase ', phase)
                if phase=='a' or phase=='A':
                    # plt.plot(bus.Vmag_NL[0,:]/(bus.kVbase_phg*1000), label='node: ' + key + ', ph: ' + str(phase))
                    look_all_dict['node: ' + key + ', ph: ' + str(phase)] = (bus.Vmag_NL[0,:])/(bus.kVbase_phg*1000)
                elif phase=='b' or phase=='B':
                    # plt.plot(bus.Vmag_NL[1,:]/(bus.kVbase_phg*1000), label='node: ' + key + ', ph: ' + str(phase))
                    look_all_dict['node: ' + key + ', ph: ' + str(phase)] = (bus.Vmag_NL[1,:])/(bus.kVbase_phg*1000)
                elif phase=='c' or phase=='C':
                    # plt.plot(bus.Vmag_NL[2,:]/(bus.kVbase_phg*1000), label='node: ' + key + ', ph: ' + str(phase))
                    look_all_dict['node: ' + key + ', ph: ' + str(phase)] = (bus.Vmag_NL[2,:])/(bus.kVbase_phg*1000)
                else:
                    print('ERROR PHASE NOT RECOGNIZED')
            # nphases = len(bus.phases)
            # for phase in np.arange(nphases):
            #     print('bus.Vmag_NL[phase,0] ', bus.Vmag_NL[phase,0])
            #     print('phase ', phase)
            #     if bus.Vmag_NL[phase,0]!=0:
            #         plt.plot(bus.Vmag_NL[phase,:]/(bus.kVbase_phg*1000), label='node: ' + key + ', ph: ' + str(phase))
            #     else:
            #         print('found a zero for bus ', key)
            #         print('phase ', phase)
        # plt.title('V magnitude')
        # plt.ylabel('p.u. Vmag')
        # plt.xlabel('Timestep')
        # plt.legend()
        # plt.show()
        look_all_df = pd.DataFrame(columns = [k for k in look_all_dict.keys()], index = [i for i in range(0, timesteps, interval)])

        for t in range(0, timesteps, interval):
            for k, v in look_all_dict.items():
                look_all_df.loc[t, k] = v[t]
                
        look_all_df.to_csv('look_all_df.csv',index=True)

    return results
        
        
        
        # for key,bus in myfeeder.busdict.items():
            # print('bus ', key)
            # print('bus.Vang_NL ', bus.Vang_NL)
            # print('bus.phases ', bus.phases)
            
            
            # PHASE ANGLES PLOTS (COMMENTED OUT)$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
            
            # for phase in bus.phases:
            #     # print('phase ', phase)
            #     if phase=='a' or phase=='A':
            #         plt.plot(bus.Vang_NL[0,:]*np.pi/180, label='node: ' + key + ', ph: ' + str(phase))
            #     elif phase=='b' or phase=='B':
            #         plt.plot(bus.Vang_NL[1,:]*np.pi/180 + 2*np.pi/3, label='node: ' + key + ', ph: ' + str(phase))
            #     elif phase=='c' or phase=='C':
            #         plt.plot(bus.Vang_NL[2,:]*np.pi/180 - 2*np.pi/3, label='node: ' + key + ', ph: ' + str(phase))
            #     else:
            #         print('ERROR PHASE NOT RECOGNIZED')


            # PHASE ANGLES PLOTS (COMMENTED OUT)$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$

            # nphases = len(bus.phases)
            # for phase in np.arange(nphases):
            #     Vangs = bus.Vang_NL[phase,:]*np.pi/180
            #     if phase == 1:
            #         Vangs += 2*np.pi/3 #angles are adjusted to be around 0 before they are plotted so that the angles for all the phases fit on the same plot
            #     elif phase == 2:
            #         Vangs += -2*np.pi/3
            #     plt.plot(Vangs, label='node: ' + key + ', ph: ' + str(phase))
        # plt.title('V angle')
        # plt.ylabel('Vang [rad]')
        # plt.xlabel('Timestep')
        # plt.legend()
        # plt.show()

if __name__ == "__main__":
    run()
