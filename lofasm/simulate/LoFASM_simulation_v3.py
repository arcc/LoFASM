import numpy as np
import numpy.linalg as LA
import scipy as sp
import scipy.integrate as integrate

# from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm
from matplotlib.ticker import LinearLocator, FormatStrFormatter
import matplotlib.pyplot as plt

import time

speed_of_light = 29979245800.0 #Units = cm/s

class antenna_elements(object):
    """A single current element for an antenna"""

    def __init__(self,location,direction,length,current):
        self.location  = np.array(location)
        self.direction = np.array(direction)
        self.length    = length
        self.current   = current

    def displacement(self,location):
        return np.array(location)-self.location

    def distance(self,location):
        dx = self.displacement(location)
        return np.sqrt(np.sum(dx*dx))

        
class antenna(object):
    """Antenna Base Class"""

    def __init__(self,location):
        self.location       = np.array(location)
        self.type           = Omni
        self.impedance      = 50
        self.V              = 0
        self.nu             = 0
        self.elements       = [] #List of antenna_elements

    def __getitem__(self,i):
        if i < len(self.elements):
            x = self.elements[i]
            return x
        else:
            raise StopIteration()
        
    def __len__(self):
        return len(self.elements)

        
    def energize(self,electric_field):
        """Calculates the voltage at the antenna terminals given an electric field assuming the antenna is a 1-D curve that is simply connected"""
        self.V = 0
        self.nu = electric_field.nu

        for element in self:
            self.V += np.dot(electric_field.eval(element.location),element.direction)*element.length
    #        self.V = np.dot(electric_field.eval(self.location),self.pol)*self.length

            
        self.calculate_currents()

    #    def calculate_currents(self):
    #        for element in self:
    #            element.current = 30*speed_of_light*(self.V/self.impedance)


    def generated_field(self):
        return antenna_field(self)

    def set_voltage(self,V):
        self.V = V
        self.calculate_currents()
    
    def read_voltage(self):
        return self.V

    def set_frequency(self,nu):
        '''Set frequency in Mhz'''
        self.nu = nu

    def read_frequency(self):
        return nu

    def power_down(self):
        self.V  = 0
        self.nu = 0


    
class dipole_antenna(antenna):
    """dipole style antenna class"""

    def __init__(self,location,pol,length):
        self.location   = np.array(location)  # [x,y,z]
        self.length     = length                #Length of Antenna in cms
        self.impedance  = 50                 #Impedence in Ohms
        self.Nelements  = 10
        self.elements   = []
        self.V          = 0
        self.nu         = 0
        self.pol        = np.array(pol)
    
    #        pol = np.array([np.cos(orientation_angle),np.sin(orientation_angle),0])
     
        dl  = length/self.Nelements
        dx  = self.pol*dl
        xstart = -length/2*self.pol + dx/2.0 + location
        for i in range(0,self.Nelements):
            xloc = xstart + dx*i
            self.elements.append(antenna_elements(xloc,self.pol,dl,0))

    def set_frequency(self,frequency):
        self.nu = frequency
        self.impedance = self.calculate_impedance(frequency,self.length)

    def calculate_currents(self):
        for element in self:
            dx = (self.location-element.location)
            d = np.sqrt(np.dot(dx,dx))
            k = self.nu*1e6/speed_of_light
            element.current = 30*speed_of_light*(self.V/self.impedance)*np.sin(k*(self.length/2.0- d))/np.cos(k*self.length/2.0)


    def calculate_impedance(self,frequency,length):
        
        '''Frequency is in Mhz,length is in cm, impedance is in Ohms. This is a WAG!'''
        return (50.0 * ((2*np.pi*1e6*frequency/speed_of_light)*length)**2.0) + 0j*((frequency-30)*10.0)
            

class electric_field(object):
    """Electric Field Base Class"""

    def __init__(self,nu):
        self.nu = nu
        self.omega = 2*np.pi*nu        
        self.type = None

    def eval(self,location):
        return 0

class plane_wave(electric_field):
    """Plane wave electric field"""

    def __init__(self,theta,phi,nu,epol,E_amp):
        self.type  = 'plane_wave'
        self.theta = theta
        self.phi   = phi
        self.nu    = nu
        self.omega = 2*np.pi*nu*1e6 #Freq
        self.k     = self.omega/speed_of_light #1/m Wave number
        self.epol  = epol
        self.E_amp = E_amp

        self.matrix = np.array([[np.sin(theta)*np.cos(phi),np.cos(phi)*np.cos(theta),-np.sin(phi)],
                                [np.sin(theta)*np.sin(phi),np.sin(phi)*np.cos(theta),np.cos(phi)],
                                [np.cos(theta),-np.sin(theta),0]]) #Perhaps conversion

        self.r_hat = np.dot(self.matrix,np.array([1,0,0]))
        self.E     = np.dot(self.matrix,epol)*E_amp

    def eval(self,location):
        return self.E*np.exp(-1j*self.k*np.dot(self.r_hat,location))


