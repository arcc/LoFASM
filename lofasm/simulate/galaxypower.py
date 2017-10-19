#! python
# Galaxy power model generation tool

import numpy as np
import sys
import datetime
import healpy as hp
import sidereal
import LoFASM_simulation_v3 as v3

class station(object):

	def __init__(self,lat,west_long,FOV_color=[0,0,0],FOV_radius=23,time=0,frequency=20.0,one_ring=False,rot_angle=0.0,pol_angle=8*np.pi/9.0):

		#self.name = name
		self.lat =       [np.float(x) for x in lat]
		self.west_long = [np.float(x) for x in lat]

		self.frequency = frequency

		self.lat_radians =       (lat[0] + lat[1]/60.0 + lat[2]/3600.0)*np.pi/180.0
		self.west_long_radians = (west_long[0] + west_long[1]/60.0 + west_long[2]/3600.0)*np.pi/180.0
		self.east_long_radians = 2*np.pi - self.west_long_radians

		self.location = sidereal.LatLon(self.lat_radians, self.east_long_radians)

		if not type(time) == datetime.datetime:
			self.time = datetime.datetime.utcnow()
		else:
			self.time = time

		self.aa = sidereal.AltAz(0,0)

		self.hpmap = hp.read_map(raw_input('Path to skymap?'), verbose=False) #Automate this - include skymaps in package?
		self.Rotator = hp.Rotator(coord=['C','G']) #If skymap is lambda Haslam

		self.lofasm = v3.LoFASM(441.0, rot_angle=rot_angle, pol_angle=pol_angle)
		self.lofasm.set_frequency(frequency)

	def gpower_integrand(self, theta, phi):

		wavelength = 299.9/self.frequency
		if (phi == 0):     phi = 0.00001
		if (phi == np.pi): phi = np.pi - 0.00001

		self.aa.alt = np.pi/2.0 - theta
		self.aa.az  = np.pi/2.0 - phi

		coords = self.aa.raDec(self.__lst_current, self.location)
		coords = self.Rotator(np.pi/2 - coords.dec, coords.ra) #if Haslam

		Tsky = hp.get_interp_val(self.hpmap, coords[0], coords[1])*(self.frequency/408.0)**(-2.55) #if Haslam

		ans = self.lofasm.beam_pattern(theta, phi, [0,0,1])
		ans += self.lofasm.beam_pattern(theta, phi, [0,1,0])
		ans *= (Tsky*(1.380e-23)/wavelength**2)/(1e-26)/2.0

		return ans

	def calculate_gnoise(self,utc):

		M = 30
		gasleg = np.polynomial.legendre.leggauss(M)
		locs = np.where(gasleg[0] > 0)
		cos_tetha = gasleg[0][locs]

		phi = np.arange(0,2*np.pi,2*np.pi/(2.0*M))
		weights = gasleg[1][locs]
		weights *= np.pi/M

		O = 0
		t = sidereal.SiderealTime.fromDatetime(utc)
		self.__lst_current = t.lst(self.east_long_radians)

		for cos_tetha1, weights1 in zip(cos_theta, weights):
			theta1 = np.arccos(cos_theta1)
			for phi1 in phi:
				O += weights1*self.gpower_integrand(theta1, phi1+1e-6)

		return O

	def calculate_gpowervslstarray(self, time_array, lst=''):

		power = []
		utc = utc_time

		ge = 'Generating models... '
		for hour in utc:
			power.append(self.calculate_gnoise(utc=hour))
			p = (str((utc.index(hour))*100/len(utc)) + '%')
			if utc.index(hour) == (len(utc)-1):
				p = 'Done'
			sys.stdout.write('\r%s%s' % (ge, p))
			sys.stdout.flush()

		return power

