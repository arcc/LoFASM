# time module

def UT_to_GMST(jd, ut):
    '''
    Convert JD, UT to unwrapped GMST.
    '''
    return 6.656306 + 0.0657098242 * (JD-2445700.5) + 1.0027279093*UT

def GMST_to_LST(gmst, lon):
    '''
    Convert GMST to Local Sideral Time (LST) given west longitude in degrees.
    Result will range from 0 - 24 hours.
    '''
    x = gmst - lon*(24./360.)
    return x % 24

def UT_to_LST(jd, ut, wlon):
    '''
    Convert from JD, UT to LST given west longitude in degrees.
    '''
    gmst = UT_to_GMST(jd, ut)
    return GMST_to_LST(gmst, lon)
