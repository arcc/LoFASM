import lofasm.bbx.bbx as b
import numpy as np
import matplotlib.pyplot as plt
import sys
import glob
import os
import argparse

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
    sub_bands = np.zeros((5 , tbins))
    sub_band_size = 100
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



def clean(data):

    lf = b.LofasmFile(fname)
    lf.read_data()      
    data = 10*np.log10(lf.data[args.lower_frequency_bin:args.upper_frequnecy_bin])

    
    norm_data, normalize_array                                  = c.normalize(data,fast=args.fast)
    o_mask   , outlier_average_top, outlier_average_bottom      = c.outlier_mask(norm_data,threshold= args.o_thresh)
    nb_mask  , percent_clean_freq_channels                      = c.narrow_band_mask(norm_data,threshold= args.nb_thresh)
    wb_mask  , percent_clean_time                               = c.wide_band_mask(norm_data,threshold= args.wb_thresh)
    
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
    lfc.set('dim2_start',lower_frequency * 1e6)
    lfc.set('dim2_span',(upper_frequency - lower_frequency)*1e6)
    lfc.set('clean', True)7uup
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
