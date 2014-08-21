#LoFASM animator
#matplotlib.use('TKAgg')
from matplotlib import animation
import matplotlib.pyplot as plt
import numpy as np
#import poco_ten_gbe as poco
import parse_data as pdat
import lofasm_dat_lib as lofasm

fig = plt.figure(figsize=(10,10))

FREQS = np.linspace(0, 200, 2048)
autos = ['AA','BB','CC','DD']
cross = ['AB','AC','AD','BC','BD','CD']
beams = ['NS','EW']

BASELINE_ID = {
    'LoFASMI' : {},
    'LoFASMII' : {
        'A' : 'INS',
        'B' : 'IEW',
        'C' : 'ONS',
        'D' : 'OEW'},
    'LoFASM3' : {},
    'LoFASMIV' : {
        'A' : 'OEW',
        'B' : 'ONS',
        'C' : 'IEW',
        'D' : 'INS'}
    }

def setup_all_plots(xmin, xmax, ymin, ymax, station, norm_cross=False):
    '''
    setup all cross-power plots
    '''
    auto_baselines = autos #['AA', 'BB', 'CC', 'DD']
    cross_baselines = cross #['AB', 'AC', 'AD', 'BC', 'BD', 'CD']
    #fig = plt.figure()
    auto_subplots = [fig.add_subplot(4,4,i) for i in [1, 6, 11, 16]]
    cross_subplots = [fig.add_subplot(4,4,i) for i in [2, 3, 4, 7, 8, 12]]
    auto_lines = []
    cross_lines = []
    fig.subplots_adjust(hspace=0.5)
    #freqs = np.linspace(0, 200, 2048)
	# set titles & plot
    for i in range(len(cross_baselines)):

        if i < 4:
            print 'auto baseline: .%s.' % auto_baselines[i]
            auto_title = BASELINE_ID[station][auto_baselines[i][0]]
            auto_subplots[i].set_title(auto_title)
            auto_subplots[i].set_xlim(xmin, xmax)
            auto_subplots[i].set_ylim(ymin, ymax)
            auto_subplots[i].grid()
            #auto_subplots[i].set_ylim(5.85, 6.05)
            auto_lines.append(auto_subplots[i].plot([],[])[0])

        cross_title = BASELINE_ID[station][cross_baselines[i][0]] + 'x' + BASELINE_ID[station][cross_baselines[i][1]]
        cross_subplots[i].set_title(cross_title)
        cross_subplots[i].set_xlim(xmin, xmax)
        cross_subplots[i].grid()

        if norm_cross:
            cross_subplots[i].set_ylim(-2,2)
            new_lines = {}
            new_lines['real'], = cross_subplots[i].plot([],[])
            new_lines['imag'], = cross_subplots[i].plot([],[])
            cross_lines.append(new_lines)
        else:
            cross_subplots[i].set_ylim(ymin, ymax)
            cross_lines.append(cross_subplots[i].plot([],[])[0])


    return tuple(auto_lines+cross_lines)


def setup_beam_plots(xmin, xmax, ymin, ymax):
	'''
	setup both beam plots
	'''
	beam_subplots = [fig.add_subplot(1,2,i) for i in range(len(beams))]
	beam_lines=[]

	#freqs = np.linspace(0, 200, 2048)
	# set titles & plot
	for i in range(len(beams)):
		beam_subplots[i].set_title(beams[i])
		beam_subplots[i].set_xlim(xmin, xmax)
		beam_subplots[i].set_ylim(ymin, ymax)
		#cross_subplots[i].set_ylim(5.85, 6.05)
		beam_subplots[i].grid()
		beam_lines.append(beam_subplots[i].plot([],[])[0])


	return tuple(beam_lines)

def setup_single_plot(baseline, xmin=0, xmax=200, ymin=0, ymax=100, norm_cross=False):
	'''
	setup single cross-power plot
	'''
	subplot = fig.add_subplot(1,1,1)
	subplot.set_title(baseline)
	subplot.set_xlim([xmin, xmax])
	subplot.set_ylabel('Arb. Power (dBm)')
	subplot.set_xlabel('MHz')
	subplot.set_ylim(ymin, ymax)
	subplot.grid()

	if norm_cross:
		plot_line = {}
		plot_line['real'], = subplot.plot([],[])
		plot_line['imag'], = subplot.plot([],[])
	else:
		plot_line, = subplot.plot([],[])
	return plot_line


def setup_color_plot(baseline, time_width_ms, xmin=0, xmax=200,
 ymin=0, ymax=100, samp_period_ms=84.8):

	'''
	setup time-frequency plot for a single baseline
	'''
	num_spectra = np.ceil(time_width_ms/float(samp_period_ms))
	empty_image = np.ones((2048,num_spectra))
	subplot = fig.add_subplot(1,1,1)
	subplot.set_title(baseline+'colormap')
	subplot.grid()
	timeFreq_plot = subplot.imshow(empty_image)
	return timeFreq_plot

