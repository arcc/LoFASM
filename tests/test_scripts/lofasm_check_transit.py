#! /usr/bin/env python2.7

from lofasm.station import LoFASM_Stations
import ephem
import numpy as np
from pytz import timezone as tz


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('sourceRA', help='''Right Ascension format "HH:MM:SS"''')
    p.add_argument('sourceDEC', help='''Declinatoin format "DD:MM:SS"''')
    p.add_argument('date',
                   help='''Date to check. format: "YYYY/MM/DD"''')
    p.add_argument('time',
                   help='''Time to check. format: "HH:MM:SS"''')
    p.add_argument('stationid', type=int,
                   choices=[1,2,3,4], help="Station ID")
    args = p.parse_args()
    

    utc = tz("UTC")
    source = ephem.FixedBody()
    source._ra = ephem.hours(args.sourceRA)
    source._dec = ephem.degrees(args.sourceDEC)
    
    lfstation = LoFASM_Stations[args.stationid]
    lfstation.date = args.date + ' ' + args.time

    rise_t = lfstation.next_rising(source)
    set_t = lfstation.next_setting(source)

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
    
    
    