class antenna_field(electric_field):
    """Electric Field from an antenna defined by an antenna class"""
    
    def __init__(self,antenna):
        self.type = 'antenna_field'
        self.antenna = antenna
        self.nu   = antenna.nu
        self.omega = 2*np.pi*self.nu*1e6
        self.k    = self.omega/speed_of_light

    def eval(self,location):

        E = np.zeros(3)*1j

        for element in self.antenna:
            xloc           = element.displacement(location)
            r              = element.distance(location)
            rhat           = (xloc)/r        
            efactor        = np.exp(-1j*self.k*r)
            I              = element.current*element.direction
            longitudinal   = np.dot(I,rhat)*rhat
            transverse     = I - longitudinal
            mixed          = I - 3*longitudinal

            E += element.length*efactor*(transverse*1j*self.omega/(r*speed_of_light**2) - mixed/((r**2) * speed_of_light) - 1j*mixed/((r**3)*self.omega))
            
        return E
        


class antenna_array(object):
    """Base class for and array of antennas"""

    def __init__(self):
        self.VtoV_matrix     = 0
        self.coupling_matrix = 0
        self.coupling_matrix_calculated = False
        self.coupling_active = False
        self.antennas    = {}
        self.nu          = 0
        self.receiver_gain = {} #Complex gain factor used when combining voltages
        
    def __getitem__(self,i):
        if i < len(self.antennas):
            x = self.antennas[i]
            return x
        else:
            raise StopIteration()
        
    def __len__(self):
        return len(self.antennas)


    def plot_array(self):
        """Plot the locations of all the antennas in the array"""

        for ant in self:
            plt.scatter(ant.location[0],ant.location[1])
            plt.draw()

    def activate_coupling(self):
        self.coupling_active = True

    def deactivate_coupling(self):
        self.coupling_active = True
        self.coupling_matrix_calculated = False
        self.coupling_matrix = 0

    def calculate_VtoV_matrix(self):
        """Calculates the first order coupling matrix"""

        self.VtoV_matrix = np.zeros([len(self),len(self)])*1j

        for i in self.antennas:
            for j in self.antennas:
                if (i != j):
                    self[j].set_voltage(1 + 0j)
                    self[i].energize(self[j].generated_field())
                    self.VtoV_matrix[i,j] = self[i].read_voltage()
                    self[j].set_voltage(0)
                    self[i].set_voltage(0)


    def calculate_full_coupling_matrix(self):
        """Calculates the full coupling matrix"""
        self.calculate_VtoV_matrix()

        [eva,b] = LA.eig(self.VtoV_matrix)
        
        a = [1.0/(1 - x) for x in eva]
        #a  = eva
        bi = LA.inv(b)
        
        self.coupling_matrix = np.dot(b,np.dot(np.diag(a),bi))

        self.coupling_matrix_calculated = True

    def calculate_coupling_effect(self):
        """Not TESTED!!"""
        if(not self.coupling_matrix_calculated):
            self.calculate_full_coupling_matrix()

        V  = np.zeros(len(self))*1j + 1.0

        Vc = np.dot(self.coupling_matrix,V)

        deltaV = Vc - V

        return deltaV

    def beam_pattern(self,theta,phi,epol):

        #Create the Incident plane wave
        pw = plane_wave(theta,phi,self.nu,epol,.01)
        #Determine the first order voltages in each antenna
        self.energize_array(pw)
        V = np.zeros(len(self))*1j        
        for i in self.antennas:
            V[i] = self[i].read_voltage()

        #Multiply by the coupling matrix to include the effects of mutual coupling
        if (self.coupling_matrix_calculated): V = np.dot(self.coupling_matrix,V)

        #Multiply by the gain factors for each antennas
        for i in self.antennas:
            V[i] *= self.receiver_gain[self.antennas[i]]

        #Sum all the voltages
        S = np.sum(V)

        #Return the total power detected        
        return np.real(np.conjugate(S)*S/len(self)**2)


    def get_proj_distances(self,theta,phi):

        dists = []

        rhat = -np.array([np.sin(theta)*np.cos(phi),np.sin(theta)*np.sin(phi),np.cos(theta)])
        for ant in self:
            dists.append(np.dot(rhat,ant.location))

        return np.array(dists)
            
        
    def get_phases(self,theta,phi,epol,limit=True):

        #Create the Incident plane wave
        pw = plane_wave(theta,phi,self.nu,epol,.01)
        #Determine the first order voltages in each antenna
        self.energize_array(pw)
        V = np.zeros(len(self))*1j        
        for i in self.antennas:
            V[i] = self[i].read_voltage()

        #Multiply by the coupling matrix to include the effects of mutual coupling
        if (self.coupling_matrix_calculated): V = np.dot(self.coupling_matrix,V)

        #Multiply by the gain factors for each antennas
        for i in self.antennas:
            V[i] *= self.receiver_gain[self.antennas[i]]

        phase = np.array([np.arctan2(x.imag,x.real) for x in V])

        if(limit):
            phase = phase -phase[0]
            loc = np.where(phase < 0)
            phase[loc] += 2*np.pi
            loc = np.where(phase > np.pi)
            phase[loc] -= 2*np.pi

        return phase


    def plot_beam_pattern3d(self):

        fig = plt.figure()
        ax = fig.gca(projection='3d')
        theta = np.arange(-np.pi/2.0, np.pi/2.0, 0.1)
        phi   = np.arange(0,2*np.pi, 0.1)
        theta, phi = np.meshgrid(theta, phi)
        X = phi.copy()
        Y = phi.copy()
        Z = phi.copy()
        for i in np.arange(theta[:,0].size):
            for j in np.arange(theta[0,:].size):
                R = self.beam_pattern(theta[i,j],phi[i,j],[0,0,1])
                R += self.beam_pattern(theta[i,j],phi[i,j],[0,1,0])
                X[i,j] = R*np.sin(theta[i,j])*np.cos(phi[i,j])
                Y[i,j] = R*np.sin(theta[i,j])*np.sin(phi[i,j])
                Z[i,j] = R*np.cos(theta[i,j])
    #        X = np.arange(-1,1,.1)
    #        Y = np.arange(-1,1,.1)        
    #        X,Y = np.meshgrid(X,Y)
    #        theta = X.copy()
    #        phi   = X.copy()
    #        Z     = X.copy()
    #        for i in np.arange(X[:,0].size):
    #            for j in np.arange(Y[0,:].size):
    #                theta = np.arctan2(Y[i,j],X[i,j])
    #                phi   = 

        surf = ax.plot_surface(X, Y, Z, rstride=1, cstride=1, cmap=cm.jet,linewidth=0, antialiased=False)
        ax.set_zlim(0.0, 1.01)        
        ax.zaxis.set_major_locator(LinearLocator(10))
        ax.zaxis.set_major_formatter(FormatStrFormatter('%.02f'))

        fig.colorbar(surf, shrink=0.5, aspect=5)

        plt.show()

    def plot_beam_pattern(self,theta,pol=[0,1,0]):

        fig = plt.figure()

        phi = np.arange(0,2*np.pi,.05)
        R = 10*np.log10([self.beam_pattern(theta,x,pol) for x in phi])

        plt.plot(phi,R)
    #        plt.polar(phi,R)

        

    def beam_pattern_integrand(self,theta,phi,epol,x):
        """Used by Omega to calculate the beam pattern"""
        return self.beam_pattern(theta,phi,epol)*np.sin(theta)

    def Omega_gfun(self,y):
        """Lower Limit in theta integration used by Omega()"""
        return 0
    
    def Omega_hfun(self,y):
        """Upper Limit in theta integration used by Omega()"""
        return np.pi/2.0 - 20*np.pi/180 # Added "- 20*np.pi/180" Oct9

    def Omega(self):
        """Calculates the integrated beam (0<theta<pi/2). Assumes Peak power is directly overhead"""

        [O1,err1] = integrate.dblquad(self.beam_pattern_integrand,0,2*np.pi,self.Omega_gfun,self.Omega_hfun,([0,0,1],0))
        [O2,err2] = integrate.dblquad(self.beam_pattern_integrand,0,2*np.pi,self.Omega_gfun,self.Omega_hfun,([0,1,0],0))

        Peak_power = self.beam_pattern(0,0,[0,0,1]) + self.beam_pattern(0,0,[0,1,0])
    #        print O1,err1
    #        print O2,err2
    #        print Peak_power
        return (O1+O2)/Peak_power

    def H_gfun(self,y):
        """Lower Limit in theta integration used by H()"""
        return np.pi/2.0 - 10*np.pi/180
    
    def H_hfun(self,y):
        """Upper Limit in theta integration used by H()"""
        return np.pi/2.0 

    def H(self):
        """Calculates the integrated beam just over the horizon (pi/2 - 10*pi/180 <theta<pi/2). Assumes Peak power is directly overhead"""

        [O1,err1] = integrate.dblquad(self.beam_pattern_integrand,0,2*np.pi,self.H_gfun,self.H_hfun,([0,0,1],0))
        [O2,err2] = integrate.dblquad(self.beam_pattern_integrand,0,2*np.pi,self.H_gfun,self.H_hfun,([0,1,0],0))

        Peak_power = self.beam_pattern(0,0,[0,0,1]) + self.beam_pattern(0,0,[0,1,0])

        return (O1+O2)/Peak_power

    def Area(self):
        """Calculates the effective area of the telescope in m**2. Assumes symmetry between top and bottoms halfs of the beam pattern. This is only true if all antennas are in a plane."""
        return (speed_of_light*(1e-2)/(1e6*self.nu))**2.0/(2*self.Omega())

    def SEFD(self):
        """Calculate the sky equivalent flux density in Jy for the array assuming sky dominated noise"""

        kT = (1.3804e-23)*10000.0*(self.nu/38.0)**(-2.55)/(1e-26)
        
        return kT/self.Area()

    
    def add_antenna(self,antenna):
        self.antennas[len(self)] = antenna

    def set_all_voltages(self,V):
        for ant in self:ant.set_voltage(V)
        
    def set_frequency(self,nu):
        self.nu = nu
        for ant in self:
            ant.set_frequency(nu)
        self.coupling_matrix_calculated = False
        self.coupling_matrix = 0
        if(self.coupling_active):
            self.calculate_full_coupling_matrix()
            
        
    def energize_array(self,electric_field):
        for ant in self:
            ant.energize(electric_field)

    def power_down(self):
        for ant in self:
            ant.power_down()
        

