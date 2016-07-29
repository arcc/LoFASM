#!/usr/bin/python2.7

DISKFILE = '/var/lofasm/ActiveDisk'
BLOCKFILE = '/var/lofasm/BlockTime'

if __name__ == "__main__":
	import argparse

	p = argparse.ArgumentParser(description="LoFASM Config")
	p.add_argument('attribute', type=str, choices=['ActiveDisk', 'BlockTime'])
	p.add_argument('value', nargs='?', default='')
	args = p.parse_args()

	if 'ActiveDisk' == args.attribute:
		choices = ['1','2']
		if args.value in choices:
			with open(DISKFILE, 'w') as f:
				f.write(args.value)
		elif args.value == '':
			with open(DISKFILE, 'r') as f:
				print f.read().strip()
		else:
			raise ValueError(args.value)
	elif 'BlockTime' == args.attribute:
		if args.value == '':
			with open(BLOCKFILE, 'r') as f:
				print f.read().strip()			
		elif int(args.value) > 0:
			with open(BLOCKFILE, 'w') as f:
				f.write(args.value)
		else:
			raise ValueError(args.value)
