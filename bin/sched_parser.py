#! /usr/bin/python


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
		help="Create/update schedule at SCHED_DIR",
		type=str)



	args = parser.parse_args()


	#open LoFASM rise times file
	cmds = []

	tz = [pytz.timezone('US/Central'),
	pytz.timezone('US/Mountain'),
	pytz.timezone('US/Eastern'),
	pytz.timezone('US/Pacific')]

	utc_tz = pytz.timezone('UTC')

	if args.sched_dir:
		import os

		rootDir = args.sched_dir.rstrip('/') + '/'
		try:
			assert(os.path.isdir(rootDir))
		except AssertionError:
			"directory does not exist: ", args.sched_dir


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

				if args.sched_dir:

					dateDir = rootDir + riseTimeUTC_str + '/'

					if not os.path.exists(dateDir):
						os.mkdir(dateDir)

					sched_file =  dateDir + 'obs_' +rightAscension[:6] + \
						declination[:7] + '.sh'

					with open(sched_file, 'a') as f:
						f.write(sched_cmd)
				else:
					print sched_cmd

	except IOError as err:
		print "Input/Ouput Error detected: ",
		print err.strerror
		print err.filename