class one_dipole(antenna_array):
    """An Array of One Dipole"""

    def __init__(self,pol_angle):
        antenna_array.__init__(self)

        ant = dipole_antenna([0,0,0], [np.cos(pol_angle),np.sin(pol_angle),0], 100.0)
        self.receiver_gain[ant]=1
        self.add_antenna(ant)


class two_dipole(antenna_array):
    """An Array of Two Dipoles"""

    def __init__(self,pol_angle,seperation=[350,0,0]):
        antenna_array.__init__(self)

        ant = dipole_antenna([0,0,0], [np.cos(pol_angle),np.sin(pol_angle),0], 100.0)
        self.receiver_gain[ant]=1
        self.add_antenna(ant)

        ant = dipole_antenna(seperation, [np.cos(pol_angle),np.sin(pol_angle),0], 100.0)
        self.receiver_gain[ant]=1
        self.add_antenna(ant)
        

class LoFASM(antenna_array):
    """LoFASM Antenna array class."""

    def __init__(self,r_inner=441,pol_angle=np.pi/2.0,N_antennas=6,delta_r=0,coupling=False,rot_angle=0.0):
        antenna_array.__init__(self)
        r_outer = np.sqrt(3.0)*r_inner        

        self.r_inner = r_inner
        self.r_outer = r_outer

        N = N_antennas
        dtheta = 2*np.pi/N

        array = np.zeros([2*N,3])
        polarization = np.zeros([2*N,3])

        phi = np.random.uniform(0,2.0*np.pi,N)
        dr    = np.sqrt(2.0*np.random.uniform(0,(delta_r**2)/2.0,N))
        for i in np.arange(0,N):
            dx = 0*dr[i]*np.cos(phi[i])
            dy = 0*dr[i]*np.sin(phi[i])
            ant = dipole_antenna([r_inner*np.cos(i*dtheta + rot_angle) + dx ,r_inner*np.sin(i*dtheta + rot_angle)+dy,0], [np.cos(pol_angle),np.sin(pol_angle),0], 200.0)
            self.receiver_gain[ant]=1
            self.add_antenna(ant)
            
        phi = np.random.uniform(0,2.0*np.pi,N)
        dr    = np.sqrt(2.0*np.random.uniform(0,(delta_r**2)/2.0,N))
        for i in np.arange(0,N):
            dx = 0*dr[i]*np.cos(phi[i])
            dy = 0*dr[i]*np.sin(phi[i])
            ant = dipole_antenna([r_outer*np.cos(i*dtheta + rot_angle + (np.pi)/(N)) + dx, r_outer*np.sin(i*dtheta + rot_angle + (np.pi)/(N)) + dy,0], [np.cos(pol_angle),np.sin(pol_angle),0], 200.0)
            self.receiver_gain[ant]=1
            self.add_antenna(ant)

        if(coupling):
            self.activate_coupling()
        

