#!/usr/bin/python
# Calibration tool

if __name__ == "__main__":

    import argparse
    import lofasmcal as lfc
    import numpy as np

    #Parse arguments
    ap = argparse.ArgumentParser()
    ap.add_argument('files', type=str)
    ap.add_argument('freq', type=float) #Freq in MHz
    ap.add_argument('station', type=int)
    args = ap.parse_args()

    files = args.files
    freq = args.freq
    station = args.station

    #Read data from files
    dh = lfc.data_handler()
    dh.read_files(files, freq, verbose=False)

    if len(dh.filelist) == 0:
        raise ValueError('No LoFASM files found')

    #Generate galaxy models
    gal = lfc.galaxy()
    g_power = gal.galaxy_power_array(dh.times_array, freq, station, verbose=False)

    #Fit data to model -> get calibration parameters
    fit = lfc.fitter(dh.data, g_power)
    cal_pars = fit.cal_pars()

    print cal_pars
