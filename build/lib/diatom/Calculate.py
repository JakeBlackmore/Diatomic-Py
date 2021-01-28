from diatom.Hamiltonian import *
import numpy
import warnings
import pyprind
import sys
'''
This module is designed as a more user-friendly version of the Hamiltonian module,
allowing simple wrappers for common problems.
'''


###############################################################################
# Start by definining a bunch of constants that are needed for the code       #
###############################################################################

'''
    Important note!

    All units in this code are SI i.e. elements in the Hamiltonian have units
    of Joules. Outputs will be on the order of 1e-30

'''

h = scipy.constants.h
muN = scipy.constants.physical_constants['nuclear magneton'][0]
bohr = scipy.constants.physical_constants['Bohr radius'][0]
eps0 = scipy.constants.epsilon_0
c = scipy.constants.c


pi = numpy.pi

DebyeSI = 3.33564e-30

###############################################################################
# Bialkali Molecular Constants                                                    #
###############################################################################

#Constants are from
# https://doi.org/10.1103/PhysRevA.96.042506
#https://doi.org/10.1103/PhysRevA.78.033434
# and https://arxiv.org/pdf/1707.02168.pdf

# RbCs Constants are from https://doi.org/10.1103/PhysRevA.94.041403
# Polarisabilities are for 1064 nm

RbCs = {    "I1":1.5,
            "I2":3.5,
            "d0":1.225*DebyeSI,
            "binding":114268135.25e6*h,
            "Brot":490.173994326310e6*h,
            "Drot":207.3*h,
            "Q1":-809.29e3*h,
            "Q2":59.98e3*h,
            "C1":98.4*h,
            "C2":194.2*h,
            "C3":192.4*h,
            "C4":19.0189557e3*h,
            "MuN":0.0062*muN,
            "Mu1":1.8295*muN,
            "Mu2":0.7331*muN,
            "a0":2020*4*pi*eps0*bohr**3,
            "a2":1997*4*pi*eps0*bohr**3,
            "Beta":0}

K41Cs = {   "I1":1.5,
            "I2":3.5,
            "d0":1.84*DebyeSI,
            "Brot":880.326e6*h,
            "Drot":0*h,
            "Q1":-0.221e6*h,
            "Q2":0.075e6*h,
            "C1":4.5*h,
            "C2":370.8*h,
            "C3":9.9*h,
            "C4":628*h,
            "MuN":0.0*muN,
            "Mu1":0.143*(1-1340.7e-6)*muN,
            "Mu2":0.738*(1-6337.1e-6)*muN,
            "a0":7.783e6*h, #h*Hz/(W/cm^2)
            "a2":0,
            "Beta":0}

K40Rb = {   "I1":4,
            "I2":1.5,
            "d0":0.62*DebyeSI,
            "Brot":1113.4e6*h,
            "Drot":0*h,
            "Q1":0.311e6*h,
            "Q2":-1.483e6*h,
            "C1":-24.1*h,
            "C2":419.5*h,
            "C3":-48.2*h,
            "C4":-2028.8*h,
            "MuN":0.0140*muN,
            "Mu1":-0.324*(1-1321e-6)*muN,
            "Mu2":1.834*(1-3469e-6)*muN,
            "a0":5.33e-5*1e6*h, #h*Hz/(W/cm^2)
            "a2":6.67e-5*1e6*h,
            "Beta":0}
###############################################################################
# Functions for the calculations to use                                       #
###############################################################################

# This is the main build function and one that the user will actually have to
# use.

