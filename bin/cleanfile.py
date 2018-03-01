#! /usr/bin/env python

from lofasm.clean import cleandata as c
import lofasm.bbx.bbx as b
import numpy as np
import matplotlib.pyplot as plt
import sys
import glob
import os
import argparse


parser = argparse.ArgumentParser()

parser.add_argument('-lf_bin', action='store', dest='lower_frequency_bin',
default = 200, help='What is the lower frequency bin?')

parser.add_argument('-uf_bin', action='store', dest='upper_frequnecy_bin',
default = 700, help='What is the upper frequency bin?')

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

lower_frequency = args.lower_frequency_bin*(100.0/1024.0)
upper_frequency = args.upper_frequnecy_bin*(100.0/1024.0)

for fname in glob.glob(args.file_name):


	lf = b.LofasmFile(fname)
	lf.read_data()
	data = 10*np.log10(lf.data[args.lower_frequency_bin:args.upper_frequnecy_bin])


	norm_data, normalize_array 									= c.normalize(data,fast=args.fast)
	o_mask   , outlier_average_top, outlier_average_bottom		= c.outlier_mask(norm_data,threshold= args.o_thresh)
	nb_mask  , percent_clean_freq_channels 						= c.narrow_band_mask(norm_data,threshold= args.nb_thresh)
	wb_mask  , percent_clean_time 								= c.wide_band_mask(norm_data,threshold= args.wb_thresh)

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


	lfc = b.LofasmFile('Clean_' + fname.rstrip('.gz'), header=lf.header, mode = 'write')

	lfc.add_data(final)

	print lower_frequency
	print upper_frequency

	lfc.set('dim1_start',lf.header['dim1_start'])
	lfc.set('dim1_span',lf.header['dim1_span'])
	lfc.set('dim2_start',lower_frequency * 1e6)
	lfc.set('dim2_span',(upper_frequency - lower_frequency)*1e6)
	lfc.set('clean', True)
	lfc.set('station',lf.header['station'])
	lfc.set('channel',lf.header['channel'])

	lfc.write()
	lfc.close()

	print 'done'

	'''
	plt.imshow(final, aspect = 'auto', origin = 'lower', cmap='gray')
	plt.colorbar()
	plt.savefig('Cleaned/' + fname.rstrip('.bbx.gz') + '.png', dpi=200)
	plt.close()
	'''
