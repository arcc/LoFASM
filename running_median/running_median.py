def running_median(y,med_range):
    """ Takes a list, y, and returns a new list with each point replaced
        by the median of the number of points in med_range."""
    if med_range%2 != 0:
        print 'Enter an even number for median range.'
        return
    ymed = [] # Empty list for new values    
    for i in range(len(y)):
        a=[] # Store values to determine new value of one point
        for j in range(i-med_range/2, i+1+med_range/2):
            if j >= 0 and j < len(y):
                a.append(y[j])
        a.sort(cmp=None, key=None, reverse=False)
        ymed.append(a[len(a)/2])
    return ymed
