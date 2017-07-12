#LoFASM animator
#matplotlib.use('TKAgg')
from matplotlib import animation
import matplotlib.pyplot as plt
import numpy as np
import parse_data as pdat
#import lofasm_dat_lib as lofasm
import sys

FREQS = np.linspace(0, 200, 2048)
autos = ['AA','BB','CC','DD']
cross = ['AB','AC','AD','BC','BD','CD']
beams = ['NS','EW']

BASELINE_ID = {
    'LoFASMI' : {
        'A' : 'INS',
        'B' : 'IEW',
        'C' : 'ONS',
        'D' : 'OEW'},
    '1' : {
        'A' : 'INS',
        'B' : 'IEW',
        'C' : 'ONS',
        'D' : 'OEW'},        
    'LoFASMII' : {
        'A' : 'INS',
        'B' : 'IEW',
        'C' : 'ONS',
        'D' : 'OEW'},
    '3' : {
        'A' : 'ONS',
        'B' : 'OEW',
        'C' : 'INS',
        'D' : 'IEW'},
    'LoFASM3' : {
        'A' : 'ONS',
        'B' : 'OEW',
        'C' : 'INS',
        'D' : 'IEW'},
    'LoFASMIV' : {
        'A' : 'OEW',
        'B' : 'ONS',
        'C' : 'IEW',
        'D' : 'INS'},
    '4':{
        'A' : 'OEW',
        'B' : 'ONS',
        'C' : 'IEW',
        'D' : 'INS'},
    'simdata' : {
        'A' : 'AAA',
        'B' : 'BBB',
        'C' : 'CCC',
        'D' : 'DDD'}
    }
BASELINES = ['AA', 'BB', 'CC', 'DD', 'AB', 'AC', 'AD', 'BC', 'BD', 'CD']

def setup_all_plots(xmin, xmax, ymin, ymax, station, crawler, norm_cross=False):
    '''
    setup all auto and cross-power plots
    '''
    fig = plt.figure(figsize=(10,10))

    auto_baselines = autos
    cross_baselines = cross

    auto_subplots = [plt.subplot2grid((4,4),(i,i)) for i in range(4)]
    cross_subplots = [plt.subplot2grid((4,4),(0,1)),
                      plt.subplot2grid((4,4),(0,2)),
                      plt.subplot2grid((4,4),(0,3)),
                      plt.subplot2grid((4,4),(1,2)),
                      plt.subplot2grid((4,4),(1,3)),
                      plt.subplot2grid((4,4),(2,3))]
    overlay_plot = plt.subplot2grid((4,4),(2,0), colspan=2, rowspan=2)

    auto_lines = []
    cross_lines = []
    overlay_lines = []

    fig.subplots_adjust(hspace=0.5)

	# set titles & plot
    for i in range(len(cross_baselines)):

        if i < 4:
            #autos
            auto_title = BASELINE_ID[station][auto_baselines[i][0]]
            auto_subplots[i].set_title(auto_title)
            auto_subplots[i].set_xlim(xmin, xmax)
            auto_subplots[i].set_ylim(ymin, ymax)
            auto_subplots[i].grid()
            auto_lines.append(auto_subplots[i].plot([],[])[0])

            #overlays
            overlay_title = 'All Channels'
            if i == 0:
                overlay_plot.set_title(overlay_title)
                overlay_plot.set_xlim(xmin, xmax)
                overlay_plot.set_ylim(ymin, ymax)
                overlay_plot.grid()
            overlay_lines.append(overlay_plot.plot([],[])[0])

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

    update_all_baseline_plots(0, fig, crawler, auto_lines+cross_lines+overlay_lines, forward=False)
    return [auto_lines+cross_lines+overlay_lines, fig]

def update_all_baseline_plots(i, fig, c, lines, norm_cross=False, forward=True):

    if forward:
        try:
            c.forward()
        except EOFError as err:
            print err
            raw_input("End of File. Press enter to quit.")
            sys.exit()


    for k in range(len(BASELINES)):
        if k < 4:
            #autos
            lines[k].set_data(FREQS, 10*np.log10(c.autos[BASELINES[k]]))
            #overlays
            lines[-(k+1)].set_data(FREQS,10*np.log10(c.autos[BASELINES[k]]))

        elif norm_cross:

			norm_val = np.array(c.cross[BASELINES[k]])/np.sqrt(np.array(c.autos[BASELINES[k][0]*2])*np.array(c.autos[BASELINES[k][1]*2]))
			lines[k]['real'].set_data(FREQS, np.real(norm_val))
			lines[k]['imag'].set_data(FREQS, np.imag(norm_val))
        else:
			lines[k].set_data(FREQS, 10*np.log10(np.abs(np.real(c.cross[BASELINES[k]]))))



    return lines
