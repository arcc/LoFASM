#! /usr/bin/python2.7

SCHED_DIR = "/home/controller/sched/"
SCHED_PROG = "/home/controller/bin/rec_target.sh"
LOG_DIR = "/home/controller/logs/"
LOG_FILE = LOG_DIR + "lofasm.log"
LOG_LIMIT = 10000 #line limit

if __name__ == "__main__":
    '''
    This LoFASM Scheduler is designed to be executed
    one hour before each UTC day. The scheduler will 
    schedule any observations for the upcoming UTC day.
    '''
    
    import os
    import logging
    from datetime import datetime, timedelta
    from subprocess import check_output

 #   with open(LOG_FILE) as log:
 #       if len(log.readlines()) >= LOG_LIMIT:
            #create new file
 #       else:
            #stay in this file


    #start logger
    logger = logging.getLogger("LoFASM Scheduler")
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler(LOG_FILE)
    log_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(log_formatter)
    logger.addHandler(fh)

    #get current UTC date
    dayOffset = timedelta(days=1)
    utcToday = datetime.utcnow().date()
    #get next UTC day
    utcTomorrow = utcToday + dayOffset
    
    utcDir = SCHED_DIR + utcTomorrow.strftime("%Y%m%d") + '/'
    
    logger.info("Scheduling jobs in " + utcDir)
    
    try:
        jobFiles = []
        for f in os.listdir(utcDir):
            if f.endswith('.lsf'):
                jobFiles.append(utcDir + f)
            else:
                pass

        for job in jobFiles:
            with open(job, 'r') as j:
                fields = {}
                lines = j.readlines()
                for l in lines:
                    lsplit = l.split()
                    print lsplit
                    if len(lsplit) > 2:
                        pass
                    else:
                        fields[lsplit[0]] = lsplit[1].rstrip('\n')
                
                sched_cmd = "at %s:%s %s/%s/%s -f %s" % (
                    fields['ObsStart'][:2],
                    fields['ObsStart'][2:4],
                    fields['ObsDate'][4:6],
                    fields['ObsDate'][-2:],
                    fields['ObsDate'][:4],
                    SCHED_PROG)
                
                logger.info('Adding job to Queue:')
                logger.info("ra: %s\tdec: %s" % (fields['RA'], fields['DEC']))
                logger.debug("cmd: %s" % sched_cmd)
                sys_output = check_output(sched_cmd.split())
                
                
    except OSError as err:
        print err.strerror, ': ', err.filename
        exit()

    
