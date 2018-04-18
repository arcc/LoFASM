
# python file for parsing LoFASM Correlator Data
import struct
import sys
import numpy as np
import parse_data_H as pdat_H
from parse_data_H import IntegrationError
from astropy.time import Time, TimeDelta
import gzip
import io

LoFASM_SPECTRA_KEY_TO_DESC = pdat_H.LoFASM_SPECTRA_KEY_TO_DESC
HDR_V1_SIGNATURE = 14613675
INTEGRATION_SIZE_B = 139264  # bytes
START_DATA = 204896
PACKET_SIZE_B = 8192
bufReal = '*' * 4096
bufCplx = '*' * 8192
bufBurst = '*' * INTEGRATION_SIZE_B
range512 = range(512)
# station polarization mapping
BASELINE_ID = {
    'LoFASMI' : {
        'A' : 'INS',
        'B' : 'IEW',
        'C' : 'ONS',
        'D' : 'OEW'},
    'LoFASMII' : {
        'A' : 'INS',
        'B' : 'IEW',
        'C' : 'ONS',
        'D' : 'OEW'},
    'LoFASM3' : {
        'A' : 'ONS',
        'B' : 'OEW',
        'C' : 'INS',
        'D' : 'IEW'},
    'LoFASMIV' : {
        'A' : 'OEW',
        'B' : 'ONS',
        'C' : 'IEW',
        'D' : 'INS'}
    }


Baselines = pdat_H.Baselines
AUTOPOLS = ['AA', 'BB', 'CC', 'DD']
CROSSPOLS = ['AB', 'AC', 'AD', 'BC', 'BD', 'CD']

##### Function Definitions
def freqRange(lowfreq=0.0, highfreq=100.0):
    ''' return frequency axis from lowfreq to highfreq MHz'''
    freqs = np.arange(1024) * 100.0 / 1024
    return freqs[freq2bin(lowfreq):freq2bin(highfreq)]

def getSampleTime(Nacc):
    """
    Return the sample time corresponding to the number
    of accumulations, Nacc.
    """
    return pdat_H.T_fpga * pdat_H.FFT_cycles * Nacc

def freq2bin(freq):
    '''
    Return bin number corresponding to frequency freq
    '''
    rbw = 200.0/2048
    return int(freq / rbw)

def bin2freq(bin):
    rbw = 200.0/2048
    return bin * rbw

def parse_filename(filename):
    '''return the file's UTC time stamp as a list
    [YYmmdd, HHMMSS, pol]
    '''

    if filename[-7:]== '.lofasm':
        filename = filename.rstrip('.lofasm')
        parse_list = filename.split('_')
    else:
        filename = filename.rstrip('.lsf')
        parse_list = filename.split('_')
    date = parse_list[0]
    timestamp = parse_list[1]
    pol = filename[(len(date)+len(timestamp)+2):]

    return [date, timestamp, pol]

def spectrum_conv_code(code_str):
    return LoFASM_SPECTRA_KEY_TO_DESC[code_str]

def fmt_header_entry(entry_str, fmt_len=8):
    '''ensure that every header entry is fmt_len characters long. if longer, then
    truncate. if shorter, then pad with white space. returns formatted string'''
    entry_str = str(entry_str)
    entry_len = len(entry_str)

    if entry_len > fmt_len:
        return entry_str[:fmt_len] #truncate
    elif entry_len < fmt_len:
        diff = fmt_len - entry_len
        return ' '*diff + entry_str #pad frnt with white space
    else:
        return entry_str

def gen_spectrum_hdr_string(hdr_dict):
    num_fields = len(hdr_dict.keys())
    hdr_str = ''
    for field in range(num_fields):
        field += 1
        hdr_str += fmt_header_entry(hdr_dict[field][1])
    return hdr_str

