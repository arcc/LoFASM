#library for LoFASM filters

import numpy as np

def running_median(y, N=50):
    '''
    Given a list, y, perform a running median filter.
    Return the resulting list.

    N is the total number of points to be considered for the
    running median. The default is 50, so for any point X(n)
    the values considered will be [X(n-25),X(n+25)], inclusive.

    If N is not an even number then it will be changed to
    even number N-1.

    If N is not an integer it will be truncated.
    '''
    N = int(N)
    
    if N % 2 != 0: 
        print 'running_median: N=%i is not even. Using N=%i instead.' % (N,N-1)
        N -= 1
        
    ymed = [] # Empty list for new values    
    for i in range(len(y)):
        a=[] # Store values to determine new value of one point
        for j in range(i-N/2, i+1+N/2):
            if j >= 0 and j < len(y):
                a.append(y[j])
        a.sort(cmp=None, key=None, reverse=False)
        ymed.append(a[(len(a)-1)/2+1])
    return ymed


def medfilt (x, k):
    """Apply a length-k median filter to a 1D array x.
    Boundaries are extended by repeating endpoints.
    """
    assert k % 2 == 1, "Median filter length must be odd."
    assert x.ndim == 1, "Input must be one-dimensional."
    k2 = (k - 1) // 2
    y = np.zeros ((len (x), k), dtype=x.dtype)
    y[:,k2] = x
    for i in range (k2):
        j = k2 - i
        y[j:,i] = x[:-j]
        y[:j,i] = x[0]
        y[:-j,-(i+1)] = x[j:]
        y[-j:,-(i+1)] = x[-1]
    return np.median (y, axis=1)
