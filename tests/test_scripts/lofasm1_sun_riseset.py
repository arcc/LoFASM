#! /usr/bin/env python2.7

LOFASM1_LAT = "26:33:19.58"  # degrees, arcmin, arcsec
LOFASM1_LON = "-97:26:31.11"  # degrees, arcmin, arcsec


if __name__ == "__main__":
    import ephem
    import numpy as np
    from pytz import timezone as tz

    central = tz("US/Central")
    utc = tz("UTC")
    
    s = ephem.Sun()
    m = ephem.Mars()
    cyga = ephem.FixedBody()
    cyga._ra = ephem.hours("19:59:28.3566")
    cyga._dec = ephem.degrees("40:44:02.096")
    
    lofasm1 = ephem.Observer()
    lofasm1.lat = LOFASM1_LAT
    lofasm1.lon = LOFASM1_LON
    lofasm1.date = "2017/11/03 06:00"  # midnight, UTC date

    rise_t = lofasm1.next_rising(cyga)
    set_t = lofasm1.next_setting(cyga)

    # fix taken from https://github.com/AaronParsons/dishpaper/blob/master/beam-gsm-cyga_response_code/CygA_func.py
    if set_t < rise_t:
        set_t = ephem.Date(set_t + 1)
        set_t = ephem.Date(set_t + ephem.minute * -4.)
    
    nextriseutc = utc.localize(rise_t.datetime())
    nextsetutc = utc.localize(set_t.datetime())

    
    dt = set_t - rise_t
    midpointutc = ephem.Date(rise_t + dt/2)
    print nextriseutc
    print nextsetutc
    print "transit duration is {}".format(nextsetutc - nextriseutc)
    print "the midpoint is {}".format(midpointutc)
    
    
    

