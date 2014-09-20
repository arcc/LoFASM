
from lofasm import future
from lofasm import parse_data as pdat
from lofasm.future import syscmd
from lofasm import lofasm_dat_lib as ldat
import numpy as np

import os
import datetime

data_home = os.environ['LOFASMDATA_HOME']
data_recent = os.environ['LOFASMDATA_RECENT']
station = os.environ['STATION']
pow_ext = '.pow'
dates_ext = '.dates'

outFileBase = data_home + '/timelapse/timelapse' 

bufferLength = datetime.timedelta(hours = 24)
now = datetime.datetime(2014,8,1) #datetime.datetime.utcnow()



fileList = future.get_spectra_range(now - bufferLength, now, data_home)
timelapseDict = {'AA':[],'BB':[],'CC':[],'DD':[]}

freq_range = (36,39) #MHz

print "processing %i files" % len(fileList)


for lofasmFile in fileList:
    lofasm_int = lofasmFile.getNextIntegration()
    for pol in lofasm_int.autos.keys():
        startBin = pdat.freq2bin(freq_range[0])
        endBin = pdat.freq2bin(freq_range[1])
        #get integration for this polarization as numpy array
        integration = np.array(lofasm_int.autos[pol])
        intMean = integration[startBin:endBin].mean()
        timelapseDict[pol].append((intMean,lofasmFile.date))
    lofasmFile._file_obj.close()

for pol in timelapseDict.keys():
    outFilePow = open(outFileBase + '_' + str(pol) + pow_ext , 'w')
    outFileDates = open(outFileBase + '_' + str(pol) + dates_ext, 'w')

    for pow, date in timelapseDict[pol]:
        outFilePow.write(str(pow) + '\n')
        outFileDates.write(date.strftime("%Y%m%d:%H%M%S")+'\n')

    outFilePow.close()
    outFileDates.close()

    
    
    
        

        



