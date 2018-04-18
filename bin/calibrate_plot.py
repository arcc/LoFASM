#! /usr/bin/env python

from lofasm.bbx import bbx
from lofasm.time import UT_to_LST
from lofasm.galaxy_model import galaxyPower
from lofasm.station import LoFASM_Stations
from astropy.time import Time
from lofasm.parse_data import freq2bin
from scipy.optimize import curve_fit
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from glob import glob

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
        x.append((start_hr,avg,powmodel))

    t, avg, gal = zip(*x)

    def lst2pow(lst):
        x = np.zeros_like(lst)
        for i in range(len(lst)):
            x[i] = galaxyPower.calculatepower(lst[i],st, args.freq,0)
        return x

    def linearData(xdata,a,b):
        return a * (lst2pow(xdata) + b)

    popt, pcov = curve_fit(linearData,t,avg)
    calib = linearData(t,*popt)
    plt.figure()
    plt.title('Power vs LST')
    plt.plot(t, 10*np.log10(avg), '.', label = 'LoFASM')
    # plt.plot(t, 10*np.log10(gal), '.', label = 'Model')
    plt.plot(t, 10*np.log10(calib), '.', label = 'Calib')
    plt.legend()
    plt.savefig('Lofasm-Calib.png')
    plt.figure()
    plt.plot(t, 10*np.log10(calib), '.', label = 'Calib')
    plt.plot(t, 10*np.log10(gal), '.', label = 'Model')
    plt.legend()
    plt.savefig('Calib-Model')
    #plt.show()
