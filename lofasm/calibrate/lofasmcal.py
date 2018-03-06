#Calibration tool for LoFASM Data:
import numpy as np
import sys, os
import glob
import datetime
import scipy.optimize

import lofasm.simulate.sidereal as sidereal
import lofasm.bbx.bbx as bb
import lofasm.parse_data as pd
import lofasm.simulate.galaxymodel as gm

class data_handler(object):
    def __init__(self):
        """Reads lofasm files and outputs data ready for calibration.
        """
        self.filelist = []
        self.times_array = []
        self.freq_bin = []
        self.data = []

    def read_files(self, files, freq, verbose=True):
        """Creates data attribute using the minimum value in frequency and time
           for each file.
        """
        self.freqmhz = freq
        self.filelist = sorted(glob.glob(files))

        #Remove non lofasm files from filelist
        for f in reversed(self.filelist):
            if not bb.is_lofasm_bbx(f):
                self.filelist.remove(f)

        re = 'Reading data...'
        for i in range(len(self.filelist)):
            f = bb.LofasmFile(self.filelist[i])
            head = f.header
            startt = head['start_time']
            timebins = head['metadata']['dim1_len']
            timelength = float(head['dim1_span'])

            # Convert header start_time to datetime object
            # ================TODO=====================================
            # Due to a bug some LoFASM data has messed up start times.
            # What follows is a hotfix so that this library can support
            # both time formats. In the future, the bug should be fixed
            # and this library should only have to support 1 time format.
            # 
            # The following loop tries each format specified in fmts.
            # If the time is parsed correctly (and does not throw an
            # exception) then the loop will be broken.
            # ==========================================================
            fmts = ["%Y-%m-%dT%H:%M:%S",  # correct time format for bbx files
                    "%Y%m%d_%H%M%S"]  # additional format found in LoFASM I files
            startt_repr = startt[:-8] if 'T' in startt else startt
            for fmt in fmts:
                try:
                    time_obj = datetime.datetime.strptime(startt_repr, fmt)
                    break
                except ValueError:
                    pass
            else:
                print "Cannot parse start time header field {}".format(startt_repr)


            # Find the frequency bin corresponding to the given frequency
            bw = (float(head['dim2_span'])/1000000.0)/head['metadata']['dim2_len']
            freqbin = int((self.freqmhz-(float(head['dim2_start'])/1000000.0))/bw)
            self.freq_bin = np.append(self.freq_bin, freqbin)

            f.read_data()
            freqbin_range = 10 #bins around specified 'freq' to read
            freqbins = f.data[freqbin-freqbin_range/2:freqbin+freqbin_range/2,:]
            min_vals_per_timebin = [np.min(x) for x in np.rot90(freqbins, k=-1)]
            min_file_val = np.min(min_vals_per_timebin)
            f.close()

            # Compute datetime of the selected timebin
            index = min_vals_per_timebin.index(min_file_val)
            seconds_into_file = (float(index)/timebins)*timelength
            seconds_into_file = datetime.timedelta(seconds=seconds_into_file)
            time_from_bin = time_obj + seconds_into_file

            self.data = np.append(self.data, min_file_val)
            self.times_array = np.append(self.times_array, time_from_bin)

            if verbose == True:
                p = (str(i*100/len(self.filelist)) + '%')
                if i+1 not in range(len(self.filelist)):
                    p = 'Done'
                sys.stdout.write("\r%s%s" % (re,p))
                sys.stdout.flush()

    def read_files_avg(self, files, freq, verbose=True):
        """Creates data attribute by averaging over a frequency bin range,
           then taking minimum value for each file.
        """
        self.freqmhz = freq
        self.filelist = sorted(glob.glob(files))

        for f in reversed(self.filelist): #Remove non lofasm files from filelist
            if not bb.is_lofasm_file(f):
                self.filelist.remove(f)

        re = 'Reading data...'
        for i in range(len(self.filelist)):
            f = bb.LofasmFile(self.filelist[i])
            head = f.header
            startt = head['start_time']
            timebins = head['metadata']['dim1_len']
            timelength = float(head['dim1_span'])

            # Convert header start_time to datetime object
            time_obj = datetime.datetime.strptime(startt[:-8],'%Y-%m-%dT%H:%M:%S')
            self.times_array = np.append(self.times_array, time_obj)
            # Find the frequency bin corresponding to the given frequency [Mhz]
            bw = (float(head['dim2_span'])/1000000.0)/head['metadata']['dim2_len']
            freqbin = int((self.freqmhz-(float(head['dim2_start'])/1000000.0))/bw)
            self.freq_bin = np.append(self.freq_bin, freqbin)

            f.read_data()
            freqbin_range = 10
            freqbins = f.data[freqbin-freqbin_range/2:freqbin+freqbin_range/2,:]
            freqavg = np.average(freqbins, axis=0)
            # min_vals = [np.min(x) for x in np.rot90(freqbins, k=-1)]
            min_file_val = np.min(freqavg)
            f.close()

            # Compute datetime of the selected timebin
            index = min_vals_per_timebin.index(min_file_val)
            seconds_into_file = (float(index)/timebins)*timelength
            seconds_into_file = datetime.timedelta(seconds=seconds_into_file)
            time_from_bin = time_obj + seconds_into_file

            self.data = np.append(self.data, min_file_val)
            self.times_array = np.append(self.times_array, time_from_bin)

            if verbose==True:
                p = (str(i*100/len(self.filelist)) + '%')
                if i+1 not in range(len(self.filelist)):
                    p = 'Done'
                sys.stdout.write("\r%s%s" % (re,p))
                sys.stdout.flush()

    def read_times(self, files):

        self.filelist = sorted(glob.glob(files))
        for f in reversed(self.filelist): #Remove non lofasm files from filelist
            if not bb.is_lofasm_file(f):
                filelist.remove(f)

        for i in range(len(self.filelist)):
            f = bb.LofasmFile(self.filelist[i])
            startt = f.header['start_time']
            time_obj = datetime.datetime.strptime(startt[:-8],'%Y-%m-%dT%H:%M:%S')
            self.times_array = np.append(self.times_array, time_obj)
            f.close()

    def gen_chunks(self, filelist, chunk_length):
        """Takes a calibration time in hours and returns
        """


