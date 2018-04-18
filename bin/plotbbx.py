#!/usr/bin/env python

from lofasm.bbx.bbx import LofasmFile
import numpy as np
import matplotlib.pyplot as plt
import os
from lofasm.parse_data_H import Baselines
import re


def plot_single_file(bbxFile, **kwargs):
    '''
    Produce waterfall plot window of a single bbx file

    power scaling is in dB; 10*np.log10(data) is plotted

    Parameters
    ----------
    bbxFile : str
        Path to bbx file to plot.
    **kwargs
        Arbitrary keyword args.
    '''

    infile = bbxFile
    f = LofasmFile(infile)
    f.read_data()
    dim10 = float(f.header['dim1_start'])
    dim11 = float(f.header['dim1_span']) + dim10
    dim20 = float(f.header['dim2_start'])
    dim21 = float(f.header['dim2_span']) + dim20

    # convert frequencies to MHz
    dim20 /= 1e6
    dim21 /= 1e6

    data = 10*np.log10(f.data)
    plt.imshow(data if f.header['metadata']['complex']==1 else np.abs(data)**2,
               aspect='auto', origin='lower', cmap ='hot',
               interpolation='none', extent=[dim10, dim11, dim20, dim21])
    plt.title(os.path.basename(infile))
    #plt.title("LoFASM {st}: ")
    plt.xlabel("Time sample")
    plt.ylabel("Frequency (MHz)")
    plt.colorbar()

    if kwargs.has_key('savefig'):
        if kwargs['savefig']:
            bn = os.path.basename(bbxFile)
            plt.savefig(bn + '.png')
    if kwargs.has_key('suppress'):
        if not kwargs['suppress']:
            plt.show()
    else:
        plt.show()
    plt.clf()

def plot_all_available_pols(bbxPrefix, **kwargs):
    '''Scan local directory for bbxPrefix and generate plot with all available
    matching polarization bbx files.

    Parameters
    ----------
    bbxPrefix : str
        bbx prefix to scan for in local directory.

        arbitrary keyword arguments
    savefig : bool
        save image in local directory if true. 
    '''

    regex = '^{}_[A-Z]{{2}}.bbx*'.format(bbxPrefix)
    files = [f for f in os.listdir('.') if re.match(regex,f)]
    if not files:
        raise RuntimeError("No files matching {}".format(regex))
    pols = kwargs['pols'].split(',')
    files = [files[i] for i in range(len(files)) if [p for p in pols if p in files[i]] ]

    for f in files:
        print "Processing {}...".format(f)
        plot_single_file(f, suppress=True, savefig=True)




if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('inputfile', help="path to input file")
    parser.add_argument('-p', action='store_true',
                         help="Set to plot all available polarizations of prefix.")
    parser.add_argument('--savefig', '-s', help="save figure in local direcotry",
                        action='store_true', dest='s')
    parser.add_argument('--pols', help="pols to plot. comma separated list",
                        default=",".join(Baselines))
    args = parser.parse_args()

    pols = (args.pols).split()

    if args.p:
        plot_all_available_pols(args.inputfile, pols=args.pols, savefig=True)
    elif args.s:
        plot_single_file(args.inputfile, suppress=True, savefig=True)
    else:
        plot_single_file(args.inputfile)