class LoFASM_ext(antenna_array):
    """LoFASM extended Antenna array class."""

    def __init__(self,r_inner=441.0,pol_angle=np.pi/2.0,N_antennas=6):
        antenna_array.__init__(self)
        r_outer = np.sqrt(3.0)*r_inner        

        N = N_antennas
        dtheta = 2*np.pi/N

        array = np.zeros([2*N,3])
        polarization = np.zeros([2*N,3])
    
        for i in np.arange(0,N):
            ant = dipole_antenna([r_inner*np.cos(i*dtheta),r_inner*np.sin(i*dtheta),0], [np.cos(pol_angle),np.sin(pol_angle),0], 100.0)
            self.receiver_gain[ant]=1
            self.add_antenna(ant)
            

        for i in np.arange(0,N):
            ant = dipole_antenna([r_outer*np.cos(i*dtheta + (np.pi)/(N)), r_outer*np.sin(i*dtheta + (np.pi)/(N)),0], [np.cos(pol_angle),np.sin(pol_angle),0], 100.0)
            self.receiver_gain[ant]=1
            self.add_antenna(ant)
        

        for i in np.arange(0,N):
            ant = dipole_antenna([2*r_inner*np.cos(i*dtheta),2*r_inner*np.sin(i*dtheta),0], [np.cos(pol_angle),np.sin(pol_angle),0], 100.0)
            self.receiver_gain[ant]=1
            self.add_antenna(ant)

        
