#!/usr/bin/env python

import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt
import numpy as np
import lofasm.calibrate.lofasmcal as lfc
from lofasm.handler import filelist, bbxfile
from lofasm.parse_data import Baselines
import sys, os
from lofasm.station import LoFASM_Stations

def shiftLeft(d, s):
    '''
    shift data by s steps to the left
    '''

    N = len(d)
    dshift = np.zeros_like(d)
    dshift[:N-s] = d[s:]
    dshift[N-s:] = d[:s]
    return dshift

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('dataDir', help='path to data directory')
    p.add_argument('frequency', type=np.float64, help='frequency')
    p.add_argument('pol', help='polarization')
    p.add_argument('stationid', type=int, choices=[1,2,3,4], help='station id')
    p.add_argument('--galaxymodel', help="use galaxy model for fit. numpy format")
    p.add_argument('--savedata', action='store_true', help='save fit data in numpy format')
    args = p.parse_args()
    pol = (args.pol).upper()
    freq = args.frequency
    dirPath = os.path.join(args.dataDir, pol)
    stationid = args.stationid
    bbxfilelist = filelist.BbxFileListHandler(dirPath, pol)
    sidereal_times = bbxfilelist.getSiderealTimes(stationid)
    N = bbxfilelist.nfiles
    freq_avg_min_ts = np.zeros(N, dtype=np.float64)

    print "\nReducing Data"
    for i in range(N):
        m = "Reducing {}/{} {}".format(i+1, N, bbxfilelist.flist[i])
        sys.stdout.write('\r'+m)
        sys.stdout.flush()
        freq_avg_min_ts[i] = bbxfile.freq_averaged_minimum(bbxfilelist.flist[i], freq)

    print "\nGenerating Galaxy Model"
    if args.galaxymodel:
        print "Using {}".format(args.galaxymodel)
        galaxymodel = np.fromfile(args.galaxymodel)
    else:
        print "Generating model from scratch"
        galaxyobj = lfc.galaxy()
        dates = bbxfilelist.getMjdDatetimeList()
        galaxymodel = gal.galaxy_power_array(dates, freq, stationid)

    params = lfc.fitter(freq_avg_min_ts, galaxymodel).popt
    timeseries_fit = (freq_avg_min_ts-params[1])/params[0]

    dname = "freq_avg_min_timeseries_galaxy_fit_{}mhz_{}_{}".format(freq, stationid, pol)
    if args.savedata:
        timeseries_fit.tofile(dname+".numpy")

    plotTitle = "LoFASM {} Average Power {} MHz".format(stationid, freq)

    min_loc = np.where(sidereal_times == min(sidereal_times))[0][0]
    galaxymodel = shiftLeft(galaxymodel, min_loc)
    timeseries_fit = shiftLeft(timeseries_fit, min_loc)
    sidereal_times = shiftLeft(sidereal_times, min_loc)
    
    plt.figure(figsize=(10,10))
    plt.title(plotTitle)
    plt.grid()
    plt.plot(sidereal_times, 10*np.log10(galaxymodel), label='Galaxy Model')
    plt.plot(sidereal_times, 10*np.log10(timeseries_fit), label='Galaxy Fit')
    plt.xlim(0,24)
    plt.xlabel("LST")
    plt.ylabel("Power (Arb. Ref.)")
    plt.legend()
    plt.savefig(dname+'.png', format='png')
