"""
This is a module to register the lofasm file formats.

Each distinctive major data format is specified by its class derived
from DataFormat.

"""
from ..bbx import bbx
import abc


class DataFormatMeta(abc.ABCMeta):
    """
    This is a Meta class for data formats registeration. In order to get a
    format registered, a member called 'format_name' has to be in the
    DataFormat subclass
    """
    def __init__(cls, name, bases, dct):
        regname = '_format_list'  # format registry. dictionary
        if not hasattr(cls, regname):
            setattr(cls, regname, {})
        if 'format' in dct:
            getattr(cls, regname)[cls.format] = cls
        super(DataFormatMeta, cls).__init__(name, bases, dct)


class DataFormat(object):
    """
    This is a base class for different lofasm data file formats
    """
    __metaclass__ = DataFormatMeta

    def __init__(self, format_cls):
        self.format_name = None
        self.format_cls = format_cls
        self.file_clas_kws = {}
        self.get_instance = None

    def instantiate_format_cls(self, filename):
        raise NotImplementedError

    def is_format(self, filename):
        raise NotImplementedError

    def read_header(self):
        raise NotImplementedError

    def read_data(self):
        raise NotImplementedError

    def write_data(self):
        raise NotImplementedError

# =============================================================================
# Data format handler definitions
# Each new data format must have its own class definition which is derived
# from DataFormat.
# =============================================================================


class BBXFormat(DataFormat):
    '''BBX File Format handler.
    This class acts as a wrapper for the lower level
    data reading methods.
    '''
    format = 'bbx'

    def __init__(self,):
        super(BBXFormat, self).__init__(bbx.LofasmFile)
        self.format_name = format
        self.get_instance = self.instantiate_format_cls

    def instantiate_format_cls(self, filename):
        """
        This is a wrapper function to instantiate bbx class. The description
        of parameters are given in ../bbx/bbx.py LofasmFile class docstring.
        """
        kwargs = self.file_clas_kws
        if filename.endswith('.gz'):
            kwargs['gz'] = True
        else:
            kwargs['gz'] = False
        file_instance = self.format_cls(filename, **kwargs)
        return file_instance

    def is_format(self, filename):
        return bbx.is_lofasm_bbx(filename)


class DataDir(DataFormat):
    '''DataDir File Format handler.
    This class acts as a wrapper for the lower level
    data reading mothods.
    '''
    format = 'data_dir'

    def __init__(self,):
        super(DataDir, self).__init__(None)
        self.format_name = format
        self.get_instance = self.instantiate_format_cls

    def instantiate_format_cls(self, filename):
        """
        This is a wrapper function to instantiate the DataDir class.
        The description of parameters is given in ../bbx/bbx.py
        LofasmFile class docstring.
        """
        return None

    def is_format(self, filename):
        return None
