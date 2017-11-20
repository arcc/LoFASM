#!/usr/bin/env python

from lofasm.bbx.bbx import LofasmFile
import numpy as np
import matplotlib.pyplot as plt
import argparse


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('inputfile', help="path to input file")
    parser.add_argument('-l', dest='loged', action='store_true', help='plot loged data')
    args = parser.parse_args()

    infile = args.inputfile
    loged = args.loged
    f = LofasmFile(infile)
    f.read_data()
    dim10 = float(f.header['dim1_start'])
    dim11 = float(f.header['dim1_span']) + dim10
    dim20 = float(f.header['dim2_start'])
    dim21 = float(f.header['dim2_span']) + dim20
    if loged:
        data = 10*np.log10(f.data)
    else:
        data = f.data
    plt.imshow(data, aspect='auto', origin='lower', cmap ='hot',
                   interpolation='none', extent=[dim10, dim11, dim20, dim21])
    plt.title(infile) 
    plt.colorbar()
    plt.show() 
