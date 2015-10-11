
from lofasm import parse_data as pdat
import numpy as np
import matplotlib.pyplot as plt

plt.ion()

fname = '20150323_033624.lofasm'

#instantiate crawler object
crawler = pdat.LoFASMFileCrawler(fname)

#parse header and read first integration
crawler.open()

#print file header information
print "===== File Header ====="
file_hdr = crawler.getFileHeader()
for key in file_hdr.keys():
    print "{} : {}".format(file_hdr[key][0], file_hdr[key][1])
print "======================"

#print number of integrations in file
print "===== No. of integrations ====="
print crawler.getNumberOfIntegrationsInFile()
print "======================"

#print file start time
print "===== File Start Time (mjd)====="
print crawler.time_start
print "======================"

print "===== File Start Time (str)====="
print crawler.time_start.datetime.strftime("%Y/%m/%d %H:%M:%S")
print "======================"


#print current integration timestamp
print "===== Integration timestamp ====="
print crawler.time
print "======================"

print "===== Integration Time (str)====="
print crawler.time.datetime.strftime("%Y/%m/%d %H:%M:%S")
print "======================"


#plot first integration
crawler.setPol('AA')
fb = crawler.get()
freqs = pdat.freqRange()
plt.figure(1)
plt.plot(freqs,10*np.log10(fb[:1024]))
plt.xlabel('Frequency (MHz)')
plt.ylabel('Power (db)')
plt.grid()

#move 25 integrations into file
crawler.forward(25)

#print new timestamp
print "===== Integration timestamp ====="
print crawler.time
print "======================"

print "===== Integration Time (str)====="
print crawler.time.datetime.strftime("%Y/%m/%d %H:%M:%S")
print "======================"


#print time (in seconds) since beginning of file
print "===== Time since file start ====="
print "{}s".format((crawler.time - crawler.time_start).sec)
print "======================"

#plot new integration
fb = crawler.get()
plt.plot(freqs,10*np.log10(fb[:1024]))

#wait for user to quit program
raw_input('press enter to quit.')
