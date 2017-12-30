#! /usr/bin/env python
'''
generate a LoFASM beam bbx data file from ring bbx data.
'''

import sys, os
import matplotlib
import numpy as np
matplotlib.use('agg')
import matplotlib.pyplot as plt
from lofasm.bbx import bbx
from lofasm.parse_data import freq2bin
from glob import glob

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('dataDir', type=str, help='path to data directory')
    p.add_argument(
    p.add_argument('--savedata', action='store_true',
                   help='save data as numpy file')
    args = p.parse_args()
