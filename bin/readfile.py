#! /usr/bin/env python2.7

if __name__ == "__main__":
    import numpy as np
    import pickle
    import argparse
    import matplotlib.pyplot as plt
    import lofasm.parse_data as pdat

    p = argparse.ArgumentParser(description='read and plot pickled lofasm data')

    p.add_argument('filename', help='file to open')

    args = p.parse_args()

    with open(args.filename, 'rb') as f:
        fdata = pickle.load(f)

    fbdata = 10*np.log10(fdata['fbdata'])
    freqs = pdat.freqRange(fdata['lfreq'],fdata['hfreq'])

    plt.plot(freqs,fbdata)
    plt.xlabel('Frequency MHz')
    plt.ylabel('Power (dB)')
    plt.title('LoFASM 3 {} {}s'.format(fdata['stime'], fdata['dtime'].total_seconds()))
    plt.grid()
    plt.show()