def Build_Hamiltonians(Nmax,Constants,zeeman=False,EDC=False,AC=False):
    '''
        This function builds the hamiltonian matrices for evalutation so that
        the user doesn't have to rebuild them every time and we can benefit from
        numpy's ability to do distributed multiplcation.



        Input arguments:
        Nmax: Maximum rotational level to include (float)
        I1_mag,I2_mag, magnitude of the nuclear spins (float)
        Constants: Dict of molecular constants (Dict of floats)
        zeeman,EDC,AC :Switches for turning off parts of the total Hamiltonian
                        can save significant time on calculations where DC and
                        AC fields are not required due to nested for loops
                        (bool)

        returns:
        H0,Hz,HDC,HAC: Each is a (2*Nmax+1)*(2*I1_mag+1)*(2*I2_mag+1)x
           (2*Nmax+1)*(2*I1_mag+1)*(2*I2_mag+1) array.
    '''
    I1 = Constants['I1']
    I2 = Constants['I2']

    H0 = Hyperfine_Ham(Nmax,I1,I2,Constants)
    if zeeman:
        Hz = Zeeman_Ham(Nmax,I1,I2,Constants)
    else:
        Hz =0.
    if EDC:
        HDC = DC(Nmax,Constants['d0'],I1,I2)
    else:
        HDC =0.
    if AC:
        HAC = (1./(2*eps0*c))*(AC_iso(Nmax,Constants['a0'],I1,I2)+\
        AC_aniso(Nmax,Constants['a2'],Constants['Beta'],I1,I2))
    else:
        HAC =0.
    return H0,Hz,HDC,HAC

def Solve(Nmax,Constants,states=True,zeeman=False,EDC=False,AC=False):

    H0,Hz,HDC,HAC = Build_Hamiltonians(Nmax,Constants,zeeman,EDC,AC)



    return eig

def SolveQuadratic(a,b,c):
    '''
    simple function to solve the quadratic formula for x. returns the most
    positive value of x supported.
    '''

    d = b**2-4*a*c # discriminant
    x1 = (-b+numpy.sqrt((b**2)-(4*(a*c))))/(2*a)
    x2 = (-b-numpy.sqrt((b**2)-(4*(a*c))))/(2*a)

    return max([x1,x2])

def LabelStates_N_MN(States,Nmax,I1,I2,locs=None):
    ''' This function returns two lists: the input states labelled by N and MN
    in the order that they are provided. The returned numbers will only be good
    if the state is well -represented in the decoupled basis.

    Optionally can return the quantum  numbers for a subset if the locs kwarg
    is provided. Each element in the list locs corresponds to the index for the
    states to label.

    Inputs:

    States, Numpy.ndarray of eigenstates, from linalg.eig
    Nmax: maximum rotational state in calculation

    I1 , I2: nuclear spin quantum numbers

    locs: list of indices of states to label
    '''
    if locs != None:
        States = States[:,locs]
    N, I1,I2 = Generate_vecs(Nmax,I1,I2)

    N2 = vector_dot(N,N)
    Nz = N[2]

    Nlabels = numpy.einsum('ik,ij,jk->k',numpy.conj(States),N2,States)
    Nlabels = numpy.round([SolveQuadratic(1,1,-1*x)  for x in Nlabels],0).real

    MNlabels = numpy.round(numpy.einsum('ik,ij,jk->k',
                                    numpy.conj(States),Nz,States),0).real

    return Nlabels,MNlabels

def LabelStates_I_MI(States,Nmax,I1,I2,locs = None):
    ''' This function returns two lists: the input states labelled by N and MN
    in the order that they are provided. The returned numbers will only be good
    if the state is well -represented in the decoupled basis


    Optionally can return the quantum  numbers for a subset if the locs kwarg
    is provided. Each element in the list locs corresponds to the index for the
    states to label.

    Inputs:

    States, Numpy.ndarray of eigenstates, from linalg.eig
    Nmax: maximum rotational state in calculation

    I1 , I2: nuclear spin quantum numbers

    locs: list of indices of states to label
    '''

    if locs != None:
        States = States[:,locs]

    I = I1 + I2

    N, I1,I2 = Generate_vecs(Nmax,I1,I2)

    I2 = vector_dot(I,I)

    Iz = I[2]

    Ilabels = numpy.einsum('ik,ij,jk->k',numpy.conj(States),I2,States)
    Ilabels = numpy.round([SolveQuadratic(1,1,-1*x)  for x in Ilabels],1).real

    MIlabels = numpy.round(numpy.einsum('ik,ij,jk->k',
                                    numpy.conj(States),Iz,States),1).real

    return Ilabels,MIlabels

