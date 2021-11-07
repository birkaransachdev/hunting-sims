# USES DSS TO SOLVE NONLINEAR POWER FLOW FOR A FEEDER OBJECT DEFINED IN THE 'SETUP' CODE


# In[35]:

from setup import *
import opendssdirect as dss
from dss import *
import os

from pprint import pprint

from scipy.sparse import csc_matrix

# In[36]:

# HELPER FUNCTIONS

# In[37]:

def DSS_loads(feeder,timestep, loud):
# Uses DSS commands to add loads to a circuit
    for key,iload in feeder.loaddict.items():
        Pvec = iload.Psched[:,timestep]
        Qvec = iload.Qsched[:,timestep]
        if loud:
            print('****************************************************************************')
            print(f'load {key}')
            print(f'Pinj: {-Pvec}') # The load values are given in load convention (extraction-positive), rather than injection-positive.
            print(f'Qinj: {-Qvec}')
            print(f'kVbase_phg: {iload.node.kVbase_phg}')
        for idx in range(0,3):
            # Constant P,Q = model 1
            if iload.phasevec[0,0] == 1:
                dss.run_command("New Load." + iload.name +"aCP Bus1=" + iload.node.name + ".1 Phases=1 Conn=Wye Model=1 kV="
                                + str(iload.node.kVbase_phg) + " kW=" + str(Pvec[0]*iload.constP) #vBase is set here using kV="..."
                                + " kvar=" + str(Qvec[0]*iload.constP) + " Vminpu=0.8 Vmaxpu=1.2")
            if iload.phasevec[1,0] == 1:
                dss.run_command("New Load." + iload.name +"bCP Bus1=" + iload.node.name + ".2 Phases=1 Conn=Wye Model=1 kV="
                                + str(iload.node.kVbase_phg) + " kW=" + str(Pvec[1]*iload.constP) #constP refers to constant power load
                                + " kvar=" + str(Qvec[1]*iload.constP) + " Vminpu=0.8 Vmaxpu=1.2")
            if iload.phasevec[2,0] == 1:
                dss.run_command("New Load." + iload.name +"cCP Bus1=" + iload.node.name + ".3 Phases=1 Conn=Wye Model=1 kV="
                                + str(iload.node.kVbase_phg) + " kW=" + str(Pvec[2]*iload.constP)
                                + " kvar=" + str(Qvec[2]*iload.constP) + " Vminpu=0.8 Vmaxpu=1.2")

            # Constant Z = model 2
            if iload.phasevec[0,0] == 1:
                dss.run_command("New Load." + iload.name +"aCZ Bus1=" + iload.node.name + ".1 Phases=1 Conn=Wye Model=2 kV="
                                + str(iload.node.kVbase_phg) + " kW=" + str(Pvec[0]*iload.constZ)
                                + " kvar=" + str(Qvec[0]*iload.constZ) + " Vminpu=0.8 Vmaxpu=1.2")
            if iload.phasevec[1,0] == 1:
                dss.run_command("New Load." + iload.name +"bCZ Bus1=" + iload.node.name + ".2 Phases=1 Conn=Wye Model=2 kV="
                                + str(iload.node.kVbase_phg) + " kW=" + str(Pvec[1]*iload.constZ)
                                + " kvar=" + str(Qvec[1]*iload.constZ) + " Vminpu=0.8 Vmaxpu=1.2")
            if iload.phasevec[2,0] == 1:
                dss.run_command("New Load." + iload.name +"cCZ Bus1=" + iload.node.name + ".3 Phases=1 Conn=Wye Model=2 kV="
                                + str(iload.node.kVbase_phg) + " kW=" + str(Pvec[2]*iload.constZ)
                                + " kvar=" + str(Qvec[2]*iload.constZ) + " Vminpu=0.8 Vmaxpu=1.2")

            # Constant I = model 5
            if iload.phasevec[0,0] == 1:
                dss.run_command("New Load." + iload.name +"aCI Bus1=" + iload.node.name + ".1 Phases=1 Conn=Wye Model=5 kV="
                                + str(iload.node.kVbase_phg) + " kW=" + str(Pvec[0]*iload.constI)
                                + " kvar=" + str(Qvec[0]*iload.constI) + " Vminpu=0.8 Vmaxpu=1.2")
            if iload.phasevec[1,0] == 1:
                dss.run_command("New Load." + iload.name +"bCI Bus1=" + iload.node.name + ".2 Phases=1 Conn=Wye Model=5 kV="
                                + str(iload.node.kVbase_phg) + " kW=" + str(Pvec[1]*iload.constI)
                                + " kvar=" + str(Qvec[1]*iload.constI) + " Vminpu=0.8 Vmaxpu=1.2")
            if iload.phasevec[2,0] == 1:
                dss.run_command("New Load." + iload.name +"cCI Bus1=" + iload.node.name + ".3 Phases=1 Conn=Wye Model=5 kV="
                                + str(iload.node.kVbase_phg) + " kW=" + str(Pvec[2]*iload.constI)
                                + " kvar=" + str(Qvec[2]*iload.constI) + " Vminpu=0.8 Vmaxpu=1.2")

    return

def DSS_lines_1ph(iline,timestep):
# Helper function for DSS_lines
    Zmat = iline.R + 1j*iline.X
    itemindex = np.where(Zmat>=1e-7)

    r11 = iline.R[itemindex][0]
    x11 = iline.X[itemindex][0]

    phasestr = "."
    if iline.phasevec[0,0] == 1:
        phasestr = phasestr + "1."
    if iline.phasevec[1,0] == 1:
        phasestr = phasestr + "2."
    if iline.phasevec[2,0] == 1:
        phasestr = phasestr + "3."
    if phasestr[len(phasestr) - 1] == ".":
        phasestr = phasestr[:-1]

    #" Length=1 " is implied when just rmatrix is given, evidently
    dss.run_command("New Line." + iline.name +" Bus1=" + iline.from_node.name + phasestr + " Bus2="
                    + iline.to_node.name + phasestr + " BaseFreq=60 Phases=1"
                    + " rmatrix = (" + str(r11) + ")"
                    + " xmatrix = (" + str(x11) + ")")
    return

