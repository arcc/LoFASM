#! /usr/bin/env python2.7

'''
script to check the coverage of an object at a
LoFASM station.
'''

if __name__ == "__main__":
    import argparse
    import numpy as np
    from numpy import float64
    import ephem
    from lofasm.bbx import bbx
    from datetime import datetime
    from astropy.time import Time

    parser = argparse.ArgumentParser()
    parser.add_argument("stationid", choices=[1,2,3,4], type=int,
                        help="LoFASM Station ID")
    parser.add_argument('-mjd', action='store_true',
                        help="if active then read date as an mjd float")
    parser.add_argument("date", type=str,
                        dest='date',
                        help="UTC date to check for coverage as %Y/%m/%d")
    parser.add_argument("right ascension", type=float64, dest='ra',
                        help="Right ascension of source")
    parser.add_argument("Declination", type=float64, dest='dec',
                        help="Declination of source")
    args = parser.parse_args()

    # currently designed to read start time from bbx file
    # header in the format: %Y%m%d_%H%M%S
    # in the future this will have to changed to handle the correct format

    fpath = "/data0/testcalib/20171103_061809_AA.bbx.gz"
    lfx = bbx.LofasmFile(fpath)
    hdr_start_time = lfx.header['start_time']
    
