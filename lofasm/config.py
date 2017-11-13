#Python Config definitions


import os
import numpy as np


def getConfig(cfgpath=os.path.join(os.environ['HOME'],
                 '.lofasm/lofasm.cfg')):
    '''
    return lofasm config parameters as a dictionary
    '''            
    try:
        return dict(np.loadtxt(cfgpath, dtype=str))
    except IOError:
        print "unable to open config file: ", cfgpath


# this block is deprecated. it stays here for now for 
# compatbility purposes.
PORT = 60001
PACKETSIZE = 8192
PACKETGROUPSIZE = 17
STATION = 3
LOGFILE = '/home/controller/logs/lofasm.log'
PIDFILE = '/tmp/lofasm_rec.pid'
DISKFILE = '/var/lofasm/ActiveDisk'
BLOCKFILE = '/var/lofasm/BlockTime'
STETHDIR = '/home/controller/var/lofasm/stethoscope/'
COLORPLOTDIR = '/home/controller/var/lofasm/colorplots/'

#db settings
dbhost = "localhost"
dbname = "lofasm"
dbuser = "lofasm"
dbpass = "l0fasm"