def DSS_lines_2ph(iline,timestep):
# Helper function for DSS_lines
    Zmat = iline.R + 1j*iline.X

    if Zmat[0][1] > 1e-7:
        Rtemp = iline.R[0:2][:,0:2]
        Xtemp = iline.X[0:2][:,0:2]
    elif Zmat[1][2] > 1e-7:
        Rtemp = iline.R[1:3][:,1:3]
        Xtemp = iline.X[1:3][:,1:3]
    elif Zmat[0][2] > 1e-7:
        Rtemp = np.array([[iline.R[0][0],iline.R[0][2]],[iline.R[2][0],iline.R[2][2]]])
        Xtemp = np.array([[iline.X[0][0],iline.X[0][2]],[iline.X[2][0],iline.X[2][2]]])

    r11 = Rtemp[0,0]
    r12 = Rtemp[1,0]
    r22 = Rtemp[1,1]

    x11 = Xtemp[0,0]
    x12 = Xtemp[1,0]
    x22 = Xtemp[1,1]

    phasestr = "."
    if iline.phasevec[0,0] == 1:
        phasestr = phasestr + "1."
    if iline.phasevec[1,0] == 1:
        phasestr = phasestr + "2."
    if iline.phasevec[2,0] == 1:
        phasestr = phasestr + "3."
    if phasestr[len(phasestr) - 1] == ".":
        phasestr = phasestr[:-1]

    dss.run_command("New Line." + iline.name +" Bus1=" + iline.from_node.name + phasestr + " Bus2="
                    + iline.to_node.name + phasestr + " BaseFreq=60 Phases=2"
                    + " rmatrix = (" + str(r11) + " | " + str(r12) + " " + str(r22) + ")"
                    + " xmatrix = (" + str(x11) + " | " + str(x12) + " " + str(x22) + ")")
    return


def DSS_lines_3ph(iline,timestep):
# Helper function for DSS_lines
    r11 = iline.R[0,0]
    r12 = iline.R[1,0]
    r22 = iline.R[1,1]
    r13 = iline.R[2,0]
    r23 = iline.R[2,1]
    r33 = iline.R[2,2]

    x11 = iline.X[0,0]
    x12 = iline.X[1,0]
    x22 = iline.X[1,1]
    x13 = iline.X[2,0]
    x23 = iline.X[2,1]
    x33 = iline.X[2,2]

    dss.run_command("New Line." + iline.name +" Bus1=" + iline.from_node.name + ".1.2.3 Bus2="
                    + iline.to_node.name + ".1.2.3 BaseFreq=60 Phases=3"
                    + " rmatrix = (" + str(r11) + " | " + str(r12) + " " + str(r22) + " | " + str(r13) + " " + str(r23) + " " + str(r33) + ")"
                    + " xmatrix = (" + str(x11) + " | " + str(x12) + " " + str(x22) + " | " + str(x13) + " " + str(x23) + " " + str(x33) + ")")
    return

def DSS_lines(feeder,timestep):
# Uses DSS commands to add lines to a circuit
    for key,iline in feeder.linedict.items():
        Zmat = iline.R + iline.X #these are non pu resistances and impedances
        if np.sum(Zmat>1e-7) == 9 or np.sum(Zmat>1e-7) == 3:
            DSS_lines_3ph(iline,timestep)
        if np.sum(Zmat>1e-7) == 4 or np.sum(Zmat>1e-7) == 2:
            DSS_lines_2ph(iline,timestep)
        if np.sum(Zmat>1e-7) == 1:
            DSS_lines_1ph(iline,timestep)
    return

def DSS_caps(feeder,timestep, loud):
# Uses DSS commands to add cap banks to a circuit
# Only set up to handle capacitors, no real power (real power would be an easy insert, though)
# Also assumes capacitors are either on or off throughout the entirety of a model's run (no switching back and forth)
    for key,icap in feeder.shuntdict.items():
        kVentry = icap.node.kVbase_phg
        if loud:
            print('****************************************************************************')
            print(f'Cap {key}')
            print(f'Q: {-icap.Qvec[:,0]}') # the capacitor values are negative in the model files because the model files are load (extraction)-positive, rather than injection-positive.
            print(f'kVbase_phg: {kVentry}')

        if icap.phasevec[0,0] == 1:
            dss.run_command("New Capacitor." + icap.name + "a Bus1=" + icap.node.name + ".1 phases=1 kVAR="
                            + str(-icap.Qvec[0,0]) + " kV=" + str(kVentry))
        if icap.phasevec[1,0] == 1:
            dss.run_command("New Capacitor." + icap.name + "b Bus1=" + icap.node.name + ".2 phases=1 kVAR="
                            + str(-icap.Qvec[1,0]) + " kV=" + str(kVentry))
        if icap.phasevec[2,0] == 1:
            dss.run_command("New Capacitor." + icap.name + "c Bus1=" + icap.node.name + ".3 phases=1 kVAR="
                            + str(-icap.Qvec[2,0]) + " kV=" + str(kVentry))
    return

def DSS_switches(feeder,timestep):
# Uses DSS commands to add switches to a circuit
# There is no 'switch' object in DSS. Instead, all lines have built-in switches. So we just add a short line.
    for key,iswitch in feeder.switchdict.items():

        if iswitch.phasevec[0,0] == 1:
            dss.run_command("New Line." + iswitch.name + "a Bus1=" + iswitch.from_node.name + ".1 Bus2="
                            + iswitch.to_node.name
                            + ".1 Phases=1 Switch=y r1=1e-4 r0=1e-4 x1=0.000 x0=0.000 c1=0.000 c0=0.000")
                            #this is based off the DSS switch approximation: r1=r0=1e-4
        if iswitch.phasevec[1,0] == 1:
            dss.run_command("New Line." + iswitch.name + "b Bus1=" + iswitch.from_node.name + ".2 Bus2="
                            + iswitch.to_node.name
                            + ".2 Phases=1 Switch=y r1=1e-4 r0=1e-4 x1=0.000 x0=0.000 c1=0.000 c0=0.000")
        if iswitch.phasevec[2,0] == 1:
            dss.run_command("New Line." + iswitch.name + "c Bus1=" + iswitch.from_node.name + ".3 Bus2="
                            + iswitch.to_node.name
                            + ".3 Phases=1 Switch=y r1=1e-4 r0=1e-4 x1=0.000 x0=0.000 c1=0.000 c0=0.000")
    return

