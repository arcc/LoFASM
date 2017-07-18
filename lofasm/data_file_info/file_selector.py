"""This is a module for selecting files from a info table. User
is able to define the file selection methods
"""
import abc
import numpy as np


class FileSelectorMeta(abc.ABCMeta):
    """
    This is a Meta class for file information collector methods registeration.
    In order ot get a method registered, a member called 'info_name' has to be
    in the InfoCollector subclass
    """
    def __init__(cls, name, bases, dct):
        regname = '_selector_list'
        if not hasattr(cls,regname):
            setattr(cls,regname,{})
        if 'selector_name' in dct:
            getattr(cls,regname)[cls.selector_name] = cls
        super(FileSelectorMeta, cls).__init__(name, bases, dct)

class FileSelector(object):
    __metaclass__ = FileSelectorMeta

    def __init__(self,):
        self.select_func = self.get_files

    def get_files(self, info_table, **kwargs):
        raise NotImplementedError

class KeySelector(FileSelector):
    """This is a class to select files by using column value match.
    """
    selector_name = 'key'
    def __init__(self):
        super(KeySelector, self).__init__()

    def get_files(self, info_table, column_name, condition):
        """
        Parameter
        ---------
        info_table: lofasm.data_file_info.LofasmFileInfo.info_table object
            The table for look up the files.
        column_name: str
            Table column name
        condition: str
            The condition for selecting the files.
        """
        col = info_table[column_name]
        selected_files = []
        if condition == '':
            raise ValueError("Condition can not be ''.")
        condition = col.dtype.type(condition)
        idx = np.where(col==condition)[0]
        files_in_dir = list(info_table['filename'][idx])
        return files_in_dir

class TimeSelector(FileSelector):
    """This is a file selector class design for the lofasm data time
    selection when time is a dimension in the data.
    """
    selector_name = 'time'
    def __init__(self):
        super(TimeSelector, self).__init__()

    def get_files(self, info_table, range):
        pass
