# LoFASM Tools 
#####r0.1
---
## Outline
-	Introduction
- 	Downloading and installing the LoFASM Tools
- 	LoFASM Executables
-	LoFASM API
-	Examples
	 

## Introduction
The purpose of this document is to serve as a manual for 
the LoFASM Tools.


## Downloading and installing the LoFASM Tools

### Platforms

The LoFASM Tools have been tested on the following operating systems:

* Mac OS X Yosemite 10.10.2
* Redhat Enterprise 6
* Ubuntu 14.04



**I cannot confirm that the LoFASM Tools will work on Windows since it has yet to be fully tested.**

### LoFASM Tools Requirements
In order to install the _lofasm_ Python package, the following conditions must be met:

*	Python version is 2.7.X
* 	numpy version 1.6.2 or newer is installed
* 	matplotlib version 1.1.1 or newer is installed
*  scipy is installed (version to be confirmed)
*  astropy is installed (version to be confirmed)

### Cloning into the LoFASM repo
The LoFASM Tools are hosted at [ARCC's Github Account](https://github.com/arcc). The repository can be downloaded by using the Git clone command in the directory you would like the repository to copied in.

	git clone https://github.com/arcc/lofasm.git
	
>If you want to save the lofasm repo in the directory _~/repos_ then navigate there with `cd ~/repos` before running the command above.

If all goes well, a new directory called `lofasm` should appear in your local directory. Use `ls` to check if the repository was created.

### Installing the LoFASM Tools
Installing the LoFASM Tools __should__ be as easy as running the Python `setup.py` file.

First, you will need to navigate to the new _lofasm_ directory.
>If you are still in the directory from which you ran the `git clone` command above, then navigating to the _lofasm_ directory is as easy as `cd lofasm`.

The contents of the _lofasm_ directory should like this:

![Alt text](/Users/louis/Documents/programming_sandbox/python/lofasm/docs/images/ls_lofasm_repo.png "lofasm directory listing")

The LoFASM tools can be installed by using the _setup.py_ script:

	sudo python setup.py install
> If you're using a virtual environment then you most likely do **not** need the `sudo` in front of the command above.

Here is an example of the output:
	
![Alt text](/Users/louis/Documents/programming_sandbox/python/lofasm/docs/images/install_output.png "setup.py output")

If all went according to plan, then the LoFASM Tools should now be completely installed. To confirm that the installation succeeded try pulling up the help menu for the LoFASM Plotter.

	lofasm_plot.py -h
	
>If the file was not found, then try looking at the output from the _setup.py_
>step to identify where the LoFASM executables have been stored. In the image above, the lines beginning with 'changing mode of' state the location of the executable LoFASM scripts. 
>
>![Alt text](/Users/louis/Documents/programming_sandbox/python/lofasm/docs/images/install_output_execs.png "lofasm executables")
>
>Once you've identified where the executables have been stored then make sure 
>the directory is in your path. 
> Use `echo $PATH` to view your current path (in BASH).


## LoFASM Executables
In this section I will list the LoFASM Executables and how to use them. 

_Note:	some of the executables in the lofasm directory are no longer used. They will soon be completely dropped. That being said, I will not be mentioning them any further in this document._

### lofasm\_plot.py
The _lofasm\_plot.py_ animates all channels from LoFASM Data in .lofasm 
format. This script can also scan .lofasm files and check them for errors and 
identify corrupt integrations.

> Usage: lofasm\_plot.py -f filename [options]
> 
> Access the help menu using `lofasm_plot.py -h`:
> 
> ![Alt text](/Users/louis/Documents/programming_sandbox/python/lofasm/docs/images/lofasm_plot_help.png "lofasm_plot.py help menu")
> 
> The only flag that _lofasm\_plot.py_ requires is `-f`, which points to 
> the LoFASM data file to be plotted. _The only exception to this is when the `-h` flag is used; this flag causes the program to print the help menu and exit. All other options are ignored._ 
> 
> Using _lofasm\_plot.py_ without any options will simply result in an 
> animated plot of the LoFASM data that the plotter is pointed to.
> 
> `lofasm_plot.py -f 20150328_210002.lofasm`
> 
> ![Alt text](/Users/louis/Documents/programming_sandbox/python/lofasm/docs/images/data_plot.png "lofasm_plot.py data plot")
> 
> When the end of the file is reached the plotter will simply stop and wait 
> until the plot window is manually closed.
> 
> #### about the plot
> _lofasm\_plot.py_ produces a figure with 11 different plots. 
> The smaller plots represent the auto and cross correlations of the 
> four LoFASM trunk lines. The four along the diagonal (INS, IEW, ONS, & OEW) 
> are the auto correlations (self-power) in each of the four LoFASM signals. 
> The other plots (above the diagonal) are the cross-powers.
> 
> The larger plot labeled 'All Channels' contains the auto-correlations plotted 
> over each other.
> 
> The x-axis and y-axis are frequency and power in all of the plots.
> 
> #### axis limits
> To change the limits on either axis use any combination of the `--xmin`, 
> `-->xmax`, `--ymin`, and `--ymax` options. xmin and xmax refer to the minimum
> and >maximum limits to the x-axis, respectively. ymin and ymax refer to the 
> minimum and maximum limits to the y-axis, respectively.
> 
> #### start position of data
> To force _lofasm\_plot.py_ to start reading data from a particular 
> place in the file either `-s` or `--start_position`. The position must 
> be given in bytes.
> 
> `lofasm_plot.py -f 20150328_210002.lofasm -s 96`
> 
> If _lofasm\_plot.py_ cannot read the first LoFASM integration 
> when initializing then an IntegrationError will be raised and 
> the program will attempt to exit cleanly.


### lofasm-chop.py
_lofasm-chop.py_ is designed to scrape a little bit of data off the top of a large file for data health checking. Instead of downloading a 20GB data file just to discover that the data is not healthy, _lofasm-chop.py_ can be used to 'sample' a .lofasm file.

All you have to do is tell lofasm-chop.py how many bytes of data (not including the file header, which gets transferred over automatically) you want to 'scrape off the top'. Optionally, an output filepath can be provided.

> Usage: lofasm-chop.py [-h] [-b B] [-o O] filename
> 
> The help menu can be accessed with `lofasm-chop.py -h`.
> 
> ![Alt text](/Users/louis/Documents/programming_sandbox/python/lofasm/docs/images/lofasm_chop_help.png "lofasm-chop.py help menu")
> 
> To copy the first 10 integrations from file _20150328\_210002.lofasm_ and 
> save them in a new file called _20150328\_210002\_chop.lofasm_ use 
> `lofasm-chop.py -b 1392640 -o 20150328_210002_chop.lofasm 20150328_210002.lofasm`
> 
> The `-b` flag accepts the number of _data_ bytes to be copied. Each LoFASM 
> integration is 139264 bytes long. In the example above, I am sampling the first 10 LoFASM integrations in _20150328\_210002.lofasm_.
> 
> The `-o` flag takes a path to the location of the new file to be created.


### simulate\_signal\_as\_AA.py
_simulate\_signal\_as\_AA.py_ uses the simulate subpackage to 
simulate LoFASM data. 

This script is meant to be used as a template for future data simulation.
Currently this script will generate a square wave and inject the signal into 
the AA channel of an other wise 'zeroed out' LoFASM data file. 

> Usage: simulate\_signal\_as\_AA.py [-h] [-p PERIOD] [-t DURATION] -f FILENAME
> 
> ![Alt text](/Users/louis/Documents/programming_sandbox/python/lofasm/docs/images/simulate_help_menu.png "simulate_signal_as_AA.py help menu")
> 
> There are only three pieces of input needed for this script. 
> 
> `-f`: path to where the simulated signal should be saved
> 
> `-p`: the period of the simulated square wave in seconds.
> 
> `-t`: the total duration of the simulated data set in seconds.


## LoFASM API
The LoFASM API is a Python package written to read and write LoFASM data.

### Package Structure
	
	lofasm
	|--simulate
	|	|--data.py
	|	`--signal.py
	|--animate_lofasm.py
	|--filter.py
	|--future.py
	|--mkid.py
	|--parse_data.py
	|--parse_data_H.py
	|--roach_comm.py
	`--write.py

### Package Conents Description
#### lofasm.simulate subpackage
The _simulate_ subpackage has two modules: _data_ & _signal_.
##### simulate.data
The class definitions in this module provide the framework to write 
filterbank data to disk in the .lofasm format. 

##### simulate.signal
This module contains functions that either generate or facilitate the 
generation of signals in LoFASM filterbank data format.

###### signal.square_wave
usage: s, t = square_wave(f[, fsamp][, T][, offset])
_f_ is the frequency of the signal in Hz.

_fsamp_ is the sampling frequency in Hz.

_T_ is the length of the data in seconds.

_offset_ is the phase offset in radians.

return numpy array with square wave

#### lofasm modules
##### animate\_lofasm.py
The _animate\_lofasm.py_ module is meant to provide functions and constants
to be used for animation purposes.
###### module attributes
_animate\_lofasm.FREQS_
> defined using numpy as `FREQS = np.linspace(0, 200, 2048)`.
> The _FREQS_ attribute is used as the x-axis array when plotting 
> LoFASM filterbank data.

_animate\_lofasm.autos_

> definition: `autos=['AA', 'BB', 'CC', 'DD']`
> 
> A Python list containing the labels of the auto-correlation plots. Each element is a string.

_animate\_lofasm.cross_

> definition: `cross = ['AB','AC','AD','BC','BD','CD']`
> 
> A Python list containing the labels of the cross-correlation plots. 
> Each individual element is a string.

_animate\_lofasm.beams_

> definition: `beams = ['NS', 'EW']`
> 
> A Python list containing the labels of the two LoFASM beam polarizations.
> This is not currently being used since there is a bug in the 
> current version of the tools affecting beam generation.

_animate\_lofasm.BASELINE\_ID_

> A Python dictionary containing the labeling of the trunk lines for each 
> LoFASM site. This dictionary is how the LoFASM Tools interpret the LoFASM 
> polarizations. 
> 
> Each element in this dictionary is itself a dictionary as well. 
> These 'second layer' dictionaries hold the labels themselves.
> 
> Legend: 
> 		INS: Inner North-South
> 		ONS: Outer North-South
> 		IEW: Inner East-West
> 		OEW: Outer East-West
> 
> The available LoFASM baseline arrangements are: 'LoFASMI', 'LoFASMII', 
> 'LoFASM3', 'LoFASMIV', & 'simdata'.
> 

_animate\_lofasm.BASELINES_

> A Python list containing both the auto-correlation and cross-correlation labels.
> 
> Definition: `BASELINES = ['AA', 'BB', 'CC', 'DD', 'AB', 'AC', 'AD', 'BC', 'BD', 'CD']`


###### module methods
*animate\_lofasm.setup\_all\_plots(xmin, xmax, ymin, ymax, station, crawler [, norm\_cross=False])*

> Docstring: setup all auto and cross-power plots
> 
> Create necessary figure plots in proper arrangement and 
> return the corresponding matplotlib line objects
> 
> _xmin_, _xmax_, _ymin_, and _ymax_ are used for limits on the plot axes. The 
> x-axes is frequency (MHz) and the y-axis is power (dB).
> 
> The _station_ argument is one of the baseline arrangments (as a string) accepted 
> by _animate\_lofasm.BASELINE\_ID_.
> 
> _crawler_ is an instance of _lofasm.parse\_data.LoFASMFileCrawler_. 
> Refer to the documentation of the _lofasm.parse\_data_ module for more 
> information on the LoFASM file crawler class.
> 
> The optional argument _norm\_cross_ is deprecated and no longer used. 
> It is left in this definition for compatiblity purposes but will soon 
> be done away with.

_animate\_lofasm.update\_all\_baseline\_plots(i, fig, crawler, lines [, norm\_cross] [, forward])_

> Update all plots created by _animate\_lofasm.setup\_all\_plots_ by incrementing 
> the file crawler to the next LoFASM integration and replacing the matplotlib 
> line object data arrays. Iterating this function using the Matplotlib animation
> library will animate the LoFASM plots as a function of time.
> 
> The _i_ argument is an integer. It does not matter what integer is placed here. 
> This argument is required by the Matplotlib animation module. _i_ will be incremented
> in between iterations by matplotlib's _FuncAnimation_ function.
> 
> _fig_: a matplotlib figure object representing the figure that contains the LoFASM 
> plots.
> 
> _crawler_: an instance of _lofasm.parse\_data.LoFASMFileCrawler_. 
> Refer to the documentation of the _lofasm.parse\_data_ module for more 
> information on the LoFASM file crawler class.
> 
> _lines_: a Python list of matplotlib 2D line objects used in the LoFASM plots. 
> 
> _norm\_cross_: This is a **deprecated** argument. It is being kept in this 
> definition for compatibility purposes. This will soon be removed.
> 
> _forward_: boolean argument. If True then increment the crawler by a single
> integration before updating plots. If False, then leave crawler where it 
> is but still update all plot data arrays.

##### filter.py

> A Python library for LoFASM filtering methods.
> 
> Available filters:
> _filter.running\_median(y [, N])_
> 
> Docstring: 
> 	  Given a list, y, perform a running median filter.
>    Return the resulting list.
>
>    N is the total number of points to be considered for the
>    running median. The default is 50, so for any point X(n)
>    the values considered will be [X(n-25),X(n+25)], inclusive.
>
>    If N is not an even number then it will be changed to
>    even number N-1.
>
>    If N is not an integer it will be truncated.

##### future.py

>Classes and function definitions that need a home.
>The methods and classes in this file were written to 
>accomplish a certain task at a certain time but did 
>not truly get integrated into the LoFASM tools.
>
>If needbe these will be fully integrated into 
>dedicated libraries at some point in the future.
>
>class _future.ComparableMixin_:
>>This class can be inherited to facilitate comparing 
>>class instances to each other. This allows for the use 
>>of the <,>,==, <=, and >= operators between the instances 
>>of two future.ComparableMixin child classes.
>>
>>This class is derived from _object_.
>>
>>Child classes __must__ have a _cmpkey attribute in order
>>to use future.ComparableMixin capabilities.
>
>class _LoFASM\_file_:
> 
>>
>>function _get\_total\_file\_size(fname)_:
>>> Description: Return total file size in bytes. 
>>> 
>>> If _fname_ points to a regular file then use
>>> _future.syscmd_ to retrieve file's total size 
>>> in bytes by parsing the output of `ls -l <fname>`.
>
>>function _syscmd(cmd)_:
>>>Description: execute Linux _cmd_ as a subprocess 
>>>and catch output.
>>>
>>>_cmd_ is a string containing a Linux command.
>
>>function _file\_datetime(filename)_:
>>>Description: return datetime.datetime object from filename
>>>
>>>_filename_ is a string containing the name of a .lofasm file as 
>>>labeled by the LoFASM Data recorder.
>>>
>>>Returns a datetime.datetime object representing the 
>>>timestamp in the filename.

##### mkid.py

> Library for parsing FPGA snapshots. Written by the CASPER community.

##### parse\_data.py

>Module for parsing LoFASM Data
>
>function _getSampletime (Nacc)_
>
>> Docstring: Return the sample time corresponding to the number of accumulations, Nacc.
>> 
>> _Nacc_ can be either an integer or a float.
>
>function _freq2bin (freq)_
>
>> Docstring: Return bin number corresponding to frequency freq
>> 
>> Returns an integer bin number. 
>> 
>> _freq2bin_ will calculate a bin number by dividing _freq_ 
>> by the resolution bandwidth, which is defined by `rbw = 200.0/2048`, 
>> and casting the result as an _int_.
>
>function _bin2freq (bin)_
>> Return frequency (MHz) corresponding to _bin_.
>> 
>> This is the opposite of _freq2bin_. 
>> 
>> _bin_ should be an integer.
>> 
>> The frequency is calculated by multiplying _bin_ by _rbw_ 
>> (see _freq2bin_ for information on how _rbw_ is defined).
>
>function _parse\_filename (filename)_
>
>> return the file's UTC time stamp as a list [YYmmdd, HHMMSS, pol]
>> 
>> _filename_ is a string containing the name of a LoFASM data file.
>> _filename_ does not need to actually point to a regular file. 
>> The UTC time stamp is obtained from the filename string itself.
>> 
>> It is important that the LoFASM filename be in the format that 
>> it was originally saved in.
>> 
>
>function *fmt\_header\_entry (entry\_str [, fmt\_len])*
>
>> Ensure that every header entry is _fmt\_len_ characters long. If longer, then
>> truncate. If shorter, then pad with white space. 
>> 
>> returns formatted string
>
>function _parse\_file\_header (file\_obj [, fileType])_
>
>> Read LoFASM file header using file\_obj.read() and return 
>> parsed information as a Python dictionary. 
>> 
>> This function preserves _file\_obj_'s file pointer location. 
>> 
>> _file\_obj_ should be a valid Python File Object
>> 
>> _fileType_ is optional and contains a string of recognized file extensions.
>> Currently, the only file extension recognized is _.lofasm_.
>
>function _parse\_hdr (hdr [, hdr\_size\_bytes] [,version])_
>
>> Parse integration header and return corresponding header dictionary
>> 
>> Usage: parse_hdr (<64bit\_string> [, version])
>> 
>> Docstring:
>> Parse the first 64 bits of a LoFASM data packet and return 
>> a dictionary containing ech header value.
>> 
>> If _hdr_ has a length greater than 8 bytes then it will be truncated 
>> and only the first 8 bytes will be parsed; everything else will be ignored.
>
>function _print\_hdr (hdr\_dict)_
>
>> Iterate through a header dictionary and print all fields and their values to 
>> the screen.
>> 
>> _hdr\_dict_ should be a dictionary as returned by _parse\_file\_header or 
>> _parse\_hdr_.
>
>function *check\_headers (file\_obj [, packet\_size\_bytes] [, verbose] [, print\_headers])*
>
>> Iterate through LoFASM Data file and check that all the header packets
>> are in place. 
>> 
>>> Note: The _verbose_ keyword argument is no longer used. 
>>> It is being left in the definition for now for compatibility purposes. 
>> 
>> Returns a tuple (_best\_loc_, _err\_counter_), 
>> where _best\_loc_ and _err\_counter_ are the best data start position 
>> and the number of bad integrations in the file, respectively.
>> 
>> _packet\_size\_bytes_ is the size of a LoFASM Network packet in bytes. 
>> The default value is 8192 and the data type should be int.
>> 
>> _print\_headers_ is a boolean argument. If set to True then print out 
>> all integration header information while scanning the file.
>
>function _get\_filesize (file\_obj)_
>
>> Usage: get\_filesize(file\_obj)
>> 
>> Returns file size, in bytes, of file pointed to by _file\_obj_.
>> _file\_obj_ must be a valid Python file object.
>> 
>> File size is calculated by using the file object's _seek_ function 
>> to navigate to the last byte in the file and retrieve the location 
>> of the file using the file object's _tell_ function.
>
>function _get\_number\_of\_integrations (file\_obj)_
>
>> Returns the number of LoFASM integrations in a .lofasm file. 
>> The return value is of type _float_.
>> 
>> The number of integrations is calculated using _get\_filesize_ to obtain 
>> the size of the file in bytes and divide it by the integration size.
>
>function *get\_next\_raw\_burst (file\_obj [, packet\_size\_bytes] [,packets\_per\_burst] [, loop\_file])*
>
>> Usage: get\_next\_raw\_burst(<file_object> [, packet_size_bytes] [, packets_per_burst] [, loop_file]) 
>> 
>> Python generator that yields a string containing data from the next 17
>> LoFASM packets in _file\_obj_ that make up a single 'burst'. 
>> If file_obj's pointer is not at zero, then assume it is in the desired
>> start position and begin reading from that point in the file.
>
>function _find\_first\_hdr\_packet (file\_obj [, packet\_size\_bytes] [, hdr\_size])_
>
>> Return start location of the first valid header packet in file.
>> 
>> _file\_obj_ is a Python file object.
>> 
>> The optional parameters, _packet\_size\_bytes_ & _hdr\_size_, 
>> must both be integers. Their default values are 8192 & 96, respectively. 
>
>function _is\_next\_packet\_header (file\_obj [, packet\_size\_bytes] [, hdr\_size\_bytes])_
>
>> Check if the next LoFASM packet is a header packet.
>
>class _LoFASM\_burst_
>
>> Class to represent an entire LoFASM burst sequence.
>> A LoFASM burst is a collection of 17 User Datagram Protocol (UDP) 
>> packets in a particular order.
>> 
>> The first of these packets is always the header packet.
>> The following 16 network packets contain raw LoFASM filterbank data.
>> 
>> All network packets have the same dimensions and are the same length.
>> 
>> 
>> _self.autos_: 
>> 
>>> A dictionary containing the LoFASM auto-correlation
>>> channels.
>> 
>> _self.cross_: 
>> 
>>> A dictionary containing the LoFASM cross-correlation
>>> channels.
>> 
>> _self.beams_: 
>> 
>>> A dictionary containing both polarizations of 
>>> the LoFASM beams. **Note: this dictionary is not created until 
>>> _self.create\_LoFASM\_beams_ is executed.**
>> 
>> _self.pack\_binary (self, spect)_:
>> 
>>> Convert filterbank data into writable binary string format.
>>> 
>>> Usage: pack\_binary (spect)
>>> 
>>> Returns: A binary string containing the filterbank data
>>> 
>>> The data type of the information stored in spect 
>>> must correspond to one of the data types used in 
>>> LoFASM bursts. (int, np.complex, or np.float64)
>>> 
>>> all elements in spect must be of the same type.
>> 
>> _getAutoCorrelationDataType (self)_:
>> 
>>> Return the data type used for auto correlation data.
>> 
>> _getCrossCorrelationDataType (self)_:
>> 
>>> Return the data type used for cross correlation data.
>> 
>> _getBeamDataType (self)_:
>> 
>>> Return the data type used for LoFASM beam data.
>> 
>> _create\_LoFASM\_beams (self)_:
>> 
>>> Generate both LoFASM beams and store them as class attributes.
>>> 
>>> This function will create the dictionary _self.beams_.
>
>class _LoFASMFileCrawler_
>
>> File crawler for LoFASM data files.
>> 
>> Usage: LoFASMFileCrawler(filename [, scan_file] [, start_loc])
>> 
>> Where _scan\_file_ is a boolean value. If True then scan and print 
>> all integration headers in file. This is an optional argument.
>> 
>> _start\_loc_ is the starting location of the data in the file. 
>> If _start\_loc is set then _scan\_file_ will be ignored and the 
>> crawler will be initiated at the given _start\_loc_.
>> 
>> 
>> function _forward (self [, N])_:
>> 
>>> Move forward by N integrations. Default is 1.
>>
>> function _backward (self [, N])_:
>> 
>>> Move backward by N integrations. Default is 1.
>> 
>> function _reset (self)_:
>> 
>>> Move back to first integration in file.
>> 
>> function _getIntegrationHeader (self)_:
>>
>>> Return integration header information as a dictionary.
>> 
>> function _getFileHeader (self)_:
>>
>>> Return LoFASM file header info as a dictionary.
>> 
>> function _getAccNum (self)_:
>> 
>>> Return LoFASM accumulation number of current integration.
>> 
>> function _getAccReference (self)_:
>> 
>>> Return reference accumulation number. This is the the accumulation 
>>> number corresponding to the first valid integration.
>> 
>> function _getFilePtr (self)_:
>> 
>>> Return file pointer location.
>> 
>> function _getIntegrationSize (self)_:
>> 
>>> Return the size of a LoFASM integration in bytes.
>> 
>> function _getFilename (self)_:
>> 
>>> Return the filename of the current LoFASM file.
>> 
>> function _print\_int\_headers (self [, state])_:
>>
>>> If _state_ is True then print integration headers after 
>>> every transition. This will print integration header 
>>> information after every _forward()_, _backward()_, and _reset()_ 
>>> command.
>>> 
>>> If _state_ is None then simply print current 
>>> integration header.
>> 

##### parse\_data\_H.py

>Constants and Error Classes 
>
>_LoFASM\_FHEADER\_TEMPLATE_:
>
>> Dictionary containing the accepted LoFASM header templates.
>
>_LoFASM\_SPECTRUM\_HEADER\_TEMPLATE_:
>
>> Dictionary containing the accepted LoFASM integration header templates.
>
>class _Header\_Error_:
>
>> Error class for bad header issues.
>
>class _IntegrationError_:
>
>> Error class for bad LoFASM integrations.

##### roach\_comm.py

>Library for functions that require talking to the ROACH Board
>
>function _connect\_roach()_:
>
>> Connect to roach board and return the fpga handle.
>> 
>> The ROACH board's IP address must be stored as environement 
>> variable 'ROACH_IP'. If the environment variable is not set 
>> then the default, `192.168.4.21`, will be used.
>> 
>> the fpga handle is an instance of corr.katcp\_wrapper.FpgaClient
>> 
>> once the fpga handle is received, the roach connection can be 
>> confirmed by looking at the output of `fpga.is_connected()`.
>
>function _getSampletime (Nacc)_:
>
>> Return the ROACH board's sampling time.
>
>function _getRoachAccLen ()_:
>
>> Return the value of the ROACH register 'acc\_len'
>
>function _getNumPacketsFromDuration (obs\_dur)_:
>
>> Return the integer number of network packets corresponding to 
>> an interval of time.
>>

##### write.py

>Methods for writing LoFASM Data to disk
>
>
>function _fmt\_header\_entry (entry\_str [, fmt\_len])_:
>
>> Ensure that every header entry is fmt\_len characters long.
>> If longer, then truncate. If shorter, then pad with white space. 
>> The resulting formatted string is then returned.
>
>function _write\_header\_to\_file (outfile, host [, Nacc] [, fpga\_clk\_T]
> [, Nchan] [, fileNotes])
>
>> Prepends data file with LoFASM spectrometer header.
>> _fpga\_clk\_T_ is the period of the FPGA clock in seconds.
>> _Nchan_ is the number of FFT bins in the spectrometer data.
>> _Nacc_ is the number of accumulations averaged over before dumping 
>> each integration.

