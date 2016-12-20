"""This is a script/module for checking the information of a list of lofasm files
and outputing the information to a simple info file.
Copyright (c) 2016 Jing Luo.
"""
from .bbx.bbx import  LofasmFile, is_lofasm_file
import os
import astropy.table as table
from astropy.io import ascii
import astropy.units as u
import numpy as np
import argparse

class LofasmFileInfo(object):
    """This class provides a storage for a list of lofasm files information
    and set of methods to check the information.
    """
    def __init__(self, files=None, info_file=None):
        """The LofasmFileInfo class reads lofasm file header and put the necessary
        information in to a astropy table for future operations.
        Or it will read exsiting information file to an astropy table for future
        operations.
        To use this class at least one way's requirement has to be met.

        Parameter
        ----------
        files : list/str, optional
            Filename or a list of filenames.
        info_file : str, optinal
            Filename for the information file.
        """
        if files is None and info_file is None:
            raise ValueError("At least one file has to be provided. [lofasm "
                             "data file or information file]")
        self.info_table = None
        if info_file is not None:
            self.info_file = info_file
            self.info_table = table.Table.read(info_file, format='ascii.ecsv')

        if files is not None:
            if np.isscalar(files):
                self.filenames = [files,]
            else:
                self.filenames = files
            for f in self.filenames:
                # skip the non-lofasm files.
                if not is_lofasm_file(f):
                    self.filenames.remove(f)

            if self.filenames is not []:
                if self.info_table is None:
                    self.info_table = self.get_files_info(self.filenames)
                else: # If the info file is not Noe, only find the new files.
                    new_files = list(set(self.info_table['filename']) - set(self.filenames))
                    if new_files != []:
                        self.new_files_table = self.get_files_info(new_files)
                        self.info_table = table.vstack([self.info_table, self.new_files_table])

    def get_files_info(self, filenames):
        """This function checks if all the lofasm files info and put them in
        an astropy table.
        """
        info_rows = []
        for f in filenames:
            # skip the non-lofasm files.
            if not is_lofasm_file(f):
                continue
            lf = LofasmFile(f)
            start_time = (float(lf.header['time_offset_J2000'].split()[0]) + \
                         float(lf.header['dim1_start']))
            end_time = (float(lf.header['dim1_span'])) + start_time
            str_start_time = lf.header['start_time']
            lofasm_station = lf.header['station']
            start_freq = (float(lf.header['dim2_start']) + \
                         float(lf.header['frequency_offset_DC'].split()[0]))
            end_freq = (float(lf.header['dim2_span']))+ start_freq
            is_cplx = lf.iscplx
            num_time_bin = lf.timebins
            num_freq_bin = lf.freqbins
            row = (f, lofasm_station, lf.header['channel'], \
                   str_start_time, start_time, end_time, start_freq, end_freq,\
                   is_cplx, num_time_bin, num_freq_bin)
            info_rows.append(row)
            lf.close()

        keys = ('filename', 'lofasm_station', 'channel', 'start_time_iso',\
                'start_time_pass_J2000', 'end_time_pass_J2000','start_freq',\
                'end_freq', 'is_complex', 'number_of_time_bin', 'number_of_freq_bin')
        data_type = ()
        for d in info_rows[0]:
            data_type += (np.dtype(type(d)),)
        t = table.Table(rows=info_rows, names=keys, meta={'name': 'lofasm file info'},\
                        dtype=tuple(data_type))
        t['start_time_pass_J2000'].unit = u.second
        t['end_time_pass_J2000'].unit = u.second
        t['start_freq'].unit = u.Hz
        t['end_freq'].unit = u.Hz
        return t

    def info_write(self, outfile):
        self.info_table.write(outfile, format='ascii.ecsv')