class galaxy(object):
    def __init__(self):

        self.rot_ang = 1
        self.pol_ang = 1

        self.lfdic = {1:{'name':'LI', 'lat':[26,33,19.676],
                         'long':[97,26,31.174], 't_offset':6.496132851851852},
                      2:{'name':'LII', 'lat':[34,4,43.497],
                         'long':[107,37,5.819], 't_offset':7.174552203703703},
                      3:{'name':'LIII', 'lat':[38,25,59.0],
                         'long':[79,50,23.0], 't_offset':5.322648148148148},
                      4:{'name':'LIV', 'lat':[34,12,3.0],
                         'long':[118,10,18.0], 't_offset':7.87811111111111}}

    def galaxy_power_array(self, time_array, freq, stationID, horizon_cutoff=0.0, config='', verbose=True,lst=False):

        time_list = list(time_array)  # Convert nparray to list - for %age
        lfs = self.lfdic[stationID]
        long_radians = (lfs['long'][0] + lfs['long'][1]/60.0 + lfs['long'][2]/3600.0)*np.pi/180.0

        LoFASM = gm.station(lfs['name'], lfs['lat'], lfs['long'],
                            FOV_color='b',
                            frequency=freq, config=config,
                            rot_angle=self.rot_ang, pol_angle=self.pol_ang,
                            horizon_cutoff_alt=horizon_cutoff)
        FOV = LoFASM.lofasm.Omega()
        conversion = np.divide((np.power(np.divide(3.0*1.0e8,45.0e6),2)),(FOV))

        power = np.multiply(LoFASM.calculate_gpowervslstarray(time_list, verbose=verbose,lst=lst),conversion)
        return power


class fitter(object):
    def __init__(self, data, galaxy):

        l = len(data)

        def fun(l,a,b):
            return a*np.array(galaxy)+b
        # popt = optimal parameters, pcov = estimated covariance of popt
        self.popt, self.pcov = scipy.optimize.curve_fit(fun,l,data)

    def cal_pars(self):

        return self.popt

