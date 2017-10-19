#! /usr/bin/env python
"""
This is a script to simulate a dispersed filter bank data.
This script assumes all the input and out put data files are in bbx formate.

"""


import lofasm.simulate.filter_bank_simulate as fbs
import lofasm.simulate.dispersion_simulate as ds
from lofasm.clean import cleandata as cd
import matplotlib.pyplot as plt
import argparse
import numpy as np
import sys
import imp

GENS = fbs.FilterBankGen._data_gen_list
MAX_TIME_DIFF = 86400.0 * 3
class ListGenAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        result = ''
        for n, g in list(GENS.items()):
            result += " " + n + ": " + g.full_name + "\n"
        print(result)
        parser.exit()

class GenHelpAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        if values in list(GENS.keys()):
            result = GENS[values].data_gen_help(True)
            print(result)
        else:
            print("'%s' is not a data built-in generator." % values)
        parser.exit()

def do_plot(fb_data, title='', save=False):
    plt.imshow(fb_data.data, aspect='auto',origin='lower', cmap='hot' \
           ,interpolation=None, extent=[fb_data.time_start, fb_data.time_end,
                                        fb_data.freq_start, fb_data.freq_end])
    plt.colorbar()
    plt.title(title)
    plt.xlabel('Time (second)')
    plt.ylabel('Frequency (Hz)')
    if not save:
        plt.show()
    else:
        plt.savefig(fd_data.name)

