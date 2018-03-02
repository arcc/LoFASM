#!/usr/bin/python2.7

'''
make waterfall plots of latest integration
'''

lastProcessedFile = '/var/run/lofasm/stethoscope/waterfall'

baselines = ['AA', 'BB', 'CC', 'DD', 'AB', 'AC', 'AD', 'BC', 'BD', 'CD']
if __name__ == "__main__":
	from lofasm import parse_data as pdat
	from lofasm import config
	import numpy as np
	import os, sys
	from subprocess import check_output
	import logging
	import matplotlib
	matplotlib.use('Agg')
	import matplotlib.pyplot as plt

	#get logger
	LOGFILE = config.LOGFILE
	logger=logging.getLogger("Stethoscope")
	logger.setLevel(logging.DEBUG)
	fh = logging.FileHandler(LOGFILE)
	log_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
	fh.setFormatter(log_formatter)
	logger.addHandler(fh)

	#get active data disk
	try:
		with open(config.DISKFILE, 'r') as f:
			DiskID = f.read().strip()
			logger.info('DISKID: {}'.format(DiskID))
	except IOError:
		print "no Active Disk File!"
		logger.critical("unable to read data disk configuration")
		sys.exit(0)

	#get current blocktime config setting
	with open(config.BLOCKFILE, 'r') as f:
		BLOCKTIME = f.read().strip()

	
	dataDir = '/data{}/'.format(DiskID)

	#get latest lofasm file
	listing = check_output('ls -rt {}'.format(dataDir).split()).split('\n')
	if '' in listing:
		listing.remove('')
	if 'lost+found' in listing:
		listing.remove('lost+found')
	latestFile = dataDir + listing[-1]

	#check if new waterfall file
	if not os.path.exists(lastProcessedFile) or \
		    open(lastProcessedFile).read() != latestFile:
		
		
	
		logger.info('Sending {} to waterfall.py'.format(latestFile))
		result = check_output(['/usr/local/bin/waterfall.py', latestFile])

		#update lastprocessedfile placeholder
		with open(lastProcessedFile, 'w') as f:
			f.write(latestFile)

		print result
	else:
		logger.info('Already processed: {}, nothing to do.'.format(latestFile))
		pass

	
	#get disk usage
	disk_usage = check_output(['df', '-h'])
	with open('/var/lofasm/stethoscope/disk','w') as f:
		for l in disk_usage.split('\n'):
			if 'data' in l:
				l = l.split()
				row = "{} {}".format(l[-1].rstrip('\n'), l[-2])
				logger.info("Disk usage: {}".format(row))
				f.write(row)
				f.write("\n")


	
