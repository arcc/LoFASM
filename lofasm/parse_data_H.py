#maps the spectra type keys to the spectra descriptions

import datetime

LOFASM_PACKET_SIZE = 139264 #17 * 8192bytes
HDR_ENTRY_LENGTH = 8
HDR_NOTES_LENGTH = 8

LOFASM_RAW_HDR_LENGTH = 12 * HDR_ENTRY_LENGTH 
LoFASM_FHDR_SIG = 'LoCo'




class LoFASM_Catalog_Record:
    __year = None
    __day = None
    __month = None
    __minute = None
    __second = None
    __hour = None
    __tsamp = None
    __fname = None
    __hdrLen = None
    __startPos = None
    __nErrors = None
    def __init__(self, record_string):
        record_items = record_string.rstrip('\n').split('|')

        self.__setYear(record_items[0][:4])
        self.__setMonth(record_items[0][4:6])
        self.__setDay(record_items[0][6:])
        self.__setHour(record_items[1])
        self.__setMinute(record_items[2])
        self.__setSecond(record_items[3])
        self.__setSampleTime(record_items[4])
        self.__setFileName(record_items[5])
        self.__setHeaderLength(record_items[6])
        self.__setDataStartPos(record_items[7])
        self.__setNumFileErrors(record_items[8])

    #setters
    def setYear(self, YY):
        self.__year = int(YY)
    def setDay(self, DD):
        self.__day = int(DD)
    def setMonth(self, MM):
        self.__month = int(MM)
    def setHour(self, HH):
        self.__hour = int(HH)
    def setMinute(self, mm):
        self.__minute = int(mm)
    def setSecond(self, ss):
        self.__second = int(ss)
    def setSampleTime(self, tsamp):
        self.__tsamp = float(tsamp)
    def setFileName(self, fname):
        self.__fname = str(fname)
    def setHeaderLength(self, hlen):
        self.__hdrLen = int(hlen)
    def setDataStartPos(self, start_pos):
        self.__startPos = int(start_pos)
    def setNumFileErrors(self, nErrs):
        self.__nErrors = int(nErrs)

        
    #getters
    def getYear(self):
        return self.__year
    def getMonth(self):
        return self.__month
    def getDay(self):
        return self.__day
    def getDateStr(self):
        sep = '/'
        return str(self.__year) + sep + str(self.__month) + sep + str(self.__day)
    def getTime(self):
        return (self.__hour, self.__minute, self.__second)
    def getDate(self):
        hour, minute, second = self.getTime()
        return datetime.datetime(self.getYear(), self.getMonth(), 
                self.getDay(), hour, minute, second)
    def getFileName(self):
        return self.__fname

    #other methods
    def calculateDeltaT(self, dateToCompare):
        '''returns datetime.timedelta object'''
        return dateToCompare - self.getDate()
    def print_info(self):
        obs_date = self.getDate().strftime('%Y/%m/%d %H:%M:%S')
        print "Observation Start Time: ", obs_date
        print "FileName: ", self.__fname
        print "Sample Time: ", self.__tsamp
        print "Header Length: ", self.__hdrLen, 'B'
        print "Data Start Position: ", self.__startPos
        print "Number of File Errors: ", self.__nErrors
    #privates
    __setYear = setYear
    __setDay = setDay
    __setMonth = setMonth
    __setHour = setHour
    __setMinute = setMinute
    __setSecond = setSecond
    __setSampleTime = setSampleTime
    __setFileName = setFileName
    __setHeaderLength = setHeaderLength
    __setDataStartPos = setDataStartPos
    __setNumFileErrors = setNumFileErrors

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
		11: ['num_int', None],
		12: ['spect_type', None],
		13: ['notes', None]}
	}



class Header_Error:
	def __init__(self, strerror='', msg=None):
		self.strerror = strerror
		self.msg = msg
