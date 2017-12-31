import numpy as np
from lofasm.parse_data import freq2bin, LoFASMFileCrawler
from astropy.time import Time
from datetime import datetime
from lofasm.parse_data_H import IntegrationError
from copy import deepcopy

def _load_data(filename, pol):
    '''
    read entire file in polarization.
    returns a tuple with a mjd list and corresponding data samples
    '''
    cwl = LoFASMFileCrawler(filename)
    cwl.open()
    cwl.setPol(pol)
    num_fbins = 1024
    if not cwl.gz:
        num_tbins = cwl.getNumberOfIntegrationsInFile()
    else:
        # using a maximum size of 5000 samples for now
        # This will break for larger lofasm files
        num_tbins = 5000
    data = np.zeros((num_fbins, num_tbins), dtype=np.float64)
    mjds = np.zeros(num_tbins, dtype=np.float64)

    # load first integration information
    data[:,0] = cwl.get()[:num_fbins]
    mjds[0] = cwl.time.mjd

    # read the rest of the file
    i=1
    badIntegration = False
    while(1):
        try:
            if badIntegration:
                cwl.moveToNextBurst()
                badIntegration = False
            else:
                cwl.forward()
            data[:,i] = cwl.get()[:num_fbins]
            mjds[i] = cwl.time.mjd
            i += 1
        except IntegrationError:
            badIntegration = True
        except EOFError:
            break
    return (mjds, data)

def freq_average_file(filename, freqs, pol, bw=1.):
    '''
    take a list of frequency bands of width bw centered at freq from 
    each filterbank sample calculate the average over time.
    the minimum value of this averaged time series will be returned.

    Parameters
    ----------
    filename : str
        the data file to process
    freqs : int or list
        list of the selected center frequencies in MHz
    pol : str
        polarization to process
    bw : float, optional
        the bandwidth to include in the frequency averaging

    Returns
    -------
    freq_avg : numpy.array
                       array of frequency averaged time series minimum values,
                       each corresponding to its respective center
                       frequency at input
    '''
    _, filedata = _load_data(filename, pol)
    freq_avg_list = []
    if isinstance(freqs, list):
        freqs.sort()
        for i in range(len(freqs)):
            lfbin = freq2bin(freqs[i] - bw / 2.)
            hfbin = freq2bin(freqs[i] + bw / 2.)
            num_fbins = hfbin - lfbin
            num_tbins = np.shape(filedata)[1]        
            avg_ts = np.average(filedata[lfbin:hfbin,:], axis=0)
            freq_avg_list.append(deepcopy(avg_ts))
        rows = len(freq_avg_list)
        cols = max([len(x) for x in freq_avg_list])
        data = np.zeros((rows,cols), dtype=np.float64)
        for i in range(rows):
            data[i,:] = freq_avg_list[i]
    else:
        lfbin = freq2bin(freqs - bw / 2.)
        hfbin = freq2bin(freqs + bw / 2.)
        num_fbins = hfbin - lfbin
        avg_ts = np.average(filedata[lfbin:hfbin,:], axis=0)
        data = avg_ts
        

    return data


def freq_averaged_minimum(filename, freqs, pol, bw=1.):
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
    freq_avg_min_list : list
                       list of frequency averaged time series minimum values,
                       each corresponding to its respective center
                       frequency at input
    '''
    
    freq_avg = freq_average_file(filename, freqs, pol, bw)
    if isinstance(freqs, list):
        mins = np.zeros(np.shape(freq_avg)[0], dtype=np.float64)
        for i in range(len(freqs)):
            mins[i] = np.min(freq_avg[i,:])
    else:
        mins = np.min(freq_avg)
    return mins
