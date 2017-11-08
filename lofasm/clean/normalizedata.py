import lofasm.bbx.bbx as b
import numpy as np
import sys
import os
import argparse

def running_median(data, median_window=201):
    """
    This is a function runs a running median filter.
    Parameters
    ----------
    data: numpy 2d array
        The data to apply the running median
    median_window: optional, int
        The running median window. If it an even integer, it will be changed to
        and odd number.
    """
    print("Applying running median filter.")
    if median_window % 2 == 0:
        median_window += 1
    half_window = median_window/2
    median_data = np.zeros(data.shape)
    t_bin = data.shape[1]
    # Get the edge window data
    median_data[:, 0:half_window] = data[:, 0:half_window]
    for ii in range(half_window, t_bin - half_window):
        median_data[:,ii] = np.median(data[:,ii - half_window:
                                           ii + half_window], axis=1)
    median_data[:, - half_window:] = data[:, - half_window:]
    return median_data

def running_min(data, running_min_window=100):
    """
    This is a function runs a running minimum filter.
    Parameters
    ----------
    data: numpy 2d array
        The data to apply the running median
    running_min_window: optional, int
        The window to apply running minimum. If it an even integer, it will be
        changed to and odd number.
    """
    if running_min_window % 2 == 0:
        running_min_window += 1
    half_window = running_min_window/2
    min_data = np.zeros(data.shape)
    f_bin = data.shape[0]
    # Get the edge window data
    full = np.vstack((data, np.zeros((half_window, data.shape[1]))))
    full = np.vstack((np.zeros((half_window, data.shape[1])), full))
    for ii in range(0, f_bin):
        windowed_data = full[ii : ii + running_min_window,:]
        nonzero = np.ma.masked_equal(windowed_data, 0)
        min_data[ii,:] = np.amin(nonzero, axis=0).data
    return min_data

def robust_normalize(data, median_window=201, running_min_window=5,
                           average_window = 201):
    """
    This is a function to normalize data. Normalize steps
    1. Running median on time axis for each frequency, to clean some short time
       loud noise.
    2. Running minimum on frequency axis for each time and average for all time
    3. Data will be divided by the average running minimum
    Parameters
    ----------
    data : numpy 2d array
        In put data
    median_window : odd int
        The running median window
    running_min_window : odd int
        The runing minimum window
    Note
    ----
    We assume the 2D array's dimension 1 is frequency axis and dimension 2 is
    time axis.
    """
    print("Performing running median filter.")
    median_data = running_median(data, median_window)
    print("Performing running minimum filter.")
    min_data = running_min(median_data, running_min_window)
    t_bin = min_data.shape[1]
    normal_data = np.zeros_like(data)
    for ii in range(0, t_bin - average_window):
        windowed_min = min_data[:, ii : ii + average_window]
        ave_min = np.sum(windowed_min, axis=1)/windowed_min.shape[1]
        normal_data[:, ii] = data[:, ii] / ave_min
    for ii in range(t_bin - average_window, t_bin):
        normal_data[:, ii] = data[:, ii] / ave_min
    return normal_data, np.sum(min_data, axis=1)/min_data.shape[1]
