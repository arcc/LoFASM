"""This is a module for collecting information for all the data files. User
is able to define the information collection methods
"""
import abc
from ..formats.format import DataFormat

HEADER_PARSE_FIELDS = ['station', 'channel', 'hdr_type', 'start_time', \
                       'data_label']

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
        self.collect_method['data_dir'] = self.get_header_info_dir

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
        return bbx_cls.header[fieldname]

    def get_header_info_raw(self,):
        raise NotImplementedError

    def get_header_info_dir(self,):
        return None

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
        self.collect_method['data_dir'] =  lambda *args: None

# This is a script to create some more built-in collector classes like stationCollector.
BUILTIN_COLLECTORS = {}
for k in HEADER_PARSE_FIELDS:
    if k in InfoCollector._info_name_list.keys():
        continue
    BUILTIN_COLLECTORS[k] = _make_header_collect_class(k)
