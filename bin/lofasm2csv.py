#!/usr/bin/python
import lofasm.parse_data as pdat
import lofasm.parse_data_H as pdat_H
from time import time
import numpy as np
from glob import glob


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
    file_listing = glob('*.lofasm')
    if len(file_listing) == 0:
        print "nothing to do here, goodbye."
    else:
        
        for LOFASM_FILE in glob('*.lofasm'):
            crawler = pdat.LoFASMFileCrawler(LOFASM_FILE)
            crawler.open()
            print "Processing ", LOFASM_FILE
            for pol in pols:
                print "Writing ", pol
                polstart = time()
                with open(LOFASM_FILE.rstrip('.lofasm') + '_' +pol + '.csv', 'wb') as polfile:
                    try:
                        writePol2(pol, polfile, crawler)
                    except pdat_H.IntegrationError:
                        print "Can't convert ", LOFASM_FILE, "... "
                        break
                        polend = time()
                        print "Wrote ", pol, " in ", polend - polstart