class chunk(object):
    def __init__(self, path):

        directory = os.path.abspath(path)
        self.filelist = sorted(glob.glob(os.path.join(directory,'*.bbx*')))

        # for f in reversed(self.filelist): #Remove non lofasm files from filelist
        #     if not bb.is_lofasm_file(f):
        #         filelist.remove(f)

class galaxymodel(object):
    pass

class calibrate(object):
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
    def __init__(self, files, station, freq=20.0, chan='CC'):

        filelist = glob.glob(files)
        self.filelist = sorted(filelist)
        self.station = station
        self.chan = chan
        self.freqmhz = freq
        self.res = len(filelist)

        time_array = []
        station_array = []
        freqbin_array = []

        for i in range(len(self.filelist)):

            head = bb.LofasmFile(self.filelist[i]).header
            file_startt = head['start_time']
            file_station = head['station']
            file_pol = head['channel']
            start_time = datetime.datetime.strptime(file_startt[:-8],
                                                    '%Y-%m-%dT%H:%M:%S')
            bw = (float(head['dim2_span'])/1000000.0)/head['metadata']['dim2_len']
            freqbin = int((self.freqmhz-(float(head['dim2_start'])/1000000.0))/bw)
            time_array.append(start_time)
            station_array.append(file_station)
            freqbin_array.append(freqbin)

        self.cali_array = [time_array, station_array]
        self.freqbins = freqbin_array

        for i in reversed(range(len(self.filelist))):
            if self.cali_array[1][i] != str(self.station):
                del self.cali_array[0][i]
                del self.cali_array[1][i]

        lfdic = {1:{'name':'LI', 'lat':[26,33,19.676], 'long':[97,26,31.174], 't_offset':6.496132851851852},
                 2:{'name':'LII', 'lat':[34,4,43.497], 'long':[107,37,5.819], 't_offset':7.174552203703703},
                 3:{'name':'LIII', 'lat':[38,25,59.0], 'long':[79,50,23.0], 't_offset':5.322648148148148},
                 4:{'name':'LIV', 'lat':[34,12,3.0], 'long':[118,10,18.0], 't_offset':7.87811111111111}}
        self.lfs = lfdic[station]

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
                del self.filelist[i]

    def chfreq(self, new_freq):
        """Change to a new calibration frequency.

        Parameters
        ----------
        new_freq : int or float
            The new frequency to work with in megahertz.
        """
        self.freq = new_freq
        self.freqbin = pd.freq2bin(new_freq)

    def get_data(self, minimum=True):
        """Return an array of lofasm data for however many files are loaded to
        calibrate class.

        Data from each file is appended to one data array after sorting
        regardless of contiguity.
        """
        dsampled_power = []
        datachunk = []
        re = 'Reading data... '
        for filename in range(len(self.filelist)):

            dat = bb.LofasmFile(self.filelist[filename])
            dat.read_data()
            avg_10freq_bins = np.average(dat.data[self.freqbins[filename]-5:self.freqbins[filename]+5,:],
                                         axis=0) ##Avg 10 bins around frequency
            if minimum == True:
                lowest_datafile_power = avg_10freq_bins.min()
                dsampled_power = np.append(dsampled_power, lowest_datafile_power)
            else:
                avg_datafile_power = np.average(avg_10freq_bins)
                dsampled_power = np.append(dsampled_power, avg_datafile_power)

            p = (str(filename*100/len(self.filelist)) + '%')
            if filename+1 not in range(len(self.filelist)):
                p = 'Done'
            sys.stdout.write("\r%s%s" % (re,p))
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

        long_radians = (self.lfs['long'][0] + self.lfs['long'][1]/60.0 + self.lfs['long'][2]/3600.0)*np.pi/180.0

        LoFASM = gm.station(self.lfs['name'],self.lfs['lat'],self.lfs['long'],FOV_color='b',
                            time=time_array[0],frequency=self.freqmhz,one_ring=False,
                            rot_angle=rot_ang,pol_angle=pol_ang)
        innerNS_FOV = LoFASM.lofasm.Omega() #0.61975795698554226
        inner_conversion_NS = np.divide((np.power(np.divide(3.0*1.0e8,45.0e6),2)),(innerNS_FOV))

        for i in range(len(time_array)):
            time_array[i] = time_array[i] + datetime.timedelta(seconds=150)# Make model times == middle of file times

        power = np.multiply(LoFASM.calculate_gpowervslstarray(time_array),inner_conversion_NS)

        return power

    def interpol_galaxy(self):
        """Return galaxy model array from pregenerated model file.
        """
        g = os.path.join(os.path.dirname(os.path.realpath(__file__)), '170204_gal.txt')
        t = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'times_hrs.txt')
        gall = np.loadtxt(g) #[20-70 MHz in 5 MHz increments]
        sidereal_model_t = np.loadtxt(t)

        west_long_deg = (self.lfs['long'][0] + self.lfs['long'][1]/60.0 + self.lfs['long'][2]/3600.0)
        east_long_deg = 360.0 - west_long_deg
        elr = east_long_deg*np.pi/180.0

        utc_data_t = self.cali_array[0]
        sidereal_data_t = []

        for i in utc_data_t:
            t = sidereal.SiderealTime.fromDatetime(i)
            sidereal_data_t.append(t.lst(elr).hours)

        freqchans = {20.0:0,25.0:1,30.0:2,35.0:3,40.0:4,45.0:5,50.0:6,55.0:7,60.0:8,65.0:9,70.0:10}
        power = []

        for i in range(len(sidereal_data_t)):
            for j in range(len(sidereal_model_t)-1):
                if sidereal_data_t[i] >= sidereal_model_t[j] and sidereal_data_t[i] <= sidereal_model_t[j+1]:
                    dt = sidereal_model_t[j+1]-sidereal_model_t[j]
                    half_bin = sidereal_model_t[j] + (dt/2.0)
                    if sidereal_data_t[i] < half_bin:
                        timebin = j
                    elif sidereal_data_t[i] >= half_bin:
                        timebin = j+1
                    power.append(gall[freqchans[self.freqmhz]][timebin])
                    print timebin
                    break

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
        if type(gbg) == type(None):

            gbg = self.galaxy()

        if type(y0) == type(None):

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

