# lofasm data lib
import struct, sys, time
import numpy as np
import corr
HDR_V1_SIGNATURE = 14613675
INTEGRATION_SIZE_B = 139264 #bytes

#functions
def getRoachAccLen():
    try:
        fpga = corr.katcp_wrapper.FpgaClient('192.168.4.21')
    except:
        print "could not get accumulation length from ROACH! Exiting..."
        sys.exit()
    time.sleep(1)

    accLen = fpga.read_uint('acc_len')
    del fpga
    return accLen

#class definitions
class LoFASM_burst:
	autos = {}
	cross = {}
	hdr = {}


	__fmt_autos = '>L'
	__fmt_cross = '>l'
	__fmt_beams = '>f'

	__type_autos = int
	__type_cross = complex
	__type_beams = np.float64

	def __init__(self, burst_string, packet_size=8192):
		

		#read header packet
		hdr_packet = burst_string[:packet_size]

		#split data portion into even and odd bins
		burst_real_even_bin = burst_string[packet_size : packet_size*3]
		burst_complex_even_bin = burst_string[packet_size*3 : packet_size*9]
		burst_real_odd_bin = burst_string[packet_size*9 : packet_size*11]
		burst_complex_odd_bin = burst_string[packet_size*11 :]

		#unpack all values
		burst_real_even_val = list(struct.unpack("4096".join(self.__fmt_autos), 
			burst_real_even_bin))
		burst_real_odd_val = list(struct.unpack("4096".join(self.__fmt_autos), burst_real_odd_bin))

		burst_complex_even_val = struct.unpack("12288".join(self.__fmt_cross), 
			burst_complex_even_bin)
		burst_complex_odd_val = struct.unpack("12288".join(self.__fmt_cross), 
			burst_complex_odd_bin)

		AABB_even = burst_real_even_val[:2048]
		CCDD_even = burst_real_even_val[2048:]
		AABB_odd = burst_real_odd_val[:2048]
		CCDD_odd = burst_real_odd_val[2048:]


		AB_even = self.__cross_make_complex(burst_complex_even_val[:2048])
		AC_even = self.__cross_make_complex(burst_complex_even_val[2048:2048*2])
		AD_even = self.__cross_make_complex(burst_complex_even_val[2048*2:2048*3])
		BC_even = self.__cross_make_complex(burst_complex_even_val[2048*3:2048*4])
		BD_even = self.__cross_make_complex(burst_complex_even_val[2048*4:2048*5])
		CD_even = self.__cross_make_complex(burst_complex_even_val[2048*5:])

		AB_odd = self.__cross_make_complex(burst_complex_odd_val[:2048])
		AC_odd = self.__cross_make_complex(burst_complex_odd_val[2048:2048*2])
		AD_odd = self.__cross_make_complex(burst_complex_odd_val[2048*2:2048*3])
		BC_odd = self.__cross_make_complex(burst_complex_odd_val[2048*3:2048*4])
		BD_odd = self.__cross_make_complex(burst_complex_odd_val[2048*4:2048*5])
		CD_odd = self.__cross_make_complex(burst_complex_odd_val[2048*5:])

		AA_even, BB_even = self.__split_autos(AABB_even)
		AA_odd, BB_odd = self.__split_autos(AABB_odd)
		CC_even, DD_even = self.__split_autos(CCDD_even)
		CC_odd, DD_odd = self.__split_autos(CCDD_odd)

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



	def __cross_make_complex(self, cross_list):
		cross_complex = []
		for i in range(len(cross_list)/2):
			cross_complex.append(complex(cross_list[i*2], 
				cross_list[i*2 + 1]))
		return cross_complex

	def __interleave_even_odd(self, even_list, odd_list):
		if len(even_list) != len(odd_list):
			print "Cannot interleave! Even and odd lists \
					must be of equal length!"

		else:
			interleave_list = []
			for i in range(len(even_list)):
				interleave_list.append(even_list[i])
				interleave_list.append(odd_list[i])

			return interleave_list
	def __split_autos(self, XXYY_list):
		'''Split XXYY_even (or XXYY_odd) into two lists 
		corresponding to XX and YY. Output is a tuple with 
		two elements, each a list: (AA_even, BB_even) or 
		(AA_odd, AA_even)
		'''
		XX_list = []
		YY_list = []

		for i in range(len(XXYY_list)/2):
			XX_list.append(XXYY_list[2*i])
			YY_list.append(XXYY_list[2*i + 1])
		return (XX_list, YY_list)

	def pack_binary(self, spect):
		'''Convert a list of powers to a writable binary string'''
		#check whether spect contains int or complex values
		bin_str = ''

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
	
	def __gen_LoFASM_beams(self, Ai=1.0, Aq=1.0):
		self.beams = {}
		AA_pow = np.array(self.autos['AA'])
		BB_pow = np.array(self.autos['BB'])
		CC_pow = np.array(self.autos['CC'])
		DD_pow = np.array(self.autos['DD'])
		BD_cross = np.array(self.cross['BD'])
		AC_cross = np.array(self.cross['AC'])
		self.beams['BN'] = BB_pow + DD_pow + (2 / (Ai * Aq)) * np.real(BD_cross)
		self.beams['BE'] = AA_pow + CC_pow + (2 / (Ai * Aq)) * np.real(AC_cross)
	
	def create_LoFASM_beams(self):
		self.__gen_LoFASM_beams()
		

def gen_LoFASM_beam(auto_Vi, auto_Vq, crossViVq, Ai=1, Aq=1):
	auto_Vi = np.array(auto_Vi)
	auto_Vq = np.array(auto_Vq)
	crossViVq = np.array(crossViVq)
	beam_power = auto_Vi + auto_Vq + (2/float(Ai*Aq))*np.real(crossViVq)
	return beam_power


