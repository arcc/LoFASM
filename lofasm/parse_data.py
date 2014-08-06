# python file for parsing LoCo Data
import lofasm_dat_lib as lofasm_dat
import struct, sys
import numpy as np
import parse_data_H as pdat_H
import datetime

LoFASM_SPECTRA_KEY_TO_DESC = pdat_H.LoFASM_SPECTRA_KEY_TO_DESC



##### Function Definitions
def freq2bin(freq):
	rbw = 200.0/2048
	return freq / rbw

def bin2freq(bin):
	rbw = 200.0/2048
	return bin * rbw


def parse_filename(filename):
	#'''returns the file's time stamp as a list
	#[YYmmdd, HHMMSS]
    #'''
    #if filename[-7:] == '.lofasm':
    #print
    filename = filename.rstrip('.lofasm')
    parse_list = filename.split('_')
   
    date = parse_list[0]
    time = parse_list[1]

    return [date, time]
def get_datetime_obj(dateStamp, timeStamp):
    '''parses LoFASM dateStamp and timeStamp and returns 
    a datetime object'''
    year = int(dateStamp[:4])
    month = int(dateStamp[4:6])
    day = int(dateStamp[6:])
    hour = int(timeStamp[:2])
    minute = int(timeStamp[2:4])
    second = int(timeStamp[4:])
    return datetime.datetime(year, month, day, 
            hour, minute, second)

def spectrum_conv_code(code_str):
	return LoFASM_SPECTRA_KEY_TO_DESC[code_str]

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
		#put file pointer back (probably not necessary)
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

	for i in range(fields_left_to_populate):
		j = i + 4 #start with 3rd field
		if i == (fields_left_to_populate - 1):
			fhdr_field_dict[j][1] = remaining_hdr_string[i*pdat_H.HDR_ENTRY_LENGTH:].strip(' ')
		else:		
			fhdr_field_dict[j][1] = remaining_hdr_string[i*pdat_H.HDR_ENTRY_LENGTH:
				(i+1)*pdat_H.HDR_ENTRY_LENGTH].strip(' ')

	#move file cursor back to original position
	file_obj.seek(freeze_pointer)

	return fhdr_field_dict





def parse_hdr(hdr, hdr_size_bytes=8, version=1):
	'''Usage: parse_hdr(<64bit_string>,[version])Parse the first 64 bits of 
	 LoFASM data packet and return a dictionary containing each header value.

		If hdr has a length greater than 8bytes then it will be truncated 
		and only the first 8 bytes will be parsed.
	'''
	#if len(hdr) > hdr_size_bytes:
	#	hdr = hdr[:hdr_size_bytes]
	#	print "hdr_length: %i" %len(hdr)

	padding_1B = "\x00"
	hdr_dict = {}
	hdr_dict['signature'] = [x for x in struct.unpack('>L', 
		padding_1B+hdr[:3])][0]
	hdr_dict['acc_num'] = [x for x in struct.unpack('>L', 
		padding_1B+hdr[3:6])][0]
	hdr_dict['hdr_cnt'] = [x for x in struct.unpack('>L', 
		2*padding_1B+hdr[6:8])][0]

	return hdr_dict
 
def print_hdr(hdr_dict):
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
	#print hdr_dict['signature']
	if hdr_dict['signature'] == lofasm_dat.HDR_V1_SIGNATURE:
		if print_header:
			print_hdr(hdr_dict)
		return True
	else:
		return False

def check_headers(file_obj, packet_size_bytes=8192, verbose=False, print_headers=False):
	#'''
	#check_headers(file_obj, packet_size_bytes=8192, verbose=False, print_headers=False)

	#Iterate through LoFASM Data file and check that all the header packets
	#are in place. 

	#Note: The verbose argument is no longer used. It is being left in the definition 
	#for now for compatibility purposes.
	#'''

    #assume the file_obj pointer is after the header!
    filesize_bytes = get_filesize(file_obj)
    number_of_packets = filesize_bytes / packet_size_bytes
    packet_counter = 0 #packet counter
    err_counter = 0
    data_begins = pdat_H.LOFASM_RAW_HDR_LENGTH
    first_header = True
    print_msg = 'Checking UDP headers in %s ...\n' % file_obj.name

    for i in range(number_of_packets):
        block = file_obj.read(packet_size_bytes)
        packet_counter += 1
        #data_begins = file_obj.tell()

        if is_header(block):
            if first_header:
                print_msg += "\n|packet|packets since hdr|loc|integration|hdr_cnt|sig|\n"
                first_header = False
            elif packet_counter < 17:
