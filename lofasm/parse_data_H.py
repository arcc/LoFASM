
#constants
HDR_ENTRY_LENGTH = 8
HDR_NOTES_LENGTH = 8
LoFASM_FHDR_SIG = 'LoCo'

T_fpga = 1e-08
Nchan = 2048
FFT_cycles = Nchan >> 1

#number of network packets in each integration
PacketsPerSample = 17

Baselines = ['AA', 'BB', 'CC', 'DD', 'AB', 'AC', 'AD', 'BC', 'BD', 'CD']

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
    1: {1: ['hdr_sig', None], # bug in integration field exists in first header version
        2: ['hdr_ver', None], # be sure to multiply 'int_time' by 2 to get accurate value
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
        12: ['notes', None]},
    3: {1: ['hdr_sig', None],
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
        12: ['ra', None],
        13: ['dec', None]},
    4: {1: ['hdr_sig', None],
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
        12: ['Nsamp', None]}, # number of spectral samples in the file
    5: {1: ['hdr_sig', None],
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
        12: ['Nsamp', None],
        13: ['TrunkA', None],
        14: ['TrunkB', None],
        15: ['TrunkC', None],
        16: ['TrunkD', None]}
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
        14: ['notes', None]},
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
        12: ['num_int', None],
        13: ['spect_type', None],
        14: ['notes', None]},
    3: {1: ['hdr_sig', None],
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
        14: ['notes', None]},
    4: {1: ['hdr_sig', None],
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
        14: ['notes', None]},
    5: {1: ['hdr_sig', None],
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
        12: ['Nsamp', None],
        13: ['TrunkA', None],
        14: ['TrunkB', None],
        15: ['TrunkC', None],

    }
}


class Header_Error:
    def __init__(self, strerror='', msg=None):
        self.strerror = strerror
        self.msg = msg

class IntegrationError:
    def __init__(self, strerror=None):
        self.strerror = strerror
    def __str__(self):
        return self.strerror
