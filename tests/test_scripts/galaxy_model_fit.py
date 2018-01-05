#!/usr/bin/env python

import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt
import numpy as np
import lofasm.calibrate.lofasmcal as lfc
from lofasm.handler import filelist, bbxfile, lofasmfile
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
    p.add_argument('stationid', type=int, choices=[1, 2, 3, 4],
                   help='station id')
    p.add_argument('--galaxymodel',
                   help="use galaxy model for fit. numpy format")
    p.add_argument('--savedata', action='store_true',
                   help='save fit data in numpy format')
    p.add_argument('--savegalaxymodel', action='store_true',
                   help="store the galaxy model in numpy format")
    p.add_argument('--lofasm', action='store_true',
                   help="process old style lofasm files")
    p.add_argument('--horizonalt', type=np.float64, default=0.0,
                   help="horizon cutoff altitude (degrees) for galaxy modeling")
    args = p.parse_args()
    pol = (args.pol).upper()
    freq = args.frequency

    stationid = args.stationid
    horizon_cutoff_alt = args.horizonalt
    if args.lofasm:
        dirPath = args.dataDir
        filelistobj = filelist.LofasmFileListHandler(dirPath)
    else:
        dirPath = os.path.join(args.dataDir, pol)
        filelistobj = filelist.BbxFileListHandler(dirPath, pol)
    sidereal_times = filelistobj.getSiderealTimes(stationid)
    N = filelistobj.nfiles
    freq_avg_min_ts = np.zeros(N, dtype=np.float64)
    dname = "freq_avg_min_timeseries_galaxy_fit_{}mhz_{}_{}_{}".format(freq,
                                                                       stationid,
                                                                       pol,
                                                                       filelistobj.file_start_mjds[0])
    print "\nReducing Data"
    for i in range(N):
        m = "Reducing {}/{} {}".format(i+1, N, filelistobj.flist[i])
        sys.stdout.write('\r'+m)
        sys.stdout.flush()
        if args.lofasm:
            freq_avg_min_ts[i] = lofasmfile.freq_averaged_minimum(filelistobj.flist[i], freq, pol)
        else:
            freq_avg_min_ts[i] = bbxfile.freq_averaged_minimum(filelistobj.flist[i], freq)

    if args.savedata:
        freq_avg_min_ts.tofile(dname+'_tsdata.numpy')
    print "\nGenerating Galaxy Model"
    if args.galaxymodel:
        print "Using {}".format(args.galaxymodel)
        galaxymodel = np.fromfile(args.galaxymodel)
    else:
        print "Generating model from scratch"
        galaxyobj = lfc.galaxy()
        dates = filelistobj.getMjdDatetimeList()
        galaxymodel = galaxyobj.galaxy_power_array(dates, freq, stationid, horizon_cutoff_alt)

    if args.savegalaxymodel:
        galaxymodel.tofile(dname+"_galmodeldata_horizon{}.numpy".format(horizon_cutoff_alt))

    params = lfc.fitter(freq_avg_min_ts, galaxymodel).popt
    timeseries_fit = (freq_avg_min_ts-params[1])/params[0]


    if args.savedata:
        timeseries_fit.tofile(dname+"_ts_fit_data_horizon{}.numpy".format(horizon_cutoff_alt))

    plotTitle = "LoFASM {} Average Power {} MHz, Horizon Cutoff Altitude={} deg".format(stationid, freq, horizon_cutoff_alt)

    min_loc = np.where(sidereal_times == min(sidereal_times))[0][0]
    galaxymodel = shiftLeft(galaxymodel, min_loc)
    timeseries_fit = shiftLeft(timeseries_fit, min_loc)
    sidereal_times = shiftLeft(sidereal_times, min_loc)
    
    plt.figure(figsize=(10,10))
    plt.title(plotTitle)
    #plt.grid()
    plt.plot(sidereal_times, 10*np.log10(galaxymodel), label='Galaxy Model')
    plt.plot(sidereal_times, 10*np.log10(timeseries_fit), label='Galaxy Fit')
    plt.xlim(0,24)
    plt.xlabel("LST")
    plt.ylabel("Power (dB, Arb. Ref.)")
    plt.legend()
    plt.savefig(dname+'_horizon{}.png'.format(horizon_cutoff_alt), format='png')
