#!/usr/bin/env python


import matplotlib
matplotlib.use("Agg")
from lofasm import parse_data as pdat
from lofasm import config
import matplotlib.pyplot as plt
import numpy as np



if __name__ == "__main__":
	import logging
	import argparse
	parser = argparse.ArgumentParser()
	parser.add_argument("filename", help="path to LoFASM file")
	args = parser.parse_args()

	f = args.filename
	
	#get logger
	LOGFILE = config.LOGFILE
	logger = logging.getLogger("waterfall.py")
	logger.setLevel(logging.DEBUG)
	fh = logging.FileHandler(LOGFILE)
	log_formatter = logging.Formatter(
		'%(asctime)s - %(name)s - %(levelname)s - %(message)s')
	fh.setFormatter(log_formatter)
	logger.addHandler(fh)

	logger.info('processing {}'.format(f))

	#Get time info
	file_name = f.split('/')[-1]
	file_time_info = f.split('.')[0].split('/')[-1]
	file_year = file_time_info[0:4]
	file_month_number = file_time_info[4:6]
	months = ['January','February','March','April','May','June','July','August','September','October','November','December']
	file_month_name = months[int(file_month_number)-1]
#	print file_month_name
	file_day = file_time_info[6:8]
	file_date_string = file_month_name+' '+file_day+', '+file_year #this is the month day and year of the obs as a string
	file_hour = file_time_info[9:11]
	file_minute =file_time_info[11:13]
	file_second = file_time_info[13:15]
	file_time_string = file_hour+':'+file_minute+':'+file_second #this is the hour:min:sec of the begining of the obs

	#sets freq band and finds bin #
	lower_freq = 15 
	higher_freq = 80
	lower_bin_number = int(lower_freq*(2048.0/200.0))
	higher_bin_number = int(higher_freq	*(2048.0/200.0))
	freqs = np.linspace(0, 200, 2048)

	#open crawler
	crawler = pdat.LoFASMFileCrawler(f)
	crawler.open()
	polarizations = ['AA','BB','CC','DD','AB','AC','AD','BC','BD','CD','BE','BN']

	length = (crawler.getNumberOfIntegrationsInFile()-1)

	#initialize memory
	
#	bufferLen = int(np.ceil(args.duration / 0.083))
	bufferShape = (2048, length+1)
	logging.debug("buffersize: ({},{})".format(
			bufferShape[0], bufferShape[1]))
#	print "buffer shape: ", bufferShape
#	print "length: ", length

	data = {
		    'AA' : np.zeros(bufferShape) ,
		    'BB' : np.zeros(bufferShape) ,
		    'CC' : np.zeros(bufferShape) ,
		    'DD' : np.zeros(bufferShape) ,
		    'AB' : np.zeros(bufferShape) ,
		    'AC' : np.zeros(bufferShape) , 
		    'AD' : np.zeros(bufferShape) ,
		    'BC' : np.zeros(bufferShape) ,
		    'BD' : np.zeros(bufferShape) ,
		    'CD' : np.zeros(bufferShape) ,
		    'BE' : np.zeros(bufferShape) ,
		    'BN' : np.zeros(bufferShape) ,
		}
	


#	print np.shape(data['AA'])
#	print length


	#read in each spec
	for spec in np.arange(length): #go through the file and get all integration

		data['AA'][:,spec] = 10*np.log10(crawler.autos['AA'])
		data['BB'][:,spec] = 10*np.log10(crawler.autos['BB'])
		data['CC'][:,spec] = 10*np.log10(crawler.autos['CC'])
		data['DD'][:,spec] = 10*np.log10(crawler.autos['DD'])
		'''
		data['AB'][:,spec] = np.abs(10*np.log10(crawler.cross['AB']))
		data['AC'][:,spec] = np.abs(10*np.log10(crawler.cross['AC']))
		data['AD'][:,spec] = np.abs(10*np.log10(crawler.cross['AD']))
		data['BC'][:,spec] = np.abs(10*np.log10(crawler.cross['BC']))
		data['BD'][:,spec] = np.abs(10*np.log10(crawler.cross['BD']))
		data['CD'][:,spec] = np.abs(10*np.log10(crawler.cross['CD']))
		data['BE'][:,spec] = 10*np.log10(crawler.beams['BE'])
		data['BN'][:,spec] = 10*np.log10(crawler.beams['BN'])
		'''

		try:
			crawler.forward()
		except:
			break
		
#		if float(spec)%(length/100) == 0 :
#			print str(int(round(float(spec)*100)/length)) + '% done'



	fig, (ax1, ax2, ax3, ax4) = plt.subplots(4,1)
	fig.suptitle(file_date_string+'\n ' +'Start Time: '+file_time_string)
	fig.set_size_inches(16,10)
#	print 'made figure'


	cmap = 'spectral'
	im1 = ax1.imshow(data['AA'][lower_bin_number:higher_bin_number], aspect='auto',clim=(30,70),interpolation='none', cmap=cmap, extent=[0,(length)*0.083/60,higher_freq,lower_freq])
	im2 = ax2.imshow(data['BB'][lower_bin_number:higher_bin_number], aspect='auto',clim=(30,70),interpolation='none', cmap=cmap, extent=[0,(length)*0.083/60,higher_freq,lower_freq])
	im3 = ax3.imshow(data['CC'][lower_bin_number:higher_bin_number], aspect='auto',clim=(30,70),interpolation='none', cmap=cmap, extent=[0,(length)*0.083/60,higher_freq,lower_freq])
	im4 = ax4.imshow(data['DD'][lower_bin_number:higher_bin_number], aspect='auto',clim=(30,70),interpolation='none', cmap=cmap, extent=[0,(length)*0.083/60,higher_freq,lower_freq])
	plt.subplots_adjust(left=0.05,right=.93,top=.93,bottom=0.07)

#	print 'imshowed'


	fig.text(0.0125,0.57,'Frequency (MHz)',rotation=90,size='x-large')
	fig.text(0.45,0.02,'Time (Min)',size='x-large')
	fig.text(1-0.027,0.57,'Power (dBm) Arb. Ref.',rotation=270,size='x-large')
#	print 'text'
	cax = fig.add_axes([.94,.07,.015,0.86])
	plt.colorbar(im1, cax=cax)#, **kw)
#	print 'colorbar'
	#plt.show()
	ax1.set_ylabel("NS")
	ax2.set_ylabel("EW")
	ax3.set_ylabel("ns")
	ax4.set_ylabel("ew")

	logger.info('saving /var/lofasm/stethoscope/waterfall.png')
	#fig.savefig('/Volumes/Macintosh HD 2/LoFASM3_plots/'+f.rstrip('.lofasm')+'.png',dpi=200)
	fig.savefig('/var/lofasm/stethoscope/waterfall.png')

	del fig
	plt.close()

	del crawler


