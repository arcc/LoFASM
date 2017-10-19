"""This is a module for collecting information for all the data files. User
is able to define the information collection methods
"""
import abc
from ..formats.format import DataFormat
import numpy as np


HEADER_PARSE_FIELDS = ['station', 'channel', 'hdr_type', 'start_time', \
                       'data_label', 'time_span']

class InfoCollectorMeta(abc.ABCMeta):
    """
    This is a Meta class for file information collector methods registeration.
    In order ot get a method registered, a member called 'info_name' has to be
    in the InfoCollector subclass
    """
    def __init__(cls, name, bases, dct):
        regname = '_info_name_list'
        if not hasattr(cls,regname):
            setattr(cls,regname,{})
        if 'info_name' in dct:
            getattr(cls,regname)[cls.info_name] = cls
        super(InfoCollectorMeta, cls).__init__(name, bases, dct)


class InfoCollector(object):
    """
    This is a base class for different file information collection method
    """
    __metaclass__ = InfoCollectorMeta

    def __init__(self,):
        self._formats = DataFormat._format_list
        self.collect_method = {}
        for fmt in self._formats.keys():
            self.collect_method[fmt] = None

    def get_info(self, fmt, **kwargs):
        return self.collect_method[fmt](**kwargs)


class HeaderInfoCollector(InfoCollector):
    def __init__(self):
        super(HeaderInfoCollector, self).__init__()
        self.collect_method['bbx'] = self.get_header_info_bbx
        self.collect_method['raw'] = self.get_header_info_raw
        self.collect_method['data_dir'] = self.get_header_info_data_dir

    def make_header_collect_method(self, fieldname, fmt):
        def header_method(fmt_cls):
            if hasattr(self, 'get_header_info_'+ fmt):
                return getattr(self, 'get_header_info_'+ fmt)(fmt_cls, fieldname)
            else:
                raise NotImplementedError
        header_method.__name__ = 'get_' + fieldname +'_'+ fmt
        header_method.__doc__ = 'This is a function to get heard information %s form %s file.\n' % (fieldname, fmt)
        header_method.__doc__ += 'Parameter\n---------\nfmt_cls : object\n file class for LoFasm %s format.\n' % (fmt)
        header_method.__doc__ += 'Return\n------\n Header information for field %s' % fieldname
        return header_method

    def get_header_info_bbx(self, bbx_cls, fieldname):
        """This function only give some basic header file as string.
        """
        if fieldname in list(bbx_cls.header.keys()):
            return bbx_cls.header[fieldname]
        else:
            return ''

    def get_header_info_raw(self,raw_cls, fieldname):
        raise NotImplementedError

    def get_header_info_data_dir(self, data_cls, fieldname):
        return ''

def _make_header_collect_class(fieldname):
    class header_info_collector(HeaderInfoCollector):
        info_name = fieldname
        def __init__(self):
            super(header_info_collector, self).__init__()
            self.column = fieldname
            for fmt in self.collect_method.keys():
                self.collect_method[fmt] = self.make_header_collect_method(fieldname, fmt)
    header_info_collector.__name__ = fieldname + 'Collector'
    header_info_collector.__doc__ =  "This is a class for collecting %s information from data file header" % fieldname
    return header_info_collector

# This can be an example.
class stationCollector(HeaderInfoCollector):
    """ This is a class for collecting station from data file header
    """
    info_name = 'station'
    def __init__(self):
        super(stationCollector, self).__init__()
        self.column = 'station'
        self.collect_method['bbx'] = self.make_header_collect_method('station', 'bbx')
        self.collect_method['raw'] = self.make_header_collect_method('station', 'raw')
        self.collect_method['data_dir'] =  lambda *args: ''

class timespanCollector(InfoCollector):
    """ This is a class for colleting timespan from data file header
    """
    info_name = 'time_span'

    def __init__(self):
        super(timespanCollector, self).__init__()
        self.column = 'time_span'
        self.collect_method['bbx'] = self.get_time_span_bbx
        self.collect_method['raw'] = lambda *args: np.nan
        self.collect_method['data_dir'] =  lambda *args: np.nan

    def get_time_span_bbx(self, bbx_cls):
        if bbx_cls.header['dim1_label'].startswith('time'):
            name = 'dim1_span'
        elif bbx_cls.header['dim2_label'].startswith('time'):
            name = 'dim2_span'
        else:
            return None
        return float(bbx_cls.header[name])

class secondJ2000Collector(InfoCollector):
    """ This is a class for colleting timespan from data file header
    """
    info_name = 'start_time_J2000'

    def __init__(self):
        super(secondJ2000Collector, self).__init__()
        self.column = 'start_time_J2000'
        self.collect_method['bbx'] = self.get_time_span_bbx
        self.collect_method['raw'] = lambda *args: np.nan
        self.collect_method['data_dir'] =  lambda *args: np.nan

    def get_time_span_bbx(self, bbx_cls):
        if bbx_cls.header['dim1_label'].startswith('time'):
            name = 'dim1_start'
        elif bbx_cls.header['dim2_label'].startswith('time'):
            name = 'dim2_start'
        else:
            return np.nan
        if 'time_offset_J2000' in bbx_cls.header.keys():
            offset = bbx_cls.header['time_offset_J2000'].split()[0]
        else:
            offset = 0.0
        return float(bbx_cls.header[name]) + float(offset)

class SamplingTimeCollector(InfoCollector):
    """ This is a class for colleting timeing time from data file header
    """
    info_name = 'sampling_time'

    def __init__(self):
        super(SamplingTimeCollector, self).__init__()
        self.column = 'sampling_time'
        self.collect_method['bbx'] = self.get_sampling_time_bbx
        self.collect_method['raw'] = lambda *args: np.nan
        self.collect_method['data_dir'] =  lambda *args: np.nan

    def get_sampling_time_bbx(self, bbx_cls):
        if bbx_cls.header['dim1_label'].startswith('time'):
            name = 'dim1'
        elif bbx_cls.header['dim2_label'].startswith('time'):
            name = 'dim2'
        else:
            return np.nan
        span = float(bbx_cls.header[name+'_span'].split()[0])
        size = float(bbx_cls.header['metadata'][name+'_len'])
        return span/size

class SamplingFreqCollector(InfoCollector):
    """ This is a class for colleting sampling frequency from data file header
    """
    info_name = 'sampling_freq'

    def __init__(self):
        super(SamplingFreqCollector, self).__init__()
        self.column = 'sampling_freq'
        self.collect_method['bbx'] = self.get_sampling_freq_bbx
        self.collect_method['raw'] = lambda *args: np.nan
        self.collect_method['data_dir'] =  lambda *args: np.nan

    def get_sampling_freq_bbx(self, bbx_cls):
        if bbx_cls.header['dim1_label'].startswith('frequency'):
            name = 'dim1'
        elif bbx_cls.header['dim2_label'].startswith('frequency'):
            name = 'dim2'
        else:
            return np.nan
        span = float(bbx_cls.header[name+'_span'].split()[0])
        size = float(bbx_cls.header['metadata'][name+'_len'])
        return span/size

# This is a script to create some more built-in collector classes like stationCollector.
BUILTIN_COLLECTORS = {}
for k in HEADER_PARSE_FIELDS:
    if k in InfoCollector._info_name_list.keys():
        continue
    BUILTIN_COLLECTORS[k] = _make_header_collect_class(k)