#                print 'early header packet!'
                print_msg += "WARNING: unexpected header packet arrived %i " % (17 - packet_counter)
                print_msg += "packets too early!\n" 
                err_counter += 1
                data_begins = file_obj.tell() - packet_size_bytes
#                print data_begins
            hdr_dict = parse_hdr(block[:8])

            print_msg += "|%i|%i|%i|" % \
				(i, packet_counter, file_obj.tell() - packet_size_bytes)

            #print "HDR:", 
            for key in hdr_dict:
                print_msg += str(hdr_dict[key]) + "|"
            print_msg += "\n"
            packet_counter = 0 #reset packet counter if header is found

    if print_headers:
        print print_msg

    return [data_begins, err_counter]

def get_filesize(file_obj):
	'''Usage: get_filesize(file_obj)
	returns file size (in bytes) of file pointed to by file_obj.'''

	freeze_pointer = file_obj.tell()
	file_obj.seek(0,2) #go to end of file
	end_pointer = file_obj.tell()
	file_obj.seek(freeze_pointer)

	return end_pointer

def get_number_of_integrations(file_obj):
	'''returns number of integrations in data file'''
	
	fileSize = get_filesize(file_obj) - parse_file_header(file_obj)[3][1]
	num_integrations = fileSize / lofasm_dat.INTEGRATION_SIZE_B
	return num_integrations


def get_next_raw_burst(file_obj, packet_size_bytes=8192, 
	packets_per_burst=17, loop_file=False):
	'''
	Usage: burst_generator = get_next_raw_burst(<file_object>\
		[, packet_size_bytes, packets_per_burst, loop_file]) 
	Python generator that yields a string containing data from the next 17
	 LoFASM packets in file_obj that make up a single \'burst\'. 
	
	If file_obj's pointer is not at zero, then assume it is in the desired
	start position and begin reading from that point in the file.
	'''
	#print "getting new data"
	file_start_position = file_obj.tell()
	burst_size = packet_size_bytes * packets_per_burst


	while 1:
		raw_dat = file_obj.read(burst_size)
		if (not raw_dat) or (len(raw_dat) < burst_size):
			if loop_file:
				print "Reached end of file. Starting over..."
				file_obj.seek(file_start_position)
				raw_dat = file_obj.read(burst_size)
				yield raw_dat
			else:
				print "No more data to read in %s" % file_obj.name
				print "Exiting..."
				exit()
		else:
			yield raw_dat

def find_first_hdr_packet(file_obj, packet_size_bytes=8192, hdr_size=8):
	'''
		Usage: find_first_hdr_packet(file_obj[, packet_size_bytes, hdr_size])
		returns file_obj but with file pointer at 
		start of first valid LoFASM Header.
	'''
	#total number of packets in file
	num_packets = get_filesize(file_obj)/packet_size_bytes

	for i in range(num_packets):
		#read packet header
		#current_location = file_obj.tell()
		#print "Checking Packet %i at %i" % (i, current_location)

		pkt_hdr = file_obj.read(hdr_size)
		

		#if header is valid then fix pointer and return file_obj
		#else continue to next packet
		if is_header(pkt_hdr, print_header=False): 
						
			if not is_next_packet_header(file_obj, 
				packet_size_bytes=packet_size_bytes,
				hdr_size_bytes=8):

				#fix pointer
				file_obj.seek(file_obj.tell() - hdr_size)
				#print "found valid header at %i!" % file_obj.tell()

				#return file_obj with fixed pointer at start of header
				return file_obj
			#else:
				#print 'next packet is header at %i' % (file_obj.tell() 
				#	+ packet_size_bytes - hdr_size)
	
		file_obj.seek(file_obj.tell() + packet_size_bytes - hdr_size)
	print "Finished searching: did not find valid header in %s" % file_obj.name

def is_next_packet_header(file_obj, packet_size_bytes=8192, hdr_size_bytes=8):
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

