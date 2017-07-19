#Calibration tool for LoFASM Data:
import os, sys
import lofasm.simulate.galaxymodel as gm
import numpy as np
#~ import matplotlib.pyplot as plt
import glob
import lofasm.bbx.bbx as bb
import lofasm.parse_data as pd
import datetime
import scipy.optimize
import datetime

class calibrate:
	"""	Class that contains and calibrates lofasm data.	

	Parameters
	----------
	files : str
		A path to lofasm `.bbx.gz` files. `*` wildcard can be used for multiple 
		files.
	station : {1, 2, 3, 4}
		The station from which the data comes from.
	freq : int or float, optional
		The frequency to calibrate at in megahertz (the default is 20.0 MHz).
	"""
	def __init__(self, files, station, freq=20.0):

		filelist = glob.glob(files)
		self.filelist = sorted(filelist)
		self.station = station
		self.freqmhz = freq
		self.freqbin = pd.freq2bin(freq)
		self.res = len(filelist)

		#~ date = self.filelist[0][-25:-17]
		#~ self.date = datetime.datetime(int(date[:4]),
									  #~ int(date[4:6]),
									  #~ int(date[-2:]), 0, 0)

		time_array = []
		station_array = []
		for i in range(len(self.filelist)):

			#~ if 'Clean_' in self.filelist[i]:
				#~ head = bb.LofasmFile(self.filelist[i]).header
				#~ file_startt = self.filelist[i][-22:-7]
				#~ file_station = head['station']

				#~ start_time = datetime.datetime.strptime(self.filelist[i][-22:-7],
																#~ '%Y%m%d_%H%M%S')

			#~ else:
			head = bb.LofasmFile(self.filelist[i]).header
			file_startt = head['start_time']
			file_station = head['station']
			start_time = datetime.datetime.strptime(file_startt[:-8],
													'%Y-%m-%dT%H:%M:%S')

			time_array.append(start_time)
			station_array.append(file_station)

		self.cali_array = [time_array, station_array]

		for i in reversed(range(len(self.filelist))):
			if self.cali_array[1][i] != str(self.station):
				del self.cali_array[0][i]
				del self.cali_array[1][i]

	def add_files(self, files):
		"""Add files to the calibrate class.

		New files are sorted, duplicates are ignored, header data is read, and 
		the file lists are appended together.

		Parameters
		----------
		files : str
			A path to lofasm `.bbx.gz` files. `*` wildcard can be used for multiple 
			files.
		"""
		new_filelist = glob.glob(files)

		for i in new_filelist:
			if i in self.filelist:
				new_filelist.remove(i)

		self.filelist = (self.filelist + new_filelist)
		self.filelist = sorted(self.filelist)

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

		for i in reversed(range(len(self.filelist))):
			if self.cali_array[1][i] != str(self.station):
				del self.cali_array[0][i]
				del self.cali_array[1][i]

	def chfreq(self, new_freq):
		"""Change to a new calibration frequency.

		Parameters
		----------
		new_freq : int or float
			The new frequency to work with in megahertz.
		"""
		self.freq = new_freq
		self.freqbin = pd.freq2bin(new_freq)

	def get_data(self):
		"""Return an array of lofasm data for however many files are loaded to
		calibrate class.

		Data from each file is appended to one data array after sorting
		regardless of contiguity.
		"""
		dsampled_power = []
		datachunk = []

		for filename in range(len(self.filelist)):

			dat = bb.LofasmFile(self.filelist[filename])
			dat.read_data()
			avg_10freq_bins = np.average(dat.data[self.freqbin-5:self.freqbin+5,:],
								   axis=0) ##Avg 10 bins around frequency
			avg_datafile_power = np.average(avg_10freq_bins)
			dsampled_power = np.append(dsampled_power, avg_datafile_power)

			#~ if (filename%100 == 0) or filename == 50:
			p = (str(filename*100/len(self.filelist)) + '%')
			sys.stdout.write("\r%s" % p)
			sys.stdout.flush()

		return dsampled_power

	def galaxy(self):
		"""Return an array of the modeled power from the galaxy.

		The model is generated using Dr. Fredrick Jenet's galaxy model generation
		script.
		The timebins will match the number of datafiles of the calibrate class.
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

		LoFASM = gm.station(lfs['name'],lfs['lat'],lfs['long'],FOV_color='b',
							time=time_array[0],frequency=self.freqmhz,one_ring='inner',
							rot_angle=rot_ang,pol_angle=pol_ang)
		innerNS_FOV = 0.61975795698554226 #LoFASM.lofasm.Omega()
		inner_conversion_NS = np.divide((np.power(np.divide(3.0*1.0e8,45.0e6),2)),(innerNS_FOV))

		for i in range(len(time_array)):	#Change starting times in UTC to LST
			time_array[i] = time_array[i] + datetime.timedelta(seconds=150)# Make model times == middle of file times

		power = np.multiply(LoFASM.calculate_gpowervslstarray(time_array),inner_conversion_NS)
		#~ power = 10*np.log10(np.array(power))
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


		if len(y0) != len(gbg):
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

		if type(gbg) == type(None):
			gbg = self.galaxy()

		if type(y0) == type(None):
			y0 = self.get_data()

		if len(y0) != len(gbg):
			raise Exception('Dimension mismatch: Array dimensions must be equal.')

		def fun(l,a,b):
			return a*np.array(gbg)+b

		popt,pcov = scipy.optimize.curve_fit(fun,l,y0)

		return popt

class calibrateio:
	"""	Class to read and calibrate raw data and write Calibrated files.

	Reads raw data from given path. Generates galaxy model and computes calibration.
	Writes Calibrated files to output path corresponding to each raw data file.
	Parameters
	----------
	files : str
		A path to lofasm `.bbx` files. `*` wildcard can be used for multiple 
		files.
	output : str
		A path were Calibrated files will be written to.
	station : {1, 2, 3, 4}
		The station from which the data comes from.
	freq : int or float, optional
		The frequency to calibrate at in megahertz (the default is 20.0 MHz).
	"""
	def __init__(self, files, output, station, freq=20.0):

		cal = calibrate(files, station, freq=freq)

		filelist = sorted(glob.glob(files))
		dat1 = bb.LofasmFile(filelist[0])
		dat1.read_data()
		avgfull = np.average(dat1.data[cal.freqbin-5:cal.freqbin+5, :],
							 axis=0) #First element of list of data arrays
		list_of_powers = [avgfull]#List of data arrays (2d)
		dat = np.average(list_of_powers[0]) #First element of dat array for calibration

		re = 'Reading data... '
		for filei in range(len(filelist)-1):

			filei += 1
			bbfile = bb.LofasmFile(filelist[filei])
			bbfile.read_data()
			### Preparing array containing full power of each file
			avgfull_power = np.average(bbfile.data[cal.freqbin-5:cal.freqbin+5, :],
										axis=0) ##Avg 10 bins around frequency
			list_of_powers.append(avgfull_power)

			### Preparing data array for calibration: Each datapoint is avg power of file
			avg_datafile_power = np.average(avgfull_power)
			dat = np.append(dat, avg_datafile_power)

			p = ((str(filei*100/len(filelist)) + '%') + ' - ['+str(filei+1)+' out of '+str(len(filelist))+' files]')
			if filei not in range(len(filelist)-1):
				p = 'Done                                                   \n'
			sys.stdout.write("\r%s%s" % (re,p))
			sys.stdout.flush()

		# print "Generating models... " done by calibration_pmts f'n
		calibration_pmts = cal.calibration_parameters(data=dat)

		sys.stdout.write('\rCalibrating and writing files... ')
		if output[-1] != '/':
			output += '/'

		for i in range(len(filelist)):
			filename = os.path.basename(filelist[i])

			calname = (output + 'Calibrated_' + filename)
			calibrated = (list_of_powers[i]-calibration_pmts[1])/calibration_pmts[0]			
			lfc = bb.LofasmFile(output + 'Calibrated_' + filename, mode = 'write')
			lfc.add_data(calibrated)
			lfc.write()
			lfc.close()

		sys.stdout.write('\rDone - '+str(len(filelist))+' calibrated files written.')
		sys.stdout.flush()

#~ x = calibrate('/home/alex22x/bin/lofasm/LoFASM_3_Data/20170204/20170204_00*_CC.bbx.gz', 4, freq=20.0)
