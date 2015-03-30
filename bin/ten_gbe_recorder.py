#!/usr/bin/python2.7
# LoFASM Recorder

import socket, sys, os
from datetime import datetime
from astropy.time import Time
from lofasm import parse_data as pdat
from lofasm.write import write_header_to_file

#hostname
host = os.environ['STATION']

# function defs
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
        write_header_to_file(output_file, host, fileNotes=opts.note, Nacc=8192)
    else:
        write_header_to_file(output_file, host, Nacc=8192)

    numPacketsToWrite = getNumberOfPackets(opts.rec_dur)
    write_packets_from_memory(output_file, record_packets_into_memory(
		sock, numPacketsToWrite))
    
