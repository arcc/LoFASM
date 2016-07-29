#! /usr/bin/env python

import numpy as np
import sidereal


east_long_radians = 4.243069944523414
lat_radians = 0.6183119763398577
lofasm4_outrigger_distance = 549.913767 #nanoseconds
#td_bin = 10 #ns
rot_ang = -10.42 * np.pi/180
cable_offset_bins = 580

# function definitions
def calcBinWidth(BW):
    '''
    calculate time delay bin width given bandwidth in Hz.

    returns time in nanoseconds
    '''
    BW = float(BW)
    return (1/BW)/1e-9
    
def shiftWaterfall(data, timestamps, RA, DEC, td_bin, orientation='left'):
    assert(type(orientation) == str), 'orientation must be a string: left or right'
    assert(orientation.lower()=='left' or orientation.lower()=='right'), 'choices for orientation are left or right'
    
    shiftedData = np.zeros(np.shape(data))

    if orientation == 'left':
        o = -1
    elif orientation == 'right':
        o = 1
    else:
        raise ValueError()
    factor = o/float(td_bin)

    for i in range(len(timestamps)):
        delay_ns = delay(RA,DEC,timestamps[i], rot_ang)
#        delay_bins = o * delay_ns / float(td_bin)
        delay_bins = factor * delay_ns
        shiftedData[:,i] = shift(data[:,i], delay_bins)

    return shiftedData

def calcDelays(RA, DEC, rot_ang, timestamps):
    delays_ns = np.zeros(len(timestamps))
    for i in range(len(timestamps)):
        delays_ns[i] = delay(RA, DEC, timestamps[i], rot_ang)
    return delays_ns

    
def delay(RA,DEC,utc, rot_ang):
    return lofasm4_outrigger_distance * (np.cos(DEC)*np.sin(lst(utc)-RA)*np.cos(rot_ang) + np.sin(rot_ang)*(np.sin(DEC)*np.cos(lat_radians)-np.cos(DEC)*np.sin(lat_radians)*np.cos(lst(utc)-RA)))

def lst(utc):
    gst = sidereal.SiderealTime.fromDatetime(utc)
    return gst.lst(east_long_radians).radians

def shift(y, s):
    '''
    shift array y by n bins cyclically
    '''

    s = int(s)
    N = len(y)
    result = np.zeros(N)

    if s > 0:
        result[:N-s] = y[s:]
        result[N-s:] = y[:s]
    elif s < 0:
        s = -1 * s
        result[:s] = y[N-s:]
        result[s:] = y[:N-s]
    elif s == 0:
        result = y
    return result

if __name__ == "__main__":
    import argparse
    import os, sys
    import pickle
    import platform
    if platform.system() == "Linux":
        import matplotlib
        matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    parser = argparse.ArgumentParser()
    parser.add_argument('input', help='path to input file')
    parser.add_argument('BW', help="bandwidth of data in MHz", type=float)    
    parser.add_argument('ra', help='Right Ascension of the source in radians', type=float)
    parser.add_argument('dec', help='Declination of the source in radians', type=float)
    parser.add_argument('-o', '--output', help='name of output image', default='out.png')
    parser.add_argument('--source', help="name of the source", type=str, default='unknownsource')
    parser.add_argument('--lbin', help='low bin', type=int, default=-1)
    parser.add_argument('--hbin', help="high bin", type=int, default=-1)
    parser.add_argument('--orientation',
                        help='direction in which to apply the delay. right or left. default is left',
                        type=str, choices=['left','right'], default='left')


    args = parser.parse_args()
    assert os.path.exists(args.input)

    infile = args.input
    RA = args.ra
    DEC = args.dec
    source = args.source
    output = args.output
    BW = args.BW * 1e6 #Hz

    #load data
    with open(infile, 'rb') as f:
        (data, timestamps) = pickle.load(f)


    print "RA: {} rad. Dec: {} rad. time resolution: {} ns".format(RA, DEC, calcBinWidth(BW))
    shiftedData = shiftWaterfall(data, timestamps, RA, DEC, calcBinWidth(BW), args.orientation)
    avg = shiftedData.sum(1)


    with open("{}.lofasm2d".format(output) if not output.endswith('.lofasm2d') else output, 'wb') as f:
        print "writing {}".format(f.name)
        pickle.dump((shiftedData, timestamps), f)

    if args.lbin is not -1:
        assert args.lbin >= 0
        lowbin = args.lbin
    else:
        lowbin = 0

    if args.hbin is not -1:
        assert args.hbin >= 0
        highbin = args.hbin
    else:
        highbin = np.shape(data)[0]

            
    fig = plt.figure(1)
    plt.subplot(211)
    plt.title(source)    
    plt.plot(avg[lowbin:highbin])
    plt.grid()

    plt.subplot(212)
    plt.imshow(10*np.log10(shiftedData[lowbin:highbin,:]), aspect='auto')
    plt.grid()

    fig.savefig(output.rstrip('.png') + '.png')
    fig.savefig("{}.png".format(output) if not output.endswith('.png') else output)    