def DSS_trans(feeder,timestep):
# Uses DSS commands to add transformers to a circuit
# Note that the kV "base" being used here is ph-ph. This runs counter to how the official opendss manual...
# ... claims bases are defined for 1-ph transformers. I've tested it, and it appears the manual is mistaken.
    for key,itrans in feeder.transdict.items():

        if itrans.phasevec[0,0] == 1:
            dss.run_command("New Transformer." + itrans.name + "a Phases=1 Windings=2 buses=["
                            + itrans.w0_node.name + ".1.0, " + itrans.w1_node.name + ".1.0] conns =[wye, wye]"
                            + " kVs=[" + str(itrans.w0_kVbase_phg*np.sqrt(3)) + ", " + str(itrans.w1_kVbase_phg*np.sqrt(3)) + "]"
                            + " kVAs=[" + str(itrans.w0_kVAbase) + ", " + str(itrans.w1_kVAbase) + "]"
                            + " %Rs=[" + str(itrans.w0_rpu*100) + ", " + str(itrans.w1_rpu*100) + "]"
                            + " XHL=" + str(itrans.xpu*100))

        if itrans.phasevec[1,0] == 1:
            dss.run_command("New Transformer." + itrans.name + "b Phases=1 Windings=2 buses=["
                            + itrans.w0_node.name + ".2.0, " + itrans.w1_node.name + ".2.0] conns =[wye, wye]"
                            + " kVs=[" + str(itrans.w0_kVbase_phg*np.sqrt(3)) + ", " + str(itrans.w1_kVbase_phg*np.sqrt(3)) + "]"
                            + " kVAs=[" + str(itrans.w0_kVAbase) + ", " + str(itrans.w1_kVAbase) + "]"
                            + " %Rs=[" + str(itrans.w0_rpu*100) + ", " + str(itrans.w1_rpu*100) + "]"
                            + " XHL=" + str(itrans.xpu*100))

        if itrans.phasevec[2,0] == 1:
            dss.run_command("New Transformer." + itrans.name + "c Phases=1 Windings=2 buses=["
                            + itrans.w0_node.name + ".3.0, " + itrans.w1_node.name + ".3.0] conns =[wye, wye]"
                            + " kVs=[" + str(itrans.w0_kVbase_phg*np.sqrt(3)) + ", " + str(itrans.w1_kVbase_phg*np.sqrt(3)) + "]"
                            + " kVAs=[" + str(itrans.w0_kVAbase) + ", " + str(itrans.w1_kVAbase) + "]"
                            + " %Rs=[" + str(itrans.w0_rpu*100) + ", " + str(itrans.w1_rpu*100) + "]"
                            + " XHL=" + str(itrans.xpu*100))
    return

#sets power flows for actuators for a given timestep
#I uncommented lines so this expects non-pu power commands, like DSS_loads
def DSS_actuators(feeder,timestep, loud):
# Uses DSS commands to add the previously solved-for values of actuator dispatch to the model as negative loads (can be on the same bus as a pre-existing load).
    for key,iact in feeder.actdict.items():
        Pvec = -iact.Pgen[:,timestep]
        Qvec = -iact.Qgen[:,timestep]
        # Pvec = -iact.Psched[:,timestep]
        # # Qvec = -iact.Qsched[:,timestep]
        # Qvec = np.zeros(3) #because load file does not have Q injections (limits) for actuators, only P and S limits
        if loud:
            print('****************************************************************************')
            print(f'actuator {key}')
            print(f'Pinj: {-Pvec}') # The P values are negated 3 lines above because the P injections are put into DSS as negative loads
            print(f'kVbase_phg: {iact.node.kVbase_phg}')
        for idx in range(0,3):
            if iact.phasevec[0,0] == 1:
                dss.run_command("New Load." + iact.name +"a Bus1=" + iact.node.name + ".1 Phases=1 Conn=Wye Model=1 kV="
                                + str(iact.node.kVbase_phg) + " kW=" + str(Pvec[0]) #vBase is set here using kV="..."
                                + " kvar=" + str(Qvec[0]) + " Vminpu=0.8 Vmaxpu=1.2")
                                # + str(iact.node.kVbase_phg) + " kW=" + str(Pvec[0]*iact.node.kVAbase) #vBase is set here using kV="..."
                                # + " kvar=" + str(Qvec[0]*iact.node.kVAbase) + " Vminpu=0.8 Vmaxpu=1.2")
            if iact.phasevec[1,0] == 1:
                dss.run_command("New Load." + iact.name +"b Bus1=" + iact.node.name + ".2 Phases=1 Conn=Wye Model=1 kV="
                                + str(iact.node.kVbase_phg) + " kW=" + str(Pvec[1])
                                + " kvar=" + str(Qvec[1]) + " Vminpu=0.8 Vmaxpu=1.2")
                                # + str(iact.node.kVbase_phg) + " kW=" + str(Pvec[1]*iact.node.kVAbase)
                                # + " kvar=" + str(Qvec[1]*iact.node.kVAbase) + " Vminpu=0.8 Vmaxpu=1.2")
            if iact.phasevec[2,0] == 1:
                dss.run_command("New Load." + iact.name +"c Bus1=" + iact.node.name + ".3 Phases=1 Conn=Wye Model=1 kV="
                                + str(iact.node.kVbase_phg) + " kW=" + str(Pvec[2])
                                + " kvar=" + str(Qvec[2]) + " Vminpu=0.8 Vmaxpu=1.2")
                                # + str(iact.node.kVbase_phg) + " kW=" + str(Pvec[2]*iact.node.kVAbase)
                                # + " kvar=" + str(Qvec[2]*iact.node.kVAbase) + " Vminpu=0.8 Vmaxpu=1.2")
    return


# In[38]:

# Functions for calculating the Y matrix for a given feeder
def DSS_getY():
    dss.Solution.BuildYMatrix(2, 1)
    dss.Circuit.SystemY()
    (Ysparse, indices, indptr) = dss.YMatrix.getYsparse(factor=False)
    Y = csc_matrix((Ysparse, indices, indptr)).toarray()

    nnodes = int(len(Y)/3)
    Ynoshunt = Y.copy()
    for i in np.arange(nnodes):
        Ynoshunt[i*3:(i+1)*3,i*3:(i+1)*3] = np.zeros((3,3))
        RowSum = np.zeros((3,3))
        for k in np.arange(nnodes):
            RowSum = RowSum + Ynoshunt[(i)*3:(i+1)*3,k*3:(k+1)*3]
        Ynoshunt[i*3:(i+1)*3,i*3:(i+1)*3] = -RowSum
    Ynoshunt_csc = csc_matrix(Ynoshunt) # returns a sparse matrix type scipy.sparse.csc.csc_matrix in the (row,col) format
    return(Ynoshunt, Ynoshunt_csc)