def LabelStates_F_MF(States,Nmax,I1,I2,locs=None):
    ''' This function returns two lists: the input states labelled by N and MN
    in the order that they are provided. The returned numbers will only be good
    if the state is well -represented in the coupled basis

    Optionally can return the quantum  numbers for a subset if the locs kwarg
    is provided. Each element in the list locs corresponds to the index for the
    states to label.

    Inputs:

    States, Numpy.ndarray of eigenstates, from linalg.eig
    Nmax: maximum rotational state in calculation

    I1 , I2: nuclear spin quantum numbers

    locs: list of indices of states to label
    '''


    if locs != None:
        States = States[:,locs]

    N, I1,I2 = Generate_vecs(Nmax,I1,I2)

    F = N + I1 + I2

    F2 = vector_dot(F,F)

    Fz = F[2]


    Flabels = numpy.einsum('ik,ij,jk->k',numpy.conj(States),F2,States)
    Flabels = numpy.round([SolveQuadratic(1,1,-1*x)  for x in Flabels],1).real

    MFlabels = numpy.round(numpy.einsum('ik,ij,jk->k',
                                    numpy.conj(States),Fz,States),1).real

    return Flabels,MFlabels

def dipole(Nmax,I1,I2,d,M):
    ''' Generates the induced dipole moment operator for a Rigid rotor.
    Expanded to cover state  vectors in the uncoupled hyperfine basis.

    '''
    shape = numpy.sum(numpy.array([2*x+1 for x in range(0,Nmax+1)]))
    Dmat = numpy.zeros((shape,shape),dtype= numpy.complex)
    i =0
    j =0
    for N1 in range(0,Nmax+1):
        for M1 in range(N1,-(N1+1),-1):
            for N2 in range(0,Nmax+1):
                for M2 in range(N2,-(N2+1),-1):
                    Dmat[i,j]=d*numpy.sqrt((2*N1+1)*(2*N2+1))*(-1)**(M1)*\
                    wigner_3j(N1,1,N2,-M1,M,M2)*wigner_3j(N1,1,N2,0,0,0)
                    j+=1
            j=0
            i+=1

    shape1 = int(2*I1+1)

    shape2 = int(2*I2+1)

    Dmat = numpy.kron(Dmat,numpy.kron(numpy.identity(shape1),
                                                    numpy.identity(shape2)))

    return Dmat

def TDM(Nmax,I1,I2,M,States,gs,locs=None):
    ''' Function to calculate the Transition Dipole Moment between a state  gs
    and a range of states. Returns the TDM in units of the permanent dipole
    moment (d0).

    Inputs:
    Nmax: Maximum rotational quantum number in original calculations
    I1,I2 : nuclear spin quantum numbers
    M: Helicity of Transition, -1 = S+, 0 = Pi, +1 = S-
    States: matrix for eigenstates of problem

    gs: index of ground state.

    locs: optional argument to calculate for subset of States, should be an
            array-like.
    '''

    dipole_op = dipole(Nmax,I1,I2,1,M)

    gs = numpy.conj(States[:,gs])
    if locs != None :
        States =  States[:,locs]

    TDM =  numpy.einsum('i,ij,jk->k',gs,dipole_op,States).real

    return TDM

def Sort_Smooth(Energy,States,pb=False):
    ''' This is a function to ensure that all eigenstates plotted change
    adiabatically, it does this by assuming that step to step the eigenstates
    should vary by only a small amount (i.e. that the  step size is fine) and
    arranging states to maximise the overlap one step to the next.

    Inputs:
    Energy : numpy.ndarray containing the eigenergies, as from numpy.linalg.eig
    States: numpy.ndarray containing the states, in the same order as Energy
    pb (bool) : optionally show progress bar
    '''
    ls = numpy.arange(States.shape[2],dtype="int")
    number_iterations = len(Energy[:,0])
    if pb:
        bar = pyprind.ProgBar(number_iterations, monitor=True)
    for i in range(1,number_iterations):
        '''
        This loop sorts the eigenstates such that they maintain some
        continuity. Each eigenstate should be chosen to maximise the overlap
        with the previous.
        '''
        #calculate the overlap of the ith and jth eigenstates
        overlaps = numpy.einsum('ij,ik->jk',
                                numpy.conjugate(States[i-1,:,:]),States[i,:,:])
        orig2 = States[i,:,:].copy()
        orig1 = Energy[i,:].copy()
        #insert location of maximums into array ls
        numpy.argmax(numpy.abs(overlaps),axis=1,out=ls)
        for k in range(States.shape[2]):
            l = ls[k]
            if l!=k:
                Energy[i,k] = orig1[l].copy()
                States[i,:,k] = orig2[:,l].copy()
        if pb:
            bar.update()
    if pb:
        print(bar)
    return Energy,States

