# This is test file for file information.
from lofasm.data_file_info import data_file_info as dif
from lofasm.fs import filter_walk
import os
import unittest

lofasm_dir = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.realpath(__file__))))

rootDir = os.path.join(lofasm_dir, 'fs')

# for backwards compatibility
datafile = rootDir

# clean up test directory
for f in filter_walk('.info', rootDir):
    os.remove(f)


class TestFileInfo(unittest.TestCase):
    def setUp(self):
        self.fileinfo = dif.LofasmFileInfo(rootDir, check_subdir=True)
        self.fileinfo.write_info_table()

    def test_current_dir(self):
        infotable = self.fileinfo.info_table
        self.assertTrue(len(infotable) == 1)
        expected_keys = ['filename', 'fileformat', 'start_time',
                         'station',	'hdr_type',	'channel']
        for k in infotable.keys():
            try:
                self.assertTrue(k in expected_keys)
            except:
                print "{} not in {}".format(k, expected_keys)

        self.assertTrue(infotable[0]['filename'] == '20170202')
        self.assertTrue(infotable[0]['fileformat'] == 'data_dir')
        self.assertTrue(os.path.exists(os.path.join(rootDir, '.info')))

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
        ssubd = os.path.join(self.fileinfo.info_table['filename'][0],
                             'obs_session')
        ssubpath = os.path.join(self.fileinfo.directory_abs_path, ssubd)
        self.assertTrue(os.path.exists(os.path.join(ssubpath, '.info')))
        ssubdcls = dif.LofasmFileInfo(ssubpath)
        self.assertTrue(ssubdcls.info_table['channel'] == ['CC'])

    def test_move_file(self):
        old_path = os.path.join(rootDir, '20170202/20170202_065550_AA.bbx.gz')
        new_path = os.path.join(rootDir, '20170202_065550_AA.bbx.gz')
        os.rename(old_path, new_path)
        new_cls = dif.LofasmFileInfo(rootDir, check_subdir=True)
        self.assertTrue(len(new_cls.info_table) == 2)
        new_sub_cls = dif.LofasmFileInfo(os.path.join(rootDir, '20170202'),
                                         check_subdir=True)
        self.assertTrue(len(new_sub_cls.info_table) == 3)
        os.rename(new_path, old_path)


if __name__ == "__main__":
    unittest.main()