def parse_file_header(file_obj, fileType='lofasm'):

    #move pointer to beginning of file
    freeze_pointer = file_obj.tell()

    if freeze_pointer != 0:
        file_obj.seek(0)

    #get file signature
    file_sig = file_obj.read(pdat_H.HDR_ENTRY_LENGTH).strip(' ')

    #check file signature
    if file_sig != pdat_H.LoFASM_FHDR_SIG:
        file_obj.seek(freeze_pointer)
        raise pdat_H.Header_Error(file_obj.name + 'may not be a proper LoFASM File.',
            'File Signature ' + file_sig + ' not recognized.')

    #get file header version from file
    file_hdr_version = int(file_obj.read(pdat_H.HDR_ENTRY_LENGTH))

    #get corresponding header template
    try:
        if fileType == 'lofasm':
            fhdr_field_dict = pdat_H.LoFASM_FHEADER_TEMPLATE[file_hdr_version]
        elif fileType == 'spectra':
            fhdr_field_dict = pdat_H.LoFASM_SPECTRUM_HEADER_TEMPLATE[file_hdr_version]

    except KeyError as err:
        print "Error: LoFASM raw file header version not recognized."
        print "Unrecognized version: ", err.message
        sys.exit()

    #populate header dict
    fhdr_field_dict[1][1] = file_sig
    fhdr_field_dict[2][1] = file_hdr_version
    fhdr_field_dict[3][1] = int(file_obj.read(pdat_H.HDR_ENTRY_LENGTH))


    fields_left_to_populate = len(fhdr_field_dict.keys()) - 3
    remaining_hdr_string = file_obj.read(fhdr_field_dict[3][1]-
        3*pdat_H.HDR_ENTRY_LENGTH)

    if file_hdr_version == 1 or file_hdr_version == 2:
        for i in range(fields_left_to_populate):
            j = i + 4 #start with 3rd field
            if i == (fields_left_to_populate - 1):
                fhdr_field_dict[j][1] = remaining_hdr_string[
                    i*pdat_H.HDR_ENTRY_LENGTH:].strip(' ')
            else:
                fhdr_field_dict[j][1] = remaining_hdr_string[
                    i*pdat_H.HDR_ENTRY_LENGTH:
                    (i+1)*pdat_H.HDR_ENTRY_LENGTH].strip(' ')
    elif file_hdr_version == 3:
        fhdr_field_dict[4][1] = remaining_hdr_string[:8].strip()
        fhdr_field_dict[5][1] = remaining_hdr_string[8:16].strip()
        fhdr_field_dict[6][1] = remaining_hdr_string[16:24].strip()
        fhdr_field_dict[7][1] = remaining_hdr_string[24:32].strip()
        fhdr_field_dict[8][1] = remaining_hdr_string[32:40].strip()
        fhdr_field_dict[9][1] = remaining_hdr_string[40:48].strip()
        fhdr_field_dict[10][1] = remaining_hdr_string[48:56].strip()
        fhdr_field_dict[11][1] = remaining_hdr_string[56:64].strip()
        fhdr_field_dict[12][1] = remaining_hdr_string[64:74].strip()
        fhdr_field_dict[13][1] = remaining_hdr_string[74:84].strip()
    elif file_hdr_version == 4:
        fhdr_field_dict[4][1] = remaining_hdr_string[:8].strip()
        fhdr_field_dict[5][1] = remaining_hdr_string[8:16].strip()
        fhdr_field_dict[6][1] = remaining_hdr_string[16:24].strip()
        fhdr_field_dict[7][1] = remaining_hdr_string[24:32].strip()
        fhdr_field_dict[8][1] = remaining_hdr_string[32:40].strip()
        fhdr_field_dict[9][1] = remaining_hdr_string[40:48].strip()
        fhdr_field_dict[10][1] = remaining_hdr_string[48:56].strip()
        fhdr_field_dict[11][1] = remaining_hdr_string[56:64].strip()
        fhdr_field_dict[12][1] = remaining_hdr_string[64:74].strip()
    elif file_hdr_version == 5:
        fhdr_field_dict[4][1] = remaining_hdr_string[:8].strip()
        fhdr_field_dict[5][1] = remaining_hdr_string[8:16].strip()
        fhdr_field_dict[6][1] = remaining_hdr_string[16:24].strip()
        fhdr_field_dict[7][1] = remaining_hdr_string[24:32].strip()
        fhdr_field_dict[8][1] = remaining_hdr_string[32:40].strip()
        fhdr_field_dict[9][1] = remaining_hdr_string[40:48].strip()
        fhdr_field_dict[10][1] = remaining_hdr_string[48:56].strip()
        fhdr_field_dict[11][1] = remaining_hdr_string[56:64].strip()
        fhdr_field_dict[12][1] = remaining_hdr_string[64:72].strip()
        fhdr_field_dict[13][1] = remaining_hdr_string[72:80].strip()
        fhdr_field_dict[14][1] = remaining_hdr_string[80:88].strip()
        fhdr_field_dict[15][1] = remaining_hdr_string[88:96].strip()
        fhdr_field_dict[16][1] = remaining_hdr_string[96:104].strip()

    #move file cursor back to original position
    file_obj.seek(freeze_pointer)
    return fhdr_field_dict

