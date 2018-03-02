#! /usr/bin/python

#simulate square wave in LoFASM data format
#inject signal into AA polarization 
#and leave all else as zeros


from lofasm.write import write_header_to_file as write_header
from lofasm.simulate import data
from lofasm.simulate import signal

import numpy as np

if __name__ == "__main__":

	import argparse

	parser = argparse.ArgumentParser(description='Simulate LoFASM Data')
	parser.add_argument("-n", "--num_samples", type=float, default=10,
		help='Duration of the simulated data in seconds.')
	parser.add_argument("-f", "--filename", required=True, type=str,
		help="target filename")


	args = parser.parse_args()


	#create signal
	s = np.zeros(args.num_samples)
	num_samples = len(s)

	#open file for writing
	print "Creating simulated LoFASM file: %s" % args.filename
	outfile = open(args.filename, 'wb')

	#write file header to disk
	print "Writing file header...", 
	write_header(outfile, 'simdata')
	print "done."

	#sample index
	i = 1

	#create empty LoFASM Burst
	burst = data.Burst()


	#generate LoFASM Bursts and write them to disk
	for dataSample in s:

		#generate spectrum for AA
		#this places the same value in all frequency bins
		spect = np.ones(1024) * dataSample
		zeros = np.zeros(1024)

		packet = data.RealPacket((spect, zeros))

		#insert spectra into AA Even index
		burst.insert(packet, 1)

		#insert spectra into AA Odd index
		burst.insert(packet, 9)

		#get writable binary string
		burst_str = burst.getBinStr()

		#write burst to disk
		print "Writing burst %i/%i..." % (i, num_samples),
		outfile.write(burst_str)
		print "done."

		#increment header
		burst.packets[0].increment()

		i += 1

	#close data file
	print "Closing data file."
	outfile.close()
