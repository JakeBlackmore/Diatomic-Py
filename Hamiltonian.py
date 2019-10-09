import numpy
from sympy.physics.wigner import wigner_3j,wigner_9j
from sympy.physics.quantum.spin import Rotation
from scipy.linalg import block_diag,eig,eigvals
import scipy.constants
import warnings

h = scipy.constants.h
muN = scipy.constants.physical_constants['nuclear magneton'][0]
bohr = scipy.constants.physical_constants['Bohr radius'][0]
eps0 = scipy.constants.epsilon_0
c = scipy.constants.c


pi = numpy.pi

DebyeSI = 3.33564e-30

RbCs = {    "IRb":1.5,
            "ICs":3.5,
            "d0":1.225*DebyeSI,
            "binding":114268135.25e6*h,
            "Brot":490.173994326310e6*h,
            "Drot":213*h,
            "QRb":-809.29e3*h,
            "QCs":59.98e3*h,
            "CRb":98.4*h,
            "CCs":194.2*h,
            "C3":192.4*h,
            "C4":19.0189557e3*h,
            "MuN":0.0062*muN,
            "MuRb":1.8295*muN,
            "MuCs":0.7331*muN,
            "a0":2020*4*pi*eps0*bohr**3,
            "a2":1997*4*pi*eps0*bohr**3,
            "Beta":0}

def Raising_operator(j):
    #produce the raising operator J+
    dimension = numpy.rint(2.0*j+1).astype(int)
    J = numpy.zeros((dimension,dimension))
    for m_j in range(numpy.rint(2.0*j).astype(int)):
        J[m_j,m_j+1]=numpy.sqrt(j*(j+1)-(j-m_j)*(j-m_j-1))
    return J

#produce the three generalised projections of angular momentum:
def X_operator(J):
    J_plus = Raising_operator(J)
    J_minus = numpy.transpose(J_plus)
    return 0.5*(J_plus+J_minus)

def Y_operator(J):
    J_plus = Raising_operator(J)
    J_minus = numpy.transpose(J_plus)
    return 0.5j*(J_minus - J_plus)

def Z_operator(J):
    J_plus = Raising_operator(J)
    J_minus = numpy.transpose(J_plus)
    return 0.5*(numpy.dot(J_plus,J_minus)-numpy.dot(J_minus,J_plus))

def vector_dot(x,y):
    ''' numpy.dot doesn't deal well with vectors of matrices'''
    X_Y = numpy.zeros(x[0].shape,dtype=numpy.complex)
    for i in range(x.shape[0]):
        X_Y += numpy.dot(x[i],y[i])
    return X_Y

def Generate_vecs(Nmax,IRb,ICs):
    '''Generate the vectors of the angular momentum operators which we need
    to be able to produce the Hamiltonian'''

    shapeN = int(numpy.sum([2*x+1 for x in range(0,Nmax+1)]))
    shapeRb = int(2*IRb+1)
    shapeCs = int(2*ICs+1)

    Nx = numpy.array([[]])
    Ny=numpy.array([[]])
    Nz= numpy.array([[]])

    for n in range(0,Nmax+1):
        Nx = block_diag(Nx,X_operator(n))
        Ny = block_diag(Ny,Y_operator(n))
        Nz = block_diag(Nz,Z_operator(n))

    Nx = Nx[1:,:]
    Ny = Ny[1:,:]
    Nz = Nz[1:,:]

    N_vec = numpy.array([numpy.kron(Nx,numpy.kron(numpy.identity(shapeRb),
                                                    numpy.identity(shapeCs))),
                        numpy.kron(Ny,numpy.kron(numpy.identity(shapeRb),
                                                    numpy.identity(shapeCs))),
                        numpy.kron(Nz,numpy.kron(numpy.identity(shapeRb),
                                                    numpy.identity(shapeCs)))])

    IRb_vec = numpy.array([numpy.kron(numpy.identity(shapeN),
                        numpy.kron(X_operator(IRb),numpy.identity(shapeCs))),
                        numpy.kron(numpy.identity(shapeN),
                        numpy.kron(Y_operator(IRb),numpy.identity(shapeCs))),
                        numpy.kron(numpy.identity(shapeN),
                        numpy.kron(Z_operator(IRb),numpy.identity(shapeCs)))])

    ICs_vec = numpy.array([numpy.kron(numpy.identity(shapeN),
                        numpy.kron(numpy.identity(shapeRb),X_operator(ICs))),
                        numpy.kron(numpy.identity(shapeN),
                        numpy.kron(numpy.identity(shapeRb),Y_operator(ICs))),
                        numpy.kron(numpy.identity(shapeN),
                        numpy.kron(numpy.identity(shapeRb),Z_operator(ICs)))])

    return N_vec,IRb_vec,ICs_vec

