#!/usr/bin/env python2.7
# LoFASM Data Plotter
import matplotlib.pyplot as plt
import numpy as np


def plot_all_baselines(burst_obj):
    '''
    plot all baselines at once.
    '''
    auto_baselines = ['AA', 'BB', 'CC', 'DD']
    cross_baselines = ['AB', 'AC', 'AD', 'BC', 'BD', 'CD']
    fig = plt.figure()
    auto_plots = [fig.add_subplot(4,4,i) for i in [1, 6, 11, 16]]
    cross_plots = [fig.add_subplot(4,4,i) for i in 
        [2, 3, 4, 7, 8, 12]]

    freqs = np.linspace(0, 200, 2048)
    # set titles & plot
    for i in range(len(cross_baselines)):
        if i < 4:
            auto_plots[i].set_title(auto_baselines[i])
            auto_plots[i].plot(freqs, 
                10*np.log10(burst_obj.autos[auto_baselines[i]]))
            auto_plots[i].set_xlim(0, 200)
        
        cross_plots[i].set_title(cross_baselines[i])
        cross_plots[i].plot(freqs, 
            10*np.log10(np.abs(burst_obj.cross[cross_baselines[i]])))
        cross_plots[i].set_xlim(0, 200)
    #fig.set_size_inches(8,8)
    #fig.set_dpi(200)
    fig.show()

##########################################################################

