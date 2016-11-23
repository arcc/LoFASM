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

def shiftWaterfall(data, timestamps, RA, DEC, td_bin, orientation='left'):
    assert(type(orientation) == str), 'orientation must be a string: left or right'
    assert(orientation.lower()=='left' or orientation.lower()=='right'), 'choices for orientation are left and right'
    
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

def delay(RA,DEC,utc, rot_ang=rot_ang):
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
    from matplotlib.ticker import FuncFormatter, FixedLocator
    parser = argparse.ArgumentParser()
    parser.add_argument('input', help='path to input file')
    parser.add_argument('ra', help='Right Ascension of the source in radians', type=float)
    parser.add_argument('dec', help='Declination of the source in radians', type=float)
    parser.add_argument('-o', '--output', help='name of output file', default='out.corrected2d')
    parser.add_argument('--orientation',
                        help='direction in which to apply the delay. right or left. default is left',
                        type=str, choices=['left','right'], default='left')


    args = parser.parse_args()
    assert os.path.exists(args.input)

    infile = args.input
    RA = args.ra
    DEC = args.dec
    output = args.output

    #load .delay2d data
    with open(infile, 'rb') as f:
        fdict = pickle.load(f)
        binwidth = fdict['binwidth']
        data = fdict['data']
        timestamps = fdict['timestamps']
    


    print "RA: {} rad. Dec: {} rad. time resolution: {} ns".format(RA, DEC, binwidth)
    shiftedData = shiftWaterfall(data, timestamps, RA, DEC, binwidth, args.orientation)
    avg = shiftedData.sum(1)

    output_dict = {
        'data': shiftedData,
        'timestamps': timestamps,
        'binwidth': binwidth,
    }


    with open("{}.corrected2d".format(output) if not output.endswith('.corrected2d') else output, 'wb') as f:
        print "writing {}".format(f.name)
        pickle.dump(output_dict, f)

    print binwidth

    def lst_tick(x, pos):
        hour = (lst(timestamps[int(x)]) * 180 / np.pi ) / 15
        minute = (hour - int(hour)) * 60.0
        second = (minute - int(minute)) * 60.0
        return "{:2d}h{:2d}m{:2.3f}s".format(int(hour), int(minute), second)

    fig, ax = plt.subplots()
    ax.xaxis.set_major_formatter(FuncFormatter(lst_tick))
    ax.xaxis.set_major_locator(FixedLocator(np.linspace(0,len(timestamps)-1,5)))
    ax.set_title(output)
    ax.imshow(10*np.log10(shiftedData), aspect='auto')
    plt.grid()

    fig.savefig(output.rstrip('.png') + '.png')
    fig.savefig("{}.png".format(output) if not output.endswith('.png') else output)    
