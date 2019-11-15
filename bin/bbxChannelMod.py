''' By Keith Boehler, 06/25/2018, bbxChannelMod

	The onjective of the program is to proform manipulations to specific frequancy bands. 
	 
'''
# set imports 
from lofasm.bbx import bbx
from lofasm import parse_data as pdat
import numpy as np
import os
import argparse
#from tests.bbx import stream_writing

# Test Append fucntion
def append_data(lfx, data):
    print "New data shape: ", data.shape
    print "New data N elements: ", data.size
    print "New data block size (bytes): ", data.nbytes
    print "New data block dtype: ", data.dtype
    lfx.add_data(data)
# Report for the Test Append Function
def report(lfx):
    def msg(m):
        m = "**********  " + m + "  **********"
        print m
    msg("Object Header Dictionary")
    print lfx.header
    msg("Internal data buffer shape")
    print lfx.data.shape
    msg("Internal data buffer dtype")
    print lfx.data.dtype
    msg("Internal data buffer size (bytes)")
    print lfx.data.nbytes
    msg("size of {} on disk (Bytes)".format(basename(lfx._hdr_fname)))
    print os.path.getsize(lfx._hdr_fname) if exists(lfx._hdr_fname) else "{} does not exist".format(basename(lfx._hdr_fname))
    msg("size of {} on disk (Bytes)".format(basename(lfx._data_fname)))
    print os.path.getsize(lfx._data_fname) if exists(lfx._data_fname) else "{} does not exist".format(basename(lfx._data_fname))
    msg("size of {} on disk (Bytes)".format(basename(lfx.fpath)))
    print os.path.getsize(lfx.fpath) if exists(lfx.fpath) else "{} does not exist".format(lfx.fpath)


# Set the parser stuff
parser = argparse.ArgumentParser()
parser.add_argument("-p","--path", help="Path to input bbx file.")
parser.add_argument("-f", "--freq", help="Set frequancy channel to be removed. In MHz.")
parser.add_argument("-o", "--outfile", help="Name for file created.")

'''
Stream Data. Open the file we want to mod. 
Prep the file we are to write too.
'''
pars_dict = vars(parser.parse_args())
bbxFileHandel = bbx.LofasmFile(pars_dict['path'])
bbxfile = pars_dict['path']
print "File to be read open. "

bbxFileHeader = bbxFileHandel.header
outPath = os.getcwd()
outPath = outPath + '/' + pars_dict['outfile']
outFile = bbx.LofasmFile(outPath, bbxFileHeader, mode = 'write')
print "File to write created. "

for i in range(int(bbxFileHeader['metadata']['dim1_len'])):
    bbxFileHandel.read_data(1) # Read one line of data
    spectra = bbxFileHandel.data[:, :] #.astype(np.float32)
    spectra[:,pdat.freq2bin(float(pars_dict['freq']))] = 0
#    report(outFile)
    append_data(outFile, spectra)
#    report(outFile)
    outFile.write()


outFile.close()
'''
data = bbxFileHandel.data[:, :].astype(np.float32)

# select frequancy to zero 
userin = float(pars_dict['freq'])
freqbin = pdat.freq2bin(userin)

# zero out that frequancy
data[:, freqbin] = 0
'''
'''
# write to new bbx file
path = os.getcwd()
path = path + '/' + pars_dict['outfile']
outFile = bbx.LofasmFile(path, bbxFileHeader, mode = 'write')
outFile.add_data(data)
outFile.write()
outFile.close()

'''
