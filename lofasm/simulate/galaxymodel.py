#Code for galaxy model generation

import numpy as np
import scipy as sp
import matplotlib.pyplot as plt
import matplotlib
import datetime
import healpy as hp
from astropy.time import Time
import sys, os
#Imports from simulate:
import sidereal #3rd party
import LoFASM_simulation_v3 as v3

class station(object):

    def __init__(self, name, lat, west_long, FOV_color=[0,0,0],
                 FOV_radius=23, time=0, frequency=20.0, config='',
                 rot_angle=0.0, pol_angle=8*np.pi/9.0,
                 horizon_cutoff_alt=0.0):

        self.name        = name
        self.lat         = [np.float(x) for x in lat]
        self.west_long   = [np.float(x) for x in west_long]

        self.FOV_color = FOV_color
        self.FOV_radius = FOV_radius
        self.frequency = frequency

        self.lat_degrees = (lat[0] + lat[1]/60.0 + lat[2]/3600.0)
        self.lat_radians = (lat[0] + lat[1]/60.0 + lat[2]/3600.0)*np.pi/180.0

        self.west_long_degrees = (west_long[0] + west_long[1]/60.0 + west_long[2]/3600.0)
        self.west_long_radians = (west_long[0] + west_long[1]/60.0 + west_long[2]/3600.0)*np.pi/180.0

        self.east_long_degrees = 360.0 - self.west_long_degrees
        self.east_long_radians = self.east_long_degrees*np.pi/180.0

        self.location = sidereal.LatLon(self.lat_radians,self.east_long_radians)

        self.FOV_collection = 0
        self.config = config
        self.horizon_cutoff_costheta = np.cos(np.pi/2 - horizon_cutoff_alt*np.pi/180.)
        
        if not type(time) == datetime.datetime:
            self.time = datetime.datetime.utcnow()
        else:
            self.time = time
        self.aa = sidereal.AltAz(0,0)
        # Read Haslam 408 MHz skymap
        self.hpmap = hp.read_map(os.path.join(os.path.dirname(__file__),
                                              "lambda_haslam408_dsds.fits.txt"),
                                 verbose=False)
        self.Rotator = hp.Rotator(coord=['C','G'])

        print "CONFIG: ", config
        if (config == 'inner' or config == 'outer'):
            radius = 441. if config == 'inner' else np.sqrt(3.)*441.
            self.lofasm = v3.LoFASM_onering(radius, rot_angle=rot_angle,
                                            pol_angle=pol_angle)
        elif config == '':
            self.lofasm = v3.LoFASM(441.0, rot_angle=rot_angle,
                                    pol_angle=pol_angle)

        self.lofasm.set_frequency(frequency)

    def lst(self):

        gst = sidereal.SiderealTime.fromDatetime(self.time)
        return gst.lst(self.east_long_radians)

    def gpower_integrand(self,theta,phi):
        """Use to calculate the total noise power due to the galaxy. Theta and phi are the zenith and az angles in radians. freq is in MHz"""

        wavelength = 299.9/self.frequency
        if(phi == 0): phi = .00001
        if(phi == np.pi): phi = np.pi - .00001

        self.aa.alt = np.pi/2.0 - theta
        self.aa.az  = np.pi/2.0 - phi

        coords = self.aa.raDec(self.__lst_current,self.location)

        coords = self.Rotator(np.pi/2 - coords.dec,coords.ra)

        Tsky = hp.get_interp_val(self.hpmap,coords[0],coords[1])*(self.frequency/408.0)**(-2.55)

        ans = self.lofasm.beam_pattern(theta,phi,[0,0,1])
        ans += self.lofasm.beam_pattern(theta,phi,[0,1,0]) 
        ans *= (Tsky*(1.3804e-23)/wavelength**2)/(1e-26)/2.0

        return ans

    def N_gfun(self,y):
        """Lower Limit in theta integration used by calcualte_gnoise()"""
        return 0.0

    def N_hfun(self,y):
        """Upper Limit in theta integration used by calculate_gnoise()"""
        return np.pi/2.0 - 10.0*np.pi/180


    def calculate_gnoise(self,t=-1,lst=False):
        '''
        if lst is false then t is treated as a datetime object in utc.
        otherwise t is a float indicating the lst in hours
        '''

        M = 30
        gasleg = np.polynomial.legendre.leggauss(M)
        locs = np.where(gasleg[0] > self.horizon_cutoff_costheta)
        cos_theta = gasleg[0][locs]

        phi = np.arange(0,2*np.pi,2*np.pi/(2.0*M))
        weights = gasleg[1][locs]
        weights *= np.pi/M

        O = 0

        # set __lst_current
        if not lst:
            utc = t
            if (utc == -1):
                self.__lst_current = self.lst() #Remove
            else:
			    t = sidereal.SiderealTime.fromDatetime(utc)
			    self.__lst_current = t.lst(self.east_long_radians)
        else: # lst==True
            self.__lst_current = sidereal.SiderealTime(t)

        for cos_theta1,weights1 in zip(cos_theta,weights):
            theta1 = np.arccos(cos_theta1)
            for phi1 in phi:
                O += weights1*self.gpower_integrand(theta1,phi1+1e-6)

        return O

    def calculate_gpowervslstarray(self,times,verbose=True,lst=False):

        power = []

        ge = "Generating models... "
        for hour in times:
            power.append(self.calculate_gnoise(t=hour,lst=lst)) #If "lst=", type(hour)==datetime.datetime is true.
            if verbose==True:
                p = (str((times.index(hour))*100/len(times)) + '%')
                if times.index(hour) == (len(times)-1):
                    p = "Done"
                sys.stdout.write("\r%s%s" % (ge,p))
                sys.stdout.flush()

        return power

