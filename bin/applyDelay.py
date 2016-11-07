#!/usr/local/opt/python/bin/python2.7

import numpy as np
import sidereal
from time import time
import sys
from astropy.coordinates import SkyCoord
from lofasm.station import lofasmStation
import datetime


east_long_radians = 4.243069944523414
lat_radians = 0.6183119763398577
lofasm4_outrigger_distance = 549.913767 #nanoseconds
#td_bin = 10 #ns
rot_ang = -10.42 * np.pi/180
cable_offset_bins = 580


# function definitions

def shiftWaterfall(data, timestamps, RA, DEC, td_bin, orientation='left'):
    assert(type(orientation) == str), 'orientation must be a string: left or right'
    assert(orientation.lower()=='left' or orientation.lower()=='right'), 'choices for orientation are left and right'
    
    shiftedData = np.zeros(np.shape(data))

    if orientation == 'left':
        o = -1
    elif orientation == 'right':
        o = 1
    else:
        raise ValueError()
    factor = o/float(td_bin)

    for i in range(len(timestamps)):
        delay_ns = delay(RA,DEC,timestamps[i], rot_ang)
#        delay_bins = o * delay_ns / float(td_bin)
        delay_bins = factor * delay_ns
        shiftedData[:,i] = shift(data[:,i], delay_bins)

    return shiftedData

def calcDelays(RA, DEC, rot_ang, timestamps):
    '''
    returns array of delay values in nanoseconds
    '''

    #initialize empty array
    delays_ns = np.zeros(len(timestamps))

    for i in range(len(timestamps)):
        delays_ns[i] = delay(RA, DEC, timestamps[i], rot_ang)
    return delays_ns

def calcDelays2(RA, DEC, rot_ang, timestamps):
    '''
    yields delay values in nanoseconds
    '''

    for i in range(len(timestamps)):
        yield delay(RA, DEC, timestamps[i], rot_ang)

def calcDelays3(params, RA, DEC, rot_ang, timestamps):
    '''
    returns array of delay values in nanoseconds
    '''

    for i in range(len(timestamps)):
        d = delay2(params, RA, timestamps[i])
        yield d


def delay(RA, DEC, utc, rot_ang=rot_ang):
    return lofasm4_outrigger_distance * (np.cos(DEC)*np.sin(lst(utc)-RA)*np.cos(rot_ang) + np.sin(rot_ang)*(np.sin(DEC)*np.cos(lat_radians)-np.cos(DEC)*np.sin(lat_radians)*np.cos(lst(utc)-RA)))

def delay2(params, RA, lst_rads):
    A,B,C,D = params
    return lofasm4_outrigger_distance * ( A*np.sin(lst_rads-RA) + B*(C - D*np.cos(lst_rads-RA)) )

def getDelayParams(DEC):
    A = np.cos(DEC) * np.cos(rot_ang)
    B = np.sin(rot_ang)
    C = np.sin(DEC)*np.cos(lat_radians)
    D = np.cos(DEC)*np.sin(lat_radians)

    return (A,B,C,D)
def lst(utc):
    gst = sidereal.SiderealTime.fromDatetime(utc)
    return gst.lst(east_long_radians).radians
def shift(y, s):
    '''
    shift array y by n bins cyclically
    '''

    s = int(s)
    N = len(y)
    result = np.zeros(N)

    if s > 0:
        result[:N-s] = y[s:]
        result[N-s:] = y[:s]
    elif s < 0:
        s = -1 * s
        result[:s] = y[N-s:]
        result[s:] = y[:N-s]
    elif s == 0:
        result = y
    return result

def shift2d(y, s):
    '''
    shift 2d array y by n bins cyclically along x axis
    '''

    s = int(s)
    N = len(y[0,:])
    result = np.zeros(np.shape(y))

    if s > 0:
        result[:,:N-s] = y[:,s:]
        result[:,N-s:] = y[:,:s]
    elif s < 0:
        s = -1 * s
        result[:,:s] = y[:,N-s:]
        result[:,s:] = y[:,:N-s]
    elif s == 0:
        result = y
    return result