def parse_hdr(hdr):
    '''
    Usage: parse_hdr(<64bit_string>,[version])
    Parse the first 64 bits of
    LoFASM data packet and return a dictionary containing each header value.

        If hdr has a length greater than 8bytes then it will be truncated
        and only the first 8 bytes will be parsed.
    '''

    padding_1B = "\x00"
    hdr_dict = {}
    hdr_dict['signature'] = [x for x in struct.unpack('>L', padding_1B+hdr[:3])][0]
    hdr_dict['acc_num'] = [x for x in struct.unpack('>L', padding_1B+hdr[3:6])][0]
    hdr_dict['hdr_cnt'] = [x for x in struct.unpack('>L', 2*padding_1B+hdr[6:8])][0]

    return hdr_dict

def print_hdr(hdr_dict):
    '''
    print header dictionary contents
    '''

    for key in hdr_dict:
        val = str(hdr_dict[key])
        if val != '0':
            print str(key) + ": " + val
        else:
            print "No header information"
            break

def is_header(hdr_raw, print_header=False):
    '''
    Determine if first 8 bytes contain the header packet's
    signature. hdr length must be 8bytes.

    returns boolean
    '''
    hdr_dict = parse_hdr(hdr_raw)

    #confirm LoFASM network packet
    if hdr_dict['signature'] == HDR_V1_SIGNATURE:
        if print_header:
            print_hdr(hdr_dict)
        return True
    else:
        return False

def check_headers(file_obj, packet_size_bytes=PACKET_SIZE_B, verbose=False, print_headers=False):
    '''
    Iterate through LoFASM Data file and check that all the header packets
    are in place.

    Note: The verbose keyword argument is no longer used. It is being left in the definition
    for now for compatibility purposes.
    '''

    freeze_pointer = file_obj.tell()

    #get file header
    file_hdr = parse_file_header(file_obj)

    #move pointer past file header
    file_obj.seek(file_hdr[3][1])

    filesize_bytes = get_filesize(file_obj)

    #get number of network packets in lofasm file
    number_of_packets = filesize_bytes / packet_size_bytes

    packet_counter = 0
    err_counter = 0
    best_loc = None
    first_header = True
    print_msg = 'Checking UDP headers in %s ...\n' % file_obj.name

    #iterate through lofasm network packets
    for i in range(number_of_packets):
        #read next packet in file
        block = file_obj.read(packet_size_bytes)

        packet_counter += 1 #increment number of packets read

        if is_header(block):
            if first_header:
                print_msg += "\n|packet|packets since hdr|loc|integration|hdr_cnt|sig|\n"
                first_header = False
                best_loc = file_obj.tell() - packet_size_bytes
            elif packet_counter < 17:
                print_msg += "WARNING: unexpected header packet arrived %i " % (17 - packet_counter)
                print_msg += "packets too early!\n"
                err_counter += 1
                best_loc = file_obj.tell() - packet_size_bytes

            hdr_dict = parse_hdr(block[:8])

            print_msg += "|%i|%i|%i|" % (i, packet_counter, file_obj.tell() - packet_size_bytes)

            #print "HDR:",
            for key in hdr_dict:
                print_msg += str(hdr_dict[key]) + "|"
            print_msg += "\n"
            packet_counter = 0 #reset packet counter
        else:
            pass

    #restore file pointer
    file_obj.seek(freeze_pointer)
    if print_headers:
        print print_msg

    return (best_loc, err_counter)

def get_filesize(file_obj):
    '''
    Usage: get_filesize(file_obj)
    returns file size (in bytes) of file pointed to by file_obj.
    '''

    freeze_pointer = file_obj.tell()

    if type(file_obj) == gzip.GzipFile:
        hdr = parse_file_header(file_obj)
        return int(hdr[12][1])*INTEGRATION_SIZE_B + 96
    else:
        file_obj.seek(0,2) #move to end of file
        end_pointer = file_obj.tell()
        file_obj.seek(freeze_pointer)
        return end_pointer

def get_number_of_integrations(file_obj):
    '''returns number of integrations in data file'''

    fileSize = get_filesize(file_obj)
    num_integrations = fileSize / INTEGRATION_SIZE_B
    return num_integrations

