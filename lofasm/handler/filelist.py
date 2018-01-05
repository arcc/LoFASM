from lofasm.bbx import bbx
from lofasm import parse_data as pdat
import matplotlib.pyplot as plt
import numpy as np
import os, sys
from glob import glob
from astropy.time import Time
from datetime import datetime
from copy import deepcopy
from ..parse_data import Baselines
import ephem
from ..station import LoFASM_Stations

LOFASM_EXTS = [".lofasm", ".lofasm.gz"]
BBX_EXTS = [".bbx", ".bbx.gz"]
KNOWN_EXTS = LOFASM_EXTS + BBX_EXTS
DATE_FMT = "%Y/%m/%d"
DATETIME_FMT = "%Y/%m/%d %H:%M:%S"

msec = 1./86400000.

class FileListHandler(object):
    def __init__(self, dirPath):
        self.rootDir = dirPath
        self.file_start_mjds = []
        # get file listing
        flist = glob(os.path.join(self.rootDir, "*"))
        # filter unknown file types from listing
        flist = [f for f in flist if [e for e in KNOWN_EXTS if f.endswith(e)]]
        flist.sort()

        self.nfiles = len(flist)

        if not self.nfiles:
            raise RuntimeError("No files in {} are readable.".format(self.rootDir))
        self.flist = flist

    def getMjdDatetimeList(self):
        '''Return list of datetime objects from file_start_mjds
        '''
        if not self.file_start_mjds:
            errmsg = "Internal list of start MJD times has not been created."
            raise NotImplemented(errmsg)
        
        dt_list = [Time(x, format='mjd').datetime for x in self.file_start_mjds]
        return dt_list

    def getSiderealTimes(self, stationid):
        '''
        return array of sidereal times
        '''
        N = self.nfiles
        sidereal_times = np.zeros(N, dtype=np.float64)
        lfstation = deepcopy(LoFASM_Stations[stationid])
        dtimes = self.getMjdDatetimeList()
        fmt = "%Y/%m/%d %H:%M:%S"
        for i in range(N):
            lfstation.date = dtimes[i].strftime(fmt)
            sidereal_times[i] = lfstation.sidereal_time()/(2*np.pi)*24.
        return sidereal_times

    def _getStartTimeFromFileHeader(self, f=None):
        raise NotImplemented("This method should be overridden by a child class")
    
    def _getFileStartTimesFromHeader(self):
        '''
        Set self.file_start_mjds by parsing file headers.
        '''
        file_start_mjds = []
        i = 1
        N = self.nfiles
        re = "Starting..."
        sys.stdout.write(re)
        sys.stdout.flush()

        # copy the internal filelist because it is not good practice to
        # operate on a list while also looping over its elements.
        flist = deepcopy(self.flist)
        for f in flist:
            re = "{}/{} -- {}".format(i, N, f)
            sys.stdout.write("\r"+re)
            sys.stdout.flush()
            try:
                mjd_timestamp = self._getMjdStartTimeFromFileHeader(f)
                if self.mjdRange:
                    # if an MJD Range was selected then only keep
                    # files that are within the window.
                    # files outside of this window are removed from
                    # the filelist, flist
                    if self._inMjdRange(mjd_timestamp):
                        file_start_mjds.append(mjd_timestamp)
                    else:
                        print "  --Removing {}".format(f)
                        self.flist.remove(f)
                else:
                    file_start_mjds.append(mjd_timestamp)
            except:
                print "\nunable to process {}\n".format(f)
                self.flist.remove(f)  # remove from file list
                
            i += 1
                
        self.file_start_mjds = file_start_mjds
        self.nfiles = len(self.flist)

    def _inMjdRange(self, mjd):
        '''Check if mjd is within selected range.
        
        Parameters
        ----------
        mjd : float
            MJD float to check.
        
        Returns
        -------
        result : bool
            If mjd is within range then return True, otherwise False.
        '''
        s, e = self.mjdRange
        return True if mjd <= e and mjd >= s else False

    # special methods
    def __len__(self):
        return self.nfiles

class LofasmFileListHandler(FileListHandler):
    def __init__(self, dirPath, mjdRange=()):
        '''Initialize a DataSet Handler for .lofasm data.
        
        Parameters
        ---------- 
        dirPath : str
            Path to the directory containing dataset files.
        mjdRange : tuple, optional
            Tuple containing (mjdMax, mjdMin) where both MJD times
            are represented by floats. If no range is specified then
            process all files in dataset directory.
        '''
        
        # verify inputs
        #assert os.path.isdir(dirPath), "Unable to open the dataset directory."
        super(LofasmFileListHandler, self).__init__(dirPath)

        self.mjdRange = mjdRange
        # get start times of all files in dataset director
        self._getFileStartTimesFromHeader()

    def _getMjdStartTimeFromFileHeader(self, f):
        lfobj = pdat.LoFASMFileCrawler(f)
        lfobj.open()
        hdr = lfobj.getFileHeader()
        mjd_timestamp = float(hdr[8][1])
        mjd_timestamp += float(hdr[9][1])*msec
        del lfobj
        return mjd_timestamp

class BbxFileListHandler(FileListHandler):
    def __init__(self, dirPath, pol, mjdRange=()):
        '''Initialize a DataSet Handler for .bbx data.
        
        Parameters
        ----------
        dirPath : str
            Path to the directory containing dataset files.
        pol : str
            One of the available BBX baselines
        mjdRange : tuple, optional
            Tuple containing (mjdMax, mjdMin) where both MJD times
            are represented by floats. If no range is specified then
            process all files in dataset directory.
        '''
        
        # verify inputs
        assert os.path.isdir(dirPath), "Unable to open the dataset directory: {}".format(dirPath)
        pol = pol.upper()
        assert pol in Baselines, "Unrecognized Baseline"
        
        super(BbxFileListHandler, self).__init__(dirPath)

        # filter out only the baseline of interest
        self.flist = [f for f in self.flist if pol in f]
        self.nfiles = len(self.flist)

        # to support multiple 'start_time' formats (due to a bug that caused them)
        self.startt_fmts = ["%Y-%m-%dT%H:%M:%S", "%Y%m%d_%H%M%S"]
        
        self.mjdRange = mjdRange
        # get start times of all files in dataset director
        self._getFileStartTimesFromHeader()
        

    def _getMjdStartTimeFromFileHeader(self, f):
        lfx = bbx.LofasmFile(f)
        hdr = lfx.header
        if not lfx.header['metadata']['dim1_len']:
            raise ValueError("no data in this file")

        startt = hdr['start_time']
        startt_repr = startt[:-8] if 'T' in startt else startt
        dfmt = self.startt_fmts[0] if 'T' in startt else self.startt_fmts[1]
        timeobj = datetime.strptime(startt_repr, dfmt)
        return Time(timeobj).mjd
        
