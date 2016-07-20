#! /usr/bin/python2.7

import multiprocessing as mp
from datetime import datetime, timedelta
import socket, os, sys, gc
import time
from lofasm.write import write_header_to_file
from lofasm import config
import signal
import logging
from subprocess import call


IP_ADDRESS = '192.168.4.5'
PORT = 60001
PACKETSIZE = config.PACKETSIZE
PACKETGROUPSIZE = config.PACKETGROUPSIZE
STATION = config.STATION
LOGFILE = config.LOGFILE
PIDFILE = config.PIDFILE
DISKFILE = config.DISKFILE
BLOCKFILE = config.BLOCKFILE


def listen(q, logger):
    with open(PIDFILE, 'a') as f:
        f.write(str(os.getpid())+'\n')

    logger.debug('{} starting with pid {}'.format(
        mp.current_process(), os.getpid()))
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((IP_ADDRESS, PORT))

    #get data block time
    with open(BLOCKFILE, 'r') as f:
        block_time = f.read().strip()

    logger.info("{} BLOCKTIME: {} seconds".format(
        mp.current_process(), block_time))

    while True:
        gc.collect()
        blockstart = datetime.now()
        blockend = blockstart + timedelta(seconds=int(block_time))
        logger.info("{}: new block: {} - {}".format(
            mp.current_process(),
            blockstart.strftime("%Y/%m/%d %H:%M:%S"),
            blockend.strftime("%H:%M:%S")))
        #block = []
        block = ''
        while datetime.now() < blockend:
            for i in range(PACKETGROUPSIZE):
                try:
                    d = sock.recv(PACKETSIZE)
                except socket.error:
                    pass

                #block.extend(d)
                block += d
                del d
        q.put((blockstart, block))
        logger.info("{}: added {} MB to queue".format(mp.current_process(), str(float(len(block))*2**-20)))
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
            #if queue not empty start taking data
            tstamp, data = q.get()
            try:
                fname = dirname + tstamp.strftime("%Y%m%d_%H%M%S")+".lofasm"
                ofile = open(fname, 'wb')
                write_header_to_file(ofile, STATION)
            except IOError as err:
                print err.strerror, err.fname
            blocksize = len(data)
            startWrite = datetime.now()
            ofile.write(data)
            del data #free memory
            time_elapsed = datetime.now() - startWrite
            ofile.close()
            q.task_done()
            logger.info("{}: wrote {:.2f} MB to {} at {} MB/s in {}s".format(
                mp.current_process(),
                float(blocksize)*2**-20, fname,
                (float(blocksize)*2**-20)/(time_elapsed).total_seconds(),
                time_elapsed.total_seconds()))

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
    Nwriters = 1
    writers = []
    lp = mp.Process(target=listen, args=(q, logger,), name='LoFASM Sniffer')
    #lp.daemon = True
    for i in range(Nwriters):
        w = mp.Process(target=write, args=(q, dirname, logger,),
            name='LoFASM Writer %i' %i)
    #    w.daemon = True
        writers.append(w)

    lp.start()
    for w in writers:
        w.start()

    #killer = CleanKiller()
    #while not killer.KILLNOW:
    #    if os.path.isfile(KILLFILE):
    #        print 'KILLNOW'
    #        lp.terminate()
    #        for i in writers:
    #            w.terminate()
    #        break

def stop():
    #touch killfile
    #print "sending kill signal...",
    #sys.stdout.flush()
    #touch_cmd = "touch {}".format(KILLFILE)
    #call(touch_cmd.split())
    #time.sleep(1)
    #if not os.path.isfile(PIDFILE):
    #    print "success"
    #else:
    #    print "failed"
    #clean up
    #os.remove(KILLFILE)

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
