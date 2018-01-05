from lofasm.bbx import bbx
import numpy as np
from lofasm.parse_data import freq2bin

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
    freq_avg_list = []
    if isinstance(freqs, list):
        freqs.sort()
        for i in range(len(freqs)):
            lfbin = freq2bin(freqs[i] - bw / 2.)
            hfbin = freq2bin(freqs[i] + bw / 2.)
            num_fbins = hfbin - lfbin
            num_tbins = np.shape(lfx.data)[1]        
            avg_ts = np.average(lfx.data[lfbin:hfbin,:], axis=0)
            freq_avg_list.append(deepcopy(avg_ts))
        rows = len(freq_avg_list)
        cols = max([len(x) for x in freq_avg])
        data = np.zeros((rows,cols), dtype=np.float64)
        for i in range(rows):
            data[i,:] = freq_avg_list[i]
    else:
        lfbin = freq2bin(freqs - bw / 2.)
        hfbin = freq2bin(freqs + bw / 2.)
        avg_ts = np.average(lfx.data[lfbin:hfbin, :], axis=0)
        data = avg_ts
    lfx.close()
    return data


def freq_averaged_minimum(filename, freqs, bw=1.):
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
    
    freq_avg = freq_average_file(filename, freqs, bw)
    if isinstance(freqs, list):
        mins = np.zeros(np.shape(freq_avg)[0], dtype=np.float64)
        for i in range(len(freqs)):
            mins[i] = np.min(freq_avg[i,:])
    else:
        mins = np.min(freq_avg)
    return mins
