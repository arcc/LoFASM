import lofasm.bbx.bbx as b
import numpy as np
import matplotlib.pyplot as plt
import sys
import glob
import os
import argparse


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


def normalize(data,fast = False,window=200):
	'''
	Returns normalized filterbank data


	Parameters
	----------
	Data 		Any size 2D array containing lofasm filterbank data 									(one frequency channels should work too)

	Fast    	True  -> normalize frequency channels w.r.t. whole file 								(faster)
				False -> normalize frequency channels w.r.t. sliding window given by variable 'window' 	(better)

	Window      Number of elements on each side of data point to consider for normalization

	'''

	normalized_data = np.ones_like(data)
	normalize_array = np.ones_like(data)
	print 'Normalizing'

	if not(fast):

		for spec in range(len(data[0,:])-(2*window)):
			spec += window
			for freq in range(len(data[:,0])):
				d = data[freq,spec]
				av = np.average(data[freq,spec-window:spec+window])
				normalized_data[freq,spec] = d/av
				normalize_array[freq,spec] = av

		for freq in range(len(data[:,0])):
			normalized_data[freq,0:window] = data[freq,0:window]/np.average(data[freq,0:(2*window)])
			normalize_array[freq,0:window] = np.average(data[freq,0:(2*window)])

		for freq in range(len(data[:,0])):
			normalized_data[freq,-window:] = data[freq,-window:]/np.average(data[freq,-(2*window):])
			normalize_array[freq,-window:] = np.average(data[freq,-(2*window):])#

	else:

		for spec in range(len(data[:,0])):
			normalized_data[spec,:] = data[spec,:]/np.average(data[spec,:])

	return normalized_data, normalize_array

def outlier_mask(data,threshold=10):
	'''
	Returns mask to cover outliers

	Parameters
	----------
	Data 		any size 2D array containing lofasm filterbank data 	(should pass normalized data)

	Threshold   set top and bottom percentile to removed 				(try 5 < threshold < 15)

	'''

	print "Removing outliers"

	outlier_mask_top = np.ones_like(data)
	outlier_mask_bottom = np.ones_like(data)
	top = np.percentile(data,100-threshold)
	bottom = np.percentile(data,threshold)

	for row in range(len(data)):
		for i in range(len(data[0,:])):
			if (data[row,i] > top):
				outlier_mask_top[row,i] = np.nan # or np.nan

	for row in range(len(data)):
		for i in range(len(data[0,:])):
			if (data[row,i] < bottom):
				outlier_mask_bottom[row,i] = np.nan # or np.nan



	outlier_average_top = np.average(data[np.isnan(outlier_mask_top)])
	outlier_average_bottom = np.average(data[np.isnan(outlier_mask_bottom)])

	outlier_mask = outlier_mask_top*outlier_mask_bottom

	return outlier_mask,outlier_average_top,outlier_average_bottom

def narrow_band_mask(data,threshold=1):
	'''
	returns mask covering frequency channels with RFI

	Keyword arguments:
	data 		any size 2D array containing lofasm filterbank data 									(should pass normalized data)

	threshold   standard deviations to flag bad freq channel											(try .5 < threshold < 1.5)
	'''

	#calculate s[f]
	nb_mask = np.ones_like(data)
	s = range(len(data))
	for f in range(len(data)):
		'''
		mu = 0
		#print "finding bad frequency bin " + str(f)
		for xt in data[f]:
			mu += xt/len(data[:,0])
		n = 0
		for xt in data[f]:
			n += (xt**2) / (mu**2)
		'''
		n=0
		for xt in data[f]:
			n += (xt**2)

		s[f]=n

	# w is s[f] with outliers removed to make std and average more sensitive
	w = []
	for f in range(len(s)):
		if s[f] < np.percentile(s,90) or s[f] > np.percentile(s,10):
			w.append(s[f])

	#add bad freq channels to mask
	for f in range(len(s)):
		if s[f] > np.average(w)+(threshold*np.std(w)) or s[f] < np.average(w)-(threshold*np.std(w)):
			nb_mask[f,:] = np.nan
	percent_clean_freq_channels = float(np.count_nonzero(~np.isnan(nb_mask[:,0])))/float(len(data[:,0]))

	return nb_mask, percent_clean_freq_channels

def wide_band_mask(data,threshold=1.7):
	'''
	returns mask covering wide frequecny band RFI

	Keyword arguments:
	data 		any size 2D array containing lofasm filterbank data 									(should pass normalized data)

	threshold   standard deviations to flag bad times          											(try 1.0 < threshold < 2.0)
	'''

	print "creating wide band mask"
	wb_mask = np.ones_like(data)
	tbins = len(data[0,:])
	sub_bands = np.zeros((5.0 , tbins))
	sub_band_size = 100.0
	for i in range(5):

		sub_bands[i] = np.nansum(data[i*sub_band_size:(i*sub_band_size)+sub_band_size,:], axis = 0)
		sub_bands[i] = sub_bands[i] / sub_band_size

	bad_bands = np.zeros((5 , tbins))

	for band in range(5):
		t = np.average(sub_bands[band])
		std = np.std(sub_bands[band])
		for time in range(len(sub_bands[band])):
			if sub_bands[band,time] > t+(threshold*std) or sub_bands[band,time] < t-(threshold*std):
				bad_bands[band,time]=1

	bad_bands = np.nansum(bad_bands,axis=0)

	for i in range(len(bad_bands)):
		if bad_bands[i] >= 3:
			wb_mask[:,i] = np.nan


	percent_clean_time = float(np.count_nonzero(~np.isnan(wb_mask[300,:])))/ len(wb_mask[300,:])

	return wb_mask, percent_clean_time

if __name__ == '__main__':
    '''
	try:
    	os.makedirs('Cleaned/')
	except OSError:
    	if not os.path.isdir('Cleaned/'):
        	raise
    '''


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


        norm_data, normalize_array 									= normalize(data,fast=args.fast)
        o_mask   , outlier_average_top, outlier_average_bottom		= outlier_mask(norm_data,threshold= args.o_thresh)
        nb_mask  , percent_clean_freq_channels 						= narrow_band_mask(norm_data,threshold= args.nb_thresh)
        wb_mask  , percent_clean_time 								= wide_band_mask(norm_data,threshold= args.wb_thresh)

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


		# plt.imshow(final, aspect = 'auto', origin = 'lower', cmap='gray')
		# plt.colorbar()
		# plt.savefig('Cleaned/' + fname.rstrip('.bbx.gz') + '.png', dpi=200)
		# plt.close()