def DSS_getY_fromFeeder(feeder, timestep=1):
    dss.run_command('clear')
    idxcount = 0
    for key,inode in feeder.busdict.items():
        if inode.type == 'SLACK' or inode.type == 'Slack' or inode.type == 'slack':
            subbusname = inode.name
            # slackbusIdx = idxcount # I dont know if this is actually useful for anything because buildYbus might adjust Y ordering
        idxcount = idxcount + 1

    subkVbase_phg = feeder.subkVbase_phg
    #subkVAbase = feeder.subkVAbase
    #loadpath = feeder.loadpath

    # Sets up the new circuit, assumes 3ph
    dss.run_command("new circuit.currentckt basekv=" + str(subkVbase_phg*np.sqrt(3)) + " pu=1.0000 phases=3 bus1="
                    + subbusname + " Angle=0 MVAsc3=200000 MVASC1=200000")
    DSS_lines(feeder,timestep)
    DSS_caps(feeder,timestep)
    DSS_switches(feeder,timestep)
    DSS_trans(feeder,timestep)

    Vbases = str(subkVbase_phg) + "," + str(subkVbase_phg*np.sqrt(3))

    for key,inode in feeder.busdict.items():
        if inode.kVbase_phg != subkVbase_phg:
            Vbases = Vbases + "," + str(inode.kVbase_phg) + "," + str(inode.kVbase_phg*np.sqrt(3))

    dss.Solution.BuildYMatrix(2, 1)
    dss.Circuit.SystemY()
    (Ysparse, indices, indptr) = dss.YMatrix.getYsparse(factor=False)
    Y = csc_matrix((Ysparse, indices, indptr)).toarray()
    #should get Y bus indexing from dss here

    #enforces no shunt admittances here
    nnodes = len(feeder.busdict)
    Ynoshunt = Y.copy()
    for i in np.arange(nnodes):
        Ynoshunt[(i)*3:(i+1)*3,(i)*3:(i+1)*3] = np.zeros((3,3))
        RowSum = np.zeros((3,3))
        for k in np.arange(nnodes):
            RowSum = RowSum + Ynoshunt[(i)*3:(i+1)*3,k*3:(k+1)*3]
        Ynoshunt[(i)*3:(i+1)*3,(i)*3:(i+1)*3] = -RowSum

    Ynoshunt_csc = csc_matrix(Ynoshunt) # returns a sparse matrix type scipy.sparse.csc.csc_matrix in the (row,col) format
    return(Ynoshunt, Ynoshunt_csc, subbusname) #should return Y bus indexing and slack bus index



# In[39]:

## FUNCTIONS FOR SOLVING POWER FLOW
## Note that these store their solutions in the feeder object by updating Vmag_NL and Vang_NL at each bus
#formerly DSSsnapshot
def DSS_run3phasePF(feeder,timestep, loud):
# Solves the nonlinear power flow for a single timestep
    dss.run_command('clear')
    for key,inode in feeder.busdict.items():
        if inode.type == 'SLACK' or inode.type == 'Slack' or inode.type == 'slack':
            subbusname = inode.name

    subkVbase_phg = feeder.subkVbase_phg
    #subkVAbase = feeder.subkVAbase
    #loadpath = feeder.loadpath

    # Sets up a brand new DSS circuit, assumes 3ph
    dss.run_command("new circuit.currentckt basekv=" + str(subkVbase_phg*np.sqrt(3)) + " pu=1.0000 phases=3 bus1="
                    + subbusname + " Angle=0 MVAsc3=200000 MVASC1=200000")
    #puts non-pu impedances into loads
    DSS_loads(feeder,timestep, loud)
    DSS_lines(feeder,timestep)
    DSS_caps(feeder,timestep, loud)
    DSS_switches(feeder,timestep)
    DSS_trans(feeder,timestep)
    DSS_actuators(feeder,timestep, loud) #sets actuator power flows at timestep to -iact.Pgen[:,timestep] and -iact.Qgen[:,timestep]

    Vbases = str(subkVbase_phg) + "," + str(subkVbase_phg*np.sqrt(3))

    for key,inode in feeder.busdict.items():
        if inode.kVbase_phg != subkVbase_phg:
            Vbases = Vbases + "," + str(inode.kVbase_phg) + "," + str(inode.kVbase_phg*np.sqrt(3))
            raise Exception("Base voltage of node is equal to feeder voltage")


    dss.run_command("Set Voltagebases=[" + Vbases + "]") #Kyle said this is necessary, but vbases are actually set manually in DSS_actuators and DSS_loads
    dss.run_command("set tolerance=0.0000000001")
    dss.run_command("calcv")
    dss.run_command("Solve")

#TODO (havent built this yet, not sure if DSS does single phase networks?)
def DSS_run1phasePF(feeder,timestep):
# Solves the nonlinear power flow for a single timestep
    dss.run_command('clear')
    for key,inode in feeder.busdict.items():
        if inode.type == 'SLACK' or inode.type == 'Slack' or inode.type == 'slack':
            subbusname = inode.name

    subkVbase_phg = feeder.subkVbase_phg
    subkVAbase = feeder.subkVAbase
    loadpath = feeder.loadpath

    # Sets up the new circuit, assumes 3ph
    dss.run_command("new circuit.currentckt basekv=" + str(subkVbase_phg*np.sqrt(3)) + " pu=1.0000 phases=3 bus1="
                    + subbusname + " Angle=0 MVAsc3=200000 MVASC1=200000")
    DSS_loads(feeder,timestep)
    DSS_lines(feeder,timestep)
    DSS_caps(feeder,timestep)
    DSS_switches(feeder,timestep)
    DSS_trans(feeder,timestep)
    DSS_actuators(feeder,timestep)

    Vbases = str(subkVbase_phg) + "," + str(subkVbase_phg*np.sqrt(3))

    for key,inode in feeder.busdict.items():
        if inode.kVbase_phg != subkVbase_phg:
            Vbases = Vbases + "," + str(inode.kVbase_phg) + "," + str(inode.kVbase_phg*np.sqrt(3))

    dss.run_command("Set Voltagebases=[" + Vbases + "]")
    dss.run_command("set tolerance=0.0000000001")
    dss.run_command("calcv")
    dss.run_command("Solve")


