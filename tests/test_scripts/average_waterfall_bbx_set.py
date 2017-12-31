#! /usr/bin/env python
import sys, os
import matplotlib
import numpy as np
matplotlib.use('agg')
import matplotlib.pyplot as plt
from lofasm.bbx import bbx
from lofasm.parse_data import freq2bin
from glob import glob
import json

def averageFileSpectra(f):
    '''Calculate average spectra in file
    '''
    lfx = bbx.LofasmFile(f)
    lfx.read_data()
    if lfx.iscplx:
        result = np.average(np.abs(lfx.data)**2, axis=1)
    else:
        result = np.average(lfx.data, axis=1)
    return result

if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument('datasetdir', type=str, help="path to dataset directory")
    p.add_argument('--savedata', action='store_true',
                   help='Save a copy of the resulting data array as a numpy file')
    args = p.parse_args()

    flist = glob(os.path.join(args.datasetdir, "*.bbx.gz"))
    flist.sort()

    lfx = bbx.LofasmFile(flist[0])
    pol = lfx.header['channel']
    lfx.close()

    data = np.zeros((1024, len(flist)), dtype=np.float64)
    for i in range(len(flist)):
        re = "Processing {}/{}".format(i+1,len(flist))
        sys.stdout.write("\r"+re)
        sys.stdout.flush()
        avgSpectra = averageFileSpectra(flist[i])
        data[:,i] = avgSpectra

    if args.savedata:
        with open('waterfall_out_data_freqvtime_{}.numpy'.format(pol), 'w') as f:
            data.tofile(f)

    plt.figure()
    plt.title("L1 Avg. PvF over Time")
    plt.imshow(10*np.log10(data), aspect='auto')
    plt.savefig('waterfall_{}.png'.format(pol), format='png')
    
