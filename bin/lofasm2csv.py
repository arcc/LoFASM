#! /usr/bin/env python
from time import time
import numpy as np
import sys
import os
from datetime import datetime


pols = ['AA', 'BB', 'CC', 'DD', 'AB', 'AC', 'AD', 'BC', 'BD', 'CD']


def writeRow(dfile, data):
    # check data type
    if type(data[0]) in [np.int64, np.float64]:
        row = ','.join([str(x) for x in data])
    elif type(data[0]) in [np.complex128, np.complex64]:
        row = ','.join([str(x.real)+str(x.imag)+'j' if x.imag < 0 else str(x.real)+'+'+str(x.imag)+'j' for x in data])

    dfile.write(row + '\n')


def writePol(pol, dfile, crawler):
    crawler.reset()
    crawler.setPol(pol)
    for i in range(crawler.getNumberOfIntegrationsInFile()):
        try:
            pows = crawler.get()[:1024]
            writeRow(dfile, pows)
            crawler.forward()
        except EOFError:
            print 'end of file'


def get_csv_filename(lofasm_file):
    dir = os.path.dirname(lofasm_file)
    basename = os.path.basename(lofasm_file).split('.')[0] + '.csv'
    csvdir = os.path.join(dir, 'csv')
    csvname = os.path.join(csvdir, basename)

    return csvname


def convert_lofasm_file(lofasm_file, pols=pols):
    """
    convert old .lofasm file to csv format.

    :param lofasm_file: str
        path to .lofasm file
    :param pols: list, optional
        list of polarizations from lofasm_file to process. default is all pols.
    """
    import lofasm.parse_data as pdat

    crawler = pdat.LoFASMFileCrawler(lofasm_file)
    crawler.open()

    if not crawler.corrupt:

        for pol in pols:
            print "Writing ", pol
            polstart = time()

            csvname = get_csv_filename(lofasm_file.split('.')[0] + '_' + pol + '.lofasm')
            if not os.path.isdir(os.path.dirname(csvname)):
                try:
                    os.makedirs(os.path.dirname(csvname))
                except:
                    print "unable to create directory : {}".format(os.path.dirname(csvname))
                    print "please create the directory manually and try again"
                    sys.stdout.flush()


            with open(csvname, 'wb') as polfile:
                writePol(pol, polfile, crawler)
            polend = time()
            print "Wrote ", pol, " in ", polend - polstart
            sys.stdout.flush()
    else:
        print "ignoring corrupt file: {}".format(lofasm_file)


def convert_bbx_file(lofasm_file):
    from lofasm.bbx import bbx

    lf = bbx.LofasmFile(lofasm_file)
    lf.read_data()

    csvname = get_csv_filename(lofasm_file)

    if not os.path.isdir(os.path.dirname(csvname)):
        try:
            os.makedirs(os.path.dirname(csvname))
        except:
            print "unable to create directory : {}".format(os.path.dirname(csvname))
            print "please create the directory manually and try again"
            sys.stdout.flush()
    wstart = time()
    with open(csvname, 'wb') as csvfile:
        for i in range(np.shape(lf.data)[1]):
            data = lf.data[:1024, i]
            writeRow(csvfile, data)
    wend = time()
    print "wrote {} in {} s".format(csvname, str(wend-wstart))
    sys.stdout.flush()


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser(description="Convert lofasm to csv format.")

    # target files will be collected into a list, even if there's only one.
    p.add_argument('lofasm_file', type=str, nargs='+',
                   help="path to lofasm file to convert")
    p.add_argument('-l', action='store_true', dest='lofasm',
                   help="if set then process as old .lofasm file")
    p.add_argument('--pols', default="AA,BB,CC,DD,AB,AC,AD,BC,BD,CD",
                   help="comma separated list of pols to process. Can only be used if \
                   -l option is set. otherwise --pols is ignored. default is \
                   AA,BB,CC,DD,AB,AC,AD,BC,BD,CD")
    args = p.parse_args()

    if args.pols:
        input_pols = [x.upper() for x in args.pols.split(',')]
        for p in input_pols:
            if p not in pols:
                raise ValueError("{} is an unrecognized pol.".format(p))

    # loop all target files and convert 1 by 1
    now = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
    print "{} - Processing {} input files.".format(now, len(args.lofasm_file))
    sys.stdout.flush()
    for target_file in args.lofasm_file:
        now = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
        print "{} - Starting to process {}".format(now, target_file)
        sys.stdout.flush()
        if args.lofasm:
            convert_lofasm_file(target_file, input_pols)
        else:
            convert_bbx_file(target_file)
 
