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
latest_files = future.get_spectra_range(now - buffer_time, now, data_home)

#get list of files in recent directory
ls_recent = os.listdir(data_recent)
for item in ls_recent:
    if item[-7:] != '.lofasm':
        #remove non-lofasm files
        ls_recent.remove(item)
    else:
        ls_recent[ls_recent.index(item)] = future.LoFASM_file(data_recent+'/'+item)

ls_recent.sort()
ls_recent.reverse() #get latest files first


for f in ls_recent:
    if f in latest_files:
        latest_files.remove(f)
    else:
        #remove file from recent directory
        rm_cmd = 'rm -f %s' % (f.parent+'/'+f.name)
        #print rm_cmd
        syscmd(rm_cmd)

        
for latest_file in latest_files:
    if latest_file in ls_recent:
        #file is already in recent directory
        print "leave-alone: %s" % (latest_file.name)
        pass
    else:
        #file needs to placed in the recent directory
        print "copying %s" % latest_file.parent+'/'+latest_file.name
        cp_cmd = 'cp %s %s' % (latest_file.parent + '/' + latest_file.name, data_recent+'/.')
        #print cp_cmd
        syscmd(cp_cmd)


