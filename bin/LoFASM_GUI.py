#fix the fucking up when closing
###always error when closing
#label time axis better
#animate colorplotter
#work on help menu
# add abilty to do multimple things at once(like closing windows when refreshing or use both plotters at once 
# example## both plotter and colorplotter at same time and a way to pause or wuit with having to crtl c

from __future__ import division
import struct
import pyfits
import time
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import sys
import os
import numpy as np
import argparse
import Tkinter
from tkFileDialog import askopenfilename
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
import tkMessageBox
from lofasm import parse_data as pdat
plt.ion()

##########################################
#########################################
####create the tkinter window and name it
root = Tkinter.Tk()
root.wm_title("LoFASM Data Viewer")


#############################################
#############################################
#### this uses argparse to create a help menu 
parser = argparse.ArgumentParser()

parser.add_argument('-lf', '--lower_frequency', action='store', dest='lower_freq',
default = 25, help='What is the lower frequency?')

parser.add_argument('-uf', '--upper_frequency', action='store', dest='upper_freq',
default = 88, help='What is the upper frequency?')

parser.add_argument('-up', '--upper_power', action='store', dest='upper_power',
default = 0, help='What is the upper power?')

parser.add_argument('-lp', '--lower_power', action='store', dest='lower_power',
default = -100, help='What is the lower power?')

parser.add_argument('-sf', '--start_frame', action='store', dest='start_frame',
default = 0, help='What frame do you want to start on? (each frame is 40ms)')

parser.add_argument('-rl', '--read_length', action='store', dest='read_length',
default = 1000, help='How many accumulations do you want to plot?')

parser.add_argument('-as', '--accumulation_stride', action='store', dest='accumulation_stride',
default = 5, help='How many frames do you want to accumulate into each plot?')

parser.add_argument('-d', '--delay', action='store', dest='delay',
default = 0.2, help='How long do you want to wait until redrawing the plot?')

parser.add_argument('-f', '--file_name', action='store', dest= 'file_name',
default = [], help='What file do you want to read?')

parser.add_argument('-cr', '--correlation', action='store', dest='correlation',
default = 'AA', help='Which correlation do you want to plot?')

parser.add_argument('--version', action='version', version='%(prog)s 1.0')

results = parser.parse_args()




#############################
#############################
#### these are some functions
def _quit():
  root.quit()



def get():
  if lfEntry.get() is not '':                   # If the Entry field is not empty 
    results.lower_freq          = lfEntry.get() # Get the new value
    l1.destroy()                                # and clear the old label   
    Tkinter.Label(master=root, text=results.lower_freq).grid(row=1, column=2) # so a new one can be drawn
    print "The new Lower Frequency is ",results.lower_freq #print to terminal for shits and gigs

  if ufEntry.get() is not '':
    results.upper_freq          = ufEntry.get()
    l2.destroy()
    Tkinter.Label(master=root, text=results.upper_freq).grid(row=2, column=2)
    print "The new upper Frequency is ",results.upper_freq

  if upEntry.get() is not '':
    results.upper_power         = upEntry.get()
    l3.destroy()
    Tkinter.Label(master=root, text=results.upper_power).grid(row=3, column=2)
    print "The new Upper power is ",results.upper_power

  if lpEntry.get() is not '':
    results.lower_power         = lpEntry.get()
    l3.destroy()
    Tkinter.Label(master=root, text=results.lower_power).grid(row=4, column=2)
    print "The new Lower power is ",results.lower_power

  if sfEntry.get() is not '':
    results.start_frame         = sfEntry.get()
    l4.destroy()
    Tkinter.Label(master=root, text=results.start_frame).grid(row=5, column=2)
    print "The new start frame is ",results.start_frame

  if rlEntry.get() is not '':
    results.read_length         = rlEntry.get()
    l5.destroy()
    Tkinter.Label(master=root, text=results.read_length).grid(row=6, column=2)
    print "The new read Length is ",results.read_length

  if asEntry.get() is not '':
    results.accumulation_stride = asEntry.get()
    l6.destroy()
    Tkinter.Label(master=root, text=results.accumulation_stride).grid(row=7, column=2)
    print "The new Accumulation stride is ",results.accumulation_stride

  if rdEntry.get() is not '':
    results.delay               = float(rdEntry.get())
    l7.destroy()
    Tkinter.Label(master=root, text=results.delay).grid(row=8, column=2)
    print "The new redraw delay is",results.delay

  if crEntry.get() is not '':
    results.delay               = rdEntry.get()
    l8.destroy()
    Tkinter.Label(master=root, text=results.correlation).grid(row=9, column=2)
    print "The new redraw delay is",results.delay

