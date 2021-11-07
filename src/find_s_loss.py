# import math
# import cmath
# import pandas as pd
# from create_hunting import calculate_impedance

# def find_S_loss():
#     nodes = [149, 1]
#     df = pd.read_excel("loss_experiment.xlsx")
#     prefixes = ["common", "low", "high"]

#     for prefix in prefixes:
#         prev_Vmag, cur_Vmag = None, None
#         prev_Vang, cur_Vang = None, None
#         is_second = False
#         for node, V_mag, V_ang in zip(df["common_node"], df["common_Vmag"], df["common_Vang"]):
#             nodes.append(node)
#             curr_Vmag_1 = V_mag 
#             curr_Vmag_2 = 

#             if is_second == False: 
#                 is_second = True
#             elif is_second == True: 
#                 is_second = False

#             if len(node) == 2: 

                



#     V1 = cmath.rect(0.99923225, math.radians(-1.20056084e+02))
#     V2 = cmath.rect(0.99722229, math.radians(-121.41723685))
#     R, X = calculate_impedance('123', nodes)
#     Z = complex(R, X)

#     S_loss = ((V1 - V2)*V1)/Z + ((V2 - V1)*V2)/Z
#     print("S_loss is", S_loss)

# def main():
#     find_S_loss()

# if __name__ == "__main__":
#     main()
