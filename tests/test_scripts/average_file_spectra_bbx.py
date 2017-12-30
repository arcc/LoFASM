#! /usr/bin/env python



if __name__ == "__main__":
    import argparse
    import matplotlib
    matplotlib.use('agg') #  on headless linux
    import matplotlib.pyplot as plt
    from lofasm.bbx import bbx
    import numpy as np

    
    p = argparse.ArgumentParser()
    p.add_argument('filename', type=str, help="path to BBX file")
    args = p.parse_args()

    lfx = bbx.LofasmFile(args.filename)
    lfx.read_data()
    startt = lfx.header['start_time']
    avg_spectra = np.average(lfx.data, axis=1)

    plt.figure()
    plt.title('L1 Average Spectra {}'.format(startt))
    plt.plot(10*np.log10(avg_spectra), label='Avg. Spectra')
    plt.legend()
    plt.savefig('{}.avg.png'.format(lfx.fname), format='png')