def getPFresults(feeder):
    for key,iline in feeder.linedict.items():
        # Reset NL line currents
        Imag_NL = np.zeros((3,1))
        Iang_NL = np.zeros((3,1))

        # Pull bus voltages out of the DSS solution
        name = iline.name
        dummyvar = dss.Circuit.SetActiveElement('Line.' + iline.name)
        lineIs = dss.CktElement.CurrentsMagAng()

        counter = 0
        assert(iline.from_phases == iline.to_phases)
        for ph in iline.from_phases:
            if ph == 'a':
                Imag_NL[0] = lineIs[counter]
                Iang_NL[0] = lineIs[counter + 1]
                counter = counter + 2
            if ph == 'b':
                Imag_NL[1] = lineIs[counter]
                Iang_NL[1] = lineIs[counter + 1]
                counter = counter + 2
            if ph == 'c':
                Imag_NL[2] = lineIs[counter]
                Iang_NL[2] = lineIs[counter + 1]
                counter = counter

    for key,iline in feeder.transdict.items():
        # Reset NL line currents
        Imag_NL = np.zeros((3,1))
        Iang_NL = np.zeros((3,1))

        # Pull bus voltages out of the DSS solution
        name = iline.name

        for ph in iline.w0_phases:
            if ph == 'a':
                dummyvar = dss.Circuit.SetActiveElement('Transformer.' + iline.name + 'A')
                lineIs = dss.CktElement.CurrentsMagAng()
                Imag_NL[0,ts] = lineIs[0]
                Iang_NL[0,ts] = lineIs[1]

            if ph == 'b':
                dummyvar = dss.Circuit.SetActiveElement('Transformer.' + iline.name + 'B')
                lineIs = dss.CktElement.CurrentsMagAng()
                Imag_NL[1] = lineIs[0]
                Iang_NL[1] = lineIs[1]

            if ph == 'c':
                dummyvar = dss.Circuit.SetActiveElement('Transformer.' + iline.name + 'C')
                lineIs = dss.CktElement.CurrentsMagAng()
                Imag_NL[2] = lineIs[0]
                Iang_NL[2] = lineIs[1]

    for key,iline in feeder.switchdict.items():
        # Reset NL line currents
        Imag_NL = np.zeros((3,1))
        Iang_NL = np.zeros((3,1))

        # Pull bus voltages out of the DSS solution
        name = iline.name

        for ph in iline.from_phases:
            if ph == 'a':
                dummyvar = dss.Circuit.SetActiveElement('Line.' + iline.name + 'A')
                lineIs = dss.CktElement.CurrentsMagAng()
                Imag_NL[0] = lineIs[0]
                Iang_NL[0] = lineIs[1]

            if ph == 'b':
                dummyvar = dss.Circuit.SetActiveElement('Line.' + iline.name + 'B')
                lineIs = dss.CktElement.CurrentsMagAng()
                Imag_NL[1] = lineIs[0]
                Iang_NL[1] = lineIs[1]

            if ph == 'c':
                dummyvar = dss.Circuit.SetActiveElement('Line.' + iline.name + 'C')
                lineIs = dss.CktElement.CurrentsMagAng()
                Imag_NL[2] = lineIs[0]
                Iang_NL[2] = lineIs[1]

    for key,bus in feeder.busdict.items():
        # Reset NL bus voltages
        Vmag_NL = np.zeros((3,1))
        Vang_NL = np.zeros((3,1))
        Vcomp = np.zeros((3,1))
        Icomp = np.zeros((3,1))
        Imag_NL = np.zeros((3,1))
        Iang_NL = np.zeros((3,1))

        # Pull bus voltages out of the DSS solution
        name = bus.name
        dummyvar = dss.Circuit.SetActiveBus(bus.name)
        busVs = dss.Bus.VMagAngle() #this is the output of DSS power flow

        #this is where busVs get put into feeder structure
        counter = 0
        for ph in bus.phases:
            if ph == 'a':
                Vmag_NL[0] = busVs[counter]
                Vang_NL[0] = busVs[counter + 1]
                counter = counter + 2
            if ph == 'b':
                Vmag_NL[1] = busVs[counter]
                Vang_NL[1] = busVs[counter + 1]
                counter = counter + 2
            if ph == 'c':
                Vmag_NL[2] = busVs[counter]
                Vang_NL[2] = busVs[counter + 1]
                counter = counter
        Vang = Vang_NL*np.pi/180 #evidently these are in degrees
        Vang[1] += 2*np.pi/3
        Vang[2] += -2*np.pi/3
        bus.Vcomp = bus.Vmag_NL*np.cos(Vang) + bus.Vmag_NL*np.sin(Vang)*1j

        #get current injection measurements (positive into network) from branch measurements
        currentInjComp = 0
        # print('bus' + key)
        for edge in bus.edges_out:
            edgeImag = edge.Imag_NL
            edgeIang = edge.Iang_NL*np.pi/180
            edgeIang[1] += 2*np.pi/3
            edgeIang[2] += -2*np.pi/3
            edgeIcomp = edgeImag*np.cos(edgeIang) + edgeImag*np.sin(edgeIang)*1j
            currentInjComp += edgeIcomp
        for edge in bus.edges_in:
            edgeImag = edge.Imag_NL
            edgeIang = edge.Iang_NL*np.pi/180
            edgeIang[1] += 2*np.pi/3
            edgeIang[2] += -2*np.pi/3
            edgeIcomp = edgeImag*np.cos(edgeIang) + edgeImag*np.sin(edgeIang)*1j
            currentInjComp += -edgeIcomp
        Icomp = currentInjComp
        Imag = np.abs(currentInjComp)
        Iang = np.arctan2(np.imag(currentInjComp),np.real(currentInjComp))

    return(Vcomp,Vmag_NL,Vang_NL,Icomp,Imag_NL,Iang_NL)