def process_config(filename):
    result = {}
    result['top'] = {}
    f = open(filename, 'r')
    lines = f.readlines()
    offset = 0
    for ii, l in enumerate(lines):
        if l.startswith('#'):
            continue
        if l == []:
            continue
        if l.startswith('<'): # read gen parameter block
            gen_name = l.replace('<','')
            gen_name = (gen_name.replace('>','')).strip()
            result[gen_name] = {}
            offset = 1
            next_line = lines[ii + offset]
            while ii + offset < len(lines):
                next_line = lines[ii+ offset]
                nl = next_line.split()
                if nl != [] and nl[0].startswith('@'):
                    param_name = nl[0].replace('@', '')
                    param_name = param_name.replace(':', '')
                    try:
                        result[gen_name][param_name] = float(nl[1])
                    except ValueError:
                        result[gen_name][param_name] = nl[1]
                    offset += 1
                else:
                    break
            continue
    return result



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Command line interfact to simulate"
                                                 " dispersed signals.")
    parser.add_argument("config",help="Configration file name")
    parser.add_argument("output",help="Output file name")
    parser.add_argument("--input",help="Reading data file name. This is for" \
                                       " injecting signal to read data " \
                                       "(default=None)",
                        default=None)
    parser.add_argument("--list_generators", help="List all the built-in signal" \
                        " and noise generators", action=ListGenAction, nargs=0)
    parser.add_argument("--generator_help", help="Print the help for a built-in" \
                        " data generator", action=GenHelpAction)
    parser.add_argument("--plot",help="Plot simulated filter bank data",
                        action="store_true",default=False)
    parser.add_argument("--saveplot",help="Save simulate data plot",
                        action="store_true",default=False)
    parser.add_argument("--savefile",help="Save intermeida files",
                        action="store_true",default=False)
    args = parser.parse_args()

    configs = process_config(args.config)
    is_plot = args.plot
    save_plot = args.saveplot
    save_file = args.savefile
    # get generators
    required_gens = list(configs.keys())
    required_gens.remove('top')
    for g in required_gens:
        if 'gen' not in list(configs[g].keys()):
            raise KeyError("parameter ''@gen:' is required for the generator.")
        if configs[g]['gen'] not in list(GENS.keys()):
            if 'path' not in list(configs[g].keys()):
                raise ImportError("No generator named '%s'" % g)
            else:
                g_path = configs[g]['path']
                foo = imp.load_source('module.name', g_path)

    if args.input is not None:
        sfd = fbs.FilterBank('read_in', from_file=True, filename=args.input, \
                             filetype='bbx')
        norm_sfd = fbs.FilterBank('Normalized_simulate', num_time_bin=sfd.num_time_bin, \
                    num_freq_bin=sfd.num_freq_bin,\
                    freq_resolution=sfd.freq_resolution, \
                    freq_start=sfd.freq_start,
                    time_start=sfd.time_start,
                    time_resolution=sfd.time_resolution,
                    data_gen=GENS['UniformDataGen'])
        d, n = cd.normalize(sfd.data)
        norm_sfd.data = d
    else:
        sfd = fbs.FilterBank('simulate', data_gen=GENS['UniformDataGen'], \
                             **configs['top'])
        print configs['top']
        sfd.generate_data(amp=0.0)
        norm_sfd = fbs.FilterBank('Normalized_simulate', num_time_bin=int(sfd.num_time_bin), \
                    num_freq_bin=int(sfd.num_freq_bin),\
                    freq_resolution=sfd.freq_resolution, \
                    freq_start=sfd.freq_start,
                    time_start=sfd.time_start,
                    time_resolution=sfd.time_resolution,
                    data_gen=GENS['UniformDataGen'])
        d = sfd.data
        n = np.ones(d.shape)
        norm_sfd.data = d
    if is_plot:
        do_plot(sfd, title='Simulated Backgroud', save=save_plot)
        do_plot(norm_sfd, title='Normalized Backgroud', save=save_plot)

    signals = {}
    noises = {}
    for g in required_gens:
        for ag in ['num_time_bin', 'num_freq_bin', 'freq_resolution', 'freq_start',\
                   'time_start', 'time_resolution']:
            if ag not in list(configs[g].keys()):
                configs[g][ag] = getattr(sfd, ag)
        gen_name = configs[g]['gen']
        gen_data = fbs.FilterBank(g, data_gen=GENS[gen_name], **configs[g])

        if GENS[gen_name].category == 'signal':
            signals[g] = gen_data
        elif GENS[gen_name].category == 'noise':
            noises[g] = gen_data
        else:
            raise KeyError("Unknown category '%s'"%GENS[gen_name].category)

    # add noise to normalized data.
    for k, v in list(noises.items()):
        v.generate_data(**configs[k])
        time_diff = norm_sfd.time_start - v.time_start
        # if simulated noise start time is too far way from target time
        # bring it to the target
        if np.abs(time_diff) > MAX_TIME_DIFF:
            raise ValueError("Noise '%s' start time '%lf' is too far away from the "
                             "target simulation start time '%lf'." %(k, v.time_start,
                             norm_sfd.time_start))
        norm_sfd += v
    noise_level = norm_sfd.data.std()
    signal = fbs.FilterBank('signals', num_time_bin=sfd.num_time_bin, \
                num_freq_bin=sfd.num_freq_bin,\
                freq_resolution=sfd.freq_resolution, \
                freq_start=sfd.freq_start,
                time_start=sfd.time_start,
                time_resolution=sfd.time_resolution,
                data_gen=GENS['UniformDataGen'])
    signal.generate_data(amp=0.0)
    for sk, sv in list(signals.items()):
        if 'snr' in list(configs[sk].keys()):
            snr = configs[sk]['snr']
            configs[sk]['amp'] = snr * noise_level
        sv.generate_data(**configs[sk])
        if is_plot:
            title = 'Simulated ' + sk + ' Signal'
            do_plot(sv, title, save=save_plot)

        time_diff =  signal.time_start - sv.time_start
        # if simulated noise start time is too far way from target time
        # bring it to the target
        if np.abs(time_diff) > MAX_TIME_DIFF:
            raise ValueError("Signal '%s' start time '%lf' is too far away from the "
                             "target simulation start time '%lf'." %(sk, sv.time_start,
                             signal.time_start))
        if 'dm' in list(configs[sk].keys()):
            dispersed_signal = ds.disperse_filterbank(configs[sk]['dm'], sv)
            signal += dispersed_signal
            if is_plot:
                title = 'Dispersed ' + sk + ' Signal'
                do_plot(dispersed_signal, title, save=save_plot)
        else:
            signal += sv

    if is_plot:
        title = 'Simulated Signal'
        do_plot(signal, title, save=save_plot)
    if save_file:
        signal.write(signal.name+'.bbx', 'bbx')

    norm_sfd += signal
    if is_plot:
        title = 'Simulated Signal and noise'
        do_plot(norm_sfd, title, save=save_plot)

    if save_file:
        norm_sfd.write(norm_sfd.name+'.bbx', 'bbx')
    # Anti-normalize signal plus noise
    sfd.data = norm_sfd.data * n
    if is_plot:
        title = 'Simulated Signal and noise unWhitened'
        do_plot(sfd, title, save=save_plot)
    sfd.write(args.output, 'bbx')
