import parse_data as pdat
import datetime
import os
import subprocess
##to be implemented in the future


##future##

class ComparableMixin(object):
    def _compare(self, other, method):
        try:
            return method(self._cmpkey(), other._cmpkey())
        except (AttributeError, TypeError):
            #no _cmpkey() or wrong type
            return NotImplemented

    def __lt__(self, other):
        return self._compare(other, lambda s,o: s < o)
    def __le__(self, other):
        return self._compare(other, lambda s,o: s <= o)
    def __eq__(self, other):
        return self._compare(other, lambda s,o: s==o)
    def __gt__(self, other):
        return self._compare(other, lambda s,o: s > o)
    def __ge__(self, other):
        return self._compare(other, lambda s,o: s <= o)
    def __ne__(self, other):
        return self._compare(other, lambda s,o: s != o)
    
class LoFASM_file(ComparableMixin):
    def __init__(self, pathtofile):
        if os.path.isdir(pathtofile):
            print "please provide a full path."
            pass
        elif not os.path.isfile(pathtofile):
            print pathtofile + " is not a normal file"
            pass
        else:
            if len(pathtofile.split('/')) > 1:
            #set parent directory
                splitpath = pathtofile.split('/')
                filename = splitpath[-1]
                
                if pathtofile[0] == '':
                    path_to_parent = '/'
                else:
                    path_to_parent = ''

                    
                for i in range(len(splitpath) - 1):
                    if i == 0:
                        path_to_parent += splitpath[i]
                    else:
                        path_to_parent = path_to_parent + '/' + splitpath[i]

                self.parent = path_to_parent
            else:
                filename = pathtofile
                self.parent = os.getcwd()
              
            self.name = filename
            
            self.date = file_datetime(self.name)
            self._file_obj = None
            self._startPos = None
            self._burstGenerator = None

    def _cmpkey(self):
        #key for rich comparisons
        return self.date
    
    def _openFile(self):
        self._file_obj = open(self.parent + '/' + self.name, 'rb')
    
    def getFileHdr(self):
        if self._file_obj:
            return pdat.parse_file_header(self._file_obj)
        else:
            self._openFile()
            return self.getFileHdr()
    
    def getFileObj(self):
        if not self._file_obj:
            self._openFile()
        return self._file_obj
            
    def get_local_list(self):
        self.local_list = []
        for item in os.listdir(self.parent):
            if item[-7:] == '.lofasm':
                self.local_list.append(item)
        self.local_list.sort()
        return self.local_list

    def getFileSize(self):
        '''return total file size in bytes'''
        return get_total_file_size(self.parent + '/' + self.name)

    def _getBurstGenerator(self):
        if self._burstGenerator:
            return self._burstGenerator
        #otherwise
        fileHdr = self.getFileHdr()
        if not self._startPos:
            self._file_obj.seek(fileHdr[3][1])
        else:
            assert(type(offset) == int)
            self._file_obj.seek(offset)
        self._burstGenerator = pdat.get_next_raw_burst(self._file_obj)
        return self._getBurstGenerator()
    
    def getNextIntegration(self):
        bgen = self._getBurstGenerator()
        return bgen.next()

def get_total_file_size(fname):
    if not os.path.isfile(fname):
        print "bad file name"
        return None
    else:
        size_cmd = "ls -l %s | awk '{print $5}'" % fname
        return int(syscmd(size_cmd).rstrip('\n'))

def syscmd(cmd):
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
    (output, err) = proc.communicate()
    if err:
        print "Error executing system command:",
        print cmd
    return output
         
def file_datetime(filename):
    """return datetime.datetime object from filename"""

    ##check if lofasm file
    if filename == '' or len(filename) < 22:
        pass
    elif filename[-7:] != '.lofasm':
        print "What is this?"
        pass
    else:
        filename = filename.rstrip('.lofasm')
        date, time = filename.split('_')

        year = int(date[:4])
        month  = int(date[4:6])
        day = int(date[6:8])
        hour = int(time[:2])
        minute = int(time[2:4])
        second = int(time[4:6])
        
        if (len(date+time) < 14):
            print "can't parse file's date :("
            pass
        else:
            return datetime.datetime(year, month, day, hour, minute, second)

def get_spectra_range(start_date, end_date, data_home=''):
    if data_home == '':
        data_home = os.environ['LOFASMDATA_HOME']

    file_buffer = []

    #now = datetime.datetime.now()
    #now = datetime.datetime(2014,8,2)
    print "Start: ", start_date
    buffer_start = start_date
    print "Buffer start: ", buffer_start
    print "Buffer length: ", end_date - start_date

    file_ext = '.lofasm'
    dir_list = []
    for item in os.listdir(data_home):
        year = None
        try:
            year = int(item)
        except ValueError as err:
            #print "could not get year from %s, skipping!" % item
            pass

        if year:
            dir_list.append(item)


    dir_list.sort()

    dir_list.reverse() #latest directory first

    for dir in dir_list:
        #print "opening %s" % dir
        year = int(dir[:4])
        month = int(dir[4:6]) 
        day = int(dir[6:8]) 

        dir_date = datetime.datetime(year, month, day)
        #print "dir_date: ", dir_date

        if datetime.date(dir_date.year,dir_date.month,dir_date.day) < datetime.date(buffer_start.year, buffer_start.month, buffer_start.day):
            #print "moving on to next directory"
            #print dir_date, " is before ", buffer_start
            #move on to next directory
            pass
        else:
            #print "sifting through lofasm files"
            local_files = []
    
            for item in os.listdir(data_home + '/' + dir):
                if item[-7:] == file_ext:

                    item_date = file_datetime(item)
                
                    local_files.append(item_date)
            local_files.sort()
            local_files.reverse() #latest files first

            for fdate in local_files:
                fyear = str(fdate.year)
                fmonth = str(fdate.month) if fdate.month > 9 else '0'+str(fdate.month)
                fday = str(fdate.day) if fdate.day > 9 else '0'+str(fdate.day)
                fhour = str(fdate.hour) if fdate.hour > 9 else '0'+str(fdate.hour)
                fmin = str(fdate.minute) if fdate.minute > 9 else '0'+str(fdate.minute)
                fsec = str(fdate.second) if fdate.second > 9 else '0'+str(fdate.second)
                pathToFile = data_home + '/' + dir + '/' + fyear + fmonth + fday + '_' + \
                    fhour + fmin + fsec + file_ext
            
            
                lofasm_file = LoFASM_file(pathToFile)
    
                if lofasm_file.date >= buffer_start:
                    if lofasm_file.getFileSize() > 100: #weed out bad files
                        #print "Adding %s" % lofasm_file.name
                        file_buffer.append(lofasm_file)

    return file_buffer