def get_next_raw_burst(file_obj, packet_size_bytes=None, packets_per_burst=None, loop_file=False):
    '''
    Usage:
    burst_generator = get_next_raw_burst(<file_object>[, packet_size_bytes, packets_per_burst, loop_file])

    Python generator that yields a string containing data from the next 17
    LoFASM packets in file_obj that make up a single 'burst'.

    If file_obj's pointer is not at zero, then assume it is in the desired
    start position and begin reading from that point in the file.
    '''

    #get file location from file handle
    file_start_position = file_obj.tell()

    #determine the number of bytes in a single integration
    if packet_size_bytes is None or packets_per_burst is None:
        burst_size = INTEGRATION_SIZE_B
    else:
        burst_size = packet_size_bytes * packets_per_burst
        print "Warning: unusual integration size ", burst_size


    while 1:
        raw_dat = file_obj.read(burst_size)
        if (not raw_dat) or (len(raw_dat) < burst_size):
            if loop_file:
                print "Reached end of file. Starting over..."
                file_obj.seek(file_start_position)
                raw_dat = file_obj.read(burst_size)
                yield LoFASM_burst(raw_dat)
            else:
                print "No more data to read in %s" % file_obj.name
                print "Exiting..."
                exit()
        else:
            #yield raw_dat
            yield LoFASM_burst(raw_dat)

def find_first_hdr_packet(file_obj, packet_size_bytes=PACKET_SIZE_B, hdr_size=8):
    '''
    Return start location of first valid header packet in file.
    '''
    #total number of packets in file
    num_packets = get_filesize(file_obj) / packet_size_bytes

    for i in range(num_packets):
        #read packet header
        pkt_hdr = file_obj.read(hdr_size)

        #if header is valid and the next packet is not a header packet
        # then fix pointer and return location
        #else continue to next packet
        if is_header(pkt_hdr, print_header=False):

            if not is_next_packet_header(file_obj, packet_size_bytes=packet_size_bytes, hdr_size_bytes=8):

                #fix pointer
                file_obj.seek(file_obj.tell() - hdr_size)

                #return new pointer location
                return file_obj.tell()

        file_obj.seek(file_obj.tell() + packet_size_bytes - hdr_size)
    print "Finished searching: did not find valid header in %s" % file_obj.name

def is_next_packet_header(file_obj, packet_size_bytes=PACKET_SIZE_B, hdr_size_bytes=8):
    '''
    Check if the next packet is a header packet
    '''
    freeze_location = file_obj.tell()
    next_pkt_location = file_obj.tell() + packet_size_bytes - hdr_size_bytes
    file_obj.seek(next_pkt_location)
    next_pkt_hdr = file_obj.read(hdr_size_bytes)
    file_obj.seek(freeze_location)
    if is_header(next_pkt_hdr):
        return True
    else:
        return False

