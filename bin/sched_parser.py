#! /usr/bin/python

#Parse Emma Handzo's LoFASM Schedule files and create LoFASM Session Files 
#and place them in the appropriate directories in the LoFASM Scheduler.
#
#LoFASM Session Files have the following format:
#
#ProjectName    ProjName
#Target         NameOfSource
#RA             DDMMSS.ss #minutes and seconds are of arc
#DEC            HHMMSS.ss
#ObsDate        YYYYMMDD #UTC
#ObsStart       SessionStartTimeInUTC
#ObsDur         SessionDurationTimeInSeconds
#StationID      stationID
#


if __name__ == "__main__":

	import argparse
	import pytz
	from datetime import datetime

	headerLen = 184
	obs_prog = '/home/controller/bin/rec_target.sh'

	parser = argparse.ArgumentParser(
		description='Parse LoFASM schedule and produce recording commands')
	parser.add_argument("filename", 
		help="path to LoFASM Rise Times File")
	parser.add_argument("station", 
		help="select lofasm station to observe with (1,2,3,4)",
		type=int,
		default=1,
		choices=[1,2,3,4])
	parser.add_argument('-w', '--SCHED_DIR', '--write',
		dest='sched_dir',
		help="Create/update schedule at SCHED_DIR. If this argument is not used then print scheduling commands with no writes.",
		type=str)
	parser.add_argument('-v', action='store_true',
			    dest='verbose',
			    help="run in verbose mode")
	parser.add_argument('--proj', dest='projectName', type=str,
		default='UntitledProject',
		help="Name of the project being scheduled.")
	parser.add_argument('--target', dest='targetName', type=str,
		default='UnknownTarget',
		help="Name of target being observed.")



	args = parser.parse_args()


	#open LoFASM rise times file
	cmds = []

	tz = [pytz.timezone('US/Central'),
	pytz.timezone('US/Mountain'),
	pytz.timezone('UTC'),
	pytz.timezone('US/Pacific')]

	utc_tz = pytz.timezone('UTC')

	if args.sched_dir:
		import os

		rootDir = args.sched_dir.rstrip('/') + '/'
		try:
			assert(os.path.isdir(rootDir))
		except AssertionError:
			print "directory does not exist: ", args.sched_dir


	try:
		with open(args.filename, 'r') as f:
			hdr = [x.strip('.') for x in f.read(headerLen).split()]
			rightAscension = hdr[8]
			declination = hdr[12]

			rawText = f.read()
			rawText = rawText.split('\n\n')
			rawText.pop()




			for entry in rawText:
				entry = entry.replace('\n', ' ')
				entry = entry.replace('t', ' ')
				entry = entry.split()

				dates = [entry[0], entry[2], entry[4], entry[6]]
				riseTimes = [entry[1], entry[3], entry[5], entry[7]]
				obsDur = entry[8:]


				riseTimeUTC = utc_tz.localize(datetime(
					int(dates[args.station-1][:4]),
					int(dates[args.station-1][5:7]),
					int(dates[args.station-1][-2:]),
					int(riseTimes[args.station-1][:2]),
					int(riseTimes[args.station-1][3:5])))
				riseTimeUTC_str = riseTimeUTC.strftime('%Y%m%d')
				

				riseTimeLocal = tz[args.station-1].normalize(
					riseTimeUTC.astimezone(tz[args.station-1]))
				
				riseTimeLocal_str = riseTimeLocal.strftime('%H:%M %m/%d/%Y')
				sched_cmd = 'at %s -f %s;' % (riseTimeLocal_str, obs_prog)
				


				if args.verbose:
					sched_filename = '_'.join([args.projectName, riseTimeLocal.strftime("%Y%m%d"),
						riseTimeLocal.strftime("%H%M%S")]) + '.lsf'
					print "#############################"
					print "Project Name:\t", args.projectName
					print "Target:\t\t", args.targetName
					print "RA:\t\t", rightAscension
					print "Dec:\t\t", declination
					print "ObsDate:\t", riseTimeLocal.strftime("%Y%m%d")
					print "ObsStart:\t", riseTimeLocal.strftime("%H%M%S")
					print "ObsDur:\t\t", obsDur[args.station-1] 
					print "schedule cmd: ", sched_cmd
					print "LoFASM Session Filename: \t", sched_filename 

				if args.sched_dir:
					dateDir = rootDir + riseTimeUTC_str + '/'
					sched_file = dateDir + '_'.join([args.projectName, riseTimeLocal.strftime("%Y%m%d"),
						riseTimeLocal.strftime("%H%M%S")]) + '.lsf'

					if not os.path.exists(dateDir):
						os.mkdir(dateDir)


					with open(sched_file, 'w') as f:
						f.write("ProjectName\t%s\n" % args.projectName)
						f.write("Target\t\t%s\n" % args.targetName)
						f.write("RA\t\t%s\n" % rightAscension)
						f.write("DEC\t\t%s\n" % declination)
						f.write("ObsDate\t\t%s\n" % riseTimeLocal.strftime("%Y%m%d"))
						f.write("ObsStart\t%s\n" % riseTimeLocal.strftime("%H%M%S"))
						f.write("ObsDur\t\t%s\n" % obsDur[args.station-1].rstrip('s'))
						f.write("StationID\t%i\n" % args.station)
						


	except IOError as err:
		print "Input/Ouput Error detected: ",
		print err.strerror
		print err.filename