def Rotational(N,Brot,Drot):
    ''' Generates the hyperfine-free hamiltonian for the rotational levels of
    a rigid-rotor like molecule '''
    N_squared = vector_dot(N,N)
    return Brot*N_squared-Drot*N_squared*N_squared

def Zeeman(Cz,J):
    ''' Linear Zeeman shift, fixed magnetic field along z '''
    Hzeeman = -Cz*J[2]
    return Hzeeman

def scalar_nuclear(Ci,J1,J2):
    ''' Returns the scalar spin-spin term of the HF Hamiltonian '''
    return Ci*vector_dot(J1,J2)

def tensor_nuclear(C3,I1,I2,N):
    ''' The tensor - nuclear spin spin interaction '''
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore",category=numpy.ComplexWarning)
        Nmax = int(numpy.round(numpy.real(numpy.amax(N[2])),1))
        I1max = numpy.real(numpy.round(numpy.amax(I1[2]),1))
        I2max = numpy.real(numpy.round(numpy.amax(I2[2]),1))

    I1shape = int(2*I1max+1)
    I2shape = int(2*I2max+1)

    Narray = numpy.zeros((1,1))

    for n in range(0,Nmax+1):
        shape = int((2*n+1)*(2*I1max+1)*(2*I2max+1))
        nsub = numpy.zeros((shape,shape))+n
        Narray = block_diag(Narray,nsub)

    Narray = Narray[1:,1:]

    prefactor = C3/((2*Narray+3)*(2*Narray-1))
    term1 = 3*numpy.dot(vector_dot(I1,N),vector_dot(I2,N))
    term2 = 3*numpy.dot(vector_dot(I2,N),vector_dot(I1,N))
    term3 = -2*vector_dot(I1,I2)*Narray*(Narray+1)
    return prefactor*(term1+term2+term3)


def Quadrupole(Q,I1,I2,N):
    ''' from 10.1103/PhysRev.91.1403, which quotes the
     quadrupole interaction for KBr'''
    Q1,Q2 = Q
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore",category=numpy.ComplexWarning)
        Nmax = int(numpy.round(numpy.real(numpy.amax(N[2])),1))
        I1max = numpy.round(numpy.real(numpy.amax(I1[2])),1)
        I2max = numpy.round(numpy.real(numpy.amax(I2[2])),1)

    Narray = numpy.array([])
    I1array = numpy.array([])
    I2array = numpy.array([])
    Narray=numpy.zeros((1,1))

    for n in range(Nmax+1):
        shape = int((2*I1max+1)*(2*I2max+1)*(2*n+1))
        subarray = numpy.zeros((shape,shape))+n
        Narray= scipy.linalg.block_diag(Narray,subarray)
    Narray = Narray[1:,1:]

    epsilon = (numpy.finfo(float).eps)

    prefactor1 = numpy.zeros(Narray.shape)
    prefactor2 = numpy.zeros(Narray.shape)

    prefactor1 = -Q1/(2*I1max*(2*I1max-1)*(2*Narray-1)\
                        *(2*Narray+3))

    term1_1= 3*(numpy.dot(vector_dot(I1,N),vector_dot(I1,N)))
    term2_1 = 1.5*vector_dot(I1,N)
    term3_1 = -1*numpy.dot(vector_dot(I1,I1),vector_dot(N,N))
    Quad1 = prefactor1*(term1_1 +term2_1+term3_1)

    prefactor2 = -Q2/(2*I2max*(2*I2max-1)*(2*Narray-1)*\
                        (2*Narray+3))

    term1_2= 3*(numpy.dot(vector_dot(I2,N),vector_dot(I2,N)))
    term2_2 = 1.5*vector_dot(I2,N)
    term3_2 = -1*numpy.dot(vector_dot(I2,I2),vector_dot(N,N))
    Quad2 = prefactor2*(term1_2 +term2_2+term3_2)

    return Quad1+Quad2

