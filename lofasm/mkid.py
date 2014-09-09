import math, binascii, random, struct
import numpy as np


def freqCombLUT(fList, sampleRate=540e6, resolution=1e4, amplitude=2**15-1):
    """ Returns data points for the DAC look-up table for I and Q.
    
        @param fList            List of desired freqs with kHz resolution, e.g., 12.34e6.
        @param sampleRate       Probably 550e6
        """
    I = [0 for i in range(int(sampleRate/resolution))]
    Q = [0 for i in range(int(sampleRate/resolution))]

    for f in fList:
        #phase = random.uniform(-math.pi, math.pi)
        phase = 0.
        I = np.add(I, singleFreqLUT(f, 'I', sampleRate, resolution, phase, amplitude))
        Q = np.add(Q, singleFreqLUT(f, 'Q', sampleRate, resolution, phase, amplitude))

    return I, Q


def singleFreqLUT(f, iq, sampleRate=540e6, resolution=1e4, phase=0, amplitude=2**15-1):
    """ Returns data points for the DAC look-up table.
    
        @param f                List of desired freqs, e.g., 12.34e6 if resolution = 1e4.
        @param sampleRate       Sample rate of DAC.
        @param resolution       Example: 1e4 for resolution of 10 kHz.
        @param phase            Constant phase offset between -pi and pi.
        """
    size = int(sampleRate/resolution)
    data = []
    for i in range(0, size):
        t = i/sampleRate
        if iq == 'I':
            data.append(int(amplitude*math.cos(2*math.pi*f*t+phase)))
        else:
            data.append(int(-amplitude*math.sin(2*math.pi*f*t+phase)))

    return data   

def gaussianLUT(sampleRate=540e6, resolution=1e4, amplitude=2**15-1, sigma=0.5):
    """ Returns a white noise LUT for DAC I and Q.

        @param sampleRate       Sample rate of DAC
        @param resolution       Example: 1e4 for resolution of 10 kHz.
        """
    size = int(sampleRate/resolution)
    I = []
    Q = []
    x = 0
    y = 0
    for i in range(0, size):
        x = int(amplitude*random.gauss(0, sigma))
        y = int(amplitude*random.gauss(0, sigma))
        I.append(x)
        Q.append(y)

    return I, Q

def chirpLUT(sampleRate=512e6, resolution=1e4, amplitude=2**15-1):
    """ Returns a chirp LUT for DAC I and Q.

        @param sampleRate       Sample rate of DAC
        @param resolution       Example: 1e4 for resolution of 10 kHz.
        """
    size = int(sampleRate/resolution)

    f = [i*resolution for i in range(0,size)]
    I, Q = [], []
    for i in range(0, size):
        t = i/sampleRate
        I.append(int(amplitude*math.cos(2*math.pi*f[i]*t)))
        Q.append(int(amplitude*math.sin(2*math.pi*f[i]*t)))

    return I, Q   

def convertToBinary4x(data):
    """ Converts two successive data points each to 16-bit binary and concatenates to one 32-bit word.
    
        @param data             Decimal data to be converted  for FPGA.
        """
    binaryData = ''
    for i in range(0, len(data)/4):
        x = struct.pack('>hhhh', data[4*i], data[4*i+1], data[4*i+2], data[2*i+3])
        binaryData = binaryData + x
    
    return binaryData

def convertToBinary128(data_I, data_Q):
    binaryData = ''
    for i in range(0, len(data_I)/4):
        x = struct.pack('>hhhh', data_I[i*4],data_I[i*4+1],data_I[i*4+2],data_I[i*4+3])
        y = struct.pack('>hhhh', data_Q[i*4],data_Q[i*4+1],data_Q[i*4+2],data_Q[i*4+3])
        binaryData = binaryData + x + y

    return binaryData
    

def convertToBinary16(data):
    """ Converts data points to 16-bit binary.
    
    @param data             Decimal data to be converted  for FPGA.
    """
    binaryData = ''
    for i in range(0, len(data)):
        x = struct.pack('h', data[i])
        binaryData = binaryData + x

    return binaryData

def convertToBinary32(data):
    """ Convert data to 32-bit binary 
    
        @param data             Decimal data to be converted  for FPGA.
        """
    binaryData = ''
    for i in range(0, len(data)):
        x = struct.pack('>l',data[i])
        binaryData = binaryData + x
    
    return binaryData

def convertToBinaryDouble(data):
    """ Convert data to double binary 
    
        @param data             Decimal data to be converted
        """
    binaryData = ''
    for i in range(0, len(data)):
        x = struct.pack('d',data[i])
        binaryData = binaryData + x
    
    return binaryData


def convertToBinary16(data):
    """ Converts data points to 16-bit binary.
    
    @param data             Decimal data to be converted  for FPGA.
    """
    binaryData = ''
    for i in range(0, len(data)):
        x = struct.pack('h', data[i])
        binaryData = binaryData + x

    return binaryData