def clear():
  results.file_name = ''
  Tkinter.Label(master=root,text="                                        ").grid(row=0, column=1)




######hits func open the file
def _open():
  results.file_name = askopenfilename(filetypes=[("allfiles","*"),("binary files","*.dat"),("FITS files","*.fits"),("LoFASM Data Files","*.lofasm")]) #open data file, currently .lofasm
  Tkinter.Label(master=root,text=results.file_name.split('/')[-1][:20]+'...').grid(row=0, column=1) #place file name in gui

def init():
  line.set_data([], [])
  return line,

def animate(i, crawler, line):
  print i 
  x = np.linspace(0, 200, 2048)
  y = 10*np.log10(crawler.autos['AA']) #only plots AA baseline
  line.set_data(x, y)
  plt.title(format(i*0.09765625,'.2f'))
  crawler.forward() #move to next integration

  return line,

def plot():
  crawler = pdat.LoFASMFileCrawler(results.file_name)

  fig = plt.figure()
  ax = plt.axes(xlim=(0, 100), ylim=(0, 100))
  line, = ax.plot([], [], lw=2)
  plt.xlabel('Frequency (MHz)')
  plt.ylabel('Power')
  # call the animator.  blit=True means only re-draw the parts that have changed.
  anim = animation.FuncAnimation(fig, animate, fargs=(crawler, line), init_func=None,frames=10000, interval=10, blit=False)
  plt.show()

#old
def plot_fits():
  fits = pyfits.open(results.file_name)

  data = fits[1].data


  test = data[0].field('DATA')

  print test[0,0,:,0]

  freqs = data[0].field('DAT_FREQ')

  #print data
  #plt.ion()
  #fig = plt.figure() 
  #fig.canvas.set_window_title('FITS plotter') 
  for i in range(results.read_length):
    plt.xlim(int(results.lower_freq),int(results.upper_freq))
    #plt.ylim(int(results.lower_power),int(results.upper_power))
    plt.title(i)
    plt.plot(freqs,10*np.log10(test[i,0,:,0]))
    #plt.xlim(25,88)
    #plt.ylim(38,65)
    plt.draw()
    time.sleep(results.delay)
    plt.clf()

#old
def read_write():
  #open file to be 'r'ead ad a 'b'inary and reads past first 80 bytes 
  infile = open(results.file_name, 'rb') 
  infile.read(80) 
  infile.read(int(results.start_frame)*8200)

  #read chunks of data
  for x in range(int(results.read_length)): #this for loop creates a list called data from the binary file
    new_bytes = infile.read((2**13)+8) 
    spec_id   = new_bytes[:8]
    spec_data = new_bytes[8:]
    data      = [x for x in struct.unpack('>2048L',spec_data)] 

    freqs     = np.arange(2048)/2047.0*200

    for i in range(len(data)):
      data[i] = (((1e-7)/0.00286990776725)*float(data[i])  / (268416)+10**-20)

    data      = [data]
    for x in range(int(results.accumulation_stride)-1): #this loop appends the list 'data'
      new_bytes = infile.read((2**13)+8) 
      spec_id   = new_bytes[:8]
      spec_data = new_bytes[8:]
      data_acc   = [x for x in struct.unpack('>2048L',spec_data)]

      for i in range(len(data_acc)):
        data_acc[i] = (((1e-7)/0.00286990776725)*float(data_acc[i])  / (268416)+10**-20)

      data.append(data_acc)
    x = freqs
    y = 10*np.log10([sum(e)/len(e) for e in zip(*data)])  

    

    plt.xlim(int(results.lower_freq),int(results.upper_freq))
    plt.ylim(int(results.lower_power),int(results.upper_power))

    plt.xlabel("Frequency (MHz)")
    plt.ylabel("Power (dB)")
    plt.title(results.start_frame)
    results.start_frame=int(results.start_frame)+1
    plt.plot(x,y) 
    plt.draw()
    time.sleep(results.delay)
    plt.clf()

  l4.destroy()
  results.start_frame=0
  Tkinter.Label(master=root, text=results.start_frame).grid(row=4, column=2)  



