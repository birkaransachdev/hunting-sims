import pandas as pd
import os
import numpy as np
from src.run_powerflow import run
from src.graph_util import find_paths, is_in_graph
import re
import datetime
from UliPlot.XLSX import auto_adjust_xlsx_column_width


is_clear = False
common_loads_zeroed = False 

def get_feeder_filepath(feeder_name):
    # if feeder_name == '13bal':
    #     folder_name = os.getcwd() + '/IEEE13bal' 
    #     impedance_file = folder_name + '/016_GB_IEEE13_balance_all_ver2.xls'
    #     load_file = folder_name + '/016_GB_IEEE13_balance_sigBuilder_Q_12_13_norm03_3_1.xlsx'
    if feeder_name == '13unbal':
        folder_name = os.getcwd() + '/src/IEEE13unb'
        impedance_file = folder_name + '/001_phasor08_IEEE13.xls'
        load_file = folder_name + '/001_phasor08_IEEE13_norm03_HIL_7_1.xlsx'
    if feeder_name == '123':
        folder_name = os.getcwd() + '/src/IEEE123' 
        impedance_file = folder_name +'/004_GB_IEEE123_OPAL.xls'
        load_file = folder_name + '/004_GB_IEEE123_netload.xlsx'
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
        # print("line_name", line_name)
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
            continue
    return r_total, x_total


def set_over_under_voltage(hi_v: int, lo_v:int, hi_nodes:list, lo_nodes: list, pu: int, power_factor: int, feeder:str):
    """
    Allows user to set an under or overvoltage in p.u.
    Calculates the total real (P) and reactive power (Q) on each node 
    """
    
    pq_ratio = np.tan(np.arccos(power_factor))

    # overvoltage path
    v_delta_hi = ((1*pu)**2 - (hi_v*pu)**2)/2
    r_hi, x_hi = calculate_impedance(feeder, hi_nodes)
    # print("r_hi", r_hi, "x_hi", x_hi)
    # print("v_delta_hi", v_delta_hi)
    # print("hi_v", hi_v, "pu", pu)
    # print("hi_nodes", hi_nodes)
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
    global common_loads_zeroed
    
    prefix = 'LD_'
    vals = {}
    max_nodelist = max(len(hi_nodes), len(lo_nodes))
    
    if not common_loads_zeroed:
        for i in range(max_nodelist):     
            if (hi_nodes[0] == lo_nodes[0]):
                vals[f'{prefix}{hi_nodes[0]}/P'] = 0
                vals[f'{prefix}{hi_nodes[0]}/Q'] = 0
                # hi_nodes.pop(0)
                # lo_nodes.pop(0)
            else: 
                break

    common_loads_zeroed = True

    for node in hi_nodes:
        p_val = hi_S[0]/len(hi_nodes)
        q_val = hi_S[1]/len(hi_nodes)
        vals[f'{prefix}{node}/P'] = p_val
        vals[f'{prefix}{node}/Q'] = q_val


    # set 692 to 0 because it's a switch, if 13 node feeder
    if (feeder == '13bal'):
        switch_node = 692
        vals[f'{prefix}{switch_node}/P'] = 0
        vals[f'{prefix}{switch_node}/Q'] = 0
        lo_nodes.remove(switch_node)

    for node in lo_nodes:    
        p_val = lo_S[0]/len(lo_nodes)
        q_val = lo_S[1]/len(lo_nodes)
        vals[f'{prefix}{node}/P'] = p_val
        vals[f'{prefix}{node}/Q'] = q_val
    
    #fill in loads excel file
    filepath = get_feeder_filepath(feeder)[1]
    load_df = pd.read_excel(filepath)
    load_df = load_df.set_index('Time')

    # 123NF
    if feeder == '123':
        model_df = pd.read_excel('src/IEEE123/004_GB_IEEE123_OPAL.xls', sheet_name = 'Bus')
        model_df['Bus_node'] =  model_df['Bus'].apply(lambda x: re.sub(r'_\w','', str(x)))
    
    # 13unbal
    if feeder == '13unbal':
        model_df = pd.read_excel('src/IEEE13unb/001_phasor08_IEEE13.xls', sheet_name = 'Bus')
        model_df['Bus_node'] = model_df['Bus'].apply(lambda x: re.sub(r'_\w','', str(x)))

    phases = ['_a', '_b', '_c']
    for k, v in vals.items():
        for p in phases:
            new_col = k+p
            if new_col in load_df.columns: 
                load_df[new_col] = v
    
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
    global is_clear
    global volt_condition
    # columns = ['timestamp of run', 'feeder_name', 'high_node', 'low_node', 'high_V', 'low_V', 'high_V (p.u.)', 'low_V (p.u.)',\
    #      'high_node_path', 'low_node_path', 'total_high_PQ', 'total_low_PQ']
    
    file_name = 'hunting_results.xlsx'
    output_df = pd.read_excel(file_name, index_col = 'index')
    # , index_col='index')
    if is_clear: 
        output_df.drop(output_df.index, inplace=True)

    volt_condition_dict = {'o': 'Overvoltage', 'u': 'Undervoltage', 'b': 'Both'}

    # create a new Hunting entry
    new_entry = {}
    new_entry['timestamp of run'] = datetime.datetime.now()
    new_entry['feeder_name'] = feeder_name
    new_entry['type'] = volt_condition_dict[volt_condition]
    new_entry['high_node'] = f'Bus_{high_nodes[-1]}'
    new_entry['low_node'] = f'Bus_{low_nodes[-1]}'
    # new_entry['high_V'] = high_voltage
    # new_entry['low_V'] = low_voltage

    


    # The number of high and low nodes in the path minus the length of the common nodes
    common_nodes = set(high_nodes).intersection(low_nodes)
    new_entry['num_high_nodes'] = len(high_nodes) - len(common_nodes)
    new_entry['num_low_nodes'] = len(low_nodes) - len(common_nodes)
    
    
    new_entry['P_per_hi (kW)'] = hi_S[0]/ new_entry['num_high_nodes']
    new_entry['Q_per_hi (kVAR)'] = hi_S[1]/ new_entry['num_high_nodes']
    new_entry['P_per_lo (kW)'] = lo_S[0]/ new_entry['num_low_nodes']
    new_entry['Q_per_lo (kVAR)'] = lo_S[1]/ new_entry['num_low_nodes']

    # parse results
    actual_high_V = np.mean(results[f'bus_{high_nodes[-1]}']['V_mag'])
    actual_low_V = np.mean(results[f'bus_{low_nodes[-1]}']['V_mag'])

    # Add actual output voltage to new_entry
    new_entry['V_hi (V p.u.)'] = round(actual_high_V, 4)
    new_entry['V_lo (V p.u.)'] = round(actual_low_V, 4)

    print('$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$')
    print(f"Voltage at {new_entry['high_node']}:", round(actual_high_V, 4), "V p.u.")
    print(f"Voltage at {new_entry['low_node']}:", round(actual_low_V, 4), "V p.u.")
    print('$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$')


    if volt_condition == 'o': 
        if ((actual_high_V - actual_low_V) > 0.075) and actual_high_V > 1.05:
            ret_val = True
        else: 
            ret_val = False
    elif volt_condition == 'u':
        if ((actual_high_V - actual_low_V) > 0.075)  and actual_low_V < 0.95: 
            ret_val = True
        else: 
            ret_val = False
    if ret_val: 
        output_df = output_df.append(new_entry, ignore_index = True)
        output_df.index.name = 'index'
        # save as Excel and align margins
        with pd.ExcelWriter(file_name) as writer:
            output_df.to_excel(writer, sheet_name="Results")
            auto_adjust_xlsx_column_width(output_df, writer, sheet_name="Results", margin=0)
    return ret_val

