from lofasm.bbx import bbx
from lofasm import parse_data as pdat
import matplotlib.pyplot as plt
import numpy as np
import os
from glob import glob
from astropy.time import Time
from datetime import datetime

LOFASM_EXTS = [".lofasm", ".lofasm.gz"]
BBX_EXTS = [".bbx", ".bbx.gz"]
KNOWN_EXTS = LOFASM_EXTS + BBX_EXTS
DATE_FMT = "%Y/%m/%d"
DATETIME_FMT = "%Y/%m/%d %H:%M:%S"

msec = 1./86400000.

class DataSetHandler(object):
    def __init__(self, dirPath):
        self.rootDir = dirPath
        
        # get file listing
        flist = glob(os.path.join(self.rootDir, "*"))
        # filter unknown file types from listing
        flist = [f for f in flist if [e for e in KNOWN_EXTS if f.endswith(e)]]
        flist.sort()

        self.nfiles = len(flist)

        if not self.nfiles:
            raise RuntimeError("No files in {} are readable.".format(self.rootDir))
        self.flist = flist

    # special methods
    def __len__(self):
        return self.nfiles

class LofasmDataSetHandler(DataSetHandler):
    def __init__(self, dirPath):
        super(LofasmDataSetHandler, self).__init__(dirPath)

        self._getFileStartTimesFromHeader()

    def _getFileStartTimesFromHeader(self):
        file_start_mjds = []
        for f in self.flist:
            lfobj = pdat.LoFASMFileCrawler(f)
            lfobj.open()
            hdr = lfobj.getFileHeader()
            mjd_timestamp = float(hdr[8][1])
            mjd_timestamp += float(hdr[9][1])*msec
            file_start_mjds.append(mjd_timestamp)
            del lfobj
        self.file_start_mjds = file_start_mjds