if __name__ == '__main__':
    import sys
    from lofasm import animate_lofasm as ani_lofasm
    from lofasm import parse_data as pdat
    from optparse import OptionParser
    from lofasm import lofasm_dat_lib as lofasm
    
    p = OptionParser()
    p.set_usage('lofasm_plot.py <lofasm_data_filename> [options]')
    p.set_description(__doc__)
    p.add_option('-f', '--filename', dest='input_filename', type='str',
        help="path to LoFASM Data file to be opened.")
    p.add_option('--packet_size_bytes', dest='packet_size_bytes', type='int',
        default=8192, help="Set the size of each packet in bytes.")
    p.add_option('--check_headers', dest='check_headers', action='store_true',
        help='Set flag to print out header information from each packet '
        + 'in file.')
    p.add_option('--start_position', dest='start_position', type='int', 
        default=-1, 
        help='Set file start position. This is also the number \
        of bytes to skip at the beginning of the file.')
    p.add_option('--plot_single_frame', dest='plot_single_frame', 
        action='store_true', help='set if you only want to plot a single '
        + 'frame.')
    p.add_option('--animate_all', dest='animate_all', 
        action='store_true', help='set to animate all baselines starting from ' 
        + 'starting position.')
    p.add_option('--animate_baseline', dest='animate_baseline', type='str', default='',
        help='select baseline to plot')
    p.add_option('--animate_beams', dest='animate_beams', action='store_true', 
        help='animate LoFASM Beams')
    p.add_option('--TimeFrequencyPlot', dest='TimeFrequencyPlot', type='str',
        help='select baseline (NS or EW) to plot TimexFrequency (colormap)')
    p.add_option('--getfilesize',dest='getFileSize',action='store_true')
    p.add_option('--xmin', dest='xmin', type='float', default=0,
        help='set the xmin value to plot')
    p.add_option('--xmax', dest='xmax', type='float', default=100,
        help='set the xmax value to plot')
    p.add_option('--ymin', dest='ymin', type='float', default=0,
        help='set the ymin value to plot')
    p.add_option('--ymax', dest='ymax', type='float', default=100,
        help='set the ymax value to plot')
    p.add_option('-l','--loop', dest='loop_file', action='store_true',
        help='set to loop through data file.')
    p.add_option('-d','--frame_duration', dest='frame_dur', type='int',
        default=1000, 
        help='duration of each animated frame in ms. default is 1000.')
    p.add_option('-w','--TF_PlotWidth', dest='TF_PlotWidth', type='float', 
        default=84.8, 
        help='specify width of TimexFrequency plot in ms. Default is 84.8ms.')
    p.add_option('--norm_cross', dest='norm_cross', action='store_true',
        help='Set flag to plot normalized cross-correlation function instead of cross-power.')
    opts, args = p.parse_args(sys.argv[1:])
    
    if not opts.input_filename:
        print "Please provide the path to the target LoFASM file using -f."
        exit()
    else:
        input_filename = opts.input_filename
        lofasm_input_file = open(input_filename, 'rb')
    hdr_dict = pdat.parse_file_header(lofasm_input_file)

    lofasm_station = hdr_dict[4][1]
    
   
    #get starting location (beginning of data)
    if opts.start_position < 0:
        print "Starting from location 0."
        crawler = pdat.LoFASMFileCrawler(opts.input_filename, scan_file=True)
    else:
        print "Skipping to specified location: %i" %( opts.start_position)
        lofasm_input_file.seek(opts.start_position) #is this still necessary?
        crawler = pdat.LoFASMFileCrawler(opts.input_filename, start_loc=opts.start_position)
        print crawler.getFileHeader()
        
    burst_size_bytes = opts.packet_size_bytes * 17
    filesize_bytes = pdat.get_filesize(lofasm_input_file)
    num_frames = int((filesize_bytes - opts.start_position) / burst_size_bytes) - 1

    #get filesize and exit
    if opts.getFileSize:
        print pdat.get_filesize(lofasm_input_file)
        exit(0)

    #plot single frame of all baselines
    if opts.plot_single_frame:
        lines = ani_lofasm.setup_all_plots(opts.xmin, opts.xmax, opts.ymin, opts.ymax, lofasm_station, crawler, opts.norm_cross)
        plot_all_baselines(crawler)
        raw_input()
    elif opts.animate_all: #Animate all baselines in time
        lines, fig = ani_lofasm.setup_all_plots(opts.xmin, opts.xmax, opts.ymin, opts.ymax, lofasm_station, crawler, opts.norm_cross)
        anim = ani_lofasm.animation.FuncAnimation(fig, 
            ani_lofasm.update_all_baseline_plots, fargs=(fig, 
                crawler, lines, opts.norm_cross), frames=num_frames, interval=opts.frame_dur, 
                )
        #print "saving video."
        #print anim.save('test.avi', codec='avi')
        ani_lofasm.plt.show()
    elif opts.animate_baseline:
        print "Plotting %s" % opts.animate_baseline

        plot_line = ani_lofasm.setup_single_plot(opts.animate_baseline, opts.xmin, opts.xmax, opts.ymin, opts.ymax, opts.norm_cross)
        anim = ani_lofasm.animation.FuncAnimation(ani_lofasm.fig, 
            ani_lofasm.update_baseline_plot, fargs=(ani_lofasm.fig, 
                burst_generator, plot_line, opts.animate_baseline, opts.norm_cross), frames=num_frames, interval=opts.frame_dur, 
                )
        ani_lofasm.plt.show()
        print "DONE"
        if opts.animate_beams:
            lines = ani_lofasm.setup_beam_plots(opts.xmin, opts.xmax, opts.ymin, opts.ymax)
            anim = ani_lofasm.animation.FuncAnimation(ani_lofasm.fig, 
                    ani_lofasm.update_beam_plots, fargs=(ani_lofasm.fig, 
                    burst_generator, lines), frames=num_frames, interval=opts.frame_dur)
        #print "saving video."
        #print anim.save('test.avi', codec='avi')
        ani_lofasm.plt.show()
    elif opts.TimeFrequencyPlot:
        print "colormap requested!"
        plot_im = ani_lofasm.setup_color_plot(opts.TimeFrequencyPlot, opts.TF_PlotWidth, opts.xmin, opts.xmax, opts.ymin, opts.ymax)
    else:
        print "No instructions given. Exiting."
        exit(0)

