#Calibration tool for LoFASM Data:

import lofasm_tools as lt
import numpy as np
import matplotlib.pyplot as plt
import glob
import lofasm.bbx.bbx as bb
import datetime
import scipy.optimize

class calibrate:
	"""	Class that contains and calibrates lofasm data.	

	Parameters
	----------
	files : str
		A path to lofasm `.bbx.gz` files. `*` wildcard can be used for multiple files.
	station : {1, 2, 3, 4}
		The station from which the data comes from.
	freq : int or float, optional
		The frequency to calibrate at in megahertz (the default is 20.0 MHz).
	res : int, optional
		The ammount of datapoints to downsample to (the default is 100).
	"""
	def __init__(self, files, station, freq=20.0, res=100):

		filelist = glob.glob(files)
		self.filelist = sorted(filelist)
		self.station = station
		self.freq = float(freq*10)
		self.res = len(filelist)

		date = self.filelist[0][-25:-17]
		self.date = datetime.datetime(int(date[:4]),
									  int(date[4:6]),
									  int(date[-2:]), 0, 0)

		time_array = []
		station_array = []
		for i in range(len(self.filelist)):
			head = bb.LofasmFile(self.filelist[i]).header
			file_startt = head['start_time']
			file_station = head['station']

			start_time = datetime.datetime.strptime(file_startt[:-8],
													'%Y-%m-%dT%H:%M:%S')
			time_array.append(start_time)
			station_array.append(file_station)
		self.cali_array = [time_array, station_array]

	#~ def add_files(self, files):
#~ 
		#~ 

	#~ def chfreq(self, new_freq):
#~ 
		#~ self.freq = int(new_freq*10.0)

	def get_data(self, dsample=True):
		"""Return an array of lofasm data for however many files are loaded to
		calibrate class.

		Data from each file is appended to one data array after sorting
		regardless of contiguity.

		Parameters
		----------
		dsample : bool
		"""
		data_power = []
		datachunk = []

		for filename in range(len(self.filelist)):

			dat = bb.LofasmFile(self.filelist[filename])
			dat.read_data()
			data_power = np.append(data_power,
								   np.average(dat.data[self.freq-5:self.freq+5,:],
								   axis=0)) ##Avg 10 bins around freq
			if (filename%5 == 0):
				print str(filename*100/len(self.filelist)) + '%'

		if dsample:
			for i in range(len(data_power)):
				modul = len(data_power)%self.res
				R = (len(data_power)-modul)/self.res
				data_power = data_power[modul:].reshape(-1,R).mean(axis=1)

		return data_power

	def galaxy(self):
		"""Return a model of the power from the galaxy.

		The model is generated using Dr. Rick Jenet's galaxy model generation
		code.
		The timebins will match the res parameter of the calibrate class.
		"""
		rot_ang = 1
		pol_ang = 1

		time_array = self.cali_array[0]

		lfdic = {1:{'name':'LI', 'lat':[26,33,19.676], 'long':[97,26,31.174], 't_offset':6.496132851851852},
				 2:{'name':'LII', 'lat':[34,04,43.497], 'long':[107,37,5.819], 't_offset':7.174552203703703},
				 3:{'name':'LIII', 'lat':[38,25,59.0], 'long':[79,50,23.0], 't_offset':5.322648148148148},
				 4:{'name':'LIV', 'lat':[34,12,3.0], 'long':[118,10,18.0], 't_offset':7.87811111111111}}
		lfs = lfdic[self.station]
		long_radians = (lfs['long'][0] + lfs['long'][1]/60.0 + lfs['long'][2]/3600.0)*np.pi/180.0

		LoFASM = lt.station(lfs['name'],lfs['lat'],lfs['long'],FOV_color='b',
							time=self.date,frequency=self.freq,one_ring='inner',
							rot_angle=rot_ang,pol_angle=pol_ang)
		innerNS_FOV = 0.61975795698554226 #LoFASM.lofasm.Omega()
		inner_conversion_NS = np.divide((np.power(np.divide(3.0*1.0e8,45.0e6),2)),(innerNS_FOV))

		for i in range(len(time_array)):	#Change starting times in UTC to LST
			time_array[i] = time_array[i]# - datetime.timedelta(hours=lfs['t_offset']) ##Check if this timedelta is needed!
		#~ print 'Stage 1/2 Done.'

		powe = np.multiply(LoFASM.calculate_gpowervslstarray(time_array),inner_conversion_NS)
		#~ power = 10*np.log10(np.array(powe))
		print 'Done.'

		return power

	def calibrate_data(self, data=None, galaxy=None):
		"""Returns array of calibrated data.

		It fits data to a galaxy model and retrieves scaling and offset
		calibration parameters.
		The calibration parameters are applied to the data for calibration.

		Parameters
		----------
		data : numpy.ndarray, optional
			Data array of raw lofasm data to be calibrated.
			If not specified, calibrate.get_data() is used instead.
		galaxy : numpy.ndarray, optional
			Galaxy model array for data to be fitted against.
			If not specified, calibrate.galaxy() is used instead.
		See Also
		--------
		calibration_parameters : Returns only the calibration parameters.
		"""
		y0 = data
		gbg = galaxy
		l = range(self.res)
		if galaxy == None:

			gbg = self.galaxy()

		if data == None:

			y0 = self.get_data()


		if len(data) != len(galaxy):
			raise Exception('Dimension mismatch: Array dimensions must be equal.')

		def fun(l,a,b):
			return a*np.array(gbg)+b

		popt,pcov = scipy.optimize.curve_fit(fun,l,y0)

		fitted = (y0-popt[1])/popt[0]

		return fitted

	def calibration_parameters(self, data=None, galaxy=None):
		"""Returns the calibration parameters.

		Returns numpy array, `[a,b]`, where a is the scaling factor and b is
		the offset.

		It fits data to a galaxy model and retrieves scaling and offset
		calibration parameters.
		The calibration parameters are applied to the data for calibration.

		Parameters
		----------
		data : numpy.ndarray, optional
			Data array of raw lofasm data to be calibrated.
			If not specified, calibrate.get_data() is used instead.
		galaxy : numpy.ndarray, optional
			Galaxy model array for data to be fitted against.
			If not specified, calibrate.galaxy() is used instead.
		Raises
		------
		Exception
			If the dimensions of data and galaxy arrays do not match.
		See Also
		--------
		calibrate_data : Returns array of calibrated data.
		"""
		y0 = data
		gbg = galaxy
		l = range(self.res)

		if galaxy == None:
			gbg = self.galaxy()

		if data == None:
			y0 = self.get_data()

		if len(data) != len(galaxy):
			raise Exception('Dimension mismatch: Array dimensions must be equal.')

		def fun(l,a,b):
			return a*np.array(gbg)+b

		popt,pcov = scipy.optimize.curve_fit(fun,l,y0)

		return popt

#~ x = calibrate('/home/alex22x/bin/lofasm/LoFASM_3_Data/20170204/20170204_00*_CC.bbx.gz', 4, freq=20.0)
#~ x.res = 4
#~ print f
