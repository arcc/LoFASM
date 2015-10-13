LoFASM Tools : Crawler usage examples
=====================================

This quick start tutorial explains how to get started reading
*.lofasm* data files.

Note:
__The functions on this tutorial will be executed on the example file that
is included in this repository as *testdata/20150323\_033624.lofasm*.__

### LoFASM imports
```
from lofasm import parse_data as pdat
```

### Opening the *.lofasm* file
```
#instantiate the crawler instance
crawler = pdat.LoFASMFileCrawler('20150323_033624.lofasm')

#parse file header and move pointer to first integration
crawler.open()
```

### Print file header
```
print crawler.getFileHeader()
```
This will print the file header dictionary which is described by the following
 table.

| Field name | Note/Unit |
| :----------: | :----: |
| hdr_sig    |   |
| hdr_ver | file header version |
| hdr_len | length of file header in bytes |
| station | LoFASM station |
| Nbins | number of frequency bins. this will read 2048 but only the first 1024 are usable at the moment |
| fstart | MHz, start frequency |
| fstep | fractional MHz, '097' should be interpreted as '0.097 MHz' |
|mjd_day| integer mjd date |
|mjd_msec| ms, time after beginning of mjd date in milliseconds |
| int_time | integration time in seconds|
|Dfmt_ver| version of data format|
|notes| notes on observation|

### Print data start time mjd
```
print crawler.time_start
```
Times are stored as astropy time objects.

### Print time of current integration
It is possible to print out the timestamp for each integration
as the crawler moves through a LoFASM file.
```
#print timestamp for current integration (mjd)
print crawler.time

#print timestamp in datetime format
print crawler.time.datetime.strftime("%Y/%m/%d %H:%M:%S")

#print how much time (in seconds) has passed since the beginning
#of the file
print (crawler.time - crawler.time_start).sec
```



### Print integration time (TimeDelta object)
```
print crawler.int_time
```

### Set polarization
If only one polarization is going to be used in a script then
it is convenient to set it only once. Once the polarization is `set`
then all subsequent calls to `crawler.get()` will return data
corresponding to the selected polarization.
It is possible to change the default polarization at any time.
```
crawler.setPol('AA')
```

### Get spectrum
The current integration's spectrum can be accessed by using the `get` method.
`crawler.get` will return a numpy array containing a single spectrum in
the polarization requested by `crawler.set`.
```
fb = crawler.get()
```

### Plot spectrum
A spectrum can be plotted on a log10 scale using matplotlib and numpy.
```
from lofasm import parse_data as pdat
import matplotlib.pyplot as plt
import numpy as np

freqs = pdat.freqRange()
plt.plot(freqs,10*np.log10(fb))
plt.show()
```

### Navigate in time by integrations
It is possible to move to different integrations within a file
by using the `forward` and `backward` methods.
```
#move forward 1 integration
crawler.forward() # or crawler.forward(1)

#move forward 10 integrations
crawler.forward(10)

#move backward 1 integration
crawler.backward() #or crawler.backward(1)

#move backward 10 integrations
crawler.backward(10)

#move backward 15 integrations using forward
crawler.forward(-15)
```