def Export_Energy(fname,Energy,Fields=None,labels=None,
                                headers=None,dp=6,format=None):
    '''
    This exports the energy of the states for a
    '''
    # some input sanitisation, ensures that the fname includes an extension
    if fname[-4:]!=".csv":
        fname = fname+".csv"
    dp = int(numpy.round(dp))

    # check whether the user has given labels and headers or  just one
    lflag = False
    hflag = False

    if labels != None:
        labels = numpy.array(labels)
        lflag = True
    else:
        labels=[]

    if headers != None:
        hflag = True
    else:
        headers = []

    # all this is just checking whether there are headers and labels, just
    #labels, just headers or neither.

    if not hflag and lflag:
        warnings.warn("using default headers for labels",UserWarning)
        headers = ["Label {:.0f}".format(x) for x in range(len(labels[0,:]))]

    elif hflag and not lflag:
        warnings.warn("headers given without labels",UserWarning)
        headers =[]

    if len(headers) != labels.shape[0]:
        warnings.warn("Not enough headers given for chosen labels",UserWarning)
        headers = ["Label {:.0f}".format(x) for x in range(len(labels[:,0]))]

    # Now to write a string to make the output look nice. For simplicity we say
    # that all the  labels must be given to 1 dp
    if format==None:
        format = ["%.1f" for x in range(len(labels[:,0]))]

    # now just make the one for the main body of the output file. Specified by
    # the dp argument.
    if len(Energy.shape)>1:
        format2 = ["%."+str(dp)+"f" for x in range(len(Energy[:,0]))]
    else:
        format2 = ["%."+str(dp)+"f"]
    #numpy needs only one format argument
    format.extend(format2)

    headers =','.join(headers)


    headers = ','.join(["Labels" for l in range(labels.shape[0])])+",Energy (Hz)\n"+headers

    if type(Fields) != type(None):
        Energy = numpy.insert(Energy,0,Fields.real,axis=1)
        labels = numpy.insert(labels,0,[-1 for x in range(labels.shape[0])],axis=1)

    output = numpy.row_stack((labels,Energy))
    numpy.savetxt(fname,output.T,delimiter=',',header = headers,fmt=format)