def galaxy():
		"""Return a model of the power from the galaxy.

		The model is generated using Dr. Rick Jenet's galaxy model generation
		code.
		The timebins will match the res parameter of the calibrate class.
		"""
		rot_ang = 1
		pol_ang = 1


		time_array = [datetime.datetime(2017, 5, 25, 2, 0),
					  datetime.datetime(2017, 5, 26, 7, 0),
					  #~ datetime.datetime(2017, 5, 28, 1, 0),
					  #~ datetime.datetime(2017, 5, 30, 8, 0),
					  datetime.datetime(2017, 6, 4, 2, 0)]

		lfdic = {1:{'name':'LI', 'lat':[26,33,19.676], 'long':[97,26,31.174], 't_offset':6.496132851851852},
				 2:{'name':'LII', 'lat':[34,4,43.497], 'long':[107,37,5.819], 't_offset':7.174552203703703},
				 3:{'name':'LIII', 'lat':[38,25,59.0], 'long':[79,50,23.0], 't_offset':5.322648148148148},
				 4:{'name':'LIV', 'lat':[34,12,3.0], 'long':[118,10,18.0], 't_offset':7.87811111111111}}
		lfs = lfdic[4]
		long_radians = (lfs['long'][0] + lfs['long'][1]/60.0 + lfs['long'][2]/3600.0)*np.pi/180.0

		LoFASM = station(lfs['name'],lfs['lat'],lfs['long'],FOV_color='b',
						 time='',frequency=20.0,one_ring='inner',
						 rot_angle=rot_ang,pol_angle=pol_ang)
		innerNS_FOV = 0.61975795698554226 #LoFASM.lofasm.Omega()
		inner_conversion_NS = np.divide((np.power(np.divide(3.0*1.0e8,45.0e6),2)),(innerNS_FOV))

		print 'Stage 1/2 Done.'

		powe = np.multiply(LoFASM.calculate_gpowervslstarray(time_array),inner_conversion_NS)
		power = 10*np.log10(np.array(powe))
		print 'Stage 2/2 Done.'

		return power

#power = galaxy()
#plt.plot(power)
#plt.show()

#~ LoFASMI        = station('VLA',[26,33,19.676],[97,26,31.174],FOV_color='r')
#~ LoFASMI_inner  = station('VLA',[26,33,19.676],[97,26,31.174],FOV_color='r',one_ring='inner')
#~ LoFASMI_outer  = station('VLA',[26,33,19.676],[97,26,31.174],FOV_color='r',one_ring='outer')
#~ LoFASMII        = station('VLA',[34,4,43.497],[107,37,05.819],FOV_color='g')
#~ LoFASMII_inner  = station('VLA',[34,4,43.497],[107,37,05.819],FOV_color='g',one_ring='inner')
#~ LoFASMII_outer  = station('VLA',[34,4,43.497],[107,37,05.819],FOV_color='g',one_ring='outer')
#~ LoFASMIII       = station('GBT',[38,25,59.0],[79,50,23.0],FOV_color='b')
#~ LoFASMIII_inner = station('GBT',[38,25,59.0],[79,50,23.0],FOV_color='b',one_ring='inner')
#~ LoFASMIII_outer = station('GBT',[38,25,59.0],[79,50,23.0],FOV_color='b',one_ring='outer')
#~ LoFASMIV       = station('GST',[34,12,03.0],[118,10,18.0],FOV_color='bl')
#~ LoFASMIV_inner = station('GST',[34,12,03.0],[118,10,18.0],FOV_color='bl',one_ring='inner')
#~ LoFASMIV_outer = station('GST',[34,12,03.0],[118,10,18.0],FOV_color='bl',one_ring='outer')
#~ 
#~ 
#~ lfstations = {}
#~ 
#~ lfstations['LoFASMI'] = {}
#~ lfstations['LoFASMI']['full'] = LoFASMI
#~ lfstations['LoFASMI']['inner'] = LoFASMI_inner
#~ lfstations['LoFASMI']['outer'] = LoFASMI_outer
#~ 
#~ lfstations['LoFASMII'] = {}
#~ lfstations['LoFASMII']['full'] = LoFASMII
#~ lfstations['LoFASMII']['inner'] = LoFASMII_inner
#~ lfstations['LoFASMII']['outer'] = LoFASMII_outer
#~ 
#~ lfstations['LoFASMIII'] = {}
#~ lfstations['LoFASMIII']['full'] = LoFASMIII
#~ lfstations['LoFASMIII']['inner'] = LoFASMIII_inner
#~ lfstations['LoFASMIII']['outer'] = LoFASMIII_outer
