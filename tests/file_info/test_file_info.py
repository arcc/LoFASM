# This is test file for file information.
from lofasm.data_file_info import data_file_info as dif
import os
import unittest

lofasm_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
datafile = os.path.join(lofasm_dir, 'fs')

if os.path.exists(os.path.join(datafile, '.info')):
    os.remove(os.path.join(datafile, '.info'))
if os.path.exists(os.path.join(datafile, '20170202/.info')):
    os.remove(os.path.join(datafile, '20170202/.info'))
if os.path.exists(os.path.join(datafile, '20170202/obs_session/.info')):
    os.remove(os.path.join(datafile, '20170202/obs_session/.info'))

class TestFileInfo(unittest.TestCase):
    def setUp(self):
        self.fileinfo = dif.LofasmFileInfo(datafile, check_subdir=True)
        self.fileinfo.write_info_table()

    def test_current_dir(self):
        self.assertTrue(len(self.fileinfo.info_table) == 1)
        expected_keys = ['filename','fileformat', 'start_time',
                         'station',	'hdr_type',	'channel']
        for k in self.fileinfo.info_table.keys():
            self.assertTrue(k in expected_keys)
        self.assertTrue(self.fileinfo.info_table[0]['filename'] == '20170202')
        self.assertTrue(self.fileinfo.info_table[0]['fileformat'] == 'data_dir')
        self.assertTrue(os.path.exists(os.path.join(datafile, '.info')))

    def test_sub_dir(self):
        subd = self.fileinfo.info_table['filename'][0]
        subpath = os.path.join(self.fileinfo.directory_abs_path, subd)
        self.assertTrue(os.path.exists(os.path.join(subpath, '.info')))
        subdcls = dif.LofasmFileInfo(subpath)
        self.assertTrue(len(subdcls.info_table) == 4)
        self.assertTrue(len(subdcls.files['bbx']) == 3)
        self.assertTrue(len(subdcls.files['data_dir']) == 1)
        self.assertTrue(subdcls.files['data_dir'] == ['obs_session'])
        hdr_type = subdcls.info_table['hdr_type']
        filter_hdr = [x for x in hdr_type if x == 'LoFASM-filterbank']
        self.assertTrue(len(filter_hdr) == 3)

    def test_sub_sub_dir(self):
        ssubd = os.path.join(self.fileinfo.info_table['filename'][0], 'obs_session')
        ssubpath = os.path.join(self.fileinfo.directory_abs_path, ssubd)
        self.assertTrue(os.path.exists(os.path.join(ssubpath, '.info')))
        ssubdcls = dif.LofasmFileInfo(ssubpath)
        self.assertTrue(ssubdcls.info_table['channel'] == ['CC'])

    def test_move_file(self):
        old_path = os.path.join(datafile, '20170202/20170202_065550_AA.bbx.gz')
        new_path = os.path.join(datafile, '20170202_065550_AA.bbx.gz')
        os.rename(old_path, new_path)
        new_cls = dif.LofasmFileInfo(datafile, check_subdir=True)
        self.assertTrue(len(new_cls.info_table) == 2)
        new_sub_cls = dif.LofasmFileInfo(os.path.join(datafile, '20170202'), check_subdir=True)
        self.assertTrue(len(new_sub_cls.info_table) == 3)
        os.rename(new_path, old_path)
