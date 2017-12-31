#! /usr/bin/env python

'''
construct a time series of the data set by taking the average power in a frequency band
and taking the minimum value over a 5 minutes time span.
'''

import sys, os
import matplotlib
import numpy as np
matplotlib.use('agg')
import matplotlib.pyplot as plt
from lofasm.bbx import bbx
from lofasm.parse_data import freq2bin
from glob import glob
from copy import deepcopy
from lofasm.handler import bbxfile, lofasmfile

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('dataDir', type=str, help='path to data directory')
    p.add_argument('frequency', nargs='+', help='center frequency')
    p.add_argument('bandwidth', type=float, help='bandwidth to average')
    p.add_argument('--savedata', action='store_true',
                   help='save data as numpy file')
    p.add_argument('--lofasm', action='store_true',
                   help='set to process old lofasm files')
    p.add_argument('--pol', help='polarization. ignored unless --lofasm is set')
    args = p.parse_args()

    freqlist = [float(x) for x in args.frequency]
    freqlist.sort()
    flist = glob(os.path.join(args.dataDir, '*.bbx.gz'))
    flist.sort()
    
    N = len(flist)

    # get polarization
    if not args.lofasm:
        lofasm_mode = False
        lfx = bbx.LofasmFile(flist[0])
        pol = lfx.header['channel']
        lfx.close()
    else:
        lofasm_mode = True
        pol = (args.pol).upper()
    
    freqVTime = np.zeros((len(freqlist), N), dtype=np.float64)

    # loop over files
    for i in range(N):
        re = "Processing {}/{}".format(i+1, N)
        sys.stdout.write('\r'+re)
        sys.stdout.flush()
        if lofasm_mode:
            freqVTime[:,i] = lofasmfile.freq_averaged_minimum(flist[i],
                                                              freqlist,
                                                              pol,
                                                              args.bandwidth)
        else:
            freqVTime[:,i] = freq_averaged_minimum(flist[i], freqlist, args.bandwidth)

    if args.savedata:
        for i in range(len(freqlist)):
            d = freqVTime[i]
            d.tofile('freqAvgMinTimeSeries{}MHz_{}.numpy'.format(str(freqlist[i]), pol))


    plt.figure()
    for freq in freqlist:
        plt.title('frequency averaged timeseries {}MHz {}'.format(str(freq),pol))
        plt.plot(10*np.log10(freqVTime[freqlist.index(freq),:]), label='averaged time series')
        plt.legend()
        plt.savefig('frequency_averaged_minimum_timeseries_{}MHz_{}.png'.format(freq, pol), format='png')
        plt.clf()

