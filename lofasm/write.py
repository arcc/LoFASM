#methods for writing LoFASM data to disk

from astropy.time import Time
import gzip
import numpy as np
import struct

def fmt_header_entry(entry_str, fmt_len=8):
    '''
    ensure that every header entry is 8 characters long. if longer, then
    truncate. if shorter, then pad with white space. returns formatted string
    '''

    entry_str = str(entry_str)
    entry_len = len(entry_str)

    if entry_len > fmt_len:
        return entry_str[:fmt_len] #truncate
    elif entry_len < fmt_len:
        diff = fmt_len - entry_len
        return ' '*diff + entry_str #pad front with white space
    else:
        return entry_str

def write_header_to_file(outfile, host, tstart, Nacc=8192, fpga_clk_T=1e-08,
	Nchan=2048, ra='NULL', dec='NULL'):
    '''
    prepends data file with LoFASM spectrometer header.
    fpga_clk_T  is the period of the FPGA clock in seconds
    Nchan is the number of FFT bins in the spectrometer
    Nacc is the number of accumulations averaged before dumping
    '''


    stamp_mjd = str(tstart.mjd).split('.')
    FFT_clk_cycles = Nchan >> 1
    integration_time = fpga_clk_T * FFT_clk_cycles * Nacc
    BW = 200.0
    Nbins = 2048
    msec_day = 86400 * 1000

    hdr_len = fmt_header_entry('108')
    hdr_ver = fmt_header_entry('3')
    hdr_sig = fmt_header_entry('LoCo')
    fmt_ver = fmt_header_entry('1') # data format version
    station = fmt_header_entry(host)
    fstart = fmt_header_entry('0')
    fstep = fmt_header_entry(str(BW/Nbins).split('.')[1]) #mhz
    num_bins = fmt_header_entry(str(Nbins))
    mjd_day = fmt_header_entry(stamp_mjd[0])
    mjd_msec = fmt_header_entry(float('.'+stamp_mjd[1])*msec_day)
    int_time = fmt_header_entry(str(integration_time))
    ra_coord = fmt_header_entry(ra, 10)
    dec_coord = fmt_header_entry(dec, 10)

    header_str = hdr_sig + hdr_ver + hdr_len + station + num_bins + fstart +\
        fstep + mjd_day + mjd_msec + int_time + fmt_ver + ra_coord + dec_coord

    outfile.write(header_str)

def complex2str(x):
    '''
    convert a list of complex numbers into a binary
    string of 4byte _integer_ values in the following format:

    A_real, A_imag, B_real, B_imag, C_real, C_imag, ...
    '''
    import struct

    assert(type(x) is list)
    assert(type(x[0]) is complex)

    binary_str = ''

    for cval in x:
        binary_str += struct.pack('>l',cval.real)
        binary_str += struct.pack('>l',cval.imag)

    return binary_str