def DC(Nmax,d0,I1,I2):
    ''' Generates the effect of the dc Stark shift for a rigid-rotor like
    molecule '''
    shape = numpy.sum(numpy.array([2*x+1 for x in range(0,Nmax+1)]))
    HDC = numpy.zeros((shape,shape),dtype= numpy.complex)

    I1shape = int(2*I1+1)
    I2shape = int(2*I2+1)

    i =0
    j =0
    for N1 in range(0,Nmax+1):
        for M1 in range(N1,-(N1+1),-1):
            for N2 in range(0,Nmax+1):
                for M2 in range(N2,-(N2+1),-1):
                    HDC[i,j]=-d0*numpy.sqrt((2*N1+1)*(2*N2+1))*(-1)**(M1)*wigner_3j(N1,1,N2,-M1,0,M2)*wigner_3j(N1,1,N2,0,0,0)
                    j+=1
            j=0
            i+=1
    return (numpy.kron(HDC,numpy.kron(numpy.identity(I1shape),numpy.identity(I2shape))))

def AC_iso(Nmax,a0,I1,I2):
    ''' Generates the diagonal elements of the ac stark matrix'''
    shape = numpy.sum(numpy.array([2*x+1 for x in range(0,Nmax+1)]))
    I1shape = int(2*I1+1)
    I2shape = int(2*I2+1)
    HAC = numpy.zeros((shape,shape),dtype= numpy.complex)
    i=0
    j=0
    for N1 in range(0,Nmax+1):
        for M1 in range(N1,-(N1+1),-1):
            for N2 in range(0,Nmax+1):
                for M2 in range(N2,-(N2+1),-1):
                    if N1==N2 and M1 ==M2:
                        HAC[i,j]=-a0
                    j+=1
            j=0
            i+=1
    HAC[numpy.isnan(HAC)] =0
    return (numpy.kron(HAC,numpy.kron(numpy.identity(I1shape),
                                                    numpy.identity(I2shape))))

def AC_aniso(Nmax,a2,Beta,I1,I2):
    ''' Anisotropic part of the AC Stark shift'''
    I1shape = int(2*I1+1)
    I2shape = int(2*I2+1)
    shape = numpy.sum(numpy.array([2*x+1 for x in range(0,Nmax+1)]))
    HAC = numpy.zeros((shape,shape),dtype= numpy.complex)
    i=0
    j=0
    for N1 in range(0,Nmax+1):
        for M1 in range(N1,-(N1+1),-1):
            for N2 in range(0,Nmax+1):
                for M2 in range(N2,-(N2+1),-1):
                    M = M2-M1
                    HAC[i,j]= -a2*(Rotation.d(2,M,0,Beta).doit()*(-1)**M2*\
                                numpy.sqrt((2*N1+1)*(2*N2+1))*\
                                wigner_3j(N2,2,N1,0,0,0)*\
                                wigner_3j(N2,2,N1,-M2,M,M1))
                    j+=1
            j=0
            i+=1
    HAC[numpy.isnan(HAC)] =0
    return (numpy.kron(HAC,numpy.kron(numpy.identity(I1shape),
            numpy.identity(I2shape))))