def clear():
    filename = "hunting_results.xlsx"
    df = pd.read_excel(filename)
    column_names = list(df.columns)
    column_names.insert(0, "index")
    df = pd.DataFrame(columns=column_names)
    df.to_excel(filename)
    return 

def main():
    global is_clear
    global volt_condition
    global common_loads_zeroed
    common_loads_zeroed = False
    
    valid_feeder_names = ["13unbal", "123"]
    
    # Feeder name
    feeder_name = input("Please enter your feeder name: ")
    while (feeder_name not in valid_feeder_names):
        feeder_name = input("Please try again: ")

    # Hunting nodes
    if feeder_name == '123':
        sub_node = 150 #substation node
    elif feeder_name == '13unbal': 
        sub_node = 650 #substation node

    node_1 = input("Please choose your 1st hunting node: ")
    while not is_in_graph(feeder_name, node_1):
        node_1 = input("Please try again: ")
    node_2 = input("Please choose your 2nd hunting node: ")
    while not is_in_graph(feeder_name, node_2):
        node_2 = input("Please try again: ")

    node_1 = int(node_1)
    node_2 = int(node_2)
    node_1_path = find_paths(feeder_name, sub_node, node_1)
    node_2_path = find_paths(feeder_name, sub_node, node_2)


    if len(node_1_path) >= len(node_2_path):
        lo_node = node_1
        hi_node = node_2
        low_nodes = node_1_path
        high_nodes = node_2_path
    else: 
        lo_node = node_2
        hi_node = node_1
        low_nodes = node_2_path 
        high_nodes = node_1_path
    
    volt_condition = input("Do you want an overvoltage or undervoltage?\n(type o for overvoltage, u for undervoltage): ")

    # save previous output
    keep_prev = input("Do you want to keep previous output (type y to save, n to clear): ")
    if keep_prev == 'n':
        is_clear = True 

    if volt_condition == 'o':
        high_voltage = 1.1 
        low_voltage = 0.9
    elif volt_condition == 'u':
        high_voltage = 1.2
        low_voltage = 0.9

    # hi_node = 48 #high hunting node
    # lo_node = 83 #low hunting node
    pu_voltage = 2400 #per unit voltage
    power_factor = 0.9 #grid power factor
    step_change = 0.1 #change to vary the rate of convergence to Hunting
    is_hunting = False

    i = 0
    print("\nComputing Hunting Scenario Voltages...\n")
    while not is_hunting:
        print(f"\nSolving Power Flow - Scenario {i}")
        hi_S, lo_S = set_over_under_voltage(high_voltage, low_voltage, high_nodes, low_nodes, pu_voltage, power_factor, feeder_name)
        populate_sigbuilder(high_nodes, low_nodes, hi_S, lo_S, feeder_name)
        results = run(feeder_name, hi_node, lo_node, high_nodes, low_nodes)
        is_hunting = hunting_output(feeder_name, high_voltage, low_voltage, hi_S, lo_S, high_nodes, low_nodes, results)
        

        if volt_condition == 'o':
            high_voltage += step_change
        elif volt_condition == 'u':
            low_voltage -= step_change
        i+=1
    
    print(f"\nHunting has been found between nodes {lo_node} and {hi_node}!")
    print(f"\nOpen up 'hunting_results.xlsx' to view your complete results.")

if __name__ == "__main__":
    main()
