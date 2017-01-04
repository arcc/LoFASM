"""This is a script/module for checking and parsing file information to an astropy table.
Copyright (c) 2016 Jing Luo.
"""
import os
import astropy.table as table
from astropy import log
from astropy.io import ascii
import astropy.units as u
import numpy as np
from ..formats.format import DataFormat

class LofasmFileInfo(object):
    """This class provides a storage for a list of lofasm files information
    and set of methods to check the information.
    """
    def __init__(self, directory='.'):
        """
        This is a class for reading a directory's the lofasm related file or
        directories and parsing the information to an astropy table. It provides
        the writing the information to a text file as well.
        Notes
        -----
        This class only applies to one directory.

        Parameter
        ----------
        dir : str, optinal
            Filename for the directory.
        """
        # Get all the files for the directory.
        all_files = os.listdir(directory)
        self.directory = directory
        self.directory_abs_path = os.path.abspath(self.directory)
        self.directory_basename = os.path.basename(self.directory_abs_path.rstrip(os.sep))
        # different file category
        self.formats = {}
        # instantiate format classes
        for k, kv in zip(DataFormat._format_list.keys(), DataFormat._format_list.values()):
            self.formats[k] = kv()
        # set up the file category list depends on the formats
        self.files = self.check_file_types(all_files, self.directory)
        num_info_files = len(self.files['info'])
        if num_info_files < 1:
            self.info_file_name = self.directory_basename + '.info'
        else:
            if num_info_files > 1:
                log.warn("More then one .info file detected, " \
                         "use '%s' as information file." % self.files['info'][0])
            self.info_file_name = self.files['info'][0]
        self.table_update = False
        self.setup_info_table()

    def check_file_types(self, files, directory='.'):
        """
        This is a class method for checking file types. It only log the lofasm
        related files.
        """
        # Check file type
        file_type = {}
        file_type['data_dir'] = []
        file_type['info'] = []
        for fn in files:
            f = os.path.join(directory, fn)
            if fn.endswith('.info'):
                file_type['info'].append(fn)
            if os.path.isdir(f):
                file_type['data_dir'].append(fn)
            else:
                for k, kc in zip(self.formats.keys(), self.formats.values()):
                    if k not in file_type.keys():
                        file_type[k] = []
                    if kc.is_format(f):
                        file_type[k].append(fn)
                        break
        return file_type

    def get_type_map(self):
        data_files = []
        file_types = []
        for tp, flist in zip(self.files.keys(), self.files.values()):
            if not tp == 'info':
                tpl = [tp] * len(flist)
                data_files += flist
                file_types += tpl
        type_map = dict(zip(data_files, file_types))
        return type_map

    def setup_info_table(self):
        # Check directories
        for d in self.files['data_dir']:
            fs = os.listdir(os.path.join(self.directory, d))
            if any(ff.endswith('.info') for ff in fs):
                continue
            else:
                self.files['data_dir'].remove(d)

        type_map = self.get_type_map()
        # Check out info_file
        info_file = os.path.join(self.directory, self.info_file_name)
        if os.path.isfile(info_file):
            self.info_table = table.Table.read(info_file, format='ascii.ecsv')
            new_files = list(set(type_map.keys()) - set(self.info_table['filename']))
            if new_files != []:
                new_file_tp = [type_map[f] for f in new_files]
                new_f_table = table.Table([new_files, new_file_tp], \
                                           names=('filename', 'filetype'))
                self.info_table = table.vstack([self.info_table, new_f_table])
                if 'data_dir' in new_file_tp:
                    self.info_table.meta['haschild'] = True
                self.table_update = True
        else:
            if len(self.files['data_dir']) > 0:
                haschild = True
            else:
                haschild = False
            self.info_table = table.Table([type_map.keys(), type_map.values()], \
                                          names=('filename', 'filetype'),\
                                          meta={'name':self.directory_basename + '_info_table',
                                                'haschild': haschild})
            self.table_update = True

    def add_columns(self):
        """This method needs a FileInfoCollector class
        """
        pass

    def write_info_table(self):
        outpath = os.path.join(self.directory_abs_path, self.info_file_name)
        if self.table_update:
            self.info_table.write(outpath, format='ascii.ecsv', overwrite=True)


    #     self.info_table = None
    #     if info_file is not None:
    #         self.info_file = info_file
    #         self.info_table = table.Table.read(info_file, format='ascii.ecsv')
    #
    #     if files is not None:
    #         if np.isscalar(files):
    #             self.filenames = [files,]
    #         else:
    #             self.filenames = files
    #         for f in self.filenames:
    #             # skip the non-lofasm files.
    #             if not is_lofasm_file(f):
    #                 self.filenames.remove(f)
    #
    #         if self.filenames is not []:
    #             if self.info_table is None:
    #                 self.info_table = self.get_files_info(self.filenames)
    #             else: # If the info file is not Noe, only find the new files.
    #                 new_files = list(set(self.info_table['filename']) - set(self.filenames))
    #                 if new_files != []:
    #                     self.new_files_table = self.get_files_info(new_files)
    #                     self.info_table = table.vstack([self.info_table, self.new_files_table])
    #     # TODO: In the future, more then filter bank data file can be processed
    #     self.match_keys = ['filename', 'lofasm_station', 'channel','is_complex']
    #     self.range_keys = ['time', 'freq']
    #     self.key_map = {'time' : '_time_pass_J2000',
    #                     'freq' : '_freq'}
    # def get_files_info(self, filenames):
    #     """This function checks if all the lofasm files info and put them in
    #     an astropy table.
    #     """
    #     info_rows = []
    #     for f in filenames:
    #         # skip the non-lofasm files.
    #         if not is_lofasm_file(f):
    #             continue
    #         lf = LofasmFile(f)
    #         start_time = (float(lf.header['time_offset_J2000'].split()[0]) + \
    #                      float(lf.header['dim1_start']))
    #         end_time = (float(lf.header['dim1_span'])) + start_time
    #         str_start_time = lf.header['start_time']
    #         lofasm_station = lf.header['station']
    #         start_freq = (float(lf.header['dim2_start']) + \
    #                      float(lf.header['frequency_offset_DC'].split()[0]))
    #         end_freq = (float(lf.header['dim2_span']))+ start_freq
    #         is_cplx = lf.iscplx
    #         num_time_bin = lf.timebins
    #         num_freq_bin = lf.freqbins
    #         row = (f, lofasm_station, lf.header['channel'], \
    #                str_start_time, start_time, end_time, start_freq, end_freq,\
    #                is_cplx, num_time_bin, num_freq_bin)
    #         info_rows.append(row)
    #         lf.close()
    #
    #     keys = ('filename', 'lofasm_station', 'channel', 'start_time_iso',\
    #             'start_time_pass_J2000', 'end_time_pass_J2000','start_freq',\
    #             'end_freq', 'is_complex', 'number_of_time_bin', 'number_of_freq_bin')
    #     data_type = ()
    #     for d in info_rows[0]:
    #         data_type += (np.dtype(type(d)),)
    #     t = table.Table(rows=info_rows, names=keys, meta={'name': 'lofasm file info'},\
    #                     dtype=tuple(data_type))
    #     t['start_time_pass_J2000'].unit = u.second
    #     t['end_time_pass_J2000'].unit = u.second
    #     t['start_freq'].unit = u.Hz
    #     t['end_freq'].unit = u.Hz
    #
    #     return t
    #
    # def info_write(self, outfile):
    #     self.info_table.write(outfile, format='ascii.ecsv')
    #
    # def get_files_by_key_name(self, key, condition):
    #     """
    #     This function returns the reqired file names by the giving key and
    #     condition
    #     Parameter
    #     ---------
    #     key : str
    #         The key for requesting a lofasm file.
    #     condition : str
    #         The key value for requesting.
    #
    #     Return
    #     ------
    #     A list of file names that are requied.
    #
    #     Raise
    #     -----
    #     KeyError
    #     """
    #     if key not in self.match_keys:
    #         raise KeyError("Key '" + key + "' is not in match searchable.")
    #     if key == 'is_complex':
    #         if isinstance(condition, bool):
    #             pass
    #         elif isinstance(condition, str) and condition.lower() in ['y', 'yes','true']:
    #             condition = True
    #         else: # If condition is not in ['y', 'yes','true', True], it is a no.
    #             condition = False
    #
    #     grp = self.info_table.group_by(key)
    #     mask = grp.groups.keys[key] == condition
    #     select_file = grp.groups[mask]['filename']
    #     return list(select_file)
    #
    # def get_files_by_range(self, key, lower_limit, higher_limit):
    #     """
    #     This is a method to get the required file by the range of key value. It
    #     will return a list of files. Right now it only has time and frequency
    #     built in. time is searching as seconds pass J2000, and frequency is at Hz
    #     Parameter
    #     ---------
    #     key : str
    #         The key for requesting a lofasm file.
    #     lower_limit : float
    #         The lower limit for the range selection
    #     higher_limit : float
    #         The higher limit fo the range selection.
    #
    #     Return
    #     ------
    #     A list of file names that are requied.
    #
    #     Raise
    #     -----
    #     KeyError
    #     """
    #     if key not in self.range_keys:
    #         raise KeyError("Key '" + key + "' is not in range searchable.")
    #
    #     start_col_key = 'start' + self.key_map[key]
    #     end_col_key = 'end' + self.key_map[key]
    #     select_file = []
    #     for i in range(len(self.info_table)):
    #         file_range = np.array([self.info_table[start_col_key][i], \
    #                                self.info_table[end_col_key][i]])
    #         select_range = np.array([lower_limit, higher_limit])
    #         if (lower_limit >= file_range[0] and lower_limit <= file_range[1]) or \
    #            (higher_limit >= file_range[0] and higher_limit <= file_range[1]):
    #             select_file.append(self.info_table['filename'][i])
    #         elif lower_limit <= file_range[0] and higher_limit >= file_range[1]:
    #             select_file.append(self.info_table['filename'][i])
    #         else:
    #             continue
    #     return select_file