###########################
### functions for colorplot LOUIS
def freq2bin(freq):
  num_channels = 2048
  bandwidth = 200.0 #MHz
  rbw = bandwidth/num_channels

  bin_num = np.ceil(float(freq)/rbw)
  return bin_num

def sec2bin(sec_to_find,num_bins,total_time_sec):

  binwidth = total_time_sec/float(num_bins)
  offset_from_bin0 = sec_to_find % total_time_sec
  bin_num = int(np.ceil(offset_from_bin0 * binwidth) )
  #print bin_num
  return bin_num

def grab_spects(num_spects,infile):
  spect_array = []
  for i in range(num_spects):
    infile.read(8)
    spect_array.append(10*np.log10(np.array(struct.unpack('>2048L',infile.read(1024*8))))) # reda entire chunk intead of just first half
    #infile.read(1024*4)
  return spect_array  
  ######end of colorplot funcs (louis)

  ###################
  #####this is the colorplotter
def colorplot():
  infile = open(results.file_name, 'rb') 
  infile.read(80) # read past header

  seconds_per_spect = .0419
  seconds_to_plot = float(180)
  num_spect_to_plot = int(np.ceil(seconds_to_plot / seconds_per_spect))
  spect_array = []#np.zeros([num_spect_to_plot,2048])
  #infile.seek(80) # go back to beginning of data


  stride=100


  for i in range(num_spect_to_plot):
    spect_id = infile.read(8) #pass spectrum ID
    raw_dat = infile.read(1024*8) #read actual data (all 0 - 200mhz)
    spect_array.append(10*np.log10(np.array(struct.unpack('>2048L',raw_dat))))
      #for i in range(len(data_acc)):
        #spect_array[i] = (((1e-7)/0.00286990776725)*float(spect_array[i])  / (268416)+10**-20)

#spect_array = np.array(spect_array)

  bin_width = seconds_to_plot/float(num_spect_to_plot) #seconds/bin
  plt.ion()
  fig = plt.figure(num=None, figsize=(14, 3), dpi=100, facecolor='w', edgecolor='k')#figsize=(14,3), dpi=100)
  yticks = [freq2bin(x) for x in np.arange(0,200,10)]
  ytick_labels = [str(x) for x in np.arange(0,200,10)]
  xticks = [sec2bin(x,num_spect_to_plot,seconds_to_plot) for x in np.arange(0,10,1)]
  xtick_labels = [str(x) for x in np.arange(0,10,1)]

  colorplot = fig.add_subplot(111)
  plt.title('colorplot viewer')
  

  #plt.ylabel('Frequency (MHz)')
  #plt.yticks([x*200.0/2047 for x in range(2048)])

  line_colorplot = colorplot.imshow(np.transpose(spect_array))
  line_colorplot.set_interpolation('nearest')
  #colorplot.set_yticks([x for x in range(1024)])
  #print "the ylim is: ",colorplot.get_ylim()
  colorplot.set_yticks(yticks)
  colorplot.set_yticklabels(ytick_labels)
  colorplot.set_xticks(xticks)
  colorplot.set_xticklabels(xtick_labels)
  
  plt.ylabel('freqs')
  plt.xlabel('time')
  plt.ylim(200,927) #set upper and lower frew # create way to grab from gui # this is bin number not freq number
  fig.canvas.draw()
  raw_input('press enter to contine')
  while 1:

    new_spects = grab_spects(stride,infile)
    #print "new spectrum!"

    #remove first spectrum in spect_array
    new_array=spect_array[stride:]

    for i in range(stride):
      new_array.append(new_spects[i])
  #update diagram

    new_array = new_array

    line_colorplot.set_array(np.transpose(new_array))
    spect_array = new_array
    fig.canvas.draw()
    time.sleep(.1)
