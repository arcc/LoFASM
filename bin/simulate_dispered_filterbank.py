#! /usr/bin/env python
"""
This is a script to simulate a dispersed filter bank data.
"""


import lofasm.simulate.filter_bank_simulate as fbs
import lofasm.simulate.dispersion_simulate as ds
import matplotlib as plt
import argparse
import numpy as np
import sys

class ListGenAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        gens = fbs.FilterBankGen._data_gen_list
        result = ''
        for n, g in list(gens.items()):
            result += " " + n + ": " + g.full_name + "\n"
        print(result)
        parser.exit()

class GenHelpAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        gens = fbs.FilterBankGen._data_gen_list
        if values in list(gens.keys()):
            result = gens[values].data_gen_help(True)
            print(result)
        else:
            print("'%s' is not a data built-in generator." % values)
        parser.exit()

def do_plot(fb_data, save=False):
    plt.imshow(fb_data.data, aspect='auto',origin='lower', cmap='hot' \
           ,interpolation=None, extent=[fb_data.time_start, fb_data.time_end,
                                        fb_data.freq_start, fb_data.freq_end])
    plt.colorbar()
    if not save:
        plt.show()
    else:
        plt.savefig(fd_data.name)

def process_cofig(filename):
    f = open(filename, 'r')
    for l in f.readlines():
        print l

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Command line interfact to simulate"
                                                 " dispersed signals.")
    parser.add_argument("config",help="Configration file name")
    parser.add_argument("output",help="Output file name")
    parser.add_argument("--input",help="Reading data file name (default=None)",
                        default=None)
    parser.add_argument("--list_generators", help="List all the built-in signal" \
                        " and noise generators", action=ListGenAction, nargs=0)
    parser.add_argument("--generator_help", help="Print the help for a built-in" \
                        " data generator", action=GenHelpAction)
    parser.add_argument("--plot",help="Plot simulated filter bank data",
                        action="store_true",default=False)
    parser.add_argument("--saveplot",help="Save simulate data plot",
                        action="store_true",default=False)
    args = parser.parse_args()

    configs = process_cofig(args.config)