####Class Definitions
class LoFASM_burst:
    '''
    class to represent an entire LoFASM Burst sequence.
    A LoFASM Burst is a collection of 17 UDP network packets.
    The first packet is always the header packet.
    The 16 network packets that follow raw LoFASM filterbank
    data.
    '''

    __fmt_autos = '>L'
    __fmt_cross = '>l'
    __fmt_beams = '>f'

    __type_autos = int
    __type_cross = complex
    __type_beams = np.float64

    def __init__(self, burst_string, packet_size=PACKET_SIZE_B,
                 unpack_binary=True):
        '''
        initialize LoFASM Burst instance
        '''

        self.autos = {}
        self.cross = {}
        self.hdr = {}
        self.packet_size = packet_size

        # read header packet
        hdr_packet = burst_string[:packet_size]

        # in this version, we need only to be able to read the first
        # 8 bytes of the header packet because the header packet
        # consists of the same 8byte row repeating itself.
        # in the future it would be good to take full advantage of this
        # header packet to store more meta-data at the FPGA level.
        self.hdr = parse_hdr(hdr_packet[:8])
        self.raw = burst_string
        if unpack_binary:
            self._unpack_burst(burst_string)
        else:
            self._bufRaw = io.BytesIO()
            self._bufRaw.write(burst_string)
            self._bufRaw.seek(0)
            # initialize buffers for each polarization
            for key in Baselines:
                if key[0] == key[1]:
                    self.autos[key] = io.BytesIO()
                    self.autos[key].write(bufReal)
                    self.autos[key].seek(0)
                else:
                    self.cross[key] = io.BytesIO()
                    self.cross[key].write(bufCplx)
                    self.cross[key].seek(0)
            self._load_raw()

    def _load_raw(self, iburst=None):
        '''load each polarization as raw data
        '''
        raw = self._bufRaw
        if iburst is not None:
            raw.seek(0)
            raw.write(iburst)
        # skip past the header packet
        raw.seek(8192)
        
        for isOdd in [False, True]:
            # if isOdd is False load even bins
            # if True then load odd bins
            if isOdd:
                for k in AUTOPOLS:
                    self.autos[k].seek(4)
                for k in CROSSPOLS:
                    self.cross[k].seek(8)
            
            # only read half of the packets since we are ignoring the
            # second half of the channels below.
            
            # load AA & BB bins
            for i in range512:
                self.autos['AA'].write(raw.read(4))
                self.autos['BB'].write(raw.read(4))
                self.autos['AA'].seek(4, 1)
                self.autos['BB'].seek(4, 1)
            # move forward 4096 bytes to the next packet
            raw.seek(4096, 1)
            # load CC & DD bins
            for i in range512:
                self.autos['CC'].write(raw.read(4))
                self.autos['DD'].write(raw.read(4))
                self.autos['CC'].seek(4, 1)
                self.autos['DD'].seek(4, 1)
            raw.seek(4096, 1)
            # load bins for cross power
            for k in CROSSPOLS:
                for i in range512:
                    self.cross[k].write(raw.read(8))
                    self.cross[k].seek(8, 1)
                raw.seek(4096, 1)

                

    def _unpack_burst(self, burst_string):
        '''unpack contents of burst_string into class attributes
        '''
        packet_size = self.packet_size

        #split data portion into even and odd bins
        burst_real_even_bin = burst_string[packet_size:packet_size*3]
        burst_complex_even_bin = burst_string[packet_size*3:packet_size*9]
        burst_real_odd_bin = burst_string[packet_size*9:packet_size*11]
        burst_complex_odd_bin = burst_string[packet_size*11:]

        #unpack all values
        burst_real_even_val = list(struct.unpack("4096".join(self.__fmt_autos),
                                                 burst_real_even_bin))
        burst_real_odd_val = list(struct.unpack("4096".join(self.__fmt_autos),
                                                burst_real_odd_bin))
        burst_complex_even_val = struct.unpack("12288".join(self.__fmt_cross),
                                               burst_complex_even_bin)
        burst_complex_odd_val = struct.unpack("12288".join(self.__fmt_cross),
                                              burst_complex_odd_bin)

        blocksize = 2048 #values

        #read blocks
        AABB_even = burst_real_even_val[:blocksize]
        CCDD_even = burst_real_even_val[blocksize:]
        AABB_odd = burst_real_odd_val[:blocksize]
        CCDD_odd = burst_real_odd_val[blocksize:]

        #get lists of complex values
        AB_even = self.__cross_make_complex(burst_complex_even_val[:blocksize])
        AC_even = self.__cross_make_complex(burst_complex_even_val[blocksize:blocksize*2])
        AD_even = self.__cross_make_complex(burst_complex_even_val[blocksize*2:blocksize*3])
        BC_even = self.__cross_make_complex(burst_complex_even_val[blocksize*3:blocksize*4])
        BD_even = self.__cross_make_complex(burst_complex_even_val[blocksize*4:blocksize*5])
        CD_even = self.__cross_make_complex(burst_complex_even_val[blocksize*5:])

        AB_odd = self.__cross_make_complex(burst_complex_odd_val[:blocksize])
        AC_odd = self.__cross_make_complex(burst_complex_odd_val[blocksize:blocksize*2])
        AD_odd = self.__cross_make_complex(burst_complex_odd_val[blocksize*2:blocksize*3])
        BC_odd = self.__cross_make_complex(burst_complex_odd_val[blocksize*3:blocksize*4])
        BD_odd = self.__cross_make_complex(burst_complex_odd_val[blocksize*4:blocksize*5])
        CD_odd = self.__cross_make_complex(burst_complex_odd_val[blocksize*5:])

        #seperate different inputs
        AA_even, BB_even = self.__split_autos(AABB_even)
        AA_odd, BB_odd = self.__split_autos(AABB_odd)
        CC_even, DD_even = self.__split_autos(CCDD_even)
        CC_odd, DD_odd = self.__split_autos(CCDD_odd)

        #create power spectrum for each input and the cross correlations
        self.autos['AA'] = self.__interleave_even_odd(AA_even, AA_odd)
        self.autos['BB'] = self.__interleave_even_odd(BB_even, BB_odd)
        self.autos['CC'] = self.__interleave_even_odd(CC_even, CC_odd)
        self.autos['DD'] = self.__interleave_even_odd(DD_even, DD_odd)

        self.cross['AB'] = self.__interleave_even_odd(AB_even, AB_odd)
        self.cross['AC'] = self.__interleave_even_odd(AC_even, AC_odd)
        self.cross['AD'] = self.__interleave_even_odd(AD_even, AD_odd)
        self.cross['BC'] = self.__interleave_even_odd(BC_even, BC_odd)
        self.cross['BD'] = self.__interleave_even_odd(BD_even, BD_odd)
        self.cross['CD'] = self.__interleave_even_odd(CD_even, CD_odd)

    def __split_autos(self, XXYY_list):
        '''
        Split XXYY_even (or XXYY_odd) into two lists
        corresponding to XX and YY. Return a tuple with
        two elements, each a list: (AA_even, BB_even) or
        (AA_even, AA_odd).
        '''

        XX_list = []
        YY_list = []

        for i in range(len(XXYY_list)/2):
            XX_list.append(XXYY_list[2*i])
            YY_list.append(XXYY_list[2*i + 1])

        return (XX_list, YY_list)

    def __cross_make_complex(self, cross_list):
        '''
        Convert cross_list into complex
        cross_list.

        cross_list must be in the format
        [real0, imag0, real1, imag1, real2, imag2, ...]
        and must contain an even number of elements.
        '''

        cross_complex = []
        for i in range(len(cross_list)/2):
            cross_complex.append(complex(cross_list[i*2], cross_list[i*2+1]))

        return cross_complex

    def __interleave_even_odd(self, even_list, odd_list):
        '''
        Iterate and interleave even_list and odd_list.
        Return interleaved list.
        '''

        if len(even_list) != len(odd_list):
            print 'interleave even: ', len(even_list)
            print 'interleave odd: ', len(odd_list)
            print "Cannot interleave! Even and odd lists must be of equal length!"
        else:
            interleave_list = []
            for i in range(len(even_list)):
                interleave_list.append(even_list[i])
                interleave_list.append(odd_list[i])

            return interleave_list

    def pack_binary(self, spect):
        '''
        Convert spectrum data into writable binary string

        usage: pack_binary(spect)
        returns: binary str containing data in spect

        the data type of the information stored in spect
        must correspond to one of the data types used in
        LoFASM Bursts. (int, np.complex, or np.float64)

        all elements in spect must be of the same data type.
        '''

        bin_str = ''

        #check whether spect contains int or complex values
        if (type(spect[0]) is self.__type_autos):
            format = self.__fmt_autos
            for val in spect:
                bin_str += struct.pack(format, val)
        elif type(spect[0]) is self.__type_cross:
            format = self.__fmt_cross
            for val in spect:
                bin_str += struct.pack(format, val.real)
                bin_str += struct.pack(format, val.imag)
        elif type(spect[0]) is self.__type_beams:
            format = self.__fmt_beams
            for val in spect:
                bin_str += struct.pack(format, val)

        return bin_str

    def getAutoCorrelationDataType(self):
        '''
        Return the data type used for
        auto correlation data.
        '''

        return self.__fmt_autos

    def getCrossCorrelationDataType(self):
        '''
        Return the data type used for
        cross correlation data.
        '''
        return self.__fmt_cross

    def getBeamDataType(self):
        '''
        Return the data type used for beamed data.
        '''
        return self.__fmt_beams

    def __gen_LoFASM_beams(self, Ai=1.0, Aq=1.0):
        '''
        generate LoFASM beams and store them in self.beams

        this method creates and initializes self.beams.
        '''

        self.beams = {}
        AA_pow = np.array(self.autos['AA'])
        BB_pow = np.array(self.autos['BB'])
        CC_pow = np.array(self.autos['CC'])
        DD_pow = np.array(self.autos['DD'])
        BD_cross = np.array(self.cross['BD'])
        AC_cross = np.array(self.cross['AC'])
        self.beams['BN'] = BB_pow + DD_pow + (2/(Ai*Aq)) * np.real(BD_cross)
        self.beams['BE'] = AA_pow + CC_pow + (2/(Ai*Aq)) * np.real(AC_cross)

    def create_LoFASM_beams(self):
        self.__gen_LoFASM_beams()

