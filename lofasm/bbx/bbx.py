# bbx python package:

from astropy.time import Time
import sys
import gzip
import numpy as np
import struct

#LoFASM file class by Andrew Danford


class LofasmFileClass(object):
    def __init__(self, LoFASMFile):
        self.file_name = LoFASMFile
        self.raw_file = gzip.open(self.file_name,'rb')
        self.header = {}
        line1 = self.raw_file.readline().strip().replace('%', '')
        if line1 not in ['\x02BX',]:
            raise TypeError("File '%s' is not a lofasm file" % LoFASMFile)
        line = self.raw_file.readline()
        while line.startswith('%'): #Fix this
            line = line.strip()
            line = line.replace('%', '')
            line = line.replace(':', '')
            line = line.split()
            self.header[line[0]] = line[1] #Fix This #what is it with this header
            line = self.raw_file.readline()
        line_last = line.split()
        self.header['timebins'] = int(line_last[0])
        self.header['freqbins'] = int(line_last[1])
        self.timebins = self.header['timebins']
        self.freqbins = self.header['freqbins']

        # determine whether data is real or complex
        #  real (auto correlation) data: 1
        #  complex (cross correlation) data: 2
        #  other: unknown
        if int(line_last[2]) == 1:
            self.iscplx = False
        elif int(line_last[2]) ==2:
            self.iscplx = True
        else:
            raise RuntimeError("Cannot determine data type.")

    def read_data(self, num_time_bin=None):  # Read data still not perfect.
        """
        parse data in .bbx.gz file and load into self.data

        :param num_time_bin: int
            the number of time bins to read.
            if not provided then read the entire file

            Note:
            if num_time_bin is larger than the number of time bins
             in the file then read the entire file.
            A value of 0 will result in nothing being read.
        """

        if num_time_bin:
            if num_time_bin > self.timebins:
                num_time_bin = self.timebins
            elif num_time_bin < 0:
                return
        else:
            num_time_bin = self.timebins

        if not self.iscplx:
            self.data = np.zeros((int(self.freqbins), int(num_time_bin)), dtype=np.float64)
            self.dtype = self.data.dtype
            for col in range(num_time_bin):
                spec = struct.unpack('2048d',self.raw_file.read(16384))
                self.data[:,col] = spec
        else:
            self.data = np.zeros((int(self.freqbins), int(num_time_bin)), dtype=np.complex64)
            self.dtype = self.data.dtype
            for col in range(num_time_bin):
                spec_cmplx = struct.unpack('4096d', self.raw_file.read(16384*2))
                i=0
                for row in range(len(spec_cmplx)/2):
                    self.data[row,col] = np.complex64(complex(spec_cmplx[i], spec_cmplx[i+1]))
                    i += 2

    def close(self):
        self.raw_file.close()