#class definitions
class SkySource(object):
    """SkySource class to store source coordinates and generate expected time delays.
    Time delay information corresponds to data taken in the LoFASM Outrigger mode. 
    Currently only useful for LoFASM 4 data.
    """

    def __init__(self, ra, dec, lofasm_station, unit='rad'):
        '''
        initialize the source sky coordinates.

        Parameters
        ------------

        ra : float
            right ascension. can be either in units of radians or degrees. 

        dec : float
            declination. can be either in units of radians or degrees.

        unit : str, optional
            the unit of ra and dec (either 'rad' or 'deg'). 
            ra and dec must have the same unit.

        lofasm_station : lofasm.station.lofasmStation
            the LoFASM Station object representing a particular LoFASM station
        '''

        if not isinstance(lofasm_station, lofasmStation):
            raise TypeError, 'lofasmStation must be an instance of lofasm.station.lofasmStation'

        self.coord = SkyCoord(ra, dec, unit=unit)
        self.station = lofasm_station

        self._calcDelayParams()

    def _calcDelayParams(self):
        '''
        calculate the time-independent factors needed to calculate source delay times
        '''
        DEC = self.coord.dec.rad
        rot_ang = self.station.rot_ang
        lat_radians = self.station.lat.rad

        self._A = np.cos(DEC) * np.cos(rot_ang)
        self._B = np.sin(rot_ang)
        self._C = np.sin(DEC)*np.cos(lat_radians)
        self._D = np.cos(DEC)*np.sin(lat_radians)

        del DEC, rot_ang, lat_radians

    def getDelays(self, lsts):
        '''
        compute the expected delay (in nanoseconds) for each lst value in lsts.

        only compatible with outrigger data.

        Parameters
        ----------

        lsts : iterable
            iterable containing LST times in *radians* for which to compute the delays

        Returns
        ----------

        numpy.ndarray containing the delay for each LST value in lsts. 
        delay values are in units of nanoseconds
        '''

        #check timestamp type
        if isinstance(lsts[0], datetime.datetime):
            lsts = np.array([lst(x) for x in lsts])
        else:
            lsts = np.array(lsts)

        RA = self.coord.ra.rad

        return lofasm4_outrigger_distance * ( self._A*np.sin(lsts-RA) + self._B*(self._C - self._D*np.cos(lsts-RA)) )

    def getDelayBins(self, lsts, binwidth_ns=10.0, offset=0):

        delays_ns = self.getDelays(lsts)
        result = [int(round(offset + -1*x/binwidth_ns)) for x in delays_ns]

        return result

    def getLightcurve(self, data, lsts, binwidth_ns=10.0, offset=0):
        '''
        return lightcurve for this source by extracting the power along 
        the corresponding sky-track from data.
        '''
        N = len(lsts)
        bins = self.getDelayBins(lsts, binwidth_ns, offset)

        lightcurve = np.zeros(N)

        for i in range(N):
            lightcurve[i] = data[bins[i], i]

        return lightcurve
    def __repr__(self):
        return "SkySource object: RA={} rad, DEC={} rad".format(self.coord.ra.rad, self.coord.dec.rad)


if __name__ == "__main__":
    import argparse
    import os, sys
    import pickle
    import platform
    if platform.system() == "Linux":
        import matplotlib
        matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.ticker import FuncFormatter, FixedLocator
    parser = argparse.ArgumentParser()
    parser.add_argument('input', help='path to input file')
    parser.add_argument('ra', help='Right Ascension of the source in radians', type=float)
    parser.add_argument('dec', help='Declination of the source in radians', type=float)
    parser.add_argument('-o', '--output', help='name of output file', default='out.corrected2d')
    parser.add_argument('--orientation',
                        help='direction in which to apply the delay. right or left. default is left',
                        type=str, choices=['left','right'], default='left')


    args = parser.parse_args()
    assert os.path.exists(args.input)

    infile = args.input
    RA = args.ra
    DEC = args.dec
    output = args.output

    #load .delay2d data
    with open(infile, 'rb') as f:
        fdict = pickle.load(f)
        binwidth = fdict['binwidth']
        data = fdict['data']
        timestamps = fdict['timestamps']
    


    print "RA: {} rad. Dec: {} rad. time resolution: {} ns".format(RA, DEC, binwidth)
    shiftedData = shiftWaterfall(data, timestamps, RA, DEC, binwidth, args.orientation)
    avg = shiftedData.sum(1)

    output_dict = {
        'data': shiftedData,
        'timestamps': timestamps,
        'binwidth': binwidth,
    }


    with open("{}.corrected2d".format(output) if not output.endswith('.corrected2d') else output, 'wb') as f:
        print "writing {}".format(f.name)
        pickle.dump(output_dict, f)

    print binwidth

    def lst_tick(x, pos):
        hour = (lst(timestamps[int(x)]) * 180 / np.pi ) / 15
        minute = (hour - int(hour)) * 60.0
        second = (minute - int(minute)) * 60.0
        return "{:2d}h{:2d}m{:2.3f}s".format(int(hour), int(minute), second)

    fig, ax = plt.subplots()
    ax.xaxis.set_major_formatter(FuncFormatter(lst_tick))
    ax.xaxis.set_major_locator(FixedLocator(np.linspace(0,len(timestamps)-1,5)))
    ax.set_title(output)
    ax.imshow(10*np.log10(shiftedData), aspect='auto')
    plt.grid()

    fig.savefig(output.rstrip('.png') + '.png')
    fig.savefig("{}.png".format(output) if not output.endswith('.png') else output)    
