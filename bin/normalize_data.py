#! /usr/bin/env python

from lofasm.clean import cleandata as c
import lofasm.bbx.bbx as b
import numpy as np
import matplotlib.pyplot as plt
import sys
import os
import argparse

def do_normalize(infile, fast_method, window_size, outfile, compress):
    # Set up output name
    name_field = os.path.splitext(infile)
    if name_field[1] == '.gz':
        name_field = os.path.splitext(name_field[0])
    base_name  = name_field[0]
    # read in data.
    lf = b.LofasmFile(infile)
    lf.read_data()
    # Normalize
    norm_data, normalize_array = c.normalize(lf.data, fast=fast_method,
                                              window=window_size)
    # Out put data.
    if outfile == "":
        outfile = base_name + '_normalized.bbx'
        if compress:
            outfile += '.gz'
    else:
        if not outfile.endswith('gz'):
            if compress:
                outfile += '.gz'

    outfile = b.LofasmFile(outfile, header=lf.header, mode = 'write')
    outfile.add_data(norm_data)
    outfile.write()
    outfile.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('infilename', help="The input data file name.")
    parser.add_argument('-o', dest='outfilename', default="",
                        help="The output data file name.")
    parser.add_argument('-f', dest='fast',action='store_true',
                        help='Using the fast method to normalize data. ')
    parser.add_argument('-w', dest='window_size',default=200,
                        help='Normalize window size')
    parser.add_argument('-c', dest='compress',action='store_true',
                        help='A flag for compressing data.')

    # Parse the commonline parameters
    args = parser.parse_args()
    infile = args.infilename
    outfile = args.outfilename
    compress = args.compress
    window_size = int(args.window_size)

    do_normalize(infile, args.fast, window_size, outfile, compress)
