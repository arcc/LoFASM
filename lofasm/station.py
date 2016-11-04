#station.py


from astropy.coordinates import EarthLocation, Latitude, Longitude
import numpy as np


class lofasmStation(object):
	def __init__(self, name, lat, lon, rot_ang=0.0):

		if not isinstance(lat, Latitude):
			raise TypeError, 'lat must be an instance of astropy.coordinates.Latitude'
		elif not isinstance(lon, Longitude):
			raise TypeError, 'lon must be an instance of astropy.coordintes.Latitude'
		self.name = name
		self.lat = lat
		self.lon = lon
		self.rot_ang = rot_ang
	def __repr__(self):
		return "<LoFASM Station {}, lat {} lon {}".format(self.name, self.lat.rad, self.lon.rad)


station={
	1: None,
	2: None,
	3: None,
	4: lofasmStation('LoFASM4',Latitude("35:14:50.0", "deg"), Longitude("-116:47:35.77", "deg"), -10.42 * np.pi/180)
}