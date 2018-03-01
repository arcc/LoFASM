#!/usr/bin/env python2.7
#LoFASM Filterbank Plotter



def setup_plot(fig, ax, xmin,xmax,ymin,ymax,station, fbFile):
    ax.set_title('LoFASM %s' %station)
    ax.set_xlim([xmin,xmax])
    ax.set_ylim([ymin,ymax])
    ax.grid()
    line, = ax.plot([],[])
    return [line, fig]

def update_plot(i, line, fbFile):
    try:
        data = unpack('>2048L',fbFile.read(2048*4))
        line.set_data(FREQS,10*np.log10(data))
        return [line]
    except IOError as err:
        print err.strerror
        print err.filename


if __name__ == "__main__":
    import matplotlib.pyplot as plt
    import matplotlib.animation as animation
    import numpy as np
    import argparse
    from struct import unpack
    from sidereal import MJD

    parser = argparse.ArgumentParser(
        description="LoFASM Filberbank File Plotter")
    parser.add_argument("fb_file", type=str,
        help="LoFASM filterbank file to plot")
    parser.add_argument('--xmin', type=float,
        default=0.0,
        help="xmin")
    parser.add_argument('--xmax', type=float,
        default=100.0,
        help="xmax")
    parser.add_argument('--ymin', type=float,
        default=0,
        help="ymin")
    parser.add_argument('--ymax', type=float,
        default=100,
        help="ymax")
    parser.add_argument('-o',
        dest='output',
        action='store_true',
        help='if used then save a plot of the first integration in the file and exit.')
    args = parser.parse_args()

    BASELINES = ['AA', 'BB', 'CC', 'DD', 'AB', 'AC', 'AD', 'BC',
    'BD', 'CD']
    FREQS = np.linspace(0, 200, 2048)

    fig, ax = plt.subplots()

    try:
        with open(args.fb_file, 'rb') as f:
            #read header length
            hdr_len = int(f.read(10).strip())
            hdr_ver = int(f.read(10).strip())
            station = f.read(10).strip()
            numInt = int(f.read(10).strip())
            nBins = int(f.read(10).strip())
            fstart = float(f.read(10).strip())
            fstep = float(f.read(10).strip())
            mjd_day = float(f.read(10).strip())
            mjd_ms = float(f.read(10).strip())
            intTime = float(f.read(10).strip())
            target = f.read(10).strip()

            mjd = MJD(mjd_day + mjd_ms/86400000.0)
            startTime = mjd.datetime()



            line, fig = setup_plot(fig, ax, args.xmin, args.xmax, args.ymin,
                args.ymax, station, f)

            if args.output:
                update_plot(0,line, f)
                plt.draw()
                plt.savefig('lofasm3_%s.jpg' % startTime.strftime('%Y%m%d_%H%M%S'))
            else:
                anim = animation.FuncAnimation(fig,
                    update_plot,
                    fargs=(line, f),
                    frames=2049,
                    interval=300)

                plt.show()
                print 'exiting'




    except IOError as err:
        print err.strerror
        print err.filename
        exit()