# This function is pretty much the same as the getPFresults above. savePFresults saves results to the feeder objects, and does not return anything.
def savePFresults(feeder,ts,alarm):
# 'Alarm' is a boolean that can be turned on or off. It prints a warning if any voltages are outside of bounds.
    for key,iline in feeder.linedict.items():
        # Reset NL line currents
        iline.Imag_NL[:,ts:ts+1] = np.zeros((3,1))
        iline.Iang_NL[:,ts:ts+1] = np.zeros((3,1))
        # Pull bus voltages out of the DSS solution
        name = iline.name
        dummyvar = dss.Circuit.SetActiveElement('Line.' + iline.name)
        lineIs = dss.CktElement.CurrentsMagAng()
        counter = 0
        assert(iline.from_phases == iline.to_phases)
        for ph in iline.from_phases:
            if ph == 'a':
                iline.Imag_NL[0,ts] = lineIs[counter]
                iline.Iang_NL[0,ts] = lineIs[counter + 1]
                counter = counter + 2
            if ph == 'b':
                iline.Imag_NL[1,ts] = lineIs[counter]
                iline.Iang_NL[1,ts] = lineIs[counter + 1]
                counter = counter + 2
            if ph == 'c':
                iline.Imag_NL[2,ts] = lineIs[counter]
                iline.Iang_NL[2,ts] = lineIs[counter + 1]
                counter = counter

    for key,iline in feeder.transdict.items():
        # Reset NL line currents
        iline.Imag_NL[:,ts:ts+1] = np.zeros((3,1))
        iline.Iang_NL[:,ts:ts+1] = np.zeros((3,1))
        # Pull bus voltages out of the DSS solution
        name = iline.name
        for ph in iline.w0_phases:
            if ph == 'a':
                dummyvar = dss.Circuit.SetActiveElement('Transformer.' + iline.name + 'A')
                lineIs = dss.CktElement.CurrentsMagAng()
                iline.Imag_NL[0,ts] = lineIs[0]
                iline.Iang_NL[0,ts] = lineIs[1]
            if ph == 'b':
                dummyvar = dss.Circuit.SetActiveElement('Transformer.' + iline.name + 'B')
                lineIs = dss.CktElement.CurrentsMagAng()
                iline.Imag_NL[1,ts] = lineIs[0]
                iline.Iang_NL[1,ts] = lineIs[1]
            if ph == 'c':
                dummyvar = dss.Circuit.SetActiveElement('Transformer.' + iline.name + 'C')
                lineIs = dss.CktElement.CurrentsMagAng()
                iline.Imag_NL[2,ts] = lineIs[0]
                iline.Iang_NL[2,ts] = lineIs[1]

    for key,iline in feeder.switchdict.items():
        # Reset NL line currents
        iline.Imag_NL[:,ts:ts+1] = np.zeros((3,1))
        iline.Iang_NL[:,ts:ts+1] = np.zeros((3,1))
        # Pull bus voltages out of the DSS solution
        name = iline.name
        for ph in iline.from_phases:
            if ph == 'a':
                dummyvar = dss.Circuit.SetActiveElement('Line.' + iline.name + 'A')
                lineIs = dss.CktElement.CurrentsMagAng()
                iline.Imag_NL[0,ts] = lineIs[0]
                iline.Iang_NL[0,ts] = lineIs[1]
            if ph == 'b':
                dummyvar = dss.Circuit.SetActiveElement('Line.' + iline.name + 'B')
                lineIs = dss.CktElement.CurrentsMagAng()
                iline.Imag_NL[1,ts] = lineIs[0]
                iline.Iang_NL[1,ts] = lineIs[1]
            if ph == 'c':
                dummyvar = dss.Circuit.SetActiveElement('Line.' + iline.name + 'C')
                lineIs = dss.CktElement.CurrentsMagAng()
                iline.Imag_NL[2,ts] = lineIs[0]
                iline.Iang_NL[2,ts] = lineIs[1]

    #KEITH This sets up the power check below
    busPinjCommandDict = dict()
    busQinjCommandDict = dict()
    for key,iload in feeder.loaddict.items():
        # print('1111111 load key ', key)
        busPinjCommandDict[key] = -iload.Psched[:,ts]
        busQinjCommandDict[key] = -iload.Qsched[:,ts]
    for key,iact in feeder.actdict.items():
        # print('1111111 act key ', key)
        if key in busPinjCommandDict.keys():
            busPinjCommandDict[key] += iact.Pgen[:,ts]
            busQinjCommandDict[key] += iact.Qgen[:,ts]
        else:
            busPinjCommandDict[key] = iact.Pgen[:,ts]
            busQinjCommandDict[key] = iact.Qgen[:,ts]
    for key,icap in feeder.shuntdict.items():
        if key in busPinjCommandDict.keys():
            busQinjCommandDict[key] += icap.Qvec[:,0]
        else:
            busQinjCommandDict[key] = icap.Qvec[:,0]

    for key,bus in feeder.busdict.items():
        # Reset NL bus voltages
        bus.Vmag_NL[:,ts:ts+1] = np.zeros((3,1))
        bus.Vang_NL[:,ts:ts+1] = np.zeros((3,1))
        bus.Vcomp[:,ts:ts+1] = np.zeros((3,1))
        bus.Icomp[:,ts:ts+1] = np.zeros((3,1))
        bus.Imag_NL[:,ts:ts+1] = np.zeros((3,1))
        bus.Iang_NL[:,ts:ts+1] = np.zeros((3,1))

        # Pull bus voltages out of the DSS solution
        name = bus.name
        dummyvar = dss.Circuit.SetActiveBus(bus.name)
        busVs = dss.Bus.VMagAngle() #this is the output of DSS power flow
        #for i in dir(dss.Bus): print(i)
        #busIs =

        #this is where busVs get put into feeder structure
        counter = 0
        for ph in bus.phases:
            if ph == 'a':
                bus.Vmag_NL[0,ts] = busVs[counter]
                bus.Vang_NL[0,ts] = busVs[counter + 1]
                counter = counter + 2
            if ph == 'b':
                bus.Vmag_NL[1,ts] = busVs[counter]
                bus.Vang_NL[1,ts] = busVs[counter + 1]
                counter = counter + 2
            if ph == 'c':
                bus.Vmag_NL[2,ts] = busVs[counter]
                bus.Vang_NL[2,ts] = busVs[counter + 1]
                counter = counter
        # print('BUS ANG RETURNED BY DSS', bus.Vang_NL[:,ts:ts+1])

        Vang = bus.Vang_NL[:,ts]*np.pi/180 #evidently these are in degrees(?)
        # Vang[1] += 2*np.pi/3
        # Vang[2] += -2*np.pi/3 #5/8/20 commented these out bc 3ph ohms law needs 120 deg shifts
        bus.Vcomp[:,ts] = bus.Vmag_NL[:,ts]*np.cos(Vang) + bus.Vmag_NL[:,ts]*np.sin(Vang)*1j

        if alarm == 1:
            if (bus.Vmag_NL[0,ts]/(1000*bus.kVbase_phg)>1.1 or (bus.Vmag_NL[0,ts]/(1000*bus.kVbase_phg)<0.9 and bus.phasevec[0,0]==1)):
                print('Voltage violation: Phase 1, timestep ' + str(ts) + ' ' + bus.name)
            if (bus.Vmag_NL[1,ts]/(1000*bus.kVbase_phg)>1.1 or (bus.Vmag_NL[1,ts]/(1000*bus.kVbase_phg)<0.9 and bus.phasevec[1,0]==1)):
                print('Voltage violation: Phase 2, timestep ' + str(ts) + ' ' + bus.name)
            if (bus.Vmag_NL[2,ts]/(1000*bus.kVbase_phg)>1.1 or (bus.Vmag_NL[2,ts]/(1000*bus.kVbase_phg)<0.9 and bus.phasevec[2,0]==1)):
                print('Voltage violation: Phase 3, timestep ' + str(ts) + ' ' + bus.name)

        #get current injection measurements (positive into network) from branch measurements
        currentInjComp = 0
        # print('bus' + key)
        for edge in bus.edges_out:
            edgeImag = edge.Imag_NL[:,ts]
            edgeIang = edge.Iang_NL[:,ts]*np.pi/180
            # edgeIang[1] += 2*np.pi/3
            # edgeIang[2] += -2*np.pi/3 #5/8/20 commented these out bc 3ph ohms law needs 120 deg shifts
            edgeIcomp = edgeImag*np.cos(edgeIang) + edgeImag*np.sin(edgeIang)*1j
            currentInjComp += edgeIcomp
        for edge in bus.edges_in:
            edgeImag = edge.Imag_NL[:,ts]
            edgeIang = edge.Iang_NL[:,ts]*np.pi/180
            # edgeIang[1] += 2*np.pi/3
            # edgeIang[2] += -2*np.pi/3 #5/8/20 commented these out bc 3ph ohms law needs 120 deg shifts
            edgeIcomp = edgeImag*np.cos(edgeIang) + edgeImag*np.sin(edgeIang)*1j
            currentInjComp += -edgeIcomp
        bus.Icomp[:,ts] = currentInjComp
        bus.Imag_NL[:,ts] = np.abs(currentInjComp)
        bus.Iang_NL[:,ts] = np.arctan2(np.imag(currentInjComp),np.real(currentInjComp))
        # print('busiIcomp' + str(currentInjComp)) #appears to be working
        # print('busiImag_NL' + str(bus.Imag_NL[:,ts]))
        # print('busiIang_NL' + str(bus.Iang_NL[:,ts]))

        if alarm == 1:
            if key in busPinjCommandDict.keys():
                S_tolratio = .05 #should set this up by alarm
                sinjComp = np.multiply(bus.Vcomp[:,ts]/1000, np.conj(bus.Icomp[:,ts])) #gives non PU power in kW
                # print('1111111 sinjComp', sinjComp)
                # print('1111111 sinjComp[0]', sinjComp[0])
                # print('1111111 key ', key)
                # print('1111111 busPinjCommandDict[key]', busPinjCommandDict[key])
                # tol = abs(sinjComp[0])*S_tolratio
                lowTol = 1-S_tolratio
                hiTol = 1+S_tolratio

                if  abs(np.real(sinjComp[0]))>hiTol*abs(busPinjCommandDict[key][0]) or abs(np.real(sinjComp[0]))<lowTol*abs(busPinjCommandDict[key][0]):# and bus.phasevec[0,0]==1)):
                    print('Power mismatch (DSS is messing with S either bc V it out of bounds, or there is a voltage instabiltity): Phase 1, timestep ' + str(ts) + ' ' + bus.name + ' Pcmd:' + str(busPinjCommandDict[key][0]) + ' Pactuated:' + str(np.real(sinjComp[0])))
                if  abs(np.real(sinjComp[1]))>hiTol*abs(busPinjCommandDict[key][1]) or abs(np.real(sinjComp[1]))<lowTol*abs(busPinjCommandDict[key][1]):# and bus.phasevec[1,0]==1)):
                    print('Power mismatch (DSS is messing with S either bc V it out of bounds, or there is a voltage instabiltity): Phase 2, timestep ' + str(ts) + ' ' + bus.name + ' Pcmd:' + str(busPinjCommandDict[key][1]) + ' Pactuated:' + str(np.real(sinjComp[1])))
                if  abs(np.real(sinjComp[2]))>hiTol*abs(busPinjCommandDict[key][2]) or abs(np.real(sinjComp[2]))<lowTol*abs(busPinjCommandDict[key][2]):# and bus.phasevec[2,0]==1)):
                    print('Power mismatch (DSS is messing with S either bc V it out of bounds, or there is a voltage instabiltity): Phase 3, timestep ' + str(ts) + ' ' + bus.name + ' Pcmd:' + str(busPinjCommandDict[key][2]) + ' Pactuated:' + str(np.real(sinjComp[2])))

                if  abs(np.imag(sinjComp[0]))>hiTol*abs(busQinjCommandDict[key][0]) or abs(np.imag(sinjComp[0]))<lowTol*abs(busQinjCommandDict[key][0]):# and bus.phasevec[0,0]==1)):
                    print('Power mismatch (DSS is messing with S either bc V it out of bounds, or there is a voltage instabiltity): Phase 1, timestep ' + str(ts) + ' ' + bus.name + ' Qcmd:' + str(busQinjCommandDict[key][0]) + ' Qactuated:' + str(np.imag(sinjComp[0])))
                if  abs(np.imag(sinjComp[1]))>hiTol*abs(busQinjCommandDict[key][1]) or abs(np.imag(sinjComp[1]))<lowTol*abs(busQinjCommandDict[key][1]):# and bus.phasevec[1,0]==1)):
                    print('Power mismatch (DSS is messing with S either bc V it out of bounds, or there is a voltage instabiltity): Phase 2, timestep ' + str(ts) + ' ' + bus.name + ' Qcmd:' + str(busQinjCommandDict[key][1]) + ' Qactuated:' + str(np.imag(sinjComp[1])))
                if  abs(np.imag(sinjComp[2]))>hiTol*abs(busQinjCommandDict[key][2]) or abs(np.imag(sinjComp[2]))<lowTol*abs(busQinjCommandDict[key][2]):# and bus.phasevec[2,0]==1)):
                    print('Power mismatch (DSS is messing with S either bc V it out of bounds, or there is a voltage instabiltity): Phase 3, timestep ' + str(ts) + ' ' + bus.name + ' Qcmd:' + str(busQinjCommandDict[key][2]) + ' Qactuated:' + str(np.imag(sinjComp[2])))

    return