def Hyperfine_Ham(Nmax,I1_mag,I2_mag,Consts):
    ''' The field-free Hyperfine hamiltonian '''
    N,I1,I2 = Generate_vecs(Nmax,I1_mag,I2_mag)
    H = Rotational(N,Consts['Brot'],Consts['Drot'])+\
    scalar_nuclear(Consts['CRb'],N,I1)+scalar_nuclear(Consts['CCs'],N,I2)+\
    scalar_nuclear(Consts['C4'],I1,I2)+tensor_nuclear(Consts['C3'],I1,I2,N)+\
    Quadrupole((Consts['QRb'],Consts['QCs']),I1,I2,N)
    return H

def Zeeman_Ham(Nmax,I1_mag,I2_mag,Consts):
    ''' assembles the Zeeman term and generates operator vectors'''
    N,I1,I2 = Generate_vecs(Nmax,I1_mag,I2_mag)
    H = Zeeman(Consts['MuRb'],I1)+Zeeman(Consts['MuCs'],I2)+\
                Zeeman(Consts['MuN'],N)
    return H

def Build_Hamiltonians(Nmax,I1,I2,Constants,zeeman=False,DC=False,AC=False):
    ''' This function builds the hamiltonian matrices for evalutation so that
    the user doesn't have to rebuild them every time and we can benefit from
    numpy's ability to do distributed multiplcation.'''
    H0 = Hyperfine_Ham(Nmax,I1,I2,Constants)
    if zeeman:
        Hz = Zeeman_Ham(Nmax,I1,I2,Constants)
    else:
        Hz =0.
    if DC:
        HDC = DC(Nmax,Constants['d0'],I1,I2)
    else:
        HDC =0.
    if AC:
        HAC = AC_iso(Nmax,Constants['a0'],I1,I2)+\
        AC_aniso(Nmax,Constants['a2'],Constants['Beta'],I1,I2)
    else:
        HAC =0.
    return H0,Hz,HDC,HAC

def Vary_magnetic(Hams,fields0,Bz,return_states = False):
    H0,Hz,HDC,HAC = Hams
    E,B,I = fields0

    if type(Hz) != numpy.ndarray:
        warnings.warn("Hamiltonian is zero: nothing will change")

    EigenValues = numpy.zeros((H0.shape[0],len(Bz)))
    if return_states:
        States = numpy.zeros((H0.shape[0],H0.shape[0],len(Bz)))
    for i,b in enumerate(Bz):
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore",category=numpy.ComplexWarning)
            H = H0+E*HDC+I*HAC+b*Hz
            if return_states:
                Eigen = eig(H)
                order = numpy.argsort(Eigen[0])
                EigenValues[:,i]=Eigen[0][order]
                States[:,:,i] = Eigen[1][:,order]
            else:
                Eigen = eigvals(H)
                EigenValues[:,i]=numpy.sort(Eigen)
    if return_states:
        return EigenValues,States
    else:
        return EigenValues

def Vary_ElectricDC(Hams,fields0,Ez,return_states = False):
    E,B,I = fields0
    H0,Hz,HDC,HAC = Hams
    EigenValues = numpy.zeros((H0.shape[0],len(Ez)))

    if type(HDC) != numpy.ndarray:
        warnings.warn("Hamiltonian is zero: nothing will change")

    if return_states:
        States = numpy.zeros((H0.shape[0],H0.shape[0],len(Ez)))
    for i,e in enumerate(Ez):
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore",category=numpy.ComplexWarning)
            H = H0+e*HDC+I*HAC+B*Hz
            if return_states:
                Eigen = eig(H)
                order = numpy.argsort(Eigen[0])
                EigenValues[:,i]=Eigen[0][order]
                States[:,:,i] = Eigen[1][:,order]
            else:
                Eigen = eigvals(H)
                EigenValues[:,i]=numpy.sort(Eigen)
    if return_states:
        return EigenValues,States
    else:
        return EigenValues

