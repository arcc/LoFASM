#!/usr/bin/env python
import matplotlib
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib.figure import Figure
import matplotlib.animation as animation
from lofasm import parse_data as pdat
from lofasm.filter import running_median
import matplotlib.pyplot as plt
import sys
import numpy as np
import argparse
from tkFileDialog import askopenfilename
plt.ion()
import time
import Tkinter as tk
import ttk
import matplotlib.pyplot as plt
import thread
import os
import warnings

warnings.filterwarnings('ignore',r'divide by zero encountered in log10')

#############################################
#### this uses argparse to create a help menu
parser = argparse.ArgumentParser()

parser.add_argument('-lf', '--lower_frequency', action='store', dest='lower_freq',
default = 0, help='What is the lower frequency?')

parser.add_argument('-uf', '--upper_frequency', action='store', dest='upper_freq',
default = 100, help='What is the upper frequency?')

parser.add_argument('-up', '--upper_power', action='store', dest='upper_power',
default = 100, help='What is the upper power?')

parser.add_argument('-lp', '--lower_power', action='store', dest='lower_power',
default = 0, help='What is the lower power?')

parser.add_argument('-sf', '--start_frame', action='store', dest='start_frame',
default = 0, help='What frame do you want to start on? (each frame is 40ms)')

parser.add_argument('-rl', '--read_length', action='store', dest='read_length',
default = 1000, help='How many accumulations do you want to plot?')

parser.add_argument('-as', '--accumulation_stride', action='store', dest='accumulation_stride',
default = 5, help='How many frames do you want to accumulate into each plot?')

parser.add_argument('-d', '--delay', action='store', dest='delay',
default = 0.2, help='How long do you want to wait until redrawing the plot?')

parser.add_argument('-f', '--file_name', action='store', dest= 'file_name',
default = '', help='What file do you want to read?')

parser.add_argument('-cr', '--correlation', action='store', dest='current_correlation',
default = 'AA', help='Which correlation do you want to plot?')

parser.add_argument('-rmw', '--running_median_window', action='store', dest='running_median_window',
default = '50', help='How many frames to running median?')

parser.add_argument('--version', action='version', version='%(prog)s 1.0')

results = parser.parse_args()



class LoFASMGUIapp(tk.Tk):

    def __init__(self, *args, **kwargs):

        tk.Tk.__init__(self, *args, **kwargs)

        tk.Tk.wm_title(self, "LoFASM Client")


        container = tk.Frame(self)
        container.pack(side="top", fill="both", expand = True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)
        menubar = tk.Menu(container)
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="Save settings")
        filemenu.add_separator()
        filemenu.add_command(label="Exit")#, command=exit)
        menubar.add_cascade(label="File", menu=filemenu)
        tk.Tk.config(self, menu=menubar)


        self.frames = {}

        for F in (StartPage, PageOne, GraphPage):

            frame = F(container, self)

            self.frames[F] = frame

            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame(GraphPage)


    def show_frame(self, cont):
        '''
        '''

        frame = self.frames[cont]
        frame.tkraise()
class StartPage(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self,parent)
        label = tk.Label(self, text="Start Page")
        label.pack(pady=10,padx=10)

        self.button = ttk.Button(self, text="Visit Page 1",
                            command=lambda: controller.show_frame(PageOne))
        self.button.pack()

        self.button3 = ttk.Button(self, text="Graph Page",
                            command=lambda: controller.show_frame(GraphPage))
        self.button3.pack()
