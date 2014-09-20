from lofasm import parse_data as pdat
from lofasm import future
from lofasm.future import syscmd

import os
import datetime


data_home = os.environ['LOFASMDATA_HOME']
data_recent = os.environ['LOFASMDATA_RECENT']

buffer_time = datetime.timedelta(hours = 24)
now = datetime.datetime.utcnow()

#get latest lofasm files
files_to_copy = future.get_spectra_range(now - buffer_time, now, data_home)

#get list of files in recent directory
listdir = os.listdir(data_recent)
listdir.sort()
listdir.reverse() #get latest files first

recent_files = []

for item in listdir:
    if item[-7:] == '.lofasm':
        recent_files.append(future.LoFASM_file(data_recent+'/'+item))
    else:
        #prune non-lofasm files
        print "pruning %s " % item
        rm_cmd = "rm -f %s" %( data_recent + '/' + item)



for f in recent_files:
    if f in files_to_copy:
        #already copied
        files_to_copy.remove(f)
    else:
        #remove file from recent directory
        rm_cmd = 'rm -f %s' % (f.parent+'/'+f.name)
        print rm_cmd
        syscmd(rm_cmd)

        
for latest_file in files_to_copy:
    if not isinstance(latest_file,future.LoFASM_file):
        print "ignoring", latest_file
        pass
    if future.get_total_file_size(latest_file) < 100:
        print "file too small"
        pass
    else:
        #file needs to placed in the recent directory
        print "copying %s" % latest_file.parent+'/'+latest_file.name
        cp_cmd = 'cp %s %s' % (latest_file.parent + '/' + latest_file.name, data_recent+'/.')
        print cp_cmd
        syscmd(cp_cmd)


