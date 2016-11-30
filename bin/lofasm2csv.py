import lofasm.parse_data as pdat
import lofasm.parse_data_H as pdat_H
from time import time
import csv
import numpy as np

# LOFASM_FILE = '20160223_163528.lofasm'

pols = ['AA','BB','CC','DD','AB','AC','AD','BC','BD','CD']


def writePol(pol, csvWriter, crawler):
    crawler.reset()
    crawler.setPol(pol)
    for i in range(crawler.getNumberOfIntegrationsInFile()):
        try:
            pow = crawler.get()[:1024]
            csvWriter.writerow(pow)
            crawler.forward()
        except EOFError:
            print 'end of file'

def writeRow(dfile, data):
    #check data type
    if type(data[0]) == np.int64:
        row = ','.join([str(x) for x in data])
    elif type(data[0]) == np.complex128:
        row = ','.join([str(x.real)+str(x.imag)+'j' if x.imag < 0 else str(x.real)+'+'+str(x.imag)+'j' for x in data])
    dfile.write(row + '\n')

def writePol2(pol, dfile, crawler):
    crawler.reset()
    crawler.setPol(pol)
    for i in range(crawler.getNumberOfIntegrationsInFile()):
        try:
            pows = crawler.get()[:1024]
            writeRow(dfile, pows)
            crawler.forward()
        except EOFError:
            print 'end of file'


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser(description="Convert lofasm to csv format.")
    p.add_argument('lofasm_file', type=str,
                   help="path to lofasm file to convert")
    args = p.parse_args()

    LOFASM_FILE = args.lofasm_file

    crawler = pdat.LoFASMFileCrawler(LOFASM_FILE)
    crawler.open()

    for pol in pols:
        print "Writing ", pol
        polstart = time()
        with open(LOFASM_FILE.rstrip('.lofasm') + '_' +pol + '.csv', 'wb') as polfile:
            writePol2(pol, polfile, crawler)
        polend = time()
        print "Wrote ", pol, " in ", polend - polstart
