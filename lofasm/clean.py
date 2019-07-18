# lofasm cleaning routines

from .bbx import bbx
import numpy as np
from copy import deepcopy

def running_median(x, r=50, axis=0):
    '''
    execute running median filter on x.

    Parameters
    ----------
    x : array_like
        Array to be filtered
    r : int
        number of elements to include in running window on each side
        of current position
    axis : int
        axis along which to execute running filter

    Returns
    -------
    y : ndarray
        an array containing the resultant filtered data
    '''
    assert axis < x.ndim, "Axis is out of bounds"
    assert x.shape[axis] > 2*r+1, "Window size (2*r+1) must be smaller than number of points along axis"
    assert axis <= 1, "only 1d and 2d arrays supported"

    if axis == 1:
        x = np.rot90(x)

    y = np.zeros_like(x)
    for i in range(r):
        y[i, :] = np.median(x[:i+r+1, :], axis=0)
        y[-(i+1), :] = np.median(x[-(i+1+r):, :], axis=0)
    for i in range(x.shape[0] - 2*r):
        j = i + r
        y[j, :] = np.median(x[j-r:j+r+1, :], axis=0)

    if axis == 1:
        y = np.rot90(y, k=-1)

    return y

def running_minimum(x, r=50, axis=0):
    '''
    execute running min filter on x.

    Parameters
    ----------
    x : array_like
        array to be filtered
    r : int
        number of elements to include in running window on each side
        of current position
    axis : int
        axis along which to execute running filter

    Returns
    -------
    y : ndarray
        an array containing the resultant filtered data
    '''
    assert axis < x.ndim, "Axis is out of bounds"
    assert x.shape[axis] > 2*r+1, "window size (2*r+1) must be less than number of points along axis"
    assert axis <= 1, "only 1d and 2d arrays supported"

    if axis == 1:
        x = np.rot90(x)

    y = np.zeros_like(x)
    for i in range(r):
        y[i, :] = np.amin(x[:i+r+1, :], axis=0)
        y[-(i+1), :] = np.amin(x[-(i+1+r):, :], axis=0)
    for i in range(x.shape[0] - 2*r):
        j = i + r
        y[j, :] = np.amin(x[j-r:j+r+1, :], axis=0)
    
    if axis == 1:
        y = np.rot90(y, k=-1)

    return y