#####################end colorplot

def help():
   tkMessageBox.showinfo("Help Menu", "Welcome to the help page. you are retarded")  

##########those were all the function ^^^^^^^^^
##################################################
###################################################



#this is the GUI
####################################
#### These are the Labels on the left
Tkinter.Label(master=root, text="Lower Frequency").grid(row=1)
Tkinter.Label(master=root, text="Upper Frequency").grid(row=2)
Tkinter.Label(master=root, text="Upper Power").grid(row=3)
Tkinter.Label(master=root, text="Lower Power").grid(row=4)
Tkinter.Label(master=root, text="Start Frame").grid(row=5)
Tkinter.Label(master=root, text="Read Length").grid(row=6)
Tkinter.Label(master=root, text="Accumulation Stride").grid(row=7)
Tkinter.Label(master=root, text="Redraw Delay").grid(row=8)
Tkinter.Label(master=root, text="Correlation").grid(row=9)

######################################
#### These are the Labels on the right 
l1=Tkinter.Label(master=root, text=results.lower_freq)
l1.grid(row=1, column=2)

l2=Tkinter.Label(master=root, text=results.upper_freq)
l2.grid(row=2, column=2)

l3=Tkinter.Label(master=root, text=results.upper_power)
l3.grid(row=3, column=2)

l4=Tkinter.Label(master=root, text=results.lower_power)
l4.grid(row=4, column=2)

l5=Tkinter.Label(master=root, text=results.start_frame)
l5.grid(row=5, column=2)

l6=Tkinter.Label(master=root, text=results.read_length)
l6.grid(row=6, column=2)

l7=Tkinter.Label(master=root, text=results.accumulation_stride)
l7.grid(row=7, column=2)

l8=Tkinter.Label(master=root, text=results.delay)
l8.grid(row=8, column=2)

l9=Tkinter.Label(master=root, text=results.correlation)
l9.grid(row=9, column=2)

###############################
#### These are the Entry fields 
lfEntry = Tkinter.Entry(master=root)
lfEntry.grid(row=1, column=1)

ufEntry = Tkinter.Entry(master=root)
ufEntry.grid(row=2, column=1)

upEntry = Tkinter.Entry(master=root)
upEntry.grid(row=3, column=1)

lpEntry = Tkinter.Entry(master=root)
lpEntry.grid(row=4, column=1)

sfEntry = Tkinter.Entry(master=root)
sfEntry.grid(row=5, column=1)

rlEntry = Tkinter.Entry(master=root)
rlEntry.grid(row=6, column=1)

asEntry = Tkinter.Entry(master=root)
asEntry.grid(row=7, column=1)

rdEntry = Tkinter.Entry(master=root)
rdEntry.grid(row=8, column=1)

crEntry = Tkinter.Entry(master=root)
crEntry.grid(row=9, column=1)


######################
#### These are buttons
Tkinter.Button(root, text='open', command=_open).grid(row=0, column=0)
Tkinter.Button(root, text='clear', command=clear).grid(row=0, column=2)
Tkinter.Button(root, text='plot', command=plot).grid(row=10, column=0)
Tkinter.Button(root, text='get', command=get).grid(row=10, column=1)
Tkinter.Button(root, text='quit',command=_quit).grid(row=10, column=2)
Tkinter.Button(root, text='plot fits',command=plot_fits).grid(row=11)
Tkinter.Button(root, text='colorplot', command=colorplot).grid(row=11,column=1)
Tkinter.Button(root, text='help', command= help).grid(row=11,column=2)
#create button that ressets ###DATA




Tkinter.mainloop()


