#!/usr/bin/python
import parse_data as pdat
import numpy as np
import struct
import os
import datetime
import lofasm_dat_lib as lofasm
def get_avg_pow_in_range(fname, start_bin, end_bin, baseline):
    '''determines average power in specified range of frequency
    bins. does *not* include the end bin in calculation.'''

    print "\nOpening ", fname.split('/')[-1]
    if end_bin < start_bin:
        #swap order
        a = end_bin
        end_bin = start_bin
        start_bin = a
        del a
    bins = np.arange(start_bin, end_bin)
    total_power = 0
    for bin in bins:
        print "Acquiring bin: ", bin 
        total_power += get_avg_pow(fname, bin, baseline)
    avg_pow = total_power/float(len(bins))
    return avg_pow

def get_avg_pow(fname, bin, baseline):
    '''scans all integrations in fname and returns the mean power
    in the specified frequency bin. '''

    fileDate, fileTime = pdat.parse_filename(fname)
    file_obj = open(fileDate + '/' + fname, 'rb')
    

    hdr_dict = pdat.parse_file_header(file_obj)
    file_obj.seek(int(hdr_dict[3][1])) #move ptr past file header
    burst_gen = pdat.get_next_raw_burst(file_obj)
    

    num_bins = int(hdr_dict[5][1])
    #bin = int(pdat.freq2bin(freq))

    #print 'Frequency: %3.0f MHz has been mapped to bin %i' % (freq, bin)
    num_integrations = pdat.get_number_of_integrations(file_obj)
    #num_vals = num_bins * num_integrations
    
    pow_sum = 0
    
    for i in range(num_integrations):
        data_int = lofasm.LoFASM_burst(burst_gen.next())
        if opts.baseline in data_int.autos.keys():
            pow_sum += data_int.autos[opts.baseline][bin]
        elif opts.baseline in data_int.cross.keys():
            pow_sum += data_int.cross[opts.baseline][bin]

    pow_avg = pow_sum / np.float(num_integrations)


    file_obj.close()
    return pow_avg



def get_file_list(fNameStart, fNameStop, root_dir = os.getcwd()):
    startDate, startTime = pdat.parse_filename(fNameStart)
    stopDate, stopTime = pdat.parse_filename(fNameStop)

    #dir_listing = os.listdir(root_dir)

    if startDate == stopDate:
        file_listing = os.listdir(startDate)
        startFileIndex = file_listing.index(fNameStart)
        endFileIndex = file_listing.index(fNameStop)

        #only consider files within our desired time frame
        file_listing = file_listing[startFileIndex:endFileIndex+1]

    elif int(startDate) > int(stopDate):
        print "Swapping order of start and end points!"
        #swap start and end filenames
        x = fNameStart
        fNameStart = fNameStop
        fNameStop = x
        del x
        file_listing = get_file_list3(fNameStart, fNameStop, root_dir)
    elif int(startDate) < int(stopDate):
        dir_listing = os.listdir(root_dir)
        startDateIndex = dir_listing.index(startDate)
        stopDateIndex = dir_listing.index(stopDate)
        dir_listing = dir_listing[startDateIndex:stopDateIndex+1]
        file_listing = []
        for date in dir_listing:
            if date == startDate:
                files_in_dir = os.listdir(date)
                startIndex = files_in_dir.index(fNameStart)
                file_listing.extend(files_in_dir[startIndex:])
            elif date == stopDate:
                files_in_dir = os.listdir(date)
                stopIndex = files_in_dir.index(fNameStop)
                file_listing.extend(files_in_dir[:stopIndex+1])
            else:
                file_listing.extend(os.listdir(date))

    return file_listing

if __name__ == "__main__":
    from optparse import OptionParser
    import matplotlib.pyplot as plt
    import sys

    p = OptionParser()
    p.set_usage('timelapse.py usage TBD.')
    p.set_description(__doc__)
    p.add_option('-s', dest='start_file', type='str', default=None,
                help='path to the first LoFASM file in timelapse.')
    p.add_option('-e', dest='end_file', type='str',
                help='path to the last LoFASM file in timelapse.')
    p.add_option('-f', dest='freq', type='float', default=None,
                help='frequency to plot over specified time.')
    p.add_option('--start_freq', dest='start_freq', type='float', default=None,
                help = 'start frequency (MHz)')
    p.add_option('--end_freq', dest='end_freq', type='float', default=None, help='end frequency (MHz)')
    p.add_option('-b', dest='baseline', type='str', default='AA', help='Choose a baseline to average & plot.')


    opts, args = p.parse_args(sys.argv[1:])

    #check input parameters
    if opts.start_file is None:
        print 'I need a starting place.'
        sys.exit()
    elif opts.end_file is None:
        print 'I need an ending place.'
        sys.exit()
    elif os.path.isdir(opts.start_file):
        print opts.start_file, " is not a regular LoFASM file."
        sys.exit()
    elif os.path.isdir(opts.end_file):
        print opts.end_file, " is not a regular LoFASM file."
        sys.exit()
    elif opts.freq is None and opts.start_freq is None:
        print "Choose a frequency (MHz) or range of frequencies to plot."
        sys.exit()

#############################################################################
    lofasm_file_list = get_file_list(opts.start_file, opts.end_file)
    startDateStamp, startTimeStamp = pdat.parse_filename(lofasm_file_list[0])
    startDateTime = pdat.get_datetime_obj(startDateStamp, startTimeStamp)

    pow_list = []
    time_list = []
    #if single freq bin then calculate power in that bin
    if opts.freq:
        for fname in lofasm_file_list:
            print fname
            bin = pdat.freq2bin(opts.freq)
            pow_list.append(get_avg_pow(fname, bin, opts.baseline))
            dateStamp, timeStamp = pdat.parse_filename(fname.split('/')[-1])
            currDateTime = pdat.get_datetime_obj(dateStamp, timeStamp)

            days_passed = (currDateTime - startDateTime).total_seconds() / 86400.0

            time_list.append(days_passed)
            print pow_list
            print time_list
    else:
        #if a frequency range is specified then calculate average power
        # in all enclosed bins
        startBin = int(pdat.freq2bin(opts.start_freq))
        endBin = int(pdat.freq2bin(opts.end_freq))
        print "averaging power from bin %i to %i" % (startBin, endBin)
        #print lofasm_file_list
        #raw_input()
        for fname in lofasm_file_list:
            print "iter: ", fname
            pow_list.append(get_avg_pow_in_range(fname, startBin, endBin, opts.baseline))
            dateStamp, timeStamp = pdat.parse_filename(fname.split('/')[-1])
            currDateTime = pdat.get_datetime_obj(dateStamp, timeStamp)
            days_passed = (currDateTime - startDateTime).total_seconds() / 86400.0

            time_list.append(days_passed)

            print pow_list
            print time_list
        #plt.plot(time_list, 10*np.log10(pow_list),'*')
    plt.plot(10*np.log10(pow_list), '*-')
    plt.grid()
    plt.show()
