#!/usr/local/opt/python/bin/python2.7


import sys
import numpy as np
import applyDelay as s
import pickle
import platform
if platform.system() == "Linux":
    import matplotlib
    matplotlib.use('Agg')
import matplotlib.pyplot as plt
from time import time
from lofasm import filter
from datetime import datetime
import sidereal
from lofasm.timeit import timeit
plt.ion()

centertime_bin = s.cable_offset_bins
east_long_radians = 4.243069944523414


def calcBinWidth(BW):
    '''
    calculate time delay bin width given bandwidth in Hz.

    returns time in nanoseconds
    '''
    BW = float(BW)
    return (1/BW)/1e-9

def lst(utc):
    gst = sidereal.SiderealTime.fromDatetime(utc)
    return gst.lst(east_long_radians).radians

def lha(utc, RA):
    return lst(utc) - RA

def getLightCurve(data, timestamps, RA, DEC, winsize=0, orientation='left'):
    '''
    apply tdelay shift to data for each timestamp in timestamps
    '''

    assert( winsize % 2 == 0), 'winsize must be an even number or zero'
    assert( winsize >= 0), 'winsize must be positive'

    N = len(timestamps)

    start_dcalc = time()

    sys.stdout.flush()
    delays = s.calcDelays(RA, DEC, s.rot_ang, timestamps)
    end_dcalc = time()



    if orientation == 'left':
        o = -1
    elif orientation == 'right':
        o = 1
    else:
        raise ValueError()
    
    factor = o / calcBinWidth(100000000.0)
    dbins = factor * delays

    start_curve = time()

    #initialize lightcurve array
    lightcurve = np.zeros(N)

    w = winsize/2
    
    for i in range(N):
        k = int(centertime_bin + dbins[i])
        lightcurve[i] = data[k, i]
    end_curve = time()

    print "delay calc time: {:.2f}, curve calc time: {:.2f}".format(end_dcalc - start_dcalc, end_curve-start_curve)
    return lightcurve
def getLightCurve2(data, timestamps, RA, DEC, winsize=0, orientation='left'):
    '''
    apply tdelay shift to data for each timestamp in timestamps
    '''

    assert( winsize % 2 == 0), 'winsize must be an even number or zero'
    assert( winsize >= 0), 'winsize must be positive'

    N = len(timestamps)

    start_dcalc = time()

    delays = s.calcDelays2(RA, DEC, s.rot_ang, timestamps)
    end_dcalc = time()



    if orientation == 'left':
        o = -1
    elif orientation == 'right':
        o = 1
    else:
        raise ValueError()
    
    binfactor = o / calcBinWidth(100000000.0)


    #initialize lightcurve array
    start_curve = time()    
    lightcurve = np.zeros(N)

    w = winsize/2
    
    i = 0
    for delay in delays:
        k = int(centertime_bin + binfactor * delays.next())
        lightcurve[i] = data[k, i]
        i += 1
    end_curve = time()

    print "delay calc time: {:.2f}, curve calc time: {:.2f}".format(end_dcalc - start_dcalc, end_curve-start_curve)
    return lightcurve
def getLightCurve3(data, timestamps, RA, DEC, winsize=0, orientation='left'):
    '''
    apply tdelay shift to data for each timestamp in timestamps
    '''

    assert( winsize % 2 == 0), 'winsize must be an even number or zero'
    assert( winsize >= 0), 'winsize must be positive'

    N = len(timestamps)

    start_dcalc = time()

    params = s.getDelayParams(DEC)    


    delays = s.calcDelays3(params, RA, DEC, s.rot_ang, timestamps)
    end_dcalc = time()



    if orientation == 'left':
        o = -1
    elif orientation == 'right':
        o = 1
    else:
        raise ValueError()
    
    binfactor = o / calcBinWidth(100000000.0)


    #initialize lightcurve array
    lightcurve = np.zeros(N)

    w = winsize/2
    
    i = 0
    start_curve = time()    
    for delay in delays:
        k = int(np.ceil(centertime_bin + (binfactor * delay)))
        lightcurve[i] = data[k, i]
        i += 1
#        print 'ra,dec,iter, elapsed time in loop: {},{},{},{}'.format(RA,DEC,i,time()-start_curve)
    end_curve = time()

#    print "i: {} delay calc time: {}, curve calc time: {}".format(i,end_dcalc - start_dcalc, end_curve-start_curve)
    return (lightcurve, delays)
  

if __name__ == "__main__":
    import argparse
    import os, sys
    from time import time
    from lofasm import filter
    from matplotlib.ticker import FuncFormatter, FixedLocator

    parser = argparse.ArgumentParser()
    parser.add_argument('ra', help='ra in radians', type=float)
    parser.add_argument('dec', help='dec in radians', type=float)
    parser.add_argument('input', help="path to input lofasm2d file")
    parser.add_argument('output', help='name of output', type=str)
    parser.add_argument('windowsize', help='number of nearby bins to consider, default is 0', default=0, type=int)
    parser.add_argument('--orientation', default='left', choices=['left', 'right'],
                        type=str, help='shift direction. usually left for AB and right for BC')
    
    args = parser.parse_args()

    assert os.path.exists(args.input)
    assert args.windowsize >= 0
    
    #import loadfiles as lf

    infile = args.input
    RA = args.ra
    DEC = args.dec
    winsize = args.windowsize

    
    #load file
    start_load = time()
    print "Reading file: {}".format(infile),
    sys.stdout.flush()
    with open(infile, 'rb') as f:
        fdict = pickle.load(f)
        data = fdict['data']
        timestamps = fdict['timestamps']
        BW = fdict['BW']
    end_load = time()

    print "\t done in {} s".format(end_load - start_load)

    lightcurve = getLightCurve(data, timestamps, RA, DEC, winsize, args.orientation)

    output_dict = {
        'data': lightcurve,
        'timestamps': timestamps,
        'BW': BW
    }

    #save intermediate data to disk
    fout = args.output if args.output.endswith('.lightcurve') else args.output + '.lightcurve'
    with open(fout, 'wb') as f:
        pickle.dump(output_dict, f)



    #plot data
    def lst_tick(x, pos):
        hour = (lst(timestamps[int(x)]) * 180 / np.pi ) / 15
        minute = (hour - int(hour)) * 60.0
        second = (minute - int(minute)) * 60.0
        lha_val = lha(timestamps[int(x)], RA)
        return "{:2d}h{:2d}m{:2.3f}s\n{:2.2f}rad".format(int(hour), int(minute), second, lha_val)

    fig, ax = plt.subplots()
    ax.xaxis.set_major_formatter(FuncFormatter(lst_tick))
    ax.xaxis.set_major_locator(FixedLocator(np.linspace(0,len(timestamps)-1,5)))
    plt.xlabel('LST')
    ax.set_title(args.output)
    plt.plot(lightcurve)
    plt.grid()
    plt.savefig(fout + '.png', format='png')

    
    
