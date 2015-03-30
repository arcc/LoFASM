#library for functions that require talking to the ROACH Board

import os, time
from parse_data_H import T_fpga, FFT_cycles, PacketsPerSample
import numpy as np


#get ROACH ip from environment variable
try:
    roach_ip = os.environ['ROACH_IP']
except KeyError as err:
    print "ROACH_IP environment variable not set!"
    print "Defaulting to 192.168.4.21"
    roach_ip = '192.168.4.21'

#connect to roach board
def connect_roach():
    import corr
    fpga = corr.katcp_wrapper.FpgaClient(roach_ip)
    time.sleep(0.5)
    return fpga

def getSampleTime(Nacc):
    return T_fpga * FFT_cycles * Nacc

def getRoachAccLen():
    fpga = connect_roach()
    return fpga.read_uint('acc_len')

def getNumPacketsFromDuration(obs_dur):
    """
    Return the number of network packets corresponding to
    an interval of time.
    """
    obs_dur = float(obs_dur)
    return int(PacketsPerSample * np.ceil(obs_dur /
            getSampleTime(getRoachAccLen())))
