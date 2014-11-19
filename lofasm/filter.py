#library for LoFASM filters

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
