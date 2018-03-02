#! /usr/bin/env python2.7

#LoFASM script to grab the beginning of a LoFASM file.

def exit_clean(infile=None, outfile=None):
	'''
	try to exit gracefully
	'''
	import sys 

	if infile:
		infile.close()
	if outfile:
		outfile.close()
	sys.exit()

def chopByBytes(infile, Nbytes, outfile):
	'''
	chop Nbytes data bytes from top of outfile
	'''

	hdr_len = 96 #version 2

	head = infile.read(hdr_len + Nbytes)

	outfile = open(outfile, 'wb')

	outfile.write(head)

	outfile.close()


if __name__ == "__main__":
	import argparse

	parser = argparse.ArgumentParser(description='Extract LoFASM data sample.')
	parser.add_argument("-b", type=int, default=None,
		help="Specify the number of data bytes to chop off the top.\
		Must be an integer. Do not include the header length when counting bytes, it is \
		copied automatically.")
	parser.add_argument("filename", help='path to .lofasm file')
	parser.add_argument("-o", type=str, default='lofasm_sample.lofasm',
		help='path to output file')

	args = parser.parse_args()
	
	#check that file exists
	try:
		f = open(args.filename, 'rb')
	except IOError as err:
		print err
		exit_clean()

	#chop file
	if args.b:
		chopByBytes(f, args.b, outfile=args.o)
	else:
		#exit
		print "Goodbye"
		exit_clean()




