#methods to facilitate creating LoFASM data 
#structures for simulating purposes

import numpy as np
import struct

#method definitions

#class definitions
class NetworkPacket(object):
	'''
	LoFASM Network Packet
	'''

	def __init__(self):
		#length of network packet in bytes
		self.packet_length = 8192

		#format codes for struct.pack
		self._fmt_real = '>L'
		self._fmt_complex = '>l'
		self._fmt_beams = '>f'
		self._fmt_hdr = '>L'

		#number of rows in each data packet
		self._rows = 1024

class DataPacket(NetworkPacket):
	'''
	LoFASM Network Data Packet
	'''

	
	def __init__(self, complex=False):

		#run super's init
		super(DataPacket, self).__init__()

		#number of columns per row
		self._cols = 2

		#data placeholder
		if complex:
			self.data = np.array([np.complex(x) for x in np.zeros(2048)])
		else:
			self.data = np.zeros((self._rows, self._cols))

class RealPacket(DataPacket):
	'''
	LoFASM Real Data Packet

	RealPacket instances are designed to hold real values 
	only.
	'''

	def __init__(self, data=np.array([])):
		'''
		Usage: rp = RealPacket(data)

		Inputs: data as a 2D numpy array or a tuple of two 
		1D numpy arrays.

		In either case, the data elements must be real values.

		If data is a 2D numpy array the shape of data must be (1024,2).
		If data is a tuple containing two 1D numpy arrays then 
		their shape must be (1024,).

		All values are converted to binary as 4-byte integers.
		'''

		#run inherited init function
		super(RealPacket, self).__init__()

		if type(data) is tuple:
			assert((np.shape(data[0] == (1024,))) and \
				(np.shape(data[1] == (1024,))))

			aa, bb = data

			for i in range(len(self.data)):
				self.data[i][0] = aa[i]
				self.data[i][1] = bb[i]
		else:
		    if data.any():
		    	assert(np.shape(data) == (1024,2))
		    	self.data = data

	def getBinStr(self):
		'''
		Return real data packet as a writable binary string.
		'''

		bin_str = ''
		for j in range(len(self.data)):
			for k in range(len(self.data[0])):
				try:
					bin_str += struct.pack(self._fmt_real, self.data[j][k])
				except struct.error as err:
					print err
					print 'fmt: ', self._fmt_real
					print 'val: ', self.data[j][k]

		return bin_str

class ComplexPacket(DataPacket):
	'''
	LoFASM Complex Data Packet

	ComplexPacket instances are designed to hold complex values 
	only.

	'''
	def __init__(self, data=np.array([])):
		'''
		Usage: cp = ComplexPacket(data)

		Where data is a 1D array containing 2048 complex values. 
		Each element must have data type complex. 
		The (real an imaginary) values are converted to 4-byte signed integers.
		'''

		#run inherited init function
		super(ComplexPacket, self).__init__(complex=True)

		if data.any():
			assert(np.shape(data) == (1024,))
			self.data = data

	def getBinStr(self):
		'''
		Return complex data packet as a writeable binary string.
		'''

		bin_str = ''

		for j in range(1024):
			bin_str += struct.pack(self._fmt_complex, np.real(self.data[j]))
			bin_str += struct.pack(self._fmt_complex, np.imag(self.data[j]))

		return bin_str