def Vary_Intensity(Hams,fields0,I_app,return_states = False):
    H0,Hz,HDC,HAC = Hams
    E,B,I = fields0
    if type(HAC) != numpy.ndarray:
        warnings.warn("Hamiltonian is zero: nothing will change")

    EigenValues = numpy.zeros((H0.shape[0],len(I_app)))
    if return_states:
        States = numpy.zeros((H0.shape[0],H0.shape[0],len(I_app)))
    for i,Int in enumerate(I_app):
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore",category=numpy.ComplexWarning)
            H = H0+E*HDC+Int*HAC+B*Hz
            if return_states:
                Eigen = eig(H)
                order = numpy.argsort(Eigen[0])
                EigenValues[:,i]=Eigen[0][order]
                States[:,:,i] = Eigen[1][:,order]
            else:
                Eigen = eigvals(H)
                EigenValues[:,i]=numpy.sort(Eigen)
    if return_states:
        return EigenValues,States
    else:
        return EigenValues

def Vary_Beta(Hams,fields0,Angles,Molecule_pars,return_states = False):
    Nmax,I1,I2,a2 = Molecule_pars
    H0,Hz,HDC,HAC = Hams
    E,B,I = fields0
    if I == 0:
        warnings.warn("Intensity is zero: nothing will change")

    EigenValues = numpy.zeros((H0.shape[0],len(Bz)))
    if return_states:
        States = numpy.zeros((H0.shape[0],H0.shape[0],len(Bz)))
    for i,beta in enumerate(Angles):
        HAC = AC_aniso(Nmax,a2,beta,I1,I2)
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore",category=numpy.ComplexWarning)
            H = H0+E*HDC+I*HAC+B*Hz
            if return_states:
                Eigen = eig(H)
                order = numpy.argsort(Eigen[0])
                EigenValues[:,i]=Eigen[0][order]
                States[:,:,i] = Eigen[1][:,order]
            else:
                Eigen = eigvals(H)
                EigenValues[:,i]=numpy.sort(Eigen)
    if return_states:
        return EigenValues,States
    else:
        return EigenValues


if __name__=="__main__":
    import matplotlib.pyplot as pyplot
    import scipy.constants
    import time
    ''' My test is building a zeeman structure plot for N<= 5 takes ~20 mins'''
    B = 0
    I = 0
    E = 0

    h = scipy.constants.h
    muN = scipy.constants.physical_constants['nuclear magneton'][0]
    bohr = scipy.constants.physical_constants['Bohr radius'][0]
    eps0 = scipy.constants.epsilon_0
    c = scipy.constants.c

    DebyeSI = 3.33564e-30 #C m/Debye

    Nmaximum = 1
    IRb =RbCs['IRb']
    ICs =  RbCs['ICs']

    Nshape = numpy.sum([2*x+1 for x in range(0,Nmaximum+1)])

    HFShape = int(Nshape*(2*IRb+1)*(2*ICs+1))

    Steps = 150
    bvary = numpy.linspace(0,200,Steps)
    start = time.time()
    #Energies = numpy.empty((HFShape,Steps))
    # build the hamiltonian without any fields
    N,I1,I2 = Generate_vecs(Nmaximum,IRb,ICs)
    #H0 = Hyperfine_Ham(Nmaximum,IRb,ICs,Constants)
    #Hz = Zeeman_Ham(Nmaximum,IRb,ICs,Constants)
    #HDC = DC(Nmaximum,Constants['d0'],IRb,ICs)
    #HAC = AC_iso(Nmaximum,Constants['a0'],IRb,ICs)+\
    #AC_aniso(Nmaximum,Constants['a2'],Constants['Beta'],IRb,ICs)

    Hamiltonian = Build_Hamiltonians(Nmaximum,IRb,ICs,RbCs,zeeman=True)
    energy = Vary_magnetic(Hamiltonian,(B,I,E),bvary)