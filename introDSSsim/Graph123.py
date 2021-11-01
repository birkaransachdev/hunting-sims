import networkx as nx
import matplotlib.pyplot as plt
from networkx.algorithms.smetric import s_metric
import pandas as pd 
import os
import numpy as np


def create_graph():
    filepath = os.getcwd() + '/IEEE123/123NF_graph.xlsx'
    g = nx.Graph()
    
    graph_df = pd.read_excel(filepath)
    for index, row in graph_df.iterrows():
        nd_start = int(row.iloc[0])
        for i in range(3):
            if not np.isnan(row.iloc[i+1]): 
                nd_end= int(row[f'TO_{i}'])
                g.add_edge(nd_start, nd_end)
    return g

def find_paths(start, end):
    g = create_graph()
    for path in nx.all_simple_paths(g, source=start, target=end):
        return path 

def is_in_graph(node):
    g = create_graph()
    try:
        int(node)
    except ValueError:
        return False

    if int(node) in list(g.nodes):
        return True
    else: 
        return False

# def main():
#     start = 150 
#     end = 4
#     find_paths(start, end)
    
# if __name__ == "__main__":
#     main()