class LoFASM_onering(antenna_array):
    """LoFASM Antenna array class with only one ring."""

    def __init__(self,r_inner=441,pol_angle=np.pi/2.0,N_antennas=6,delta_r=0,
                 delta_phase=0,rot_angle=0.0):
        antenna_array.__init__(self)

        N = N_antennas
        dtheta = 2*np.pi/N

        array = np.zeros([2*N,3])
        polarization = np.zeros([2*N,3])

        phi = np.random.uniform(0,2.0*np.pi,N)
        dr    = np.sqrt(2.0*np.random.uniform(0,(delta_r**2)/2.0,N))
        gain_phi = np.random.uniform(-delta_phase/2,delta_phase/2.0,N)*1j
        for i in np.arange(0,N):
            dx = 0*dr[i]*np.cos(phi[i])
            dy = 0*dr[i]*np.sin(phi[i])
            ant = dipole_antenna([r_inner*np.cos(i*dtheta + rot_angle) + dx ,
                                  r_inner*np.sin(i*dtheta + rot_angle)+dy,0],
                                 [np.cos(pol_angle),np.sin(pol_angle),0],
                                 100.)
            self.receiver_gain[ant]=1
            self.receiver_gain[ant] *= np.exp(gain_phi[i])
            self.add_antenna(ant)


class LoFASM_outrigger(antenna_array):
    """LoFASM Antenna array class with only an outrigger (no rings)."""

    def __init__(self,r_inner=441,pol_angle=np.pi/2.0,delta_r=0,
                 delta_phase=0,rot_angle=0.0):
        antenna_array.__init__(self)

        N = 1
        dtheta = 2*np.pi/N

        array = np.zeros([2*N,3])
        polarization = np.zeros([2*N,3])

        phi = np.random.uniform(0,2.0*np.pi,N)
        dr    = np.sqrt(2.0*np.random.uniform(0,(delta_r**2)/2.0,N))
        gain_phi = np.random.uniform(-delta_phase/2,delta_phase/2.0,N)*1j

        dx = 0*dr[0]*np.cos(phi[0])
        dy = 0*dr[0]*np.sin(phi[0])
        ant = dipole_antenna([0, 0, 0],
                             [np.cos(pol_angle),np.sin(pol_angle),0],
                             100.)
        self.receiver_gain[ant]=1
        self.receiver_gain[ant] *= np.exp(gain_phi[i])
        self.add_antenna(ant)
    

class phased_array_grid(antenna_array):
    """Phase Array class NxN uniform grid."""

    def __init__(self,dx=1,dy=1,pol_angle=np.pi/2.0,N_antennas_x=4,N_antennas_y=4,dipole_length=1.0):
        antenna_array.__init__(self)

        for i_x in np.arange(0,N_antennas_x):
            for i_y in np.arange(0,N_antennas_y):
                ant = dipole_antenna([i_x*dx,i_y*dy,0],[np.cos(pol_angle),np.sin(pol_angle),0],dipole_length)

                self.receiver_gain[ant]=1
                self.add_antenna(ant)
                
            

           