# In[41]:


## FOR REPORTING POWER FLOW SOLUTIONS


# In[42]:


def export_Measurements(feeder):
# Turns the Vmag_NL and Vang_NL values within a feeder's bus dictionary into a csv file for the L-PBC team
# Also creates a csv with line currents, in case they find it useful for testing at LBL
    current_directory = os.getcwd()
    load_directory = feeder.loadfolder
    final_directory = os.path.join(load_directory, 'Results')
    if not os.path.exists(final_directory):
        os.makedirs(final_directory)
    os.chdir(final_directory)

    Vtargdf = pd.DataFrame()
    Idatdf = pd.DataFrame()
    KVbasedf = pd.DataFrame()

    for key,ibus in feeder.busdict.items(): #for each bus
        phAname = ibus.name + '_a'
        phBname = ibus.name + '_b'
        phCname = ibus.name + '_c'
        #save the voltages for all time steps
        phAmag = ibus.Vmag_NL[0,:]/(ibus.kVbase_phg*1000)
        phBmag = ibus.Vmag_NL[1,:]/(ibus.kVbase_phg*1000)
        phCmag = ibus.Vmag_NL[2,:]/(ibus.kVbase_phg*1000)

        phAang = ibus.Vang_NL[0,:]
        phBang = ibus.Vang_NL[1,:]
        phCang = ibus.Vang_NL[2,:]

        Vtargdf[phAname + '_mag'] = phAmag
        Vtargdf[phAname + '_ang'] = phAang
        Vtargdf[phBname + '_mag'] = phBmag
        Vtargdf[phBname + '_ang'] = phBang
        Vtargdf[phCname + '_mag'] = phCmag
        Vtargdf[phCname + '_ang'] = phCang

    for key,iline in feeder.linedict.items():
        phAname = iline.name + '_a'
        phBname = iline.name + '_b'
        phCname = iline.name + '_c'

        phAmag = iline.Imag_NL[0,:]
        phBmag = iline.Imag_NL[1,:]
        phCmag = iline.Imag_NL[2,:]

        phAang = iline.Iang_NL[0,:]
        phBang = iline.Iang_NL[1,:]
        phCang = iline.Iang_NL[2,:]

        Idatdf[phAname + '_mag'] = phAmag
        Idatdf[phAname + '_ang'] = phAang
        Idatdf[phBname + '_mag'] = phBmag
        Idatdf[phBname + '_ang'] = phBang
        Idatdf[phCname + '_mag'] = phCmag
        Idatdf[phCname + '_ang'] = phCang

    for key,iline in feeder.transdict.items():
        phAname = iline.name + '_a'
        phBname = iline.name + '_b'
        phCname = iline.name + '_c'

        phAmag = iline.Imag_NL[0,:]
        phBmag = iline.Imag_NL[1,:]
        phCmag = iline.Imag_NL[2,:]

        phAang = iline.Iang_NL[0,:]
        phBang = iline.Iang_NL[1,:]
        phCang = iline.Iang_NL[2,:]

        Idatdf[phAname + '_mag'] = phAmag
        Idatdf[phAname + '_ang'] = phAang
        Idatdf[phBname + '_mag'] = phBmag
        Idatdf[phBname + '_ang'] = phBang
        Idatdf[phCname + '_mag'] = phCmag
        Idatdf[phCname + '_ang'] = phCang

    for key,iline in feeder.switchdict.items():
        phAname = iline.name + '_a'
        phBname = iline.name + '_b'
        phCname = iline.name + '_c'

        phAmag = iline.Imag_NL[0,:]
        phBmag = iline.Imag_NL[1,:]
        phCmag = iline.Imag_NL[2,:]

        phAang = iline.Iang_NL[0,:]
        phBang = iline.Iang_NL[1,:]
        phCang = iline.Iang_NL[2,:]

        Idatdf[phAname + '_mag'] = phAmag
        Idatdf[phAname + '_ang'] = phAang
        Idatdf[phBname + '_mag'] = phBmag
        Idatdf[phBname + '_ang'] = phBang
        Idatdf[phCname + '_mag'] = phCmag
        Idatdf[phCname + '_ang'] = phCang

    #[jasper] create output of KVbase values
    for key,ibus in feeder.busdict.items():
        phAname = ibus.name + '_a'
        phBname = ibus.name + '_b'
        phCname = ibus.name + '_c'

        #not sure why this is done like this
        with warnings.catch_warnings(record=True) as w:
            phA_KVbase = ibus.Vmag_NL[0,:]/ibus.Vmag_NL[0,:]*ibus.kVbase_phg
            phB_KVbase = ibus.Vmag_NL[1,:]/ibus.Vmag_NL[1,:]*ibus.kVbase_phg
            phC_KVbase = ibus.Vmag_NL[2,:]/ibus.Vmag_NL[2,:]*ibus.kVbase_phg

        KVbasedf[phAname + '_KVbase'] = phA_KVbase
        KVbasedf[phBname + '_KVbase'] = phB_KVbase
        KVbasedf[phCname + '_KVbase'] = phC_KVbase
        #[end]

        #then save results to a csv
    Vtargdf.to_csv('voltage_data.csv')
    Idatdf.to_csv('current_data.csv')
    KVbasedf.to_csv('KVbase_values.csv')

    os.chdir(current_directory)
    return
