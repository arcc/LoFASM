#! /usr/bin/env python

'''
1. easiest way to use this code is to just run it in the folder with the data you want to clean.
example:

cleandata.py

this will clean all the data and put it in the same folder the raw data was in so it can be easily moved however we choose

2.  if you want to get more specific you can you the filename flag -fn and a star *
examples:

cleandata.py -fn *CC.bbx.gz

this will clean all CC polarizations



cleandata.py -fn 20160929*.bbx.gz

this will clean all the data from sept 29 2016


cleandata.py -fn 20160929_001641_CC.bbx.gz

this will clean the file 20160929_001641_CC.bbx.gz



cleandata.py -fn [file, file, file, ...]

this will clean the files that you passed through the list

3. cleandata can also be import and its functions used
for jing to inject the simulated signal would look something like this

import everything_else
import cleandata as c

lf = b.LofasmFile(file_name)
lf.read_data()

norm_data, normalize_array  = c.normalize(lf.data)

filterbank_with_injected_signal = (norm_data+injected signal) * normalize_array

the last line is basically where everything happens
norm_data is the normalized filter bank data
normalize_array is an array with the values used to normalize

so just add or multiple your injected signal into norm_data and multiply by normalize array to get you filterbank data with injected signal back to original units


'''


if __name__ == '__main__':

    import numpy as np
    import matplotlib.pyplot as plt
    import sys
    import glob
    import os
    import argparse
    from lofasm.bbx import bbx as b
    from lofasm.clean import cleandata as cd

    parser = argparse.ArgumentParser()

    parser.add_argument('-lf_bin', action='store', dest='lower_frequency_bin',
    default = 0, help='What is the lower frequency bin?')

    parser.add_argument('-uf_bin', action='store', dest='upper_frequency_bin',
    default = 0, help='What is the upper frequency bin?')

    parser.add_argument('-f', dest='fast',
    default = False, help='Do you want to normalize with the fast option?')

    parser.add_argument('-ot', action='store', dest='o_thresh',
    default = 10, help='What is the threshold to be used for creating the outlier mask?')

    parser.add_argument('-nt', action='store', dest='nb_thresh',
    default = 1, help='What is the threshold to be used for creating the narrow band mask?')

    parser.add_argument('-wt', action='store', dest='wb_thresh',
    default = 1.7, help='What is the threshold to be used for creating the wide band mask?')

    parser.add_argument('-pol', action='store', dest='polarization',
    default = 'CC', help = 'what is the polarization you want to clean?')

    parser.add_argument('-fn', action='store', dest='file_name',
    default = '*.bbx.gz',
    help = 'do you want to clean a specific file or type of file? try ')

    args = parser.parse_args()

    # lower_frequency = args.lower_frequency_bin*(100/1024)
    # upper_frequency = args.upper_frequnecy_bin*(100/1024)

    for fname in glob.glob(args.file_name):
        lf = b.LofasmFile(fname)
        lf.read_data()
        if args.upper_frequency_bin == 0:
            args.upper_frequency_bin = int(lf.header['metadata']['dim2_len'])
        if 'frequency_offset_DC' in lf.header.keys():
            freq_off_set_DC = float(lf.header['frequency_offset_DC'].split()[0])
        else:
            freq_off_set_DC = 0.0

        freq_step = float(lf.header['dim2_span'])/float(lf.header['metadata']['dim2_len'])
        freq_start = float(lf.header['dim2_start']) + freq_off_set_DC
        lower_frequency = freq_start + args.lower_frequency_bin * freq_step
        upper_frequency = freq_start + args.upper_frequency_bin * freq_step
        print lower_frequency, upper_frequency
        data = 10*np.log10(lf.data[args.lower_frequency_bin:args.upper_frequency_bin])


        norm_data, normalize_array = cd.normalize(data,fast=args.fast)
        o_mask, outlier_average_top, outlier_average_bottom = cd.outlier_mask(norm_data,threshold= args.o_thresh)
        nb_mask, percent_clean_freq_channels = cd.narrow_band_mask(norm_data,threshold= args.nb_thresh)
        wb_mask, percent_clean_time = cd.wide_band_mask(norm_data,threshold= args.wb_thresh)

        print fname + '---------------------------'
        print 'top outlier average               : '+str(outlier_average_top)
        print 'bottom outlier average            : '+str(outlier_average_bottom)
        print 'percentage of clean freq channels : '+str(percent_clean_freq_channels)
        print 'percentage of clean time          : '+str(percent_clean_time)
        print ''
        print '-------------------------------------------------------'

        final = norm_data*wb_mask*o_mask*nb_mask
        final[np.isnan(final)]=1
        final = final*normalize_array


        lfc = b.LofasmFile('Clean_' + fname.rstrip('.gz'), mode = 'write')

        lfc.add_data(final)



        lfc.set('dim1_start',lf.header['dim1_start'])
        lfc.set('dim1_span',lf.header['dim1_span'])
        lfc.set('dim2_start',lower_frequency )
        lfc.set('dim2_span',(upper_frequency - lower_frequency))
        lfc.set('clean', True)
        lfc.set('station',lf.header['station'])
        lfc.set('channel',lf.header['channel'])

        lfc.write()
        lfc.close()

        print 'done'
