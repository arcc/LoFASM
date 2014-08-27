
#constants
HDR_ENTRY_LENGTH = 8
HDR_NOTES_LENGTH = 8
LoFASM_FHDR_SIG = 'LoCo'

T_fpga = 1e-08
Nchan = 2048
FFT_cycles = Nchan >> 1
PacketsPerSample = 17


LoFASM_SPECTRA_KEY_TO_DESC = {
	'AA': 'OEW_POW', 
	'BB': 'ONS_POW',
	'CC': 'IEW_POW',
	'DD': 'INS_POW',
	'AB': 'OEWxONS',
	'AC': 'OEWxIEW',
	'AD': 'OEWxINS',
	'BC': 'ONSxIEW',
	'BD': 'ONSxINS',
	'CD': 'IEWxINS',
	'BN': 'BEAM_NS',
	'BE': 'BEAM_EW'
	}

LoFASM_FHEADER_TEMPLATE = {
	1: {1: ['hdr_sig', None],
		2: ['hdr_ver', None],
		3: ['hdr_len', None],
		4: ['station', None],
		5: ['Nbins', None],
		6: ['fstart', None],
		7: ['fstep', None],
		8: ['mjd_day', None],
		9: ['mjd_msec', None],
		10: ['int_time', None],
		11: ['Dfmt_ver', None],
		12: ['notes', None]},
    2: {1: ['hdr_sig', None],
		2: ['hdr_ver', None],
		3: ['hdr_len', None],
		4: ['station', None],
		5: ['Nbins', None],
		6: ['fstart', None],
		7: ['fstep', None],
		8: ['mjd_day', None],
		9: ['mjd_msec', None],
		10: ['int_time', None],
		11: ['Dfmt_ver', None],
		12: ['notes', None]}
	}
LoFASM_SPECTRUM_HEADER_TEMPLATE = {
	1: {1: ['hdr_sig', None],
		2: ['hdr_ver', None],
		3: ['hdr_len', None],
		4: ['station', None],
		5: ['Nbins', None],
		6: ['fstart', None],
		7: ['fstep', None],
		8: ['mjd_day', None],
		9: ['mjd_msec', None],
		10: ['int_time', None],
		12: ['num_int', None],
		13: ['spect_type', None],
		14: ['notes', None]}
	}



class Header_Error:
	def __init__(self, strerror='', msg=None):
		self.strerror = strerror
		self.msg = msg
