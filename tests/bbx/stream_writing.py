import unittest
import os
from lofasm.bbx import bbx
import numpy as np
from os.path import exists, basename
# test blocks for streaming
zeros_row = np.zeros((1,1024), dtype=np.float64)
zeros_block = np.zeros((10,1024), dtype=np.float64)
ones_row = np.ones((1,1024), dtype=np.float64)
ones_block = np.ones((9,1024), dtype=np.float64)
def msg(m):
    m = "##########  " + m + "  ##########"
    print m

def append_data(lfx, data):
    print "New data shape: ", data.shape
    print "New data N elements: ", data.size
    print "New data block size (bytes): ", data.nbytes
    print "New data block dtype: ", data.dtype
    lfx.add_data(data)

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

fname = 'testfile.bbx'
# purge file if it already exists
if os.path.exists(fname):
    os.remove(fname)
lfx = bbx.LofasmFile('testfile.bbx', mode='write', gz=True)
# set required header fields with fake information
lfx.set('station', 'fake')
lfx.set('channel', 'fake')
lfx.set('dim1_start', '0')
lfx.set('dim1_span', '1')
lfx.set('dim2_start', '0')
lfx.set('dim2_span', '1')
lfx.set('data_label', 'filterbank')
report(lfx)
msg("Appending row of ones to internal buffer:")
append_data(lfx, ones_row)
report(lfx)
msg("Dumping internal buffer to disk")
lfx.write()
report(lfx)
msg("Appending block of 2's to internal buffer:")
append_data(lfx, ones_block*2)
report(lfx)
msg("Appending block of 5's to internal buffer:")
append_data(lfx, ones_block*5)
report(lfx)
msg("Dumping internal buffer to disk")
lfx.write()
report(lfx)
lfx.close()
report(lfx)






