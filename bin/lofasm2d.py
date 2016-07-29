#!/usr/bin/env python


import matplotlib
matplotlib.use("TkAgg")
from lofasm import parse_data as pdat
from lofasm import parse_data_H as pdat_H
import matplotlib.pyplot as plt
import numpy as np
from lofasm import filter
import sidereal
from datetime import datetime
from time import time

east_long_radians = 4.243069944523414
lat_radians = 0.6183119763398577
lofasm4_outrigger_distance = 549.913767 #nanoseconds
td_bin = 10 #ns
rot_ang = -10.42 * np.pi/180


if __name__ == "__main__":
    import argparse
    import os, sys
    import pickle
    parser = argparse.ArgumentParser()
    parser.add_argument("filelist",
                        help="file containing paths to lofasm files to process. one on each line.")
    parser.add_argument("polarization",
                        help="choice of polarization to process", type=str)
    parser.add_argument('-c', '--cadence', help="process every Nth sample. default is 10", type=int, default=10)
    parser.add_argument('-k','--stride', help="median filter stride. default is 5", type=int, default=5)
    parser.add_argument('-o', '--output',help="output file. default is 'out'", default='out.lofasm2d')
    parser.add_argument('-hf', help="max frequency (MHz). default is 100.0", type=float, default=100.0)
    parser.add_argument('-lf', help="min frequency (MHz). default is 0.0", type=float, default=0.0)
    parser.add_argument('-p', help="save 2d plot", action='store_true')
    args = parser.parse_args()


    
    assert os.path.exists(args.filelist) #ensure input filelist exists
    assert args.hf <= 100.0
    assert args.lf >= 0.0

    #output file name
    fout = open("{}_{}{}".format(args.output,args.polarization.upper(), ".lofasm2d") \
                if not args.output.endswith('.lofasm2d') else args.output,'wb')
    
    #parse input filelist
    with open(args.filelist, 'r') as f:
        flist = [x.rstrip('\n') for x in f if x.rstrip('\n').endswith('.lofasm') and not x.startswith('#')]

    Nfiles = len(flist)
    Tsamp = pdat.getSampleTime(8192)
    dur_sec = 300.0 #file duration in seconds
    cadence = args.cadence
    medfilt_stride = args.stride
    #pol = args.polarization.upper()
    MAXSIZE = int(Nfiles * dur_sec / Tsamp / cadence) + 1
    HBIN = pdat.freq2bin(args.hf)
    LBIN = pdat.freq2bin(args.lf)
    Nbins = HBIN - LBIN
    print "bins: ({}, {}), BW: {}".format(HBIN,LBIN, args.hf-args.lf)


    #initialize data array in memory
    data = np.zeros((Nbins,MAXSIZE))
    timestamps = []

    print "shape of initialized array: {}".format(np.shape(data))

    #loop over files and extract necessary samples
    i=0
    dfft = np.zeros(Nbins, dtype=np.complex) #initialize placeholder
    enterDataset = time()
    for f in flist:
        try:
            enterLoop = time()
            print "{}/{} processing {}".format(flist.index(f), len(flist), f),
            sys.stdout.flush()
            crawler = pdat.LoFASMFileCrawler(os.path.join(os.path.dirname(args.filelist), f))        
            crawler.open()
            crawler.setPol(args.polarization.upper())
            n = crawler.getNumberOfIntegrationsInFile() / cadence
            timestamps.append(crawler.time.datetime)

            dfilt = filter.medfilt(np.conj(crawler.get()[LBIN:HBIN]), medfilt_stride)
            dfft_raw = np.fft.fft(dfilt)
            dfft[:Nbins/2] = dfft_raw[Nbins/2:]
            dfft[Nbins/2:] = dfft_raw[:Nbins/2]
            data[:,i] = np.abs(dfft)**2

            
            i+=1
            for k in range(n-1):
                crawler.forward(cadence)
                timestamps.append(crawler.time.datetime)
                
                dfilt = filter.medfilt(np.conj(crawler.get()[LBIN:HBIN]), medfilt_stride)
                dfft_raw = np.fft.fft(dfilt)
                dfft[:Nbins/2] = dfft_raw[Nbins/2:]
                dfft[Nbins/2:] = dfft_raw[:Nbins/2]
                data[:,i] = np.abs(dfft)**2
                
                i+=1
            exitLoop = time()
            print "\t {}s".format(exitLoop - enterLoop)
        except pdat_H.IntegrationError:
            print "encountered bad data: skipping {}".format(f)
            sys.stdout.flush()
            pass
    exitDataset = time()
    print "Processed entire dataset in {}s".format(exitDataset - enterDataset)

    #truncate whitespace
    data = data[:,:len(timestamps)]
    
    pickle.dump((data,timestamps),fout)
    fout.close()


    if args.p:
        fig = plt.figure()
        plt.title(args.output)
        plt.imshow(10*np.log10(data), aspect='auto')
        plt.xlabel('sample')
        plt.ylabel('delay')
        plt.grid()        
        fig.savefig(args.output.rstrip('.png') + ".png")

        
    del data
        
    
