#!/usr/bin/env python
# python script to read ADC voltanges and report voltage ADC counts
#-----------------------------------------------------------------
import sys, os, random,numpy
import matplotlib, corr, time,struct, math,pylab,mkid
import datetime

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


try:
    load_fpga = sys.argv[1]
except:
    print "Usage:",sys.argv[0], "need to set loading firmware"; sys.exit(1)
roach='192.168.4.21'# roach IP adr
katcp_port=7147
timeout=10
fpga=corr.katcp_wrapper.FpgaClient(roach,katcp_port)
time.sleep(1)   # wait for roach to connect (number of seconds).
if sys.argv[2] == '0':
    boffile = 'adc_snap4x_test_zdock0_2014_Jul_09_1920.bof'
elif sys.argv[2] =='1':
    boffile = 'adc_snap4x_test_zdock1_2014_Jul_09_1956.bof'

if load_fpga == '1':  # force bof program
	fpga.progdev(boffile)     #enable to load the firmware
	time.sleep(1)   # wait for roach to start to send or received data
	list_reg=fpga.listdev()

	print 'fpga start list of register: ...'
	print list_reg
	print 'fpga end list of register: ...'

	print 'fpga configured with : '
	print boffile
	
else: # don't reload your firmware (keep the old firmware)
	print 'fpga already configured with : '
	print boffile
fname_I = 'adc_RF_I' 
fname_Q = 'adc_RF_Q' 
ext='.dat'

print 'Configuring snapI_ctrl_reg , snapQ_ctrl_reg ,  and startSNAP_reg...'
#fpga.write_int('snap64_I_ctrl',0)
fpga.write_int('snap64_Q_ctrl',0)
fpga.write_int('startSNAP',2)

print 'Set the snap CTRL...'

#fpga.write_int('snap64_I_ctrl',1)
fpga.write_int('snap64_Q_ctrl',1)
#fpga.write_int('snap64_I_ctrl',0)
fpga.write_int('snap64_Q_ctrl',0)

print 'Trig Data Acquisition : RF_I, RF_Q...'
fpga.write_int('startSNAP',1)
time.sleep(0.5)
fpga.write_int('startSNAP',2)

print 'Read buffer size ...'
snapI_size=fpga.read_int('snap64_I_addr')+1
snapQ_size=fpga.read_int('snap64_Q_addr')+1
buf_size=snapQ_size							#  snapI_size must be = snapI_size
print 'Reading %i values from snapI_size'%(snapI_size)
print 'Reading %i values from snapQ_size'%(snapQ_size)

print 'Read Data buffer : RF_I, RF_Q...'
binaryDataIm = fpga.read('snap64_I_bram_msb', buf_size*4)
binaryDataIl = fpga.read('snap64_I_bram_lsb', buf_size*4)
binaryDataQm = fpga.read('snap64_Q_bram_msb', buf_size*4)
binaryDataQl = fpga.read('snap64_Q_bram_lsb', buf_size*4)
dataI = mkid.convBinData_rev16x4(binaryDataIl,binaryDataIm)
dataQ = mkid.convBinData_rev16x4(binaryDataQl,binaryDataQm)
##########################################################"
dataI=numpy.reshape(dataI,4*buf_size)
dataQ=numpy.reshape(dataQ,4*buf_size)
'''
print 'Save data on disk...'
now = datetime.datetime.now()
now_addon = '_'+str(now.year) + '_'+str(now.month)+ '_'+str(now.day) + '_'+str(now.hour) + '_'+str(now.minute)+ext     


fullfilename_I =  fname_I + now_addon

fullfilename_Q =  fname_Q + now_addon

f_I = open(fullfilename_I ,'w')
for iter in range(0,len(dataI)):
    f_I.write(str(dataI[iter])+'\n');
f_I.close()

f_Q = open(fullfilename_Q,'w')
for iter in range(0,len(dataQ)):
    f_Q.write(str(dataQ[iter])+'\n');
f_Q.close()

'''
import pylab
rmsI = calculateRMS(dataI)
rmsQ = calculateRMS(dataQ)
enobI = calculateENOB(rmsI)
enobQ = calculateENOB(rmsQ)
print 'RMS:'
print 'I: ', rmsI,'\t Q: ', rmsQ
print 'ENOB:'
print 'I: ', enobI,'\t Q: ', enobQ

pylab.subplot(221)
matplotlib.pylab.ylabel('Channel_I')
pylab.plot(dataI, label='I Channel data (ch_I)')


pylab.subplot(222)
matplotlib.pylab.ylabel('Channel_Q')
pylab.plot(dataQ, label='Q Channel data (ch_Q)')

pylab.subplot(223)
pylab.hist(dataI,1000)

pylab.subplot(224)
pylab.hist(dataQ,1000)

pylab.show()