class PageOne(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        label = tk.Label(self, text="Page One!!!")
        label.pack(pady=10,padx=10)

        button1 = ttk.Button(self, text="Back to Home",
                            command=lambda: controller.show_frame(StartPage))
        button1.pack()
class GraphPage(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.freqs = np.linspace(0, 200, 2048)
        self.filter_bank_data = np.zeros((2048,65))
        self.t = 0
        self.openedfile = False

        self.button_home = tk.Button(self,text='Home',command=lambda: controller.show_frame(StartPage)).grid(row=9 , column=0)

        self.top = tk.Toplevel()
        self.top.title("About this application...")

        msg = tk.Message(self.top, text='about_message')
        msg.pack()

        button = tk.Button(self.top, text="Dismiss", command=self.top.destroy)
        button.pack()

        #self.create_figure()

        self.fig = Figure(figsize=(8,6), dpi=75)

        self.populate_page()
        self.play=False

    def populate_page(self):
        '''
        this creates the button, fields, and canvas. also grids them
        '''


        #Gui Row 0
        self.file_name_label=tk.Label(master=self, text='File Name:')
        self.file_name_label.grid(row=0, column=0,sticky='E')
        self.current_file_name_label=tk.Label(master=self, text=results.file_name.split('/')[-1])
        self.current_file_name_label.grid(row=0, column=1)
        self.button_open = tk.Button(self,text='open',command=lambda: self._open()).grid(row=0,column=2)

        #Gui Row 1
        self.correlation_label=tk.Label(master=self, text="Correlation to Plot:")
        self.correlation_label.grid(row=1,column=1,sticky='E')
        self.correlation_variable = tk.StringVar(self)
        self.correlation_variable.set('AA') # initial value
        option = tk.OptionMenu(self, self.correlation_variable,'AA','BB','CC','DD','AB','AC','AD','BC','BD','CD')
        option.grid(row=1 , column=0)
        self.current_correlation_label=tk.Label(master=self, text=results.current_correlation)
        self.current_correlation_label.grid(row=1,column=2)

        #Gui Row 2
        self.l4=tk.Label(master=self, text="Upper Frequency:")
        self.l4.grid(row=2,column=0,sticky='E')
        self.ufEntry = tk.Entry(master=self)
        self.ufEntry.grid(row=2, column=1)
        self.l8=tk.Label(master=self, text=str(results.upper_freq)+' MHz')
        self.l8.grid(row=2, column=2,sticky='E')


        #Gui Row 3
        self.l3=tk.Label(master=self, text="Lower Frequency:")
        self.l3.grid(row=3,column=0,sticky='E')
        self.lfEntry = tk.Entry(master=self)
        self.lfEntry.grid(row=3, column=1)
        self.l7=tk.Label(master=self, text=str(results.lower_freq)+' MHz')
        self.l7.grid(row=3, column=2,sticky='E')




        #Gui Row 4
        self.l5=tk.Label(master=self, text="Upper Power:")
        self.l5.grid(row=4,column=0,sticky='E')
        self.upEntry = tk.Entry(master=self)
        self.upEntry.grid(row=4, column=1)
        self.l9=tk.Label(master=self, text=str(results.upper_power)+' dBm')
        self.l9.grid(row=4, column=2,sticky='E')


        #Gui Row 5
        self.l6=tk.Label(master=self, text="Lower Power:")
        self.l6.grid(row=5,column=0,sticky='E')
        self.lpEntry = tk.Entry(master=self)
        self.lpEntry.grid(row=5, column=1)
        self.l10=tk.Label(master=self, text=str(results.lower_power)+' dBm')
        self.l10.grid(row=5, column=2,sticky='E')

        #GUI row 6
        self.label_acc_stride=tk.Label(master=self, text="Acc stride:")
        self.label_acc_stride.grid(row=6,column=0,sticky='E')
        self.label_acc_stride_Entry = tk.Entry(master=self)
        self.label_acc_stride_Entry.grid(row=6, column=1)
        self.l12=tk.Label(master=self, text=str(results.accumulation_stride)+' integrations')
        self.l12.grid(row=6, column=2,sticky='E')

        #gui Row 7
        self.label_power=tk.Label(master=self, text="Start Time:")
        self.label_power.grid(row=7,column=0,sticky='E')
        self.label_power_Entry = tk.Entry(master=self)
        self.label_power_Entry.grid(row=7, column=1)
        self.l11=tk.Label(master=self, text='T+ 00:00:00.00')
        self.l11.grid(row=7, column=2,sticky='E')



        #Gui Row 8
        self.button_help = tk.Button(self,text='help').grid(row=8,column=0)#,sticky=tk.W+tk.E+tk.N+tk.S)#make the help button taller
        plot_runningmedian = tk.StringVar()
        plot_runningmedian.set("L") # initialize
        radiobutton_median = tk.Radiobutton(self, text='plot running median',variable=plot_runningmedian)
        radiobutton_median.grid(row=8,column=1)
        self.button_get  = tk.Button(self,text='get',command=lambda: self.get()).grid(row=8,column=2)

        #Gui Row 9

        self.button_plot = tk.Button(self,text='plot',command=lambda: self.plot()).grid(row=9, column=1, columnspan=2, rowspan=1)#,sticky=tk.W+tk.E+tk.N+tk.S)
        #self.button_quit = tk.Button(self,text='quit').grid(row=7,column=0)

        #self.button_home = tk.Button(self,text='Home',command=lambda: controller.show_frame(StartPage)).grid(row=7 , column=0)#,sticky=tk.W+tk.E+tk.N+tk.S)
        #Gui Row 8
        tk.Button(self,text='newfunc').grid(row=10,column=0,sticky=tk.W+tk.E+tk.N+tk.S)
        self.button_plot2 = tk.Button(self,text='colorplot').grid(row=10, column=1, columnspan=2, rowspan=1)#,sticky=tk.W+tk.E+tk.N+tk.S)


        #pause play step button

        tk.Button(self,text='step back').grid(row=0,column=3,sticky=tk.W+tk.E)
        tk.Button(self,text='play/pause',command=lambda: self.plot()).grid(row=0,column=4,sticky=tk.W+tk.E)
        tk.Button(self,text='step forward',command=lambda: self.step_forward()).grid(row=0,column=5,sticky=tk.W+tk.E)
        #tk.Scale(self, from_=0, to=200, orient=tk.HORIZONTAL).grid(row=1,column=3,columnspan=3,sticky=tk.W+tk.E)
        ttk.Scrollbar(self,orient=tk.HORIZONTAL).grid(row=1,column=3,columnspan=3,sticky=tk.W+tk.E)

        #Create canvas for the matplotlib figures
        canvas = FigureCanvasTkAgg(self.fig, self)
        canvas.show()
        canvas.get_tk_widget().grid(row=2 , column=3,rowspan=11,columnspan=3)#.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)


        '''
        canvas2 = FigureCanvasTkAgg(self.fig2 , self)
        canvas2.show()
        canvas2.get_tk_widget().grid(row=11 , column=0 , columnspan=4)


        toolbar = NavigationToolbar2TkAgg(canvas, self)
        toolbar.update()
        canvas._tkcanvas.grid(row=1 , column=12)#pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        '''

    def create_figure(self):
        '''
        create matplotlib figures
        '''
        #self.fig = Figure(figsize=(8,6), dpi=75)
        self.pow_spec_plot = self.fig.add_subplot(211)
        self.pow_spec_plot.set_xlim(0,100)
        self.pow_spec_plot.set_ylim(0,100)
        self.pow_spec_plot.set_ylabel('Power (dBm)')
        self.pow_spec_plot.set_xlabel('Frequency (MHz)')
        self.pow_spec_plot.set_title('T+00:00:00.00blah blah blah')
        self.line, = self.pow_spec_plot.plot([],[],linewidth=0.3)
        self.line.set_data(self.freqs,np.zeros(len(self.freqs)))



        #self.fig2 = Figure(figsize=(12,4), dpi=75)
        self.filter_bank_plot = self.fig.add_subplot(212)
        self.im = self.filter_bank_plot.imshow(self.filter_bank_data, aspect='auto',interpolation='none', cmap='spectral')
        #self.im.set_data(self.filter_bank_data)
        self.filter_bank_plot.set_ylim(0,1024)
        self.filter_bank_plot.axvline(x=64, color='r')
        self.filter_bank_plot.set_xlabel('Time (bins)')
        self.filter_bank_plot.set_ylabel('Frequency (bins)')
        self.fig.colorbar(self.im, orientation='vertical')
        #self.filter_bank_plot.show()

    def step_forward(self):
        corr=list(results.current_correlation)
        if corr[0]==corr[1]:
            power_mid = 10*np.log10(self.crawler_mid.autos[results.current_correlation])
            power_front = 10*np.log10(self.crawler_front.autos[results.current_correlation])
        else:
            power_mid = 10*np.log10(self.crawler_mid.cross[results.current_correlation])
            power_front = 10*np.log10(self.crawler_front.autos[results.current_correlation])

        self.line.set_ydata(power_front)
        self.crawler_mid.forward()
        self.crawler_front.forward
        self.filter_bank_data = np.hstack((self.filter_bank_data,(power_mid).reshape((2048,1))))
        self.filter_bank_data = np.delete(self.filter_bank_data,0,1)
        self.im.set_data(self.filter_bank_data)
        self.pow_spec_plot.set_title('T+'+str(round(self.t/10.24,2)))
        self.t+=1

    def step_backward(self):
        corr=list(results.current_correlation)
        if corr[0]==corr[1]:
            power_mid = 10*np.log10(self.crawler_mid.autos[results.current_correlation])
            power_front = 10*np.log10(self.crawler_front.autos[results.current_correlation])
        else:
            power_mid = 10*np.log10(self.crawler_mid.cross[results.current_correlation])
            power_front = 10*np.log10(self.crawler_front.autos[results.current_correlation])

        self.crawler.backward()
        self.filter_bank_data = np.hstack((self.filter_bank_data,(power_mid).reshape((2048,1))))
        self.filter_bank_data = np.delete(self.filter_bank_data,0,1)
        self.im.set_data(self.filter_bank_data)
        self.pow_spec_plot.set_title('T+'+str(round(self.t/10.24,2)))
        self.t-=1

    def get(self):
        '''
        retrieve values
        '''
        if self.correlation_variable.get():
            results.current_correlation = self.correlation_variable.get()
            self.current_correlation_label.configure(text=results.current_correlation)

        if self.lfEntry.get():                   # If the Entry field is not empty
            results.lower_freq = float(self.lfEntry.get()) # Get the new value
            self.l7.configure(text=str(results.lower_freq)+' MHz') # update label
            #self.pow_spec_plot.set_xlim(int(results.lower_freq),int(results.upper_freq))
            #self.filter_bank_plot.set_ylim(int(int(results.lower_freq)*10.24),int(int(results.upper_freq)*10.24))
            self.pow_spec_plot.set_xlim(pdat.freq2bin(results.lower_freq),pdat.freq2bin(results.upper_freq))
            self.filter_bank_plot.set_ylim(pdat.freq2bin(results.lower_freq),pdat.freq2bin(results.upper_freq))

        if self.ufEntry.get():                   # If the Entry field is not empty
            results.upper_freq = float(self.ufEntry.get()) # Get the new value
            self.l8.configure(text=str(results.upper_freq)+' MHz') # update label
            #self.pow_spec_plot.set_xlim(int(results.lower_freq),int(results.upper_freq))
            #self.filter_bank_plot.set_ylim(int(int(results.lower_freq)*10.24),int(int(results.upper_freq)*10.24))
            self.pow_spec_plot.set_xlim(pdat.freq2bin(results.lower_freq),pdat.freq2bin(results.upper_freq))
            self.filter_bank_plot.set_ylim(pdat.freq2bin(results.lower_freq),pdat.freq2bin(results.upper_freq))

        if self.upEntry.get():                   # If the Entry field is not empty
            results.upper_power = self.upEntry.get() # Get the new value
            self.l9.configure(text=str(results.upper_power)+' dBm') # update label
            self.pow_spec_plot.set_ylim(int(results.lower_power),int(results.upper_power))

        if self.lpEntry.get():                   # If the Entry field is not empty
            results.lower_power = self.lpEntry.get() # Get the new value
            self.l10.configure(text=str(results.lower_power)+' dBm') # update label
            self.pow_spec_plot.set_ylim(int(results.lower_power),int(results.upper_power))

    def _open(self):
        results.file_name = askopenfilename(filetypes=[("allfiles","*"),("binary files","*.dat"),("FITS files","*.fits"),("LoFASM Data Files","*.lofasm")]) #open data file, currently .lofasm
        #tk.Label(master=self,text=results.file_name.split('/')[-1][:20]+'...').grid(row=0, column=1)
        tk.Label(master=self,text=os.path.basename(results.file_name)[:20]
                 +'...').grid(row=0, column=1)

        self.crawler_mid = pdat.LoFASMFileCrawler(results.file_name)
        self.crawler_front = pdat.LoFASMFileCrawler(results.file_name)
        self.crawler_mid.open()
        self.crawler_front.open()

        for i in range(63):
            data = 10*np.log10(self.crawler_front.autos[results.current_correlation])
            self.filter_bank_data = np.hstack((self.filter_bank_data, data.reshape((2048,1))))
            self.crawler_front.forward()
        print np.shape(self.filter_bank_data)

        self.create_figure()

        self.openedfile = True

    def animate(self,i):
        #a = time.time()

        #wait for a lofasm file to be opened
        if not self.openedfile:
            return

        corr=list(results.current_correlation)
        if corr[0]==corr[1]:
            power_mid = 10*np.log10(self.crawler_mid.autos[results.current_correlation])
            power_front = 10*np.log10(self.crawler_front.autos[results.current_correlation])
        else:
            power_mid = 10*np.log10(self.crawler_mid.cross[results.current_correlation])
            power_front = 10*np.log10(self.crawler_front.autos[results.current_correlation])
        #print str(time.time()-a)+'second to read data'
        if self.play == True:

            self.line.set_ydata(power_mid)

            print "front"
            a = time.time()
            self.crawler_front.forward()

            self.crawler_mid.forward()
            print time.time()-a
            print '````'
            self.filter_bank_data = np.hstack((self.filter_bank_data,(power_front).reshape((2048,1))))
            self.filter_bank_data = np.delete(self.filter_bank_data,0,1)
            self.im.set_data(self.filter_bank_data)
            self.pow_spec_plot.set_title('T+'+str(round(self.t/10.24,2)))
            self.t+=1

        else:
            pass

    def animate2(self,i):
        a = time.time()
        corr=list(results.current_correlation)
        if corr[0]==corr[1]:
            power = 10*np.log10(self.crawler.autos[results.current_correlation])
        else:
            power = 10*np.log10(self.crawler.cross[results.current_correlation])
        print 'it took '+str(time.time()-a)+"to do that"

        if self.play == True:
            self.crawler.forward()
            #stuff = np.linspace(0,500,2048)
            #print power[300:500]
            self.filter_bank_data = np.hstack((self.filter_bank_data,(power).reshape((2048,1))))

            self.filter_bank_data = np.delete(self.filter_bank_data,0,1)
            print self.filter_bank_data[400:500,-1]
            #self.im.autoscale()

            self.im.set_data(self.filter_bank_data)
            #self.crawler.forward()

            return  self.im,
        else:
            pass

    def plot(self):
        '''
        '''
        if self.play == False:
            self.play = True
            self.pow_spec_plot.set_xlim(results.lower_freq,results.upper_freq)
            self.pow_spec_plot.set_ylim(results.lower_power,results.upper_power)
            print 'playing'
        else:
            self.play = False
            print "paused"


if __name__ == '__main__':
    try:
        app = LoFASMGUIapp()

        anim = animation.FuncAnimation(app.frames[GraphPage].fig,
            app.frames[GraphPage].animate,
            init_func=None,
            frames=10000, interval=83.*1.5, blit=False)
        app.mainloop()
    except KeyboardInterrupt:
        exit()






