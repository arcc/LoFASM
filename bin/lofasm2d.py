#!/usr/bin/env python
#file: lofasm2d.py
#author: Louis Dartez

import platform
if platform.system() == "Linux":
    import matplotlib
    matplotlib.use("Agg")
from lofasm import parse_data as pdat
from lofasm import parse_data_H as pdat_H
import matplotlib.pyplot as plt
from matplotlib.ticker import FixedLocator, FuncFormatter
import numpy as np
from lofasm import filter
import sidereal
from datetime import datetime
from time import time

east_long_radians = 4.243069944523414
lat_radians = 0.6183119763398577
lofasm4_outrigger_distance = 549.913767 #nanoseconds
td_bin = 10 #ns, TODO: this is only the case for BW=100MHz!!!
rot_ang = -10.42 * np.pi/180 #adjusts for the alignment of outrigger/fullstation system


#functions
def lst(utc):
    gst = sidereal.SiderealTime.fromDatetime(utc)
    return gst.lst(east_long_radians).radians

if __name__ == "__main__":
    import argparse
    import os, sys
    import pickle

    description = '''lofasm2d.py: Read LoFASM Data and create 2d timelapse plot.
    This script will output the 2d data array as a pickle serial file as well as 
    plot the data and save it in PNG format.
    '''
    
    parser = argparse.ArgumentParser(description=description)
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
    assert args.hf <= 100.0 #frequency range, MHz
    assert args.lf >= 0.0

    #output file
    fout = open("{}_{}{}".format(args.output,args.polarization.upper(), ".lofasm2d") \
                if not args.output.endswith('.lofasm2d') else args.output,'wb')
    
    #parse input filelist
    with open(args.filelist, 'r') as f:
        #only take files which end in ".lofasm" and are not commented out with '#'
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


    #initialize complex data array in memory
    data = np.zeros((Nbins,MAXSIZE), dtype=np.complex)
    timestamps = []

    print "shape of initialized array: {}".format(np.shape(data))

    #loop over files and extract necessary samples
    i=0
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

            #apply median filter
            dfilt = filter.medfilt(crawler.get()[LBIN:HBIN], medfilt_stride)

            #dfft_raw = np.fft.fft(dfilt)
            #dfft[:Nbins/2] = dfft_raw[Nbins/2:]
            #dfft[Nbins/2:] = dfft_raw[:Nbins/2]
            #data[:,i] = np.abs(dfft)**2

            data[:,i] = dfilt #complex array
            
            i+=1
            for k in range(n-1):
                crawler.forward(cadence)
                timestamps.append(crawler.time.datetime)
                dfilt = filter.medfilt(np.conj(crawler.get()[LBIN:HBIN]), medfilt_stride)

                #dfft_raw = np.fft.fft(dfilt)
                #dfft[:Nbins/2] = dfft_raw[Nbins/2:]
                #dfft[Nbins/2:] = dfft_raw[:Nbins/2]

                #data[:,i] = np.abs(dfft)**2
                data[:,i] = dfilt
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

    output = {
        'data': data,
        'timestamps': timestamps,
        'BW': args.hf - args.lf
        }
    
    pickle.dump(output,fout)
    fout.close()


    if args.p:
        fig, ax = plt.subplots()
        plt.title(args.output)
        
        #x axis LST formatting
        def x_tick(x, pos):
            hour = (lst(timestamps[int(x)]) * 180 / np.pi ) / 15
            minute = (hour - int(hour)) * 60.0
            second = (minute - int(minute)) * 60.0
            return "{:2d}h{:2d}m{:2.3f}s".format(int(hour), int(minute), second)

        x_formatter = FuncFormatter(x_tick)
        x_locator = FixedLocator(np.linspace(0, len(timestamps)-1, 5))
        ax.xaxis.set_major_formatter(x_formatter)
        ax.xaxis.set_major_locator(x_locator)

        # y axis Frequency formatting
        def y_tick(x, pos):
            return "{:2.1f}".format(pdat.bin2freq(x))

        y_formatter = FuncFormatter(y_tick)
        y_locator = FixedLocator([pdat.freq2bin(x) for x in np.arange(args.lf,args.hf,10)])
        ax.yaxis.set_major_formatter(y_formatter)
        ax.yaxis.set_major_locator(y_locator)

        plt.imshow(10*np.log10(np.abs(data)**2), aspect='auto')
        plt.xlabel('LST')
        plt.ylabel('Frequency (MHz)')
        plt.grid()        
        fig.savefig(args.output + '.png')

        
    del data
        
    
