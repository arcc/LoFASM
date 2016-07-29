#! /usr/bin/env python


import sys, os
import numpy as np
import applyDelay as s
import pickle
import platform
if platform.system() == "Linux":
    import matplotlib
    matplotlib.use('Agg')
import matplotlib.pyplot as plt
from time import time
import multiprocessing as mp
import lightcurve as lc
plt.ion()


if __name__ == "__main__":
    import argparse
    import os, sys
    from time import time
    from lofasm import filter
    import lightcurve as lc

    parser = argparse.ArgumentParser()
    parser.add_argument('inputfile', help="path to input file")
    parser.add_argument('-w', '--windowsize', help="window to consider when computing the lightcurve of each slice. default is 0",
                        type=int, default=0)
    parser.add_argument('-o', '--outputfile', dest='outfile',
                        help='path to output file to store 2d map')
    parser.add_argument('--ra',nargs=2,
                        help='min and max values for Right Ascension, in radians. format: --ra 0.0 6.2831',
                        default=['0.0', '6.2831'], type=float)
    parser.add_argument('--dec', nargs=2,
                        help='min and max values for Declination, in radians. format: --dec -3.1415 3.1415',
                        default=['-3.1415', '3.1515'],type=float)
    parser.add_argument('--Nra', help='integer number of RA values, default is 10', default=10, type=int)
    parser.add_argument('--Ndec', help='integer number of DEC values, default is 10', default=10, type=int)
    args = parser.parse_args()
    
    assert os.path.exists(args.inputfile)
    assert (args.windowsize >= 0), 'windows size must be a positive integer'

    minRA, maxRA = args.ra
    minDEC, maxDEC = args.dec
    Nra = args.Nra
    Ndec = args.Ndec
    infile = args.inputfile
    winSize = args.windowsize

    assert(minRA >= 0.0 and minRA <= 2*np.pi), 'minimum RA value must be a positive value between 0 and 2*pi'
    assert(maxRA >= 0.0 and maxRA <= 2*np.pi), 'maximum RA value must be a positive value between 0 and 2*pi'
    assert(minDEC >= -1*np.pi and minDEC <= np.pi), 'Declination value must be within the range -pi..pi'
    assert(maxDEC >= -1*np.pi and maxDEC <= np.pi), 'Declination value must be within the range -pi..pi'

    RA_range = np.linspace(minRA, maxRA, Nra)
    DEC_range = np.linspace(minDEC, maxDEC, Ndec)
    
    #initialize shared memory array
    shared_array_base = mp.Array(np.ctypeslib.ctypes.c_double, Nra*Ndec) 
    shared_array = np.ctypeslib.as_array(shared_array_base.get_obj())
    shared_array = shared_array.reshape(Ndec, Nra)
    
    #load data file
    start_load = time()
    print "Reading file: {}".format(infile),
    sys.stdout.flush()
    with open(infile, 'rb') as f:
        data, timestamps = pickle.load(f)
    end_load = time()
    print "\t done in {} s".format(end_load - start_load)

    dt = (timestamps[-1] - timestamps[0]).__str__()

    #defined here so that skymap inherits the current scope environment
    def skymap( (i, k) ):
        print "{}: ({}, {})".format(os.getpid(), i, k)
        pval = lc.getLightCurve(data, timestamps, RA_range[k], DEC_range[i], winSize).sum()
        shared_array[i, k] = pval
        return

    # populate argument list
    pool_args = []
    for i in range(Ndec):
        for k in range(Nra):
            pool_args.append( (i, k) )

    print "parent: {}".format(os.getpid())
    pool = mp.Pool(mp.cpu_count())
    pool.map(skymap, pool_args)

    #save intermediate data to disk
    with open(os.path.join(os.path.dirname(infile), os.path.basename(args.outfile)+'.skymap'), 'wb') as f:
        pickle.dump(shared_array, f)

    #plot as save skymap image to disk
    
    plt.figure()
    plt.imshow(10*np.log10(shared_array), aspect='auto', extent=[minRA, maxRA, minDEC, maxDEC])
    plt.grid()
    plt.title(dt)
    plt.savefig(args.outfile+'.png')