def update_all_baseline_plots(i, fig, burst_gen, lines, norm_cross=False):
    print i
    baselines = ['AA', 'BB', 'CC', 'DD', 'AB', 'AC', 'AD', 'BC', 'BD', 'CD']
    burst_raw = burst_gen.next()
    pdat.print_hdr(pdat.parse_hdr(burst_raw))
    burst = lofasm.LoFASM_burst(burst_raw)


    # set titles & plot
    #plt.title("Frame %i " % i)
    for k in range(len(baselines)):
        if k < 4:

            lines[k].set_data(FREQS, 10*np.log10(burst.autos[baselines[k]]))
			#lines[i].set_xlim(0, 200)
        elif norm_cross:
			#lines[i].set_title(cross_baselines[i])
			norm_val = np.array(burst.cross[baselines[k]])/np.sqrt(np.array(burst.autos[baselines[k][0]*2])*np.array(burst.autos[baselines[k][1]*2]))
			lines[k]['real'].set_data(FREQS, np.real(norm_val))
			lines[k]['imag'].set_data(FREQS, np.imag(norm_val))
        else:
#			lines[k].set_data(FREQS, 10*np.log10(np.abs(burst.cross[baselines[k]])))
			lines[k].set_data(FREQS, 10*np.log10(np.abs(np.real(burst.cross[baselines[k]]))))
			#print np.imag(burst.cross[baselines[k]])
			#stop
			#lines[i].set_xlim(0, 200)
	
	#raw_input('press enter')
    return lines

def update_beam_plots(i, fig, burst_gen, lines):
    '''
	plot both beams at once.
	'''
    print i
	#auto_baselines = ['AA', 'BB', 'CC', 'DD']
	#cross_baselines = ['AB', 'AC', 'AD', 'BC', 'BD', 'CD']
    baselines = ['NS','EW']
	#fig = plt.figure()
	#auto_plots = [fig.add_subplot(4,4,i) for i in [1, 6, 11, 16]]
	#cross_plots = [fig.add_subplot(4,4,i) for i in 
	#	[2, 3, 4, 7, 8, 12]]

    burst_raw = burst_gen.next()
    pdat.print_hdr(pdat.parse_hdr(burst_raw))
    burst = lofasm.LoFASM_burst(burst_raw)
	
	#freqs = np.linspace(0, 200, 2048)
	# set titles & plot
    plt.title("Frame %i " % i)
    for k in range(len(baselines)):
        if baselines[k] == 'NS':
            beam = lofasm.gen_LoFASM_beam(burst.autos['BB'], burst.autos['DD'], burst.cross['BD'])
        elif baselines[k] == 'EW':
            beam = lofasm.gen_LoFASM_beam(burst.autos['AA'], burst.autos['CC'], burst.cross['AC'])
        lines[k].set_data(FREQS,10*np.log10(beam))

		#if k < 4:
			#lines[i].title(i)
		#	lines[k].set_data(FREQS, 
		#		10*np.log10(burst.autos[baselines[k]]))
			#lines[i].set_xlim(0, 200)
		#else:
			#lines[i].set_title(cross_baselines[i])
		#	lines[k].set_data(FREQS, 
				#take absolute value for cross products
		#		10*np.log10(np.abs(burst.cross[baselines[k]])))
			#lines[i].set_xlim(0, 200)

	#raw_input('press enter')
    return lines



def update_baseline_plot(i, fig, burst_gen, plot_line, baseline, norm_cross=False):
    print i
    burst_raw = burst_gen.next()
    pdat.print_hdr(pdat.parse_hdr(burst_raw))
    burst = lofasm.LoFASM_burst(burst_raw)
    plt.title(baseline+': Frame %i' % i)
    if baseline in autos:
        print 'updating auto %s' % baseline
        plot_line.set_data(FREQS,10*np.log10(burst.autos[baseline]))
    elif baseline in cross:
        print 'updating cross %s' % baseline
        if norm_cross:
            norm_val = np.array(burst.cross[baseline])/np.sqrt(np.array(burst.autos[baseline[0]*2])*np.array(burst.autos[baseline[1]*2]))
            plot_line['real'].set_data(FREQS, np.real(norm_val))
            plot_line['imag'].set_data(FREQS, np.imag(norm_val))
        else:
            plot_line.set_data(FREQS, 10*np.log10(np.abs(burst.cross[baseline])))
    elif baseline in beams:
        print 'updating BEAM %s' % baseline
		#create LoFASM Beam
        print "Generating LoFASM Beam: %s" % baseline

        if baseline == 'NS':
            beam = lofasm.gen_LoFASM_beam(burst.autos['BB'], 
				burst.autos['DD'], burst.cross['BD'])
        elif baseline == 'EW':
            beam = lofasm.gen_LoFASM_beam(burst.autos['AA'], 
				burst.autos['CC'], burst.cross['AC'])
        else:
            print 'unrecognized beam'
            print 'exiting'
            exit(0)
        plot_line.set_data(FREQS,10*np.log10(beam))

    return plot_line


