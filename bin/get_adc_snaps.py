#!/usr/bin/env python

#-----------------------------------------------------------------
import numpy
from astropy.time import Time

def getTimeStampUTC():
    stamp_utc = Time.now().datetime.strftime('%Y%m%d_%H%M%S')
    return stamp_utc

def calculateRMS(data):
    data = numpy.array(data)
    return numpy.sqrt(data.var())

def calculateENOB(rms):
    return numpy.log2(rms)

def convBinData_rev16x4(binDataString_lsb,binDataString_msb):
    """ Converts the contents of the binary data string from BRAM64
        into an array.  Assumes data is 16 bits.

        @param binDataString    The data string.
        """
    data1=[]	    
    for i in range(len(binDataString_msb)/4):
        data1.append(struct.unpack('>h', binDataString_msb[i*4:i*4+2])[0])
        data1.append(struct.unpack('>h', binDataString_msb[i*4+2:i*4+4])[0])
        data1.append(struct.unpack('>h', binDataString_lsb[i*4:i*4+2])[0])
        data1.append(struct.unpack('>h', binDataString_lsb[i*4+2:i*4+4])[0])
        
    return data1

#-----------------------------------------------------------------


if __name__ == "__main__":
    '''
    If run as a stand-alone program, this script will communicate with the
    local ROACH Board (at 192.168.4.21) and snap some data off of the
    individual ADC boards.

    This is achieved by loading the ROACH board with two different
    BOF files; each ADC board requires its own BOF for now.

    The resulting timeseries and histograms will be saved in a binary file
    that is time stamped in UTC and placed in the appropriate directory.
    '''
    
    import sys, os
    import random
    import time
    import struct
    import datetime
    
    import matplotlib.pyplot as plt
    

    import corr
    from lofasm import mkid
    #from astropy.time import Time

    
    roach_ip = '192.168.4.21'
    katcp_port = 7147


    fpga=corr.katcp_wrapper.FpgaClient(roach_ip, katcp_port)
    time.sleep(1)   # wait for roach to connect (number of seconds).

    adc_boffiles = ['adc_snap4x_test_zdock0_2014_Jul_09_1920.bof',
                    'adc_snap4x_test_zdock1_2014_Jul_09_1956.bof']

    for boffile in adc_boffiles:
        fpga.progdev(boffile)     #enable to load the firmware
        time.sleep(1)   # wait for roach to start to send or received data
        list_reg=fpga.listdev()

        print 'fpga start list of registers: ...'
        print list_reg
        print 'fpga end list of registers: ...'



        fname_I = 'adc%i_RF_I_' % adc_boffiles.index(boffile) 
        fname_Q = 'adc%i_RF_Q_' % adc_boffiles.index(boffile)
        ext='.snap'

        print 'Configuring snapI_ctrl_reg , snapQ_ctrl_reg ,  and startSNAP_reg...'
        fpga.write_int('snap64_I_ctrl',0)
        fpga.write_int('snap64_Q_ctrl',0)
        fpga.write_int('startSNAP',2)

        print 'Set the snap CTRL...'

        fpga.write_int('snap64_I_ctrl',1)
        fpga.write_int('snap64_Q_ctrl',1)
        fpga.write_int('snap64_I_ctrl',0)
        fpga.write_int('snap64_Q_ctrl',0)

        print 'Trig Data Acquisition : RF_I, RF_Q...'
        fpga.write_int('startSNAP',1) #begin acquisition
        time.sleep(0.5)
        fpga.write_int('startSNAP',2) #end acquisition

        print 'Read buffer size ...'
        snapI_size=fpga.read_int('snap64_I_addr')+1
        snapQ_size=fpga.read_int('snap64_Q_addr')+1
        buf_size=snapQ_size		#snapI_size must be = snapI_size
        print 'Reading %i values from snapI_size' % (snapI_size)
        print 'Reading %i values from snapQ_size' % (snapQ_size)

        print 'Read Data buffer : RF_I, RF_Q...'
        binaryDataIm = fpga.read('snap64_I_bram_msb', buf_size*4)
        binaryDataIl = fpga.read('snap64_I_bram_lsb', buf_size*4)
        binaryDataQm = fpga.read('snap64_Q_bram_msb', buf_size*4)
        binaryDataQl = fpga.read('snap64_Q_bram_lsb', buf_size*4)
        dataI = mkid.convBinData_rev16x4(binaryDataIl,binaryDataIm)
        dataQ = mkid.convBinData_rev16x4(binaryDataQl,binaryDataQm)

        dataI=numpy.reshape(dataI,4*buf_size)
        dataQ=numpy.reshape(dataQ,4*buf_size)

        #save data to disk
        timeStamp = getTimeStampUTC()
        try:
            root_dir = os.environ['LOFASMDATA_HOME']
        except KeyError as err:
            print "The environment variable %s does not exist!" % err.message
            exit()
        save_dir = root_dir + '/snaps/'
        fullFilenameI = save_dir + fname_I + timeStamp + ext
        fullFilenameQ = save_dir + fname_Q + timeStamp + ext

        f_I = open(fullFilenameI, 'w')
        f_Q = open(fullFilenameQ, 'w')
        for i in range(len(dataI)):
            f_I.write(str(dataI[i])+'\n')
            f_Q.write(str(dataQ[i])+'\n')
        f_I.close()
        f_Q.close()  
