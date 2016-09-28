#! /usr/bin/python2.7

import multiprocessing as mp
from datetime import datetime, timedelta
import socket, os, sys, gc
import time
from lofasm.write import write_header_to_file
from lofasm import config
import signal
import logging
from subprocess import call, check_call, CalledProcessError
from astropy.time import Time

#IP address & port to listen on
IP_ADDRESS = '192.168.4.5'
PORT = 60001

#packet info to listen for
#These config settings are superfluous and should be hardcoded
PACKETSIZE = config.PACKETSIZE
PACKETGROUPSIZE = config.PACKETGROUPSIZE

#lofasm station
STATION = config.STATION

#file to record log information
LOGFILE = config.LOGFILE

#Process ID file
PIDFILE = config.PIDFILE

#file containing current data disk ID
DISKFILE = config.DISKFILE

#file specifying duration of each data file
BLOCKFILE = config.BLOCKFILE


def listen(q, logger):
    '''
    LoFASM Listener
    
    Listening process. This function runs until manually killed.
    Listen and bind to the to ip address,port in the LoFASM config.

    raw UDP packets are collected as bitstrings in chunks. The size of
    each chunk will be 139264 bytes, or 136 kB.

    upon collection, each data chunk is added to a shared memory queue
    for the LoFASM Writer to obtain and write to disk.
    '''
    
    # save PID to file
    with open(PIDFILE, 'a') as f:
        f.write(str(os.getpid())+'\n')

    #log start message
    logger.debug('{} starting with pid {}'.format(
        mp.current_process(), os.getpid()))

    #network SOCKet setup. We are using raw datagram (UDP) packets.
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((IP_ADDRESS, PORT))

    #get data block time from the blockfile
    with open(BLOCKFILE, 'r') as f:
        block_time = f.read().strip()

    #log the current block time setting
    logger.info("{} BLOCKTIME: {} seconds".format(
        mp.current_process(), block_time))

    while True:
        gc.collect() #garbage collection...just to be sure

        #get data block start & end times
        blockstart = datetime.now()
        blockend = blockstart + timedelta(seconds=int(block_time))
        
        logger.info("{}: new block: {} - {}".format(
            mp.current_process(),
            blockstart.strftime("%Y/%m/%d %H:%M:%S"),
            blockend.strftime("%H:%M:%S")))

        block = ''
        while datetime.now() < blockend:
            for i in range(PACKETGROUPSIZE):
                try:
                    d = sock.recv(PACKETSIZE)
                except socket.error:
                    pass
                
                block += d
                del d #this could be slowing us down
                
        #place new data in shared memory queue
        q.put((blockstart, block)) 
        
        logger.info("{}: added {} MB to queue".format(mp.current_process(),
                    str(float(len(block))*2**-20)))
        del block #free memory
    return

def write(q, dirname, logger):
    dirname = dirname if dirname.endswith('/') else dirname + '/'

    with open(PIDFILE, 'a') as f:
        f.write(str(os.getpid())+'\n')

    logger.debug('{} starting with pid {}'.format(
        mp.current_process(), os.getpid()))

    while True:
        if not q.empty():
            gc.collect()
            #if queue not empty start grabbing data from the queue
            tstamp, data = q.get()

            try:
                fpath = dirname + tstamp.strftime("%Y%m%d_%H%M%S")+".lofasm"

                #open file & write header
                ofile = open(fpath, 'wb')
                write_header_to_file(ofile, STATION, Time(tstamp))

            except IOError as err:
                print err.strerror, err.fpath

            blocksize = len(data)

            startWrite = datetime.now()
            ofile.write(data)
            del data #free memory
            time_elapsed = datetime.now() - startWrite

            ofile.close()

            q.task_done()

            logger.info("{}: wrote {:.2f} MB to {} at {} MB/s in {}s".format(
                mp.current_process(),
                float(blocksize)*2**-20, fpath,
                (float(blocksize)*2**-20)/(time_elapsed).total_seconds(),
                time_elapsed.total_seconds()))

            #gzip data file
            logger.info("{}: initiating archiving and compression process for {}".format(
                mp.current_process(),
                fpath))
            try:
                args = ["loco2bx.py", "{}".format(fpath)]
                callstart = Time.now()
                check_call(args)
                callend = Time.now()
                callduration = (callend - callstart).sec
                logger.info("archived and compressed {} in {:.2f} seconds".format(
                    fpath, callduration))
            except CalledProcessError as err:
                logger.error("command failed (errno {}): {}".format(err.returncode, args))
                logger.error(err.message)

            #remove .lofasm file
            try:
                logger.debug("removing {}".format(fpath))
                os.remove(fpath)
            except:
                logger.error("unable to remove {}".format(fpath))

class CleanKiller(object):
    def __init__(self):
        self.KILLNOW = False

        signal.signal(signal.SIGINT, self.kill)
        signal.signal(signal.SIGTERM, self.kill)
    def kill(self, signo, sigframe):
        self.KILLNOW = True

def main():
    with open(PIDFILE, 'a') as f:
        f.write(str(os.getpid())+'\n')

    logger = logging.getLogger("LoFASM Recorder")
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler(LOGFILE)
    log_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(log_formatter)
    logger.addHandler(fh)

    #get active data disk
    with open(DISKFILE, 'r') as f:
        DiskID = f.read().strip()

    dirname = '/data{}/'.format(DiskID)
    logger.info("Active Data Disk {}".format(dirname))

    q = mp.JoinableQueue()
    Nwriters = 2
    writers = []
    lp = mp.Process(target=listen, args=(q, logger,), name='LoFASM Sniffer')

    for i in range(Nwriters):
        w = mp.Process(target=write, args=(q, dirname, logger,),
            name='LoFASM Writer %i' %i)

        writers.append(w)

    lp.start()
    for w in writers:
        w.start()

def stop():

    for line in open(PIDFILE, 'r'):
        os.kill(int(line.strip()), signal.SIGTERM)
    os.remove(PIDFILE)

if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser(description="LoFASM Recorder")
    p.add_argument('command', type=str,
        choices=['start', 'stop', 'reset', 'status'],
        help="command: either start, stop, or reset.")

    args = p.parse_args()
    if 'start' == args.command:
        #only start if no pid exists already
        if not os.path.isfile(PIDFILE):
            main()
        else:
            raise RuntimeError("pid file still exists. recorder already running?")
    elif 'stop' == args.command:
        stop()
    elif 'restart' == args.command:
        stop()
        main()
    elif 'status' == args.command:
        if os.path.isfile(PIDFILE):
            print 'running'
        else:
            print 'stopped'
