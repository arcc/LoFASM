#! /usr/bin/env python
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from glob import glob
from lofasm.bbx import bbx
from lofasm.time import UT_to_LST
from lofasm.galaxy_model import galaxyPower
from lofasm.station import LoFASM_Stations
from astropy.time import Time
from lofasm.parse_data import freq2bin
from scipy.optimize import curve_fit


def avgpow(lf,freq):
    x = lf.data[freq2bin(freq), :]
    return(np.mean(x))



if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('fnames',nargs='+')
    p.add_argument('freq',type = float)
    args = p.parse_args()

    x = []

    for f in args.fnames:
        lf = bbx.LofasmFile(f)
        lf.read_data()
        pows = lf.data[freq2bin(args.freq),:]
        avg = np.mean(pows)
        start = lf.header['start_time']
        start_cv = Time(start, scale = 'utc')
        st = int(lf.header['station'])
        lfstation = LoFASM_Stations[st]
        lon = lfstation.lon * 180 / np.pi
        start_sr = start_cv.sidereal_time('mean', lon)
        start_hr = start_sr.hour

        powmodel = galaxyPower.calculatepower(start_hr,st,args.freq,0)
        x.append((start,avg,powmodel))

    t, avg, gal = zip(*x)
    def linearData(l,a,b):
        return(a*np.array(gal)+b)
    popt, pcov = curve_fit(linearData,len(avg),avg)
    calib = linearData(1,*popt)
    plt.figure()
    plt.title('Power vs LST')
    plt.plot(t, 10*np.log10(avg), '.', label = 'LoFASM')
    plt.plot(t, 10*np.log10(gal), '.', label = 'Model')
    plt.plot(t, 10*np.log10(calib), '.', label = 'Calib')
    plt.legend()
    plt.figure()
    plt.plot(t, 10*np.log10(calib), '.', label = 'Calib')
    plt.plot(t, 10*np.log10(gal), '.', label = 'Model')
    plt.legend()
    plt.show()
