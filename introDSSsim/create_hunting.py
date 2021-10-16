from typing import ClassVar
from numpy.lib.shape_base import apply_along_axis
import pandas as pd
import os
import numpy as np
from main import run
from Graph123 import find_paths
from pandas.io.parsers import read_table
import re

def get_feeder_filepath(feeder_name):
    if feeder_name == '13bal':
        folder_name = os.getcwd() + '/IEEE13bal' 
        impedance_file = folder_name + '/016_GB_IEEE13_balance_all_ver2.xls'
        load_file = folder_name + '/016_GB_IEEE13_balance_sigBuilder_Q_12_13_norm03_3_1.xlsx'
    if feeder_name == '123':
        folder_name = os.getcwd() + '/IEEE123' 
        impedance_file = folder_name +'/004_GB_IEEE123_OPAL.xls'
        load_file = folder_name + '/004_GB_IEEE123_netload.xlsx'
        # load_file = folder_name + '/004_123NF_PVpen100_nocloud_minutewise_whead.xlsx'
    
    return impedance_file, load_file 
        
def calculate_impedance(feeder_name: str, nodes: list) -> tuple():
    """
    Calculates the R and X of a given line
    """
    
    impedance_file = get_feeder_filepath(feeder_name)[0]

    imp_df = pd.read_excel(impedance_file, sheet_name = 'Multiphase Line')
    r_total = 0 
    x_total = 0
    for i in range(len(nodes) - 1):
        line_name = f'LN_{nodes[i]}_{nodes[i+1]}'
        if line_name in list(imp_df.ID):
            line_df = imp_df.loc[imp_df.ID == line_name]
            length = float(line_df['Length (length_unit)'])
            
            if np.isnan(float(line_df['r21 (ohm/length_unit)'])):
                # Resistance - R
                r_aa = float(line_df['r11 (ohm/length_unit)'])
                r_line = length*r_aa
                r_total += r_line

                # Reactance - X
                x_aa = float(line_df['x11 (ohm/length_unit)'])
                x_line = length*x_aa
                x_total += x_line
            else: 
                # Resistance - R
                r_aa, r_bb, r_cc = float(line_df['r11 (ohm/length_unit)']), float(line_df['r22 (ohm/length_unit)']), float(line_df['r33 (ohm/length_unit)'])
                r_ab, r_ac, r_bc = float(line_df['r21 (ohm/length_unit)']), float(line_df['r31 (ohm/length_unit)']), float(line_df['r32 (ohm/length_unit)'])
                r_line = length*(r_aa + r_bb + r_cc - r_ab - r_ac - r_bc)/3
                r_total += r_line

                # Reactance - X
                x_aa, x_bb, x_cc = float(line_df['x11 (ohm/length_unit)']), float(line_df['x22 (ohm/length_unit)']), float(line_df['x33 (ohm/length_unit)'])
                x_ab, x_ac, x_bc = float(line_df['x21 (ohm/length_unit)']), float(line_df['x31 (ohm/length_unit)']), float(line_df['x32 (ohm/length_unit)'])
                x_line = length*(x_aa + x_bb + x_cc - x_ab - x_ac - x_bc)/3
                x_total += x_line
            
        else:
            print(f"Line {line_name} impedances not found!")
    # print("r_total_fin", r_total, "x_total_fin", x_total)
    return r_total, x_total


def set_over_under_voltage(hi_v: int, lo_v:int, hi_nodes:list, lo_nodes: list, pu: int, power_factor: int, feeder:str):
    """
    Allows user to set an under or overvoltage in p.u.
    Calculates the total real (P) and reactive power (Q) on each node 
    """
    
    pq_ratio = np.tan(np.arccos(power_factor))

    # overvoltage path
    v_delta_hi = ((1*pu)**2 - (hi_v*2400)**2)/2
    r_hi, x_hi = calculate_impedance(feeder, hi_nodes)
    # print('r_hi', r_hi, 'x_hi', x_hi)
    A_hi = np.array([[r_hi,x_hi],[0.484,-1]])
    B_hi = np.array([v_delta_hi,0])
    C_hi = np.linalg.solve(A_hi,B_hi)
    C_hi = C_hi/1000

    v_delta_lo = ((1*pu)**2 - (lo_v*2400)**2)/2
    r_lo, x_lo = calculate_impedance(feeder, lo_nodes)
    A_lo = np.array([[r_lo,x_lo],[0.484,-1]])
    B_lo = np.array([v_delta_lo,0])
    C_lo = np.linalg.solve(A_lo,B_lo)
    C_lo = C_lo/1000

    return C_hi, C_lo



