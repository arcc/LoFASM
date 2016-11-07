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
        return "<LoFASM Station {}, lat {} lon {}".format(self.name, self.lat.rad, self.lon.rad)

class nullStation(lofasmStation):
    def __init__(self):
        lofasmStation.__init__(self, '', Latitude(0.0, 'deg'), Longitude(0.0, 'deg'))
    def __repr__(self):
        return "<Null Station {}, lat {} lon {}".format(self.name, self.lat.rad, self.lon.rad)
    def __str__(self):
        return self.__repr__()
station={
    1: None,
    2: None,
    3: None,
    4: lofasmStation('LoFASM4',Latitude("35:14:50.0", "deg"), Longitude("-116:47:35.77", "deg"), -10.42 * np.pi/180)
}