class HeaderPacket(NetworkPacket):
	'''
	LoFASM Header Packet
	'''
	def __init__(self, acc_num=None, hdr_cnt=0xabcd, sig=0xdefcab):
		#run inherited init function
		super(HeaderPacket, self).__init__()

		self._hdr_cnt = hdr_cnt
		self._sig = sig
		self._pad_1B = "\x00"

		if not acc_num:
			#initialize to 1 if no argument is given
			self.acc_num = 1
		else:
			self.acc_num = acc_num

	def increment(self, step=1, carry=True):
		'''
		Increment acc_num by step

		If maximum is reached, then return to 1.

		The highest value for acc_num is 2**24-1 (16777215).

		If step is an integer less than 0 then the absolute value
		will be used.

		If step is type float then it will truncated to an integer.
		'''

		max_acc = 16777215

		if step < 0:
			step = abs(step)

		if type(step) is float:
			step = int(step)

		new_acc = self.acc_num + step

		if new_acc > max_acc:
			if carry:
				new_acc = max_acc - new_acc
			else:
				new_acc = 1

		self.acc_num = new_acc

	def getBinStr(self):
		'''
		Return entire header packet as a writeable 
		binary string.

		All header values are packed in big endian format, '>L'.
		'''

		sig = struct.pack(self._fmt_hdr, self._sig)[-3:] #remove leading byte
		acc_num = struct.pack(self._fmt_hdr, self.acc_num)[-3:]
		hdr_cnt = struct.pack(self._fmt_hdr, self._hdr_cnt)[-2:]

		row = sig + acc_num + hdr_cnt

		return row * self._rows

class Burst(object):
	'''
	LoFASM Burst

	A collection of 17 LoFASM Network packets.

	The first packet is always a HeaderPacket.
	The following 16 packets contain LoFASM filterbank
	data.

	The Burst format is as follows. 

	===========================================
	| Packet No. |   Frame   |  FFT Channels  |
	===========================================
	|      0     |   Header  |      N/A       |
	|      1     | A*A & B*B |      Even      |
	|      2     | C*C & D*D |      Even      |
	|      3     |    A*B    |      Even      |
	|      4     |    A*C    |      Even      |
	|      5     |    A*D    |      Even      |
	|      6     |    B*C    |      Even      |
	|      7     |    B*D    |      Even      |
	|      8     |    C*D    |      Even      |
	|      9     | A*A & B*B |      Odd       |
	|     10     | C*C & D*D |      Odd       |
	|     11     |    A*B    |      Odd       |
	|     12     |    A*C    |      Odd       |
	|     13     |    A*D    |      Odd       |
	|     14     |    B*C    |      Odd       |
	|     15     |    B*D    |      Odd       |
	|     16     |    C*D    |      Odd       |
	===========================================

	Each burst contains all of the filterbank for a single LoFASM integration.
	'''

	def __init__(self):
		'''
		Initialize a simulated LoFASM Burst

		Usage: burst = Burst()
		'''

		#index ranges for real and complex data packets
		self.__real_packets = [1, 2, 9, 10]
		self.__complex_packets = [3, 4, 5, 6, 7, 8, 11, 12, 13, 14, 15, 16]

		#initialize empty LoFASM Burst
		self.packets = [None] * 17

		self.packets[0] =HeaderPacket()

		for i in range(16):
			i += 1

			if i in self.__real_packets:
				self.packets[i] = RealPacket()
			elif i in self.__complex_packets:
				self.packets[i] = ComplexPacket()

	def getBinStr(self):
		'''
		Return LoFASM Burst as a writeable binary string.
		'''

		bin_str = ''

		for packet in self.packets:
			bin_str += packet.getBinStr()
			#print struct.unpack('>10L',packet.getBinStr()[:10*4])

		return bin_str

	def insert(self, packet, index, header=False):
		'''
		insert data packet into burst

		Usage: Burst.insert(packet, index, [header])

		packet must be of the type that is expected for placement at index.

		If header is true, then index is ignored. 
		Header packets are placed at index 0, always.

		Only instances of HeaderPacket can be inserted as header packets.

		index must be an integer. If a float is used, then it will be truncated.

		If a value less than 0 is given then the absolute value will be used instead.
		'''

		#force positive
		if index < 0:
			index = abs(index)

		#force int
		if type(index) != int:
			index = int(index)

		if header:
			assert(isinstance(packet, HeaderPacket))
			self.packets[0] = packet

		elif index in self.__real_packets:
			assert(isinstance(packet, RealPacket))
			self.packets[index] = packet

		elif index in self.__complex_packets:
			assert(isinstance(packet, ComplexPacket))
			self.packets[index] = packet

		else:
			print "Error: %i is not a valid index" % index






