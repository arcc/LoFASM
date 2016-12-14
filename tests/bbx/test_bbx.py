# run tests for bbx module


import unittest
import os
from lofasm.bbx.bbx import LofasmFile
import json
import numpy as np

dataDir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'testdata')
logFile = os.path.join(dataDir, 'testlog')

# cases to test for
# * write gzipped bbx with real data
# * write un-gzipped bbx with real data
# * write gzipped bbx with complex data
# * write un-gzipped bbx with complex data

class TestLofasmFileReading(unittest.TestCase):
    def setUp(self):
        self.test_files = [os.path.join(dataDir, x) for x in ['20161117_015320_AA.bbx',
                                                         '20161117_015320_AA.bbx.gz',
                                                         '20161117_015320_AB.bbx',
                                                         '20161117_015320_AB.bbx.gz']]

        self.log = open(logFile, 'a')

    def tearDown(self):
        self.log.close()

    # TESTS

    def test_read_header(self):
        for f in self.test_files:
            tag = os.path.basename(f).split('.bbx')[0]
            fhdr = open(os.path.join(dataDir, tag + '.hdr'), 'rb')
            hdr = json.load(fhdr)
            lf = LofasmFile(f)
            self.assertEqual(hdr, lf.header)

    def test_read_data(self):
        for f in self.test_files:
            self.log.write("################\n")
            self.log.write("# READTEST: Processing {} #\n".format(
                os.path.basename(f)))
            self.log.write("################\n")

            tag = os.path.basename(f).split('.bbx')[0]
            datfile = os.path.join(dataDir, tag+'.dat')

            self.log.write("datfile: {}\n".format(datfile))

            dat = np.fromfile(datfile)
            self.log.write("file data shape: {}\n".format(str(np.shape(dat))))
            self.log.write("first 5 elements from file: {}\n".format(str(dat[:5])))
            lf = LofasmFile(f)
            lf.read_data()

            isMatch = bool(hash(dat.tobytes('F')) == hash(lf.data.tobytes('F')))
            self.log.write("equal:{}\n".format(isMatch))
            self.log.write("cplx:{}\n".format(lf.iscplx))

            self.assertTrue(isMatch)

    def test_write_data(self):
        self.log.write("\nWRITE TEST\n")

        with open(os.path.join(dataDir, 'writeTestCplx.hdr'), 'rb') as f:
            cplx_hdr = json.load(f)
        with open(os.path.join(dataDir, 'writeTestReal.hdr'), 'rb') as f:
            real_hdr = json.load(f)
        cplx_data = np.fromfile(os.path.join(dataDir, 'writeTestCplx.npdat'))
        real_data = np.fromfile(os.path.join(dataDir, 'writeTestReal.npdat'))

        N = int(len(cplx_data)/2)
        cplx_data_new = np.zeros(N, dtype=np.complex128)
        i = 0
        for k in range(N):
            cplx_data_new[k] = np.complex(cplx_data[i], cplx_data[i+1])
            i += 2
        cplx_data = cplx_data_new

        self.log.write("cplx_data from file: {} :{}\n".format(str(np.shape(cplx_data)), str(cplx_data[:5])))
        self.log.write("real_data from file: {} :{}\n".format(str(np.shape(real_data)), str(real_data[:5])))

        cplx_data = np.reshape(cplx_data, (int(cplx_hdr['metadata']['dim2_len']),
                                           int(cplx_hdr['metadata']['dim1_len'])), 'F').astype(np.complex128)

        real_data = np.reshape(real_data, (int(real_hdr['metadata']['dim2_len']),
                                           int(real_hdr['metadata']['dim1_len'])), 'F').astype(np.float64)

        self.log.write("real_data shape: {}\n".format(str(np.shape(real_data))))
        self.log.write("\t first 5 elements: {}\n".format(str(real_data[:5,0])))
        self.log.write("cplx data shape: {}\n".format(str(np.shape(cplx_data))))
        self.log.write("\t first 5 elements: {}\n".format(str(cplx_data[:5,0])))

        # fmt: [hdr, data, complex, gzip]
        test_opts = {
            'cplx': [cplx_hdr, cplx_data, True, False],
            'cplx_gzip': [cplx_hdr, cplx_data, True, True],
            'real': [real_hdr, real_data, False, False],
            'real_gzip': [real_hdr, real_data, False, True]
        }

        test_file = 'test.bbx'

        for k in test_opts.keys():
            self.log.write("\nWRITETEST:{}\n".format(k.upper()))
            # create data file
            self.log.write("Creating {}\n".format(test_file))
            lf = LofasmFile(test_file, mode='write', gz=test_opts[k][3])
            lf.header = test_opts[k][0]
            lf.add_data(test_opts[k][1])


            self.log.write("Added data, first 10 elements: \n\t{}\n".format(str(lf.data[:10])))

            lf.write()
            lf.close()

            # read data file
            self.log.write("\nReading {}\n".format(test_file))
            lf = LofasmFile(test_file, gz=test_opts[k][3])
            lf.read_data()


            self.log.write("\tlf.data shape: {}\n".format(str(np.shape(lf.data))))
            self.log.write("\tfirst 10 elements: {}\n".format(str(lf.data[:10,0])))

            self.log.write("test: {}\n".format(str(bool(lf.data[0,0] == test_opts[k][1][0,0]))))
            self.log.write("{}\n".format(str(lf.data[0,0])))
            self.log.write("{}\n".format(str(test_opts[k][1][0,0])))

            # delete data file
            os.remove(test_file)

            # compare read hdr against original hdr
            keys = lf.header.keys()
            keys.remove('metadata')

            for key in keys:
                self.assertEqual(test_opts[k][0][key], lf.header[key])

            mkeys = lf.header['metadata'].keys()
            for key in mkeys:
                self.assertEqual(str(test_opts[k][0]['metadata'][key]),
                                 str(lf.header['metadata'][key]))

            # compare data content against original data
            for x,y in zip(lf.data.flatten('F'), test_opts[k][1].flatten('F')):
                self.assertAlmostEqual(x, y, 6)


if __name__ == "__main__":
    unittest.main()