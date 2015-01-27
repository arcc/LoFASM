import Tkinter as Tk
from lofasm import parse_data as pdat
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
import sys
import datetime


low_freq = 0
upper_freq = 100
low_power = 0
upper_power = 100
x = np.linspace(0, 200, 2048)

#this function gets the new values from the entry field and updates them
def get():
  if lfEntry.get() is not '':         # If the Entry field is not empty 
    low_freq = lfEntry.get()  
    print 'new low freq is '+low_freq        # Get the new value 
    Tk.Label(master=root, text=str(low_freq)+' MHz').grid(row=1, column=2,sticky='E')
    #return low_freq

  if ufEntry.get() is not '':         # If the Entry field is not empty 
    upper_freq = ufEntry.get()          # Get the new value 
    Tk.Label(master=root, text=str(upper_freq)+' MHz').grid(row=2, column=2,sticky='E')

  if lpEntry.get() is not '':         # If the Entry field is not empty 
    low_power = lpEntry.get()          # Get the new value 
    Tk.Label(master=root, text=str(low_power)+' dB').grid(row=3, column=2,sticky='E')

  if upEntry.get() is not '':         # If the Entry field is not empty 
    upper_power = upEntry.get()          # Get the new value 
    Tk.Label(master=root, text=str(upper_power)+' dB').grid(row=4, column=2,sticky='E')


#this functions updates the array (is called by plot())
def animate(i, crawler, line):
  #x = np.linspace(0, 200, 2048)
  y = 10*np.log10(crawler.autos['AA']) #only plots AA baseline
  line.set_data(x, y)
  delta_t = float(format(i*0.09765625,'.2f'))
  delta_t_formated = str(datetime.timedelta(seconds=delta_t))[:-4]
  plt.title('T+ '+delta_t_formated)
  crawler.forward() #move to next integration
  return line,

#This function plots the data array
def plot():

  crawler = pdat.LoFASMFileCrawler(sys.argv[1])

  fig = plt.figure()
  print low_freq
  ax = plt.axes(xlim=(low_freq, upper_freq), ylim=(low_power, upper_power))
  line, = ax.plot([], [], lw=.6)

  plt.xlabel('Frequency (MHz)')
  plt.ylabel('Power')
  # call the animator.  blit=True means only re-draw the parts that have changed.
  anim = animation.FuncAnimation(fig, animate, fargs=(crawler, line), init_func=None,frames=10000, interval=10, blit=False)
  plt.show()


#Create a background image object and save it to 'root'
root = Tk.Tk()
root.wm_title("LoFASM Data Viewer")

#Buttons
button_plot = Tk.Button(root,text='plot',command=plot).grid(row=6,column=0)
button_help = Tk.Button(root,text='help').grid(row=6,column=1)
button_get  = Tk.Button(root,text='get',command=get).grid(row=6,column=2)
button_quit = Tk.Button(root,text='quit').grid(row=7,column=0)

#Labels
Tk.Label(master=root, text='File Name:').grid(row=0, column=0,sticky='E')
Tk.Label(master=root, text=sys.argv[1]).grid(row=0, column=1,columnspan=2)#.split('/')[-1][:20]+'...').grid(row=0, column=1)
Tk.Label(master=root, text="Lower Frequency:").grid(row=1,column=0,sticky='E')
Tk.Label(master=root, text="Upper Frequency:").grid(row=2,column=0,sticky='E')
Tk.Label(master=root, text="Upper Power:").grid(row=3,column=0,sticky='E')
Tk.Label(master=root, text="Lower Power:").grid(row=4,column=0,sticky='E')

Tk.Label(master=root, text=str(low_freq)+' MHz').grid(row=1, column=2,sticky='E')
Tk.Label(master=root, text=str(upper_freq)+' MHz').grid(row=2, column=2,sticky='E')
Tk.Label(master=root, text=str(low_power)+' dBm').grid(row=3, column=2,sticky='E')
Tk.Label(master=root, text=str(upper_power)+' dBm').grid(row=4, column=2,sticky='E')


#entry fields
lfEntry = Tk.Entry(master=root)
lfEntry.grid(row=1, column=1)
ufEntry = Tk.Entry(master=root)
ufEntry.grid(row=2, column=1)
upEntry = Tk.Entry(master=root)
upEntry.grid(row=3, column=1)
lpEntry = Tk.Entry(master=root)
lpEntry.grid(row=4, column=1)


#so it stays
root.mainloop()