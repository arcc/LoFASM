#skysource.py

import numpy as np
import datetime
from station import nullStation, lofasmStation
from astropy.coordinates import SkyCoord, Angle, Longitude, Latitude
from ephem import FixedBody
import sidereal
import pytz


#class definitions
class SkySource(object):
    """SkySource class to store source coordinates and generate expected time delays.
    Time delay information corresponds to data taken in the LoFASM Outrigger mode. 
    Currently only useful for LoFASM 4 data.
    """

    def __init__(self, ra, dec, lofasm_station=nullStation(), unit='rad'):
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

        #setup ephem fixedbody object
        ra_hms = self.coord.ra.hms
        self.ephem = FixedBody()
        self.ephem._ra = "{}:{}:{}".format(ra_hms.h, ra_hms.m, ra_hms.s)
        self.ephem._dec = self.coord.dec.rad
        self.ephem._epoch = "2000"
        self.epoch = datetime.datetime(1899,12,31,12,0,0,tzinfo=pytz.utc)

    def setRA(self, ra=Longitude(0.0,'rad')):
        assert isinstance(ra, Longitude), 'ra must be a astropy.coordinates.angles.Longitude instance'
        self.coord = SkyCoord(ra.rad, self.coord.dec.rad)
        rahms = self.coord.ra.hms
        self.ephem._ra = "{}:{}:{}".format(rahms.h, rahms.m, rahms.s)

    def setDec(self, dec=Latitude(0.0,'rad')):
        assert isinstance(dec, Latitude), 'dec must be an instance of astropy.coordinates.angles.Latitude'
        self.coord = SkyCoord(self.coord.ra.rad, dec.rad)
        self.ephem._dec = self.coord.dec.rad

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

    def getDelays(self, times):
        '''
        compute the expected delay (in nanoseconds) for each lst value in times.

        only compatible with outrigger data.

        Parameters
        ----------

        times : iterable
            iterable containing LST times in *radians* for which to compute the delays

        Returns
        ----------

        numpy.ndarray containing the delay for each LST value in times. 
        delay values are in units of nanoseconds
        '''

        #check timestamp type
        if isinstance(times[0], datetime.datetime):
            lsts = np.array([self.station.lst(x) for x in times])
        else:
            lsts = np.array(times)

        RA = self.coord.ra.rad

        return self.station.outrigger_delay * ( self._A*np.sin(lsts-RA) + self._B*(self._C - self._D*np.cos(lsts-RA)) )

    def getDelayBins(self, times, binwidth_ns=10.0, offset=0):

        delays_ns = self.getDelays(times)
        result = [int(round(offset + -1*x/binwidth_ns)) for x in delays_ns]

        return result

    def AltAz(self, t, lofasm_station):

        try:
            if t.tzinfo is not pytz.utc:
                t = datetime.datetime(t.year, t.month, t.day, t.hour, t.minute, t.second, t.microsecond, tzinfo=pytz.utc)
        except AttributeError:
            raise TypeError, 'lofasm_station must be a datetime.datetime object'

        lofasm_station.observer.date = (t-self.epoch).total_seconds()/86400.0

        self.ephem.compute(lofasm_station.observer)

        return (self.ephem.alt, self.ephem.az)        

    def isVisible(self, t, lofasm_station=nullStation()):
        '''
        check to see if this source is visible by lofasm_station at time t

        parameters
        t : datetime.datetime
            timestamp
        lofasm_station : lofasm.station.lofasmStation
            object representing a lofasm station
        '''

        if lofasm_station.isNull:
            raise ValueError, 'lofasm_station must not be NULL.'
            return False

        alt, az = self.AltAz(t, lofasm_station)

#        alt_thresh = Angle(np.pi/2,'rad').rad - lofasm_station.FOV_radius.rad
        alt_thresh = lofasm_station.alt_min

        if Angle(self.ephem.alt.rad,'rad') >= alt_thresh:
            result = True
        else:
            result = False

        return result


    def getLightcurve(self, data, times, binwidth_ns=10.0, offset=0):
        '''
        return lightcurve for this source by extracting the power along 
        the corresponding sky-track from data.


        parameters
        data : numpy.ndarray 
            2d delay vs. time array
        times : list, np.ndarray, 
            1d timestamp array. if elements are datetime objects then they are converted to 
            LST radians. otherwise, it is assumed that LST in radians is being provided.
        binwidth_ns : float
            width of each delay bin in nanoseconds
        offset : int
            delay offset bin
            
        '''
        N = len(times)
        bins = self.getDelayBins(times, binwidth_ns, offset)

        lightcurve = np.zeros(N)

        for i in range(N):
            lightcurve[i] = data[bins[i], i]

        return lightcurve

    def riseNset(self, station=None):
        
        #Given the DEC, what is the hour angle of the half power point.

        if station:
            pass
        else:
            station = self.station

        if self.coord.dec.rad < station.minDec.rad or self.coord.dec.rad > station.maxDec.rad:
            raise ValueError, "Source must be within the FOV of {}.".format(statin.name)

        stationLat = station.lat.rad
        srcDec = self.coord.dec.rad
        Delta  = station.FOV_radius.rad
        cos_H = (np.cos(Delta) - np.sin(stationLat)*np.sin(srcDec))/(np.cos(stationLat)*np.cos(srcDec))
        #H is the hour angle
        H = np.arccos(cos_H)
        return Angle(H, unit='rad')
    def __repr__(self):
        return "SkySource object: RA={} rad, DEC={} rad".format(self.coord.ra.rad, self.coord.dec.rad)
