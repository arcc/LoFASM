#! /usr/bin/env python

from lofasm.clean import cleandata as c
import lofasm.bbx.bbx as b
import numpy as np
import matplotlib.pyplot as plt
import sys
import glob
import os
import time
import argparse


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
    parser.add_argument('-n', dest='normalize',action='store_true',
                        help='A flag for ouput the normalized compressing data.')
    parser.add_argument('-ot', action='store', dest='o_thresh', default = 10,
                        help='outlier mask threshold.')
    parser.add_argument('-nt', action='store', dest='nb_thresh', default = 1,
                        help='narrow band mask threshold.')
    parser.add_argument('-wt', action='store', dest='wb_thresh', default = 1.7,
                        help='wide band mask threshold.')

    # Parse the commonline parameters
    args = parser.parse_args()
    start_time = time.time()
    infile = args.infilename
    outfile = args.outfilename
    compress = args.compress
    window_size = int(args.window_size)
    norm = args.normalize
    outlier_thrhd = args.o_thresh
    narrowband_thrhd = args.nb_thresh
    wideband_thrhd = args.wb_thresh

    lf = b.LofasmFile(infile)
    lf.read_data()
    norm_data, normalize_array = c.normalize(lf.data, fast=args.fast,
                                             window=window_size)
    o_mask, outlier_average_top, outlier_average_bottom	= c.outlier_mask(norm_data,
                                             threshold= outlier_thrhd)
    nb_mask, percent_clean_freq_channels = c.narrow_band_mask(norm_data,
                                             threshold= narrowband_thrhd)
    wb_mask, percent_clean_time = c.wide_band_mask(norm_data,
                                             threshold= wideband_thrhd)

    print infile + '---------------------------'
    print 'top outlier average               : '+str(outlier_average_top)
    print 'bottom outlier average            : '+str(outlier_average_bottom)
    print 'percentage of clean freq channels : '+str(percent_clean_freq_channels)
    print 'percentage of clean time          : '+str(percent_clean_time)
    print ''
    print '-------------------------------------------------------'

    final = norm_data*wb_mask*o_mask*nb_mask
    final[np.isnan(final)]=1
    if not norm:
        final = final*normalize_array
    # get output base name
    name_field = os.path.splitext(infile)
    if name_field[1] == '.gz':
        name_field = os.path.splitext(name_field[0])
    base_name  = name_field[0]
    # Out put data.
    if outfile == "":
        outfile = base_name + '_cleand'
        if norm:
            outfile += '_normalized.bbx'
        if compress:
            outfile += '.gz'
    else:
        if not outfile.endswith('gz'):
            if compress:
                outfile += '.gz'

    lfc = b.LofasmFile(outfile, header=lf.header, mode = 'write')
    lfc.add_data(final)
    lfc.set('clean', True)
    lfc.write()
    lfc.close()
    end_time = time.time()
    cost_time = end_time - start_time
    print "It takes %s seconds to cleaning file %s.\n" % (str(cost_time), infile)
