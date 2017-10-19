"""
This is a module to register the lofasm file fomats.
"""
from ..bbx import bbx
import abc

class DataFormatMeta(abc.ABCMeta):
    """
    This is a Meta class for data formats registeration. In order ot get a format
    registered, a member called 'format_name' has to be in the DataFormat subclass
    """
    def __init__(cls, name, bases, dct):
        regname = '_format_list'
        if not hasattr(cls,regname):
            setattr(cls,regname,{})
        if 'format' in dct:
            getattr(cls,regname)[cls.format] = cls
        super(DataFormatMeta, cls).__init__(name, bases, dct)

class DataFormat(object):
    """
    This is a base class for different lofams data file formats
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


class BBXFormat(DataFormat):
    format = 'bbx'
    def __init__(self,):
        super(BBXFormat, self).__init__(bbx.LofasmFile)
        self.format_name = 'bbx'
        self.get_instance = self.instantiate_format_cls

    def instantiate_format_cls(self, filename):
        """
        This is a wrapper function for instantiate bbx class. The description of
        parameters are given in ../bbx/bbx.py LofasmFile class docstring.
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
    format = 'data_dir'
    def __init__(self,):
        super(DataDir, self).__init__(None)
        self.format_name = 'data_dir'
        self.get_instance = self.instantiate_format_cls

    def instantiate_format_cls(self, filename):
        """
        This is a wrapper function for instantiate bbx class. The description of
        parameters are given in ../bbx/bbx.py LofasmFile class docstring.
        """
        return None

    def is_format(self, filename):
        pass