class LoFASMFileCrawler(object):
    '''
    File crawler for LoFASM data files.
    '''

    def __init__(self, filename, scan_file=False, start_loc=None, gz=False,
                 generate_beams=False, unpack_binary=True):
        '''
        initialize LoFASM File Crawler instance

        Usage: crawler = LoFASMFileCrawler(filename[, scan_file][, start_loc])

        Where scan_file is a boolean value. If True then scan and print the all
        integration headers in file. This is an optional argrument.
        '''


        self.filename = filename
        self.scan_file = scan_file
        self.start_loc = start_loc
        self._status_open = False
        self.corrupt = False
        if filename.endswith('.gz') or gz:
            self.gz = True
        else:
            self.gz = gz
        self.eof = False
        self._unpack_binary = unpack_binary
        self._generate_beams = generate_beams
        self._int_hdr = {} #integration header
        self._file_hdr = {} #file header
        self._acc_num_ref = None #first integration id
        self._acc_num = None #current integration id
        self._ptr_loc = None #location of file pointer
        self._int_size = None
        self._lofasm_file = None #file handle
        self._burst = None #integration data
        self._lofasm_file_end = None #EOF
        self._print_int_headers = False
        self._data_start = None #pointer location at start of data
        self._int_time = None #TimeDelta(0.0, format='sec')
        self._pol = None #currently selected baseline

        self.autos = None
        self.cross = None
        self.beams = None

    def _find_next_burst(self, start=0):
        '''
        return the start location of the next packet burst

        return -1 on failure to find burst
        '''
        burstKey = "\xde\xfc\xab"
        blockSize = 8192*17
        burstFound = False
        testBlock = ''
        offset = start
        freeze_ptr = self._lofasm_file.tell()
        self._lofasm_file.seek(start)
        try:
            while not burstFound:
                testBlock = self._lofasm_file.read(blockSize)
                blockPtr = testBlock.find(burstKey)
                if blockPtr:
                    burstFound = True
                    blockPtr = blockPtr + offset # correct for location in file
                else: # key not found
                    offset += blockSize
        except EOFError:
            print "reached end of file."
            blockPtr = -1
        self._lofasm_file.seek(freeze_ptr)
        return blockPtr

    def moveToNextBurst(self):
        ptr = self._find_next_burst(start=self._lofasm_file.tell())
        if ptr == -1:
            raise EOFError
        self._lofasm_file.seek(ptr)
        self._update_ptr()
        self._update()

    def open(self):
        #open file
        filename = self.filename
        scan_file = self.scan_file
        start_loc = self.start_loc

        try:
            if type(filename) is file:
                self._lofasm_file = filename
            else:
                #check file extension
                if not filename.endswith('.lofasm') and \
                   not filename.endswith('.lofasm.gz'):
                    print "Warning: {} file extension not recognized.".format(
                        filename)
                    print "Attempting to open anyway."
                #get file handler
                if self.gz:
                    print "Warning: gzipped files are only supported for header versions 4 or higher."
                    self._lofasm_file = gzip.open(filename, 'rb')
                else:
                    self._lofasm_file = open(filename, 'rb')

        except IOError as err:
            print "Error opening ", filename
            print err.message
            raise IOError('{} does not exist'.format(filename))

        #get header information
        self._file_hdr = parse_file_header(self._lofasm_file)

        #find end of file
        if int(self._file_hdr[2][1]) >= 4:
            self._lofasm_file_end = self._file_hdr[3][1] + int(self._file_hdr[12][1])*INTEGRATION_SIZE_B
        else:
            self._lofasm_file_end = self._get_file_end_loc()

        #get integration/burst size
        self._int_size = INTEGRATION_SIZE_B

        if scan_file:
            self._data_start, errno = check_headers(self._lofasm_file)
        elif start_loc:
            self._data_start, errno = start_loc, 0
        else:
            try:
                self._lofasm_file.seek(self._file_hdr[3][1])
                self._update_ptr()
                self._update_data()
                self._data_start = self._file_hdr[3][1]
            except IntegrationError:
                if self._file_hdr[2][1] == 1 or self._file_hdr[2][1] == 2:
                    self._data_start = 204896
                else:
                    self._data_start = self._find_next_burst(start=0)

        #move file pointer to data location
        self._lofasm_file.seek(self._data_start)

        self._update_ptr()

        #get times
        self.int_time = TimeDelta(float(self._file_hdr[10][1]), format='sec')
        mjd_start = float(self._file_hdr[8][1])
        mjd_start += float(self._file_hdr[9][1])/1000/86400
        self.time_start = Time(mjd_start, format='mjd', scale='utc')
        self.time = self.time_start


        #increment to first integration
        try:
            self._update_data()
        except IntegrationError:
            self.corrupt = True


        #set reference accumulation number
        self._acc_num_ref = self._acc_num

        #update time
        self._update_time()

        self._status_open = True

    def isopen(self):
        return self._status_open

    def get_data_start(self):
        '''
        return the start location of the LoFASM data
        '''
        return self._data_start

    def _update(self, N=1):
        '''
        run update sequences
        1. update data arrays
        2. update time stamps
        '''

        self._update_data(N)
        self._update_time()

    def getNumberOfIntegrationsInFile(self):
        '''
        return the total number of integrations in current
        LoFASM file.
        '''

        # check file header version
        if int(self._file_hdr[2][1]) == 4:
            return int(self._file_hdr[12][1])
        else:
            return int((self._lofasm_file_end - self._data_start) / self._int_size)

    def _update_time(self):
        '''
        update time attribute according to current integration
        '''
        self.time = self.time_start + (self._acc_num - self._acc_num_ref)*self.int_time

    def _update_data(self, N=1):
        '''
        Update object's burst data by incrementng by N integrations.
        '''

        #read and update pointers
        self._move_ptr(N-1)
        data = self._lofasm_file.read(self._int_size)
        if len(data) < self._int_size:
            raise EOFError
        self._burst = LoFASM_burst(data, unpack_binary=self._unpack_binary)
        if self._generate_beams:
            self._burst.create_LoFASM_beams()
        self._update_ptr()

        #update integration header and accumulation number
        self._int_hdr = self._burst.hdr
        self._acc_num = self._int_hdr['acc_num']

        #update data arrays
        self.autos = self._burst.autos
        self.cross = self._burst.cross
        if self._generate_beams:
            self.beams = self._burst.beams


        if self._print_int_headers:
            print self._int_hdr

        #validate integration
        if self._int_hdr['signature'] != HDR_V1_SIGNATURE:
            raise IntegrationError("bad integration data")

    def _get_file_end_loc(self):
        '''Return end pointer value.'''
        freeze_ptr = self._lofasm_file.tell()
        if self._file_hdr[2][1] < 4 and self.gz:
            end_ptr = -1
        else:
            self._lofasm_file.seek(0,2) #move to end of file
            end_ptr = self._lofasm_file.tell()
        self._lofasm_file.seek(freeze_ptr) #ptr back in place
        return end_ptr

    def _move_ptr(self, N):
        '''Move file pointer up by N integrations.'''
        self._update_ptr()
        self._lofasm_file.seek(self._ptr_loc + N * self._int_size)
        self._update_ptr()

    def _update_ptr(self):
        '''
        Update pointer to LoFASM file.
        '''
        self._ptr_loc = self._lofasm_file.tell()

    def forward(self, N=1):
        '''Move forward by N integrations.
        On EOF, do nothing.
        '''

        if N < 0:
            self.backward(abs(N))
            return

        #check boundaries
        #if (self._lofasm_file_end - self._ptr_loc) >= N*INTEGRATION_SIZE_B:
        #    self._update(N)
        #else:
        #    raise EOFError

        try:
            self._update(N)
        except EOFError:
            self.eof = True
            raise EOFError

    def backward(self, N=1):
        '''Move back to previous integration.'''

        if N < 0:
            self.forward(abs(N))
            return

        #check boundaries
        if self._ptr_loc >= N*INTEGRATION_SIZE_B:
            self._update(-N)
        else:
            print "Beginning of file"

    def reset(self):
        '''
        move back to first integration in file
        '''
        self._lofasm_file.seek(self._data_start)
        self._update_ptr()
        self._update()

    def getIntegrationHeader(self):
        '''
        Return integration header as a dictionary.
        '''
        return self._int_hdr

    def getFileHeader(self):
        '''
        Return LoFASM file header as a dictionary.
        '''
        return self._file_hdr

    def getAccNum(self):
        '''
        Return accumulation number.
        '''
        return self._acc_num

    def getAccReference(self):
        '''
        Return accumulation reference value.
        '''
        return self._acc_num_ref

    def getFilePtr(self):
        '''
        Return file pointer location.
        '''
        return self._ptr_loc

    def getIntegrationSize(self):
        '''
        Return LoFASM integration size in bytes.
        '''
        return self._int_size

    def getFilename(self):
        '''
        Return filename.
        '''
        return self.filename

    def print_int_headers(self, state=None):
        '''
        Set self._print_int_headers to boolean(state).
        If state is NoneType then print current value
        of self._print_int_headers.
        '''

        if state == None:
            print "Print Integration Headers: ", bool(self._print_int_headers)
            return

        s = bool(state)
        if self._print_int_headers != s:
            print "Setting value to ", str(s)
            self._print_int_headers = s

    def setPol(self, pol):
        '''
        set polarization to be returned when self.get() is called
        '''

        pol = pol.upper()

        if pol in Baselines:
            self._pol = pol
        else:
            raise ValueError(pol)

    def get(self):
        '''
        get filterbank data in polarization set by method setPol
        returns a numpy array
        '''

        if self._pol is None:
            val = None
        elif self._pol in AUTOPOLS:
            if self._unpack_binary:
                val = np.array(self.autos[self._pol])[:1024]
            else:
                val = self.autos[self._pol]
        elif self._pol in CROSSPOLS:
            if self._unpack_binary:
                val = np.array(self.cross[self._pol])[:1024]
            else:
                val = self.cross[self._pol]

        return val


    def __repr__(self):
        return "LoFASMFileCrawler %s" % (self.getFilename())

    def __str__(self):
        return "LoFASMFileCrawler %s" % (self.getFilename())

    def __del__(self):
        del self.autos
        del self.cross
        del self.beams
        del self._burst
        del self._lofasm_file
