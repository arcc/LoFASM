#!/usr/bin/env python
# LoFASM Data Plotter
#import matplotlib.pyplot as plt
#import numpy as np


if __name__ == '__main__':
    import sys
    from lofasm import animate_lofasm as ani_lofasm
    from lofasm import parse_data as pdat
    from optparse import OptionParser
    import gzip
#    from lofasm import lofasm_dat_lib as lofasm

    p = OptionParser()
    p.set_usage('lofasm_plot.py -f lofasm_data_filename [options]')
    p.set_description(__doc__)
    p.add_option('-f', '--filename', dest='input_filename', type='str',
        help="path to LoFASM Data file to be opened.")
    p.add_option('--packet_size_bytes', dest='packet_size_bytes', type='int',
        default=8192, help="Set the size of each packet in bytes.")
    p.add_option('-s', '--start_position', dest='start_position', type='int', 
        default=-1,
        help='Set file start position. This is also the number \
        of bytes to skip at the beginning of the file.')
    p.add_option('--getfilesize', dest='getFileSize', action='store_true')
    p.add_option('--xmin', dest='xmin', type='float', default=18,
        help='set the xmin value to plot')
    p.add_option('--xmax', dest='xmax', type='float', default=80,
        help='set the xmax value to plot')
    p.add_option('--ymin', dest='ymin', type='float', default=0,
        help='set the ymin value to plot')
    p.add_option('--ymax', dest='ymax', type='float', default=100,
        help='set the ymax value to plot')
    p.add_option('-d','--frame_duration', dest='frame_dur', type='float',
        default=100, 
        help='duration of each animated frame in ms. default is 100.')
    p.add_option('-G', dest='gzip', action='store_true',
                 help="read in gzip mode. not needed if filename ends with '.gz' ")

    opts, args = p.parse_args(sys.argv[1:])
    
    if not opts.input_filename:
        print "Please provide the path to the target LoFASM file using -f."
        exit()
    else:
        input_filename = opts.input_filename
        if input_filename.endswith(".gz") or opts.gzip:
            lofasm_input_file = gzip.open(input_filename, 'r')
        else:
            lofasm_input_file = open(input_filename, 'rb')
        
    hdr_dict = pdat.parse_file_header(lofasm_input_file)

    lofasm_station = hdr_dict[4][1]
    
   
    #get starting location (beginning of data)
    if opts.start_position < 0:
        print "Starting from location 0."
        crawler = pdat.LoFASMFileCrawler(opts.input_filename)
        crawler.open()
    else:
        print "Skipping to specified location: %i" %( opts.start_position)
        lofasm_input_file.seek(opts.start_position) #is this still necessary?
        crawler = pdat.LoFASMFileCrawler(opts.input_filename, start_loc=opts.start_position)
        crawler.open()
        print crawler.getFileHeader()
        
    burst_size_bytes = opts.packet_size_bytes * 17
    filesize_bytes = pdat.get_filesize(lofasm_input_file)
    num_frames = int((filesize_bytes - opts.start_position) / burst_size_bytes) - 1

    #get filesize and exit
    if opts.getFileSize:
        print pdat.get_filesize(lofasm_input_file)
        exit(0)

    #plot single frame of all baselines
    try:
        lines, fig = ani_lofasm.setup_all_plots(opts.xmin, opts.xmax, opts.ymin, opts.ymax, lofasm_station, crawler)
        
        anim = ani_lofasm.animation.FuncAnimation(fig, 
            ani_lofasm.update_all_baseline_plots, 
            fargs=(fig, crawler, lines), 
            frames=num_frames, interval=opts.frame_dur,)

        #print "saving video."
        #print anim.save('test.avi', codec='avi')
        ani_lofasm.plt.show()
    except KeyboardInterrupt:
        exit()
    except EOFError as err:
        print err
        raw_input("press enter to quit.")