def Export_State_Comp(fname,Nmax,I1,I2,States,labels=None,
                                headers=None,dp=6,format=None):
    ''' function to export state composition in a human-readable format
    along the first row are optional headers and the labels for the basis States
    in the uncoupled basis.

    the user can supply optional labels for the states in a (x,y) list or array
    where y is the number of states and x is the number of unique labels, for
    instance a list of the N quantum  number for each state.

    they can also (optionally) supply a (x,1) list to include custom headers
    in the first row. If the labels kwarg is included and headers is not,
    then non-descriptive labels are used to ensure correct output.

    by default the output is given to 6 decimal places (truncated) this can be
    adjusted using the kwarg dp

    inputs:
    fname (string) : the filename and path to save the output file
    Nmax (int/float) : the maximum value of N used in the calculation
    I1,I2 (float) : the nuclear spin quantum numbers of nucleus 1 and 2
    States (N,M) ndarray : eigenstates stored in an (N,M) ndarray, N is the
                            number of eigenstates. M is the number of basis
                            states.
    labels (N,X) ndarray : ndarray containing X labels for each of the N states
    headers (X) ndarray-like : Ndarray-like containing descriptions of the labels
    dp (int) : number of decimal places to output the file to [default = 6]
    format (list) :  list of strings for formatting the headers. Defaults to 1 dp.

    '''

    # some input sanitisation, ensures that the fname includes an extension
    if fname[-4:]!=".csv":
        fname = fname+".csv"
    dp = int(numpy.round(dp))

    # check whether the user has given labels and headers or  just one
    lflag = False
    hflag = False

    if labels != None:
        labels = numpy.array(labels)
        lflag = True

    if headers != None:
        hflag = True
    else:
        headers = []


    # create labels for basis states from Generate_vecs
    # first step is to recreate the angular momentum operators
    N, I1,I2 = Generate_vecs(Nmax,I1,I2)

    # each basis state is an eigenstate of N^2, so N^2 is diagonal in our basis
    # with eigenvalues N(N+1)

    N2 = numpy.round([SolveQuadratic(1,1,-1*x) for x in numpy.diag(vector_dot(N,
                                                                N))],0).real

    # they are also eigenstates of Nz, I1z and I2z which are diagonal
    # in the basis that we constructed.

    MN = numpy.round(numpy.diag(N[2]),0).real
    M1 = numpy.round(numpy.diag(I1[2]),1).real
    M2 = numpy.round(numpy.diag(I2[2]),1).real

    # Now we create a list of each of the values in the right place
    state_list = ["({:.0f}:{:.0f}:{:.1f}:{:.1f})".format(N2[i],
                                    MN[i],M1[i],M2[i]) for i in range(len(MN))]
    # all this is just checking whether there are headers and labels, just
    #labels, just headers or neither.

    if not hflag and lflag:
        warnings.warn("using default headers for labels",UserWarning)
        headers = ["Label {:.0f}".format(x) for x in range(len(labels[0,:]))]

    elif hflag and not lflag:
        warnings.warn("headers given without labels",UserWarning)
        headers =[]

    if len(headers) != labels.shape[0]:
        warnings.warn("Not enough headers given for chosen labels",UserWarning)
        headers = ["Label {:.0f}".format(x) for x in range(len(labels[:,0]))]

    # Now to write a string to make the output look nice. For simplicity we say
    # that all the  labels must be given to 1 dp
    if format==None:
        format = ["%.1f" for x in range(len(headers))]

    # now just make the one for the main body of the output file. Specified by
    # the dp argument.
    format2 = ["%."+str(dp)+"f" for x in range(len(state_list))]

    #numpy needs only one format argument
    format.extend(format2)

    headers.extend(state_list)
    headers =','.join(headers)
    headers = ','.join(["Labels" for l in range(labels.shape[0])])+",States in (N:MN:M1:M2) basis\n"+headers

    output = numpy.insert(States.real,0,labels.real,axis=0)
    numpy.savetxt(fname,output.T,delimiter=',',header = headers,fmt=format)

if __name__ == "__main__":
    import os
    from scipy import constants
    print("Starting")
    h = constants.h

    cwd = os.path.dirname(os.path.abspath(__file__))

    dir = os.path.dirname(cwd)

    dir = dir+"\\Example Scripts\\Outputs"

    if not os.path.exists(dir):
        os.makedirs(dir)

    Consts = RbCs
    Nmax = 3
    H0,Hz,HDC,HAC = Build_Hamiltonians(Nmax,Consts,zeeman=True,EDC=True,AC=True)

    I = 0
    E = 0
    B = 181.5*1e-4

    H = [H0+Hz*Bz+E*HDC+I*HAC for Bz in numpy.linspace(1e-6,B,200)]

    eigvals,eigstates = numpy.linalg.eig(H)
    print("Sorting")
    eigvals,eigstates = Sort_Smooth(eigvals,eigstates,pb=True)

    eigvals = eigvals /h # convert to Hz

    N,MN = LabelStates_N_MN(eigstates[-1,:,:],Nmax,Consts['I1'],Consts['I2'])

    F,MF = LabelStates_F_MF(eigstates[-1,:,:],Nmax,Consts['I1'],Consts['I2'])

    labels = [N,MF,eigvals[-1,:]]

    headers = ["N","MF","Energy@181.5G (Hz)"]
    Export_State_Comp(dir+"\\States_{:.2f}".format(B*1e4),
                            Nmax,Consts['I1'],Consts['I2'],
                            eigstates[-1,:,:],labels=labels,headers=headers)
    labels = [N,MF]

    headers = ["N","MF"]
    Export_Energy(dir+"\\Energy_{:.2f}".format(B*1e4),
                            Nmax,Consts['I1'],Consts['I2'],
                            eigvals,1e4*numpy.linspace(1e-6,B,200),
                            labels=labels,headers=headers)
