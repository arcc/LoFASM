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
from lofasm.timeit import timeit
from lofasm import station
from lofasm import skysource
from astropy.coordinates import Latitude, Longitude
plt.ion()

def get_ra_range(minra,maxra, N):
    '''
    generate the values for the RA axis

    if minra < maxra then return an array with 2*np.pi in between
    the endpoints.

    Parameters

    minra : float
        minimum RA value
    maxra : float
        maximum RA value
    N : int
        number of points in the returned array
    '''

    if maxra < minra :
        ras = [x for x in np.linspace(minra, 2*np.pi , N)]
        ras.extend([x for x in np.linspace(0.0,maxra,N)])
        ras = np.array(ras)
    else:
        ras = np.linspace(minra,maxra,N)

    return ras


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
    parser.add_argument('-o', '--outputfile', dest='outfile', default=os.path.join(os.getcwd(),'out.skymap'),
                        help='path to output file to store 2d map')
    parser.add_argument('--ra',nargs=2,
                        help='min and max values for Right Ascension, in radians. format: --ra 0.0 6.2831',
                        default=[0.0, 6.2831], type=float)
    parser.add_argument('--dec', nargs=2,
                        help='min and max values for Declination, in radians. format: --dec -1.57 1.57',
                        default=[-1.57, 1.57], type=float)
    parser.add_argument('--Nra', help='integer number of RA values, default is 10', default=10, type=int)
    parser.add_argument('--Ndec', help='integer number of DEC values, default is 10', default=10, type=int)
    args = parser.parse_args()
    


    minRA, maxRA = args.ra
    minDEC, maxDEC = args.dec
    Nra = args.Nra
    Ndec = args.Ndec
    infile = args.inputfile
    winSize = args.windowsize

    assert os.path.exists(infile)
    assert (winSize >= 0), 'windows size must be a positive integer'
    assert(minDEC >= -1*np.pi/2 and minDEC <= np.pi/2), 'Declination value must be within the range -pi/2..pi/2: {}'.format(minDEC)
    assert(maxDEC >= -1*np.pi/2 and maxDEC <= np.pi/2), 'Declination value must be within the range -pi/2..pi/2'

    #set LoFASM station
    lofasm_station = station.station[4]


    #set right ascension and declination range
    RA_range = get_ra_range(minRA, maxRA, Nra)
    #if minDEC < lofasm_station.minDec:
    #    minDEC = lofasm_station.minDec.rad
    #if maxDEC > lofasm_station.maxDec:
    #    maxDEC = lofasm_station.maxDec.rad
    DEC_range = np.linspace(minDEC, maxDEC, Ndec)


    #initialize shared memory array
    shared_array_base = mp.Array(np.ctypeslib.ctypes.c_double, Nra*Ndec) 
    shared_array = np.ctypeslib.as_array(shared_array_base.get_obj())
    shared_array = shared_array.reshape(Ndec, Nra)

    #shared dictionary to gather cpu core execution times
    proc_time = mp.Manager().dict()
    skyPoints = mp.Manager().dict()

    #########################
    #       LOAD DATA       #
    #########################
    start_load = time()
    print "Reading file: {}".format(infile),
    sys.stdout.flush()
    with open(infile, 'rb') as f:
        contents = pickle.load(f)
        data = contents['data']
        timestamps = contents['timestamps']
        binwidth = contents['binwidth']
    end_load = time()
    print "\t done in {} s".format(end_load - start_load)

    dt = timestamps[-1] - timestamps[0]

    #convert timestamp values to lst radians
    #begin=time()
    #timestamps = [s.lst(x) for x in timestamps]
    #end=time()
    #print "timestamp to LST conversion: {}".format(end-begin)



    #defined here so that skymap inherits the current scope 
    def skymap( (i, k, proc_time, skyPoints) ):

        sys.stdout.flush()
        begin=time()

        pid = os.getpid()

        #set skyPoint object
        if pid in skyPoints.keys():
            skyPoint = skyPoints[pid]
            skyPoint.setRA(Longitude(RA_range[k], 'rad'))
            skyPoint.setDec(Latitude(DEC_range[i], 'rad'))
        else:
            skyPoint = skysource.SkySource(RA_range[k], DEC_range[i], lofasm_station=lofasm_station)

        #calculate point alts for all timestamps in radians
        alts = np.array([x[0] for x in [skyPoint.AltAz(t,lofasm_station) for t in timestamps]])

        up_indices = np.where(alts > lofasm_station.alt_min.rad)[0]

        if up_indices:

            uptimes = np.array([timestamps[x] for x in up_indices])
            upalts = np.array([alts[x] for x in up_indices])

            #rise and set times
            settime = uptimes[-1] #potentially dangerous if timestamps spans multiple transits
            risetime = uptimes[0]

            #check declination range
            #if skyPoint.coord.dec.rad > lofasm_station.maxDec.rad or skyPoint.coord.dec.rad < lofasm_station.minDec.rad:
            #    pval = 0.0
            #else:
            #    lcurve = skyPoint.getLightcurve(data, timestamps, offset=580)
            #    pval = lcurve.sum()

            #only compute light curve for points that are visible
            lcurve = skyPoint.getLightcurve(data, uptimes, offset=580)
            pval = lcurve.sum()
        else:
            pval = 0.0

        shared_array[-1*i, k] = pval

        end=time()

        if pid in proc_time.keys():
            proc_time[pid] += end-begin
        else:
            proc_time[pid] = end-begin

        return

    # populate argument list
    begin = time()
    pool_args = []
    for i in range(Ndec):
        for k in range(Nra):
            pool_args.append( (i, k, proc_time, skyPoints))
    end = time()
    print "arg list population: {} sec".format(end-begin)

    print "parent: {}".format(os.getpid())
    cpus = 1 if mp.cpu_count()==1 else mp.cpu_count()-1
    print "using {} cpu's".format(cpus)
    pool = mp.Pool(cpus)
    begin=time()
    pool.map(skymap, pool_args)
    end=time()
    print "pool execution: {}".format(end-begin)

    print "cpu info:"
    for key in proc_time.keys():
        print "{}: {}".format(key, proc_time[key])

    #save intermediate data to disk
    fname = os.path.basename(args.outfile) + "_{}x{}_ra_{}_{}_dec_{}_{}".format(Nra, Ndec, minRA, maxRA, minDEC, maxDEC)
    outfile = os.path.join(os.path.dirname(infile), fname+'.skymap')
    imgname = os.path.join(os.path.dirname(infile), fname+'_skymap.png')

    begin=time()
    with open(outfile, 'wb') as f:
        pickle.dump(shared_array, f)
    end=time()
    print "dump shared array to disk: {} sec".format(end-begin)
    #plot as save skymap image to disk

    print "data file: {}".format(outfile)
    print "image file: {}".format(imgname)
    
    plt.figure()
    plt.plot(5.23366,0.71094094, 'r*')
    plt.plot(6.122178, 1.0262536, 'b*')    
    plt.imshow(10*np.log10(shared_array), aspect='auto', extent=[minRA, maxRA, minDEC, maxDEC])
    plt.grid()
    plt.colorbar()

#    plt.plot(6.122178,1.0262536, 'b*')
#    plt.grid()
    plt.title("{}: {}, {}x{}"
        .format(os.path.basename(infile), dt.__str__(), Nra, Ndec))
    plt.xlabel('Right Ascension (radians)')
    plt.ylabel('Declination (radians)')
    plt.savefig(imgname)
