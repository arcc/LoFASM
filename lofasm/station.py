#station.py


from astropy.coordinates import EarthLocation, Latitude, Longitude, Angle
import numpy as np
from ephem import Observer
#import sidereal
import ephem


# LoFASM Station Coordinates
# in the ephem library, longitude coordinates are positive east
LoFASM1 = ephem.Observer()
LoFASM1.lat = "26:33:19.676"
LoFASM1.lon = "-97:26:31.174"
LoFASM2 = ephem.Observer()
LoFASM2.lat = "34:4:43.497"
LoFASM2.lon = "-107:37:5.819"
LoFASM3 = ephem.Observer()
LoFASM3.lat = "38:25:59.0"
LoFASM3.lon = "-79:50:23.0"
LoFASM4 = ephem.Observer()
LoFASM4.lat = "34:12:3.0"
LoFASM4.lon = "-118:10:18.0"
LoFASM_Stations = {}
LoFASM_Stations[1] = LoFASM1
LoFASM_Stations[2] = LoFASM2
LoFASM_Stations[3] = LoFASM3
LoFASM_Stations[4] = LoFASM4
for (k,v) in LoFASM_Stations.items():
    v.pressure = 0
    v.horizon = "65" #degrees


class lofasmStation(object):
    def __init__(self, name, lat, lon, rot_ang=Angle(0.0, 'rad'), elevation=0.0,outrigger_delay=0.0):


        if not isinstance(lat, Latitude):
            raise TypeError, 'lat must be an instance of astropy.coordinates.Latitude'
        elif not isinstance(lon, Longitude):
            raise TypeError, 'lon must be an instance of astropy.coordintes.Latitude'

        self.isNull = False
        self.name = name
        self.lat = lat
        self.lon = lon
        self.rot_ang = rot_ang
        self.FOV_radius = Angle(23, unit='deg')
        self.alt_min = Angle(90.0,'deg') - self.FOV_radius
        self.outrigger_delay = outrigger_delay

        #calculate range of declinations
        self.minDec = self.lat - self.FOV_radius
        self.maxDec = self.lat + self.FOV_radius

        #setup ephem.Observer representation
        self.observer = Observer()
        self.observer.lon = self.lon.deg.__str__()
        self.observer.lat = self.lat.deg.__str__()
        self.observer.elevation = elevation

    def inDecRange(self, d=Latitude(0.0,'rad')):
        assert isinstance(d, Latitude)

        if d.rad < self.minDec.rad or d.rad > self.maxDec.rad:
            return False
        else: 
            return True

    def lst(self, utc):
        gst = sidereal.SiderealTime.fromDatetime(utc)
        return gst.lst(self.lon.rad).radians

    def riseNset(self,RA,DEC):
        """Calculates the rise and set time of an object given its RA and DEC in radians. 
        Time is a datetime object. 
        beam_radius is radius of the lofasm beam pattern in degrees."""
        
        #Given the DEC, what is the hour angle of the half power point.
        delta1 = self.location.lat
        delta2 = DEC
        Delta  = self.FOV_radius*np.pi/180.0
        cos_H = (np.cos(Delta) - np.sin(delta1)*np.sin(delta2))/(np.cos(delta1)*np.cos(delta2))
        #H is the hour angle
        H = np.arccos(cos_H)
            
        risetime = (RA - self.lst().radians - H)
        settime  = (RA - self.lst().radians + H)

        if (risetime and settime) < 0:
            risetimed = risetime
            settimed = settime
        if (risetime and settime) > 0:
            risetimed = risetime
            settimed = settime
            
        if risetime < 0:
            risetime = risetime + (2*np.pi)
    
#       if (risetime and settime) < 0:
#           risetime = risetime + (2*np.pi)
#           settime = settime + (2*np.pi)
        
        return [risetime,settime,risetimed,settimed]

    def __repr__(self):
        return "<LoFASM Station {}, lat {} lon {}>".format(self.name, self.lat.rad, self.lon.rad)

class nullStation(lofasmStation):
    def __init__(self):
        '''
        empty lofasm station placeholder
        '''
        self.isNull = True
        lofasmStation.__init__(self, '', Latitude(0.0, 'deg'), Longitude(0.0, 'deg'))

    def __repr__(self):
        return "<Null Station {}, lat {} lon {}>".format(self.name, self.lat.rad, self.lon.rad)

    def __str__(self):
        return self.__repr__()
station={
    1: None,
    2: None,
    3: None,
    4: lofasmStation('LoFASM4',Latitude("35:14:50.0", "deg"), Longitude("-116:47:35.77", "deg"), -10.42 * np.pi/180, 748, 549.913767)
}