def convertToBinary32(data):
    """ Convert data to 32-bit binary 
    
        @param data             Decimal data to be converted  for FPGA.
        """
    binaryData = ''
    for i in range(0, len(data)):
        x = struct.pack('>l',data[i])
        binaryData = binaryData + x
    
    return binaryData

def convertToBinaryDouble(data):
    """ Convert data to double binary 
    
        @param data             Decimal data to be converted
        """
    binaryData = ''
    for i in range(0, len(data)):
        x = struct.pack('d',data[i])
        binaryData = binaryData + x
    
    return binaryData


def convertToBinary16(data):
    """ Converts data points to 16-bit binary.
    
    @param data             Decimal data to be converted  for FPGA.
    """
    binaryData = ''
    for i in range(0, len(data)):
        x = struct.pack('h', data[i])
        binaryData = binaryData + x

    return binaryData


def convertToBinaryDouble(data):
    """ Convert data to double binary 
    
        @param data             Decimal data to be converted
        """
    binaryData = ''
    for i in range(0, len(data)):
        x = struct.pack('d',data[i])
        binaryData = binaryData + x
    
    return binaryData


def convertToBinary32x2(data):
    """ Converts two successive data points each to 16-bit binary and concatenates to one 32-bit word.
    
        @param data             Decimal data to be converted  for FPGA.
        """
    binaryData_0 = ''
    binaryData_1 = ''
    for i in range(0, len(data)/4):
        x_0 = struct.pack('>hh', data[4*i], data[4*i+1])
        binaryData_0 = binaryData_0 + x_0
        x_1 = struct.pack('>hh', data[4*i+2], data[4*i+3])
        binaryData_1 = binaryData_1 + x_1

        
    
    return binaryData_0,binaryData_1


def convertBinData(binDataString):
    """ Converts the contents of the binary data string from BRAM or other memory
        into an array.  Assumes data resides in MS 16 bits of the 32 bit memory location.

        @param binDataString    The data string.
        """
    data = []
    for i in range(len(binDataString)/4):
        data.append(struct.unpack('>h', binDataString[i*4:i*4+2])[0])

    return data

def convertBinData16x4(binDataString_lsb,binDataString_msb):
    """ Converts the contents of the binary data string from BRAM64
        into an array.  Assumes data is 16 bits.

        @param binDataString    The data string.
        """
    data =[]
    data1 = []
    data2 =[]
    data3 = []
    data4 =[]
    
    for i in range(len(binDataString_msb)/4):
        data1.append(struct.unpack('>h', binDataString_msb[i*4:i*4+2])[0])
        data2.append(struct.unpack('>h', binDataString_msb[i*4+2:i*4+4])[0])

    for i in range(len(binDataString_lsb)/4):
        data3.append(struct.unpack('>h', binDataString_lsb[i*4:i*4+2])[0])
        data4.append(struct.unpack('>h', binDataString_lsb[i*4+2:i*4+4])[0])


    data=[data1,data2,data3,data4];
    return data

#########################################
def convBinData_rev16x4(binDataString_lsb,binDataString_msb):
    """ la convertion le contenue binaire de BRAM64 contient des mots de 16 bits concatenet
        """
    data1=[]	    
    for i in range(len(binDataString_msb)/4):
        data1.append(struct.unpack('>h', binDataString_msb[i*4:i*4+2])[0])
        data1.append(struct.unpack('>h', binDataString_msb[i*4+2:i*4+4])[0])
        data1.append(struct.unpack('>h', binDataString_lsb[i*4:i*4+2])[0])
        data1.append(struct.unpack('>h', binDataString_lsb[i*4+2:i*4+4])[0])


    return data1
#########################################################
def convertBinData16x2(binDataString):
    """ Converts the contents of the binary data string from BRAM or other memory
        into an array.  Assumes data is 16 bits.

        @param binDataString    The data string.
        """
    data =[]
    data1 = []
    data2 =[]
    for i in range(len(binDataString)/4):
        data1.append(struct.unpack('>h', binDataString[i*4:i*4+2])[0])
        data2.append(struct.unpack('>h', binDataString[i*4+2:i*4+4])[0])

    data=[data1,data2];
    return data


def convertBinData16(binDataString):
    """ Converts the contents of the binary data string from BRAM or other memory
        into an array.  Assumes data is 16 bits.

        @param binDataString    The data string.
        """
    data = []
    for i in range(len(binDataString)/4):
        data.append(struct.unpack('>h', binDataString[i*4:i*4+2])[0])
        data.append(struct.unpack('>h', binDataString[i*4+2:i*4+4])[0])

    return data





def convertBinData32(binDataString):
    """ Converts the contents of the binary data string from BRAM or other memory
        into an array.  Assumes data is 32 bits.

        @param binDataString    The data string.
        """
    data = []
    for i in range(len(binDataString)/4):
        data.append(struct.unpack('>l', binDataString[i*4:i*4+4])[0])

    return data

