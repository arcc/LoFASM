#methods for writing LoFASM data to disk

from astropy.time import Time

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

def write_header_to_file(outfile, host, Nacc=4096, fpga_clk_T=1e-08, 
	Nchan=2048, fileNotes=' '):
    '''
    prepends data file with LoFASM spectrometer header.
    fpga_clk_T  is the period of the FPGA clock in seconds
    Nchan is the number of FFT bins in the spectrometer
    Nacc is the number of accumulations averaged before dumping
    '''
    
    stamp_mjd = str(Time.now().mjd).split('.')
    FFT_clk_cycles = Nchan >> 1
    integration_time = fpga_clk_T * FFT_clk_cycles * Nacc
    BW = 200.0
    Nbins = 2048
    msec_day = 86400 * 1000

    hdr_len = fmt_header_entry('96')
    hdr_ver = fmt_header_entry('2')
    hdr_sig = fmt_header_entry('LoCo')
    fmt_ver = fmt_header_entry('1')
    station = fmt_header_entry(host)
    fstart = fmt_header_entry('0')
    fstep = fmt_header_entry(str(BW/Nbins).split('.')[1]) #mhz
    num_bins = fmt_header_entry(str(Nbins))
    mjd_day = fmt_header_entry(stamp_mjd[0])
    mjd_msec = fmt_header_entry(float('.'+stamp_mjd[1])*msec_day)
    int_time = fmt_header_entry(str(integration_time))
    notes = fmt_header_entry(fileNotes)

    header_str = hdr_sig + hdr_ver + hdr_len + station + num_bins + fstart +\
        fstep + mjd_day + mjd_msec + int_time + fmt_ver + notes
    
    outfile.write(header_str)