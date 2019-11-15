# bbx python package:

import sys
import os
from os.path import dirname, abspath, join

import gzip
import numpy as np
import struct
from copy import deepcopy
from random import choice
from string import ascii_letters, digits
from shutil import copyfileobj


SUPPORTED_FILE_SIGNATURES = ['\x02BX', 'ABX', 'BX']
SUPPORTED_ENCODING_SCHEMES = ['raw256']
SUPPORTED_HDR_TYPES = ['LoFASM-filterbank', 'LoFASM-dedispersion-dm-time']
REQUIRED_HDR_COMMENT_FIELDS = {
    'LoFASM-filterbank': ['hdr_type', 'hdr_version', 'station', 'channel',
                          'dim1_start', 'dim1_span', 'dim2_start', 'dim2_span',
                          'data_type'],
    'LoFASM-dedispersion-dm-time': ['hdr_type', 'hdr_version', 'station',
                                    'channel', 'dim1_start', 'dim1_span',
                                    'dim2_start', 'dim2_span', 'data_type']
}

def randomString(N):
    pool = ascii_letters + digits
    return ''.join(choice(pool) for i in range(N))


class LofasmFile(object):
    """Class to represent .bbx-type data files for LoFASM.
    Currently, the only data format supported is 'LoFASM-filterbank'.
    """
    def __init__(self, lofasm_file, header={'metadata':{}}, verbose=False,
                 mode='read', gz=None):

        self.debug = True if verbose else False
        self.header = deepcopy(header)

        self.iscplx = None
        self.fpath = lofasm_file
        self.fname = os.path.basename(lofasm_file)
        self.ptr = 0 # pointer location (dim1)
        self._uniqueKey = randomString(10) 

        # directory to store data and tmp files
        dataDir = os.path.dirname(os.path.abspath(self.fpath))

        # validate file open mode
        if mode.lower() not in ('read', 'write'):
            raise ValueError("Unrecognized file mode: {}".format(mode.lower()))
        else:
            mode = mode.lower()
            if mode == 'read':
                self._fmode = 'rb'
            elif mode == 'write':
                self._fmode = 'wb'
            self.mode = mode

        # check existence of file
        if not os.path.exists(lofasm_file):
            if mode == 'read':
                raise RuntimeError("File does not exist: " + str(lofasm_file))
        elif mode == 'read':
            assert(os.path.getsize(lofasm_file) > 0), "File is empty"


        if mode in ['read'] and gz == None:
            try:
                with gzip.open(self.fpath, self._fmode) as f:
                    gz = True if f.readline() else False
            except IOError as e:
                if e.message == 'Not a gzipped file':
                    gz = False
                else:
                    raise IOError, e.message
        elif mode == 'write':
            gz = True if gz else False

        self.gz = gz
        # final data file
        #self._fp = gzip.open(self.fpath, self._fmode) if gz else open(self.fpath, self._fmode)
        # temporary header and data files
        # create a separate temporary file for header and data portions
        # prepend each tmp file with "unique" random string to avoid
        # having multiple instances of this object overwrite each other
        self._hdr_fname = join(dataDir,'.'+self._uniqueKey+'.hdr')
        self._data_fname = join(dataDir, '.'+self._uniqueKey+'.dat')
        self._hdr_fp = open(self._hdr_fname, 'wb')
        self._data_fp = open(self._data_fname, 'wb')

        if mode in ['read']:
            self._fp = gzip.open(self.fpath, self._fmode) if gz else open(self.fpath, self._fmode)
            self._load_header()
        elif mode == 'write':
            self._debug("prepping file")
            self._prep_new()
            self.data = np.array([], dtype=np.float64)

        # private copy of certain methods
        self._set = self.set

    ###############################
    # Top level interface methods #
    ###############################
    def add_data(self, data):
        """
        add BBX data to memory to be written to file.

        Write 1d or 2d data to memory to be written to disk.
        If invoked with a new file then the dimension fields in the
        metadata will be set.

        Parameters
        ----------
        data : numpy.ndarray
            Data array to be added to memory
            `data.ndim` must be either 1 or 2.
            The data type of the elements in the stored array will be inferred from `data`.
            Supported data types are np.complex128 and np.float64.

        Raises
        ------
        AssertionError
            If file is not opened in write mode.

        NotImplementedError
            If the dimensions of `data` are not supported.

        ValueError
            If either the number of channels in `data` or the data type doesn't match the pre-existing data, if there is
            any.
        """
        assert(self.mode == 'write'), "File not open for writing."

        if data.ndim == 2:
            dim1_bins, dim2_bins = np.shape(data)
            data = data.flatten()
        elif data.ndim == 1:
            # treat 1d data blocks as a single "row"
            data = data.flatten()
            dim2_bins = len(data)
            dim1_bins = 1
        else:
            raise NotImplementedError, "Currently only up to 2d data is supported."

        if self._new_file:
            # set header fields based on new data block for new file
            self._set('dim1_len', dim1_bins)
            self._set('dim2_len', dim2_bins)
            self._set('complex', '2' if np.iscomplexobj(data) else '1')
            N = int(dim1_bins * dim2_bins)
            self.data = np.zeros(N, dtype=np.complex128 if np.iscomplexobj(data) else np.float64)
            # copy data to internal buffer
            self.data[:N] = data
            self._new_file = False

        else:
            old_iscplx = True if self.header['metadata']['complex'] == '2' else False
            new_iscplx = np.iscomplexobj(data)

            if old_iscplx != new_iscplx:
                raise ValueError, "new data must match existing data realness"

            if str(dim2_bins) != str(self.dim2_len):
                raise ValueError, "new data length for dim2 must match the existing data!"
            
            # update header values to reflect new data block dimensions
            # dim2 is left alone since that holds the frequency axis
            self.set('dim1_len', self.dim1_len+dim1_bins)

            # N reduces to `int(new_bins)` if internal block has been
            # recently dumped and cleared
            N = self.data.size + data.size 
            dtype = np.float64 if self.complex=='1' else np.complex128
            newdata = np.zeros(N, dtype=dtype)
            newdata[:-data.size] = self.data
            newdata[-data.size:] = data
            self.data = newdata

    def close(self):
        """
        close file object

        in reading mode, the file handle is simply closed
        in writing mode, write final header info to tmp file,
        close tmp files, concat hdr and data portions, then
        gzip the result if requested.
        """

        if self.mode == 'read':
            self._fp.close()
        elif self.mode == 'write':
            # dump header to disk and close file
            self._write_header()
            self._hdr_fp.close()
            # close data file
            self._data_fp.close()

            # concatenate hdr and data portions
            # there are simpler ways to do this.
            # but this approach will handle both normal and 
            # compressed output files
            fout = gzip.open(self.fpath, self._fmode) if self.gz else open(self.fpath, self._fmode)
            f_hdr = open(self._hdr_fname, 'rb')
            f_dat = open(self._data_fname, 'rb')
            copyfileobj(f_hdr, fout)
            copyfileobj(f_dat, fout)
            fout.close()
            f_hdr.close()
            f_dat.close()
            # clean up temporary files
            os.remove(self._hdr_fname)
            os.remove(self._data_fname)


        else:
            raise NotImplementedError("unknown file mode: {}".format(self.mode))

    def read_data(self, N=None):
        """Parse data block in LoFASM filterbank file and load into 
        memory as `self.data`.
        The resulting data array in self.data is stored as a 2d 
        array with dim1 as the vertical axis and
        dim2 as the horizontal axis.
        If reading a typical LoFASM-filterbank file then the 
        x-axis will represent the time bins and the y-axis will
        represent the frequency bins.

        Parameters
        ----------
        N : int
            The number of rows to read. If not provided, then
            attempt to read the entire file (read all rows).
            If `num_time_bin` is larger than the number of time 
            bins in the file then read the entire file.
            A value of 0 will result in nothing being read.
        Raises
        ------
        AssertionError
            If file is not open for reading
        """


        assert(self.mode == 'read'), "File not open for reading."

        if not N is None:
            if N > self.dim1_len-self.ptr:
                err = "Requested {} rows but only {} rows remain in file".format(
                        N, self.dim1_len-self.ptr
                        )
                raise RuntimeError(err)
            elif N <= 0:
                # do nothing
                return 
            elif N+self.ptr <= self.dim1_len:
                self.ptr = N+self.ptr
        else:
            N = self.dim1_len - self.ptr
            self.ptr = self.dim1_len
        


        # real data
        if not self.iscplx:
            if self.nbits == 64:
                fmt = '{}d'.format(self.dim2_len)
            elif self.nbits == 32:
                fmt = '>{}L'.format(self.dim2_len)

            self._debug('parsing real data')
            nbytes = self.freqbins * self.nbits / 8
            self.data = np.zeros((int(N), int(self.dim2_len)),
                                 dtype=np.float64)
            self.dtype = self.data.dtype
            for row in range(N):
                spec = struct.unpack(fmt, self._fp.read(nbytes))
                self.data[row,:] = spec
        # complex data
        else:
            if self.nbits == 64:
                fmt = '{}d'.format(2*self.dim2_len)
            elif self.nbits == 32:
                fmt = '>{}l'.format(2*self.dim2_len)
            self._debug('parsing complex data')
            nbytes = 2 * self.freqbins * self.nbits / 8
            self.data = np.zeros((int(N), int(self.dim2_len)), dtype=np.complex128)
            self.dtype = self.data.dtype
            for row in range(N):
                spec_cmplx = struct.unpack(fmt, self._fp.read(nbytes))
                i=0
                for col in range(len(spec_cmplx)/2):
                    self.data[row, col] = np.complex64(complex(spec_cmplx[i], spec_cmplx[i+1]))
                    i += 2

    def set(self, key, val):
        """Set header or metadata fields
        Set or create header comment fields. If the field `key` exists
        then its value will be overwritten.
        If the field does not exist, then it will be created as a 
        new comment field.
        If `key` exists as part of the metadata field, then the 
        value will be overwritten.

        Parameters
        ----------
        key : str
            Header field name as a string.
        val : str, int, float
            Value that header field will be set to
        """
        if key in self.metadata.keys():
            self.metadata[key] = val
        elif key in self.header.keys():
            self.header[key] = val
        else:
            self._debug("Creating header field {}: {}".format(key, val))
            self.header[key] = val

    def write(self):
        """
        Write current data contents to disk.

        If at the beginning of the file write the BBX header first, then the data.
        """

        assert (self.mode == 'write'), "File not open for writing."

        missing_keys = self._validate_header()
        if missing_keys:
            errmsg = "header missing required fields: {}".format(', '.join(missing_keys))
            raise RuntimeError, errmsg


        N = self.data.size
        realfmt = '{}d'.format(N)
        cplxfmt = '{}d'.format(2*N)

        if np.iscomplexobj(self.data):
            self._debug("Writing complex data")
            cplxdata = np.zeros(2*N, dtype=np.float64)
            i = 0
            for k in range(N):
                cplxdata[i] = self.data[k].real
                cplxdata[i+1] = self.data[k].imag
                i += 2
            self._fp.write(struct.pack(cplxfmt, *cplxdata))
        else:
            self._debug("Writing real data")
            self._data_fp.write(struct.pack(realfmt, *self.data))
        #clear internal data buffer
        self.data = np.array([], dtype=np.float64)

    ###################
    # Private methods #
    ###################
    def _debug(self, msg):
        if self.debug:
            print msg
            sys.stdout.flush()

    def _load_header(self):
        try:
            fsig = self._fp.readline().strip()
            if fsig.startswith('%'):
                fsig = fsig.strip('%')
            elif self.gz:
                raise IOError, "Unable to parse file. Unrecognizable file signature. Are you sure compression should be turned on?"
            else:
                raise IOError, "Unable to parse file. Unrecognizable file signature."
        except IOError as e:
            if self.gz and e.strerror == 'Not a gzipped file':
                raise IOError, "Compression parameter is True but input file is not a gzipped file"
            else:
                raise IOError, e.message

        if fsig not in SUPPORTED_FILE_SIGNATURES:
            raise NotImplementedError("{} is not a supported LoFASM file signature".format(fsig))

        # populate header dictionary with header comment fields
        line = self._fp.readline().strip()
        while line.startswith('%'):
            contents = line.strip('%').split(":")
            key = contents[0]
            val = ':'.join(contents[1:])
            self.header[key] = val.strip()
            line = self._fp.readline().strip()

        # check for hdr_type field first. This is how we determine what fields are required
        if 'hdr_type' not in self.header.keys():
            raise RuntimeError("Missing Required comment field: hdr_type")

        missing_comment_fields = []
        for key in REQUIRED_HDR_COMMENT_FIELDS[self.header['hdr_type']]:
            if key not in self.header.keys():
                missing_comment_fields.append(key)
        if missing_comment_fields:
            raise RuntimeError("Missing required comment fields for {} header type: {}".format(
                self.header['hdr_type'], ', '.join(missing_comment_fields)))

        # parse metadata line in file header
        contents = line.split()
        if len(contents) != 5:  # FixMe: this is only stable for LoFASM-filterbank files
            raise RuntimeError("Unable to parse metadata line: {}".format(line))

        metadata = {}
        metadata['dim1_len'] = int(contents[0])
        metadata['dim2_len'] = int(contents[1])

        # determine whether data is real or complex
        #  real (auto correlation) data: 1
        #  complex (cross correlation) data: 2
        #  other: unknown
        if int(contents[2]) == 1:
            metadata['complex'] = '1'
        elif int(contents[2]) == 2:
            metadata['complex'] = '2'
        else:
            raise ValueError("Cannot determine whether data is complex or real.")

        metadata['nbits'] = int(contents[3])

        if contents[4] in SUPPORTED_ENCODING_SCHEMES:
            metadata['encoding'] = contents[4]
        else:
            raise RuntimeError("Unsupported encoding scheme: {}".format(contents[4]))

        self.header['metadata'] = metadata

        if self.debug:
            for k in self.header.keys():
                if k == 'metadata':
                    x = str(metadata)
                else:
                    x = self.header[k]
                self._debug("Loaded {}: {}".format(k, x))

        self.iscplx = True if self.complex == '2' else False

    def _prep_new(self):
        """
        prepare header to begin writing a new bbx file.
        :return:
        """

        if not self.header:
            metadata = {
                'dim1_len': 0, #start with empty file
                'dim2_len': 0,
                'complex': None,
                'nbits': 64,
                'encoding': 'raw256'
            }
            if self.iscplx:
                metadata['complex'] = '2'
            elif self.iscplx is False:
                metadata['complex'] = '1'

            self.header = {'hdr_type': 'LoFASM-filterbank',
                'hdr_version': '0000803F',
                'station': None,
                'channel': None,
                'dim1_start': None,
                'dim1_label': 'time (s)',
                'dim1_span': None,
                'dim2_label': 'frequency (Hz)',
                'dim2_start': None,
                'dim2_span': None,
                'data_type': 'real64',
                'frequency_offset_DC': '0 (Hz)',
                'data_scale': '1',
                'metadata': metadata}


        self._new_file = True

    def _validate_header(self):
        """
        return True if all the required fields in self.header are set, else False
        :return: bool
            True if header is ready to be written, False otherwise
        """

        missing_keys = []
        for key in REQUIRED_HDR_COMMENT_FIELDS['LoFASM-filterbank']:
            if self.header[key] == None:
                missing_keys.append(key) 
        return missing_keys

    def _write_header(self):
        """
        write header to file if self.header is sufficiently populated
        """

        assert (self._validate_header() == []), "Header is not sufficiently populated"

        # start file with BBX file signature
        self._hdr_fp.write("%\x02BX\n")

        keystowrite = self.header.keys()
        self._hdr_fp.write("%hdr_type: {}\n".format(self.header['hdr_type']))
        keystowrite.remove('hdr_type')
        keystowrite.remove('metadata')

        # write all remaining comment fields
        for key in keystowrite:
            self._hdr_fp.write("%{}: {}\n".format(key, self.header[key]))

        # end header with metadata line
        meta = [str(x) for x in [self.dim1_len, self.dim2_len, self.complex, self.nbits, self.encoding]]
        self._hdr_fp.write("{}\n".format(' '.join(meta)))

    #################
    # Magic methods #
    #################
    def __getattr__(self, key):
        """
        Check self.header and internal scope (self.__dict__) dictionaries when
        fetching an attribute.
        :param key: str
            name of attribute
        :return:
            value of matched attribute
        :raises:
            AttributeError if attribute is not found.
        """
        if key in self.header.keys():
            val = self.header[key]
        elif key in self.metadata.keys():
            val = self.metadata[key]
        elif key == 'timebins':
            val = self.metadata['dim1_len']
        elif key == 'freqbins':
            val = self.metadata['dim2_len']
        else:
            raise AttributeError("LoFASM File class has no attribute {}".format(key))

        return val

# a light function to check if a file in lofasm bbx format.
def is_lofasm_bbx(filename):
    """ Check the file is lofasm file or not.
    """
    if filename.endswith('.gz'):
        f = gzip.open(filename,'rb')
    else:
        f = open(filename,'rb')
    line1 = f.readline().strip()
    if line1.startswith('%'):
        line1 = line1.strip('%')
    else:
        return False
    if line1 in SUPPORTED_FILE_SIGNATURES:
        return True
    else:
        return False