class calibrateio(object):
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
    def __init__(self, files, output, station, freq=20.0, ):

        cal = calibrate(files, station, freq=freq)

        filelist = sorted(glob.glob(files))
        dat1 = bb.LofasmFile(filelist[0])
        dat1.read_data()
        avgfull = np.average(dat1.data[cal.freqbins[0]-5:cal.freqbins[0]+5, :],
                             axis=0) #First element of list of data arrays
        list_of_powers = [avgfull]#List of data arrays (2d)
        dat = np.average(list_of_powers[0]) #First element of dat array for calibration

        re = 'Reading data... '
        for filei in range(len(filelist)-1):

            filei += 1
            bbfile = bb.LofasmFile(filelist[filei])
            bbfile.read_data()
            ### Preparing array containing full power of each file
            avgfull_power = np.average(bbfile.data[cal.freqbins[filei]-5:cal.freqbins[filei]+5, :],
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
        # if output[-1] != '/':
        # 	output += '/'

        output = os.path.abspath(output)
        cp_filepath = os.path.join(output, 'calibration_'+str(int(cal.freqmhz))+'mhz.txt')
        cp = []
        for i in range(len(filelist)):
            filename = os.path.basename(filelist[i])

            file_cp = [filename, cal.freqmhz, calibration_pmts[0], calibration_pmts[1]]
            cp = np.append(cp,file_cp)

        # np.savetxt(cp_filepath, cp, fmt=)

        # for i in range(len(filelist)):
        # 	filename = os.path.basename(filelist[i])

        # 	calname = (output + 'Calibrated_' + filename)
        # 	calibrated = (list_of_powers[i]-calibration_pmts[1])/calibration_pmts[0]			
        # 	lfc = bb.LofasmFile(output + 'Calibrated_' + filename, mode = 'write')
        # 	lfc.add_data(calibrated)
        # 	lfc.write()
        # 	lfc.close()

        sys.stdout.write('\rDone - '+str(len(filelist))+' calibration parameters \n written to '+cp_filepath)
        sys.stdout.flush()


