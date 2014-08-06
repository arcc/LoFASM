#!/opt/python2.7/bin/python2.7
# LoFASM Recorder

import socket, sys, os
from datetime import datetime

def create_socket(dev_ip='192.168.4.12', dev_port=60001):
    print "Setting up the socket interface"
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    #sock.bind(('192.168.4.11',60001))
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
	
def write_header_to_file(outfile, fpga_gain, Nacc, fpga_clk_T=1e-08, Nchan=2048):
    '''
    prepends data file with LoFASM spectrometer header.
    fpga_clk_T  is the period of the FPGA clock in seconds
    Nchan is the number of FFT bins in the spectrometer
    Nacc is the number of accumulations averaged before dumping
    '''
    FFT_clk_cycles = Nchan >> 1
    integration_time = fpga_clk_T * FFT_clk_cycles * Nacc
    hdr_str = ''
    fmt_sig = 'LoCo'
    fmt_ver = '1'
    station = 'LoFASMIV'
    fstart = '0'
    fstop = '200'
    gain = str(fpga_gain)
    int_time = str(integration_time)

if __name__ == "__main__":
	from optparse import OptionParser
	p = OptionParser()
	p.set_usage('ten_gbe_recorder.py')
	#p.add_option('-f','--filename',dest='output_filename',
	#	help="set name of file to save data to.")
	p.add_option('--max_packets', dest='max_packets', type='int',
		default=1000, 
		help='specify number of packets to write to disk.')
        p.add_option('-g', '--gain', dest='fpga_gain',
                help= 'fpga gain')
        p.add_option('-C',dest='continuous_write',
                help='Set to write data continously.')

	opts, args = p.parse_args(sys.argv[1:])
	
	
	sock = create_socket()
        
        stamp = datetime.now()
        timestamp = stamp.strftime('%Y%m%d_%H%M%S')
        current_date = stamp.strftime('%Y%m%d')
        root_dir = '/data'
        filename = timestamp+'_'+opts.fpga_gain+'.lofasm'
        if current_date not in os.listdir(root_dir):
            os.mkdir(root_dir+'/'+current_date)
        output_file = open(root_dir+'/'+current_date+'/'+filename,'wb')
        
	write_packets_from_memory(output_file, record_packets_into_memory(
		sock, opts.max_packets))
	
	
	
