#!/usr/bin/python2.7
# LoFASM Recorder

import socket, sys, os
from datetime import datetime
from astropy.time import Time
from lofasm import parse_data as pdat

#hostname
host = os.environ['STATION']

# function defs
def getTimeStampMJD():
    stamp_mjd = Time.now().mjd
    return stamp_mjd

def getTimeStampUTC():
    stamp_utc = Time.now().datetime.strftime('%Y%m%d_%H%M%S')
    return stamp_utc

def create_socket(dev_ip='192.168.4.5', dev_port=60001):
    print "Setting up the socket interface"
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((dev_ip, dev_port))
    print "Created bound socket on %s:%i" % (dev_ip, dev_port)
    return sock

def record_packets_into_memory(sock, MAX_PACKETS):
	packet_array = []
	num_bytes = 8192
	print "receiving packets"
	for i in range(MAX_PACKETS):
		packet_array.append(sock.recv(num_bytes))
	return packet_array
	
def write_packets_from_memory(outfile, packet_array):
	[outfile.write(x) for x in packet_array]
        print "done writing packets to:\n%s!!" % outfile.name

def getNumberOfPackets(dur_sec):
    return pdat.getNumPackets(dur_sec)

def fmt_header_entry(entry_str, fmt_len=8):
    '''ensure that every header entry is 8 characters long. if longer, then
    truncate. if shorter, then pad with white space. returns formatted string'''
    entry_str = str(entry_str)
    entry_len = len(entry_str)

    if entry_len > fmt_len:
        return entry_str[:fmt_len] #truncate
    elif entry_len < fmt_len:
        diff = fmt_len - entry_len
        return ' '*diff + entry_str #pad front with white space
    else:
        return entry_str 

def write_header_to_file(outfile, Nacc=4096, fpga_clk_T=1e-08, Nchan=2048,
        fileNotes=' '):
    '''
    prepends data file with LoFASM spectrometer header.
    fpga_clk_T  is the period of the FPGA clock in seconds
    Nchan is the number of FFT bins in the spectrometer
    Nacc is the number of accumulations averaged before dumping
    '''
    stamp_mjd = str(getTimeStampMJD()).split('.')
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

if __name__ == "__main__":
    from optparse import OptionParser
    p = OptionParser()
    p.set_usage('ten_gbe_recorder.py')
    p.add_option('-t', dest='rec_dur', help='Set the duration of the observation in seconds.', default=5)
    p.add_option('--root_dir', dest='root_dir', type='str',  help='path pointing to root data dir. default is /data1', default='/data1')
    p.add_option('--note', dest='note', type='str', help='comments notes. anything longer than 8bytes will be truncated.', default=None)

    opts, args = p.parse_args(sys.argv[1:])
    sock = create_socket()
    timestamp = getTimeStampUTC()
    current_date = timestamp[:8]
    root_dir = opts.root_dir
    filename = timestamp+'.lofasm'
    
    

    #create file directory nonexistent
    if current_date not in os.listdir(root_dir):
        os.mkdir(root_dir+'/'+current_date)
    #get file handle
    output_file = open(root_dir+'/'+current_date+'/'+filename,'wb')
    
    if opts.note:
        write_header_to_file(output_file, fileNotes=opts.note, Nacc=8192)
    else:
        write_header_to_file(output_file, Nacc=8192)

    numPacketsToWrite = getNumberOfPackets(opts.rec_dur)
    write_packets_from_memory(output_file, record_packets_into_memory(
		sock, numPacketsToWrite))
    
