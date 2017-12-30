#! /usr/bin/env python
'''
use frequency averaged time series data to synthesize a LoFASM Beam
'''

import sys, os
import matplotlib
import numpy as np
matplotlib.use('agg')
import matplotlib.pyplot as plt
from lofasm.bbx import bbx
from lofasm.parse_data import freq2bin
from glob import glob

def freq_average_file(filename, freqs, bw=1.):
    '''
    take a list of frequency bands of width bw centered at freq from 
    each filterbank sample calculate the average over time.
    the minimum value of this averaged time series will be returned.

    Parameters
    ----------
    filename : str
        the data file to process
    freq : list
        list of the selected center frequencies in MHz
    bw : float, optional
        the bandwidth to include in the frequency averaging

    Returns
    -------
    freq_avg : numpy.array
                       array of frequency averaged time series minimum values,
                       each corresponding to its respective center
                       frequency at input
    '''

    lfx = bbx.LofasmFile(filename)
    lfx.read_data()
    freqs.sort()
    num_fbins = freq2bin(freqs[0] + bw / 2.) - freq2bin(freqs[0] - bw / 2.)
    num_tbins = np.shape(lfx.data)[1]
    freq_avg = np.zeros((len(freqs), num_tbins), dtype=np.float64)
    d = np.zeros((num_fbins, num_tbins), dtype=np.float64)

    if lfx.iscplx:
        print "discarding the imaginary part"

    for i in range(len(freqs)):
        lfbin = freq2bin(freqs[i] - bw / 2.)
        hfbin = freq2bin(freqs[i] + bw / 2.)
        if lfx.iscplx:
            d[:,:] = np.real(lfx.data[lfbin:hfbin,:])
        else:
            d[:,:] = lfx.data[lfbin:hfbin,:]
        freq_avg[i,:] = np.average(d, axis=0)
    lfx.close()
    return freq_avg


    

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('polA', type=str, help='path to data directory for Pol A')
    p.add_argument('polB', type=str, help='path to data directory for Pol B')
    p.add_argument('polAB', type=str, help='path to data directory for Pol AB')
    p.add_argument('frequency', type=float, help='frequencies to calculate at')
    p.add_argument('--savedata', action='store_true',
                   help='save data as numpy file')
    args = p.parse_args()

    # currently relying on files being perfectly corresponding
    flistA = glob(os.path.join(args.polA, "*.bbx.gz"))
    flistA.sort()
    flistB = glob(os.path.join(args.polB, "*.bbx.gz"))
    flistB.sort()
    flistAB = glob(os.path.join(args.polAB, "*.bbx.gz"))
    flistAB.sort()

    
    freq = args.frequency
    avg_beam = np.zeros(len(flistA), dtype=np.float64)

    for i in range(len(flistA)):
        re = "Processing {}/{}".format(i+1,len(flistA))
        sys.stdout.write('\r'+re)
        sys.stdout.flush()
        x = np.min(freq_average_file(flistA[i], [45.])[0,:])
        y = np.min(freq_average_file(flistB[i], [45.])[0,:])
        xy = np.min(freq_average_file(flistAB[i], [45.])[0,:])

        avg_beam[i] = x + y + 2 * xy

    plt.figure()
    plt.plot(10*np.log10(avg_beam), label='avg LoFASM Beam')
    plt.legend()
    plt.grid()
    plt.savefig('avg_beam_{}MHz.png'.format(freq), format='png')