def populate_sigbuilder(hi_nodes:list, lo_nodes:list, hi_S:list, lo_S:list, feeder: str):
    prefix = 'LD_'
    vals = {}
    if hi_nodes[0] == lo_nodes[0]:
        vals[f'{prefix}{hi_nodes[0]}/P'] = 0
        vals[f'{prefix}{hi_nodes[0]}/Q'] = 0
        hi_nodes.pop(0)
        lo_nodes.pop(0)

    for node in hi_nodes:
        p_val = hi_S[0]/len(hi_nodes)
        q_val = hi_S[1]/len(hi_nodes)
        vals[f'{prefix}{node}/P'] = p_val
        vals[f'{prefix}{node}/Q'] = q_val

    # set 692 to 0 because it's a switch

    # switch_node = 692
    # vals[f'{prefix}{switch_node}/P'] = 0
    # vals[f'{prefix}{switch_node}/Q'] = 0
    # lo_nodes.remove(switch_node)

    for node in lo_nodes:    
        p_val = lo_S[0]/len(lo_nodes)
        q_val = lo_S[1]/len(lo_nodes)
        vals[f'{prefix}{node}/P'] = p_val
        vals[f'{prefix}{node}/Q'] = q_val
    
    #fill in loads excel file
    filepath = get_feeder_filepath(feeder)[1]
    # print(filepath)
    load_df = pd.read_excel(filepath)
    load_df = load_df.set_index('Time')

    if feeder == '123':
        model_df = pd.read_excel('IEEE123/004_GB_IEEE123_OPAL.xls', sheet_name = 'Bus')
        model_df['Bus_node'] =  model_df['Bus'].apply(lambda x: re.sub(r'_\w','', str(x)))
        # print('model_file', model_df['Bus_node'])

        
    phases = ['_a', '_b', '_c']
    # print("BUS_NODE", model_df['Bus_node'])
    for k, v in vals.items():
        # print(k, v)
        for p in phases:
            new_col = k+p
            if new_col in load_df.columns: 
                # print(f"yes it's it's in phase {new_col}") 
                load_df[new_col] = v
        # node_df = model_df.loc[model_df['Bus_node'] == k]
        # for i in model_df['Bus']:
        #     print("load_df[i]", i, "v", v)
        #     load_df[i] = v



    # print(load_df)
    
    # Create a Pandas Excel writer using XlsxWriter as the engine.
    writer = pd.ExcelWriter(filepath, engine='xlsxwriter')
    load_df.to_excel(writer, sheet_name='Time_Series_data')
    writer.save()
    return


# """
# Outputs results of current hunting run: 
# 1. Overvoltage at high node
# 2. Undervoltage at low node
# 3. List of high nodes 
# 4. List of low nodes
# 5. Total P & Q at high and low nodes
# """
def hunting_output(feeder_name, high_voltage, low_voltage, hi_S, lo_S, high_nodes, low_nodes, results):
    columns = ['feeder_name', 'high_node', 'low_node', 'high_V', 'low_V', 'actual_high_V', 'actual_low_V',\
         'high_node_path', 'low_node_path', 'total_high_PQ', 'total_low_PQ', 'hunting_achieved' ]
    
    # output_df = pd.DataFrame(columns=columns)
    file_name = 'hunting_result_1.csv'
    output_df = pd.read_csv(file_name, index_col='index')
    # output_df.set_index('index')
    # create a new Hunting entry
    new_entry = {}
    new_entry['feeder_name'] = feeder_name
    new_entry['high_node'] = f'Bus_{high_nodes[-1]}'
    new_entry['low_node'] = f'Bus_{low_nodes[-1]}'
    new_entry['high_V'] = high_voltage
    new_entry['low_V'] = low_voltage
    # new_entry['total_high_PQ'] = hi_S
    # new_entry['total_low_PQ'] = lo_S
    # new_entry['high_node_path'] = high_nodes
    # new_entry['low_node_path'] = low_nodes
    new_entry['num_high_nodes'] = len(high_nodes)
    new_entry['num_low_nodes'] = len(low_nodes)
    
    
    new_entry['P_per_hi'] = hi_S[0]/ new_entry['num_high_nodes']
    new_entry['Q_per_hi'] = hi_S[1]/ new_entry['num_high_nodes']
    
    new_entry['P_per_lo'] = lo_S[0]/ new_entry['num_low_nodes']
    new_entry['Q_per_lo'] = lo_S[1]/ new_entry['num_low_nodes']
        

    # parse results
    actual_high_V = max(results[f'bus_{high_nodes[-1]}']['V_mag'])
    actual_low_V = max(results[f'bus_{low_nodes[-1]}']['V_mag'])

    new_entry['actual_high_V'] = actual_high_V
    new_entry['actual_low_V'] = actual_low_V

    new_entry['hunting_achieved'] = 'yes'

    # print("output_df_before", output_df)
    # output_df = output_df.append(new_entry, ignore_index=True)
    # print(new_entry)
    output_df.loc[len(output_df.index)] = new_entry
    print("output_df", output_df)

    output_df.to_csv(file_name)

    return 

def main():
    feeder_name = '123' #feeder name
    # hi_V = np.arange(1.05, 1.65, 0.05)
    # lo_V = np.arange(0.95, 0.35, -0.05)

    # for i in range(len(lo_V)):
    # high_voltage = hi_V[i] #desired overvoltage
    # low_voltage = lo_V[i] #desired undervoltage
    
    high_voltage = 1.15 #desired overvoltage
    low_voltage = 0.85 #desired undervoltage
    
    sub_node = 150 #substation node
    hi_node = 4 #high hunting node
    lo_node = 114 #low hunting node
    pu_voltage = 2400 #per unit voltage
    
    # high_nodes = [632, 645, 646]
    # low_nodes = [632, 671, 692, 675]

    high_nodes = find_paths(sub_node, hi_node)
    low_nodes = find_paths(sub_node, lo_node)

    # print("high_nodes", high_nodes)
    # print("low_nodes", low_nodes)

    hi_S, lo_S = set_over_under_voltage(high_voltage, low_voltage, high_nodes, low_nodes, 2400, 0.9, feeder_name)
    populate_sigbuilder(high_nodes, low_nodes, hi_S, lo_S, feeder_name)
    # print('hi_S', hi_S)
    # print('lo_S', lo_S)
    results = run(feeder_name, hi_node, lo_node)
    # print("Results of hunting are:", results)
    hunting_output(feeder_name, high_voltage, low_voltage, hi_S, lo_S, high_nodes, low_nodes, results)
    print(f"Simulation is complete for low node {lo_node} and high node {hi_node}")

if __name__ == "__main__":
    main()
