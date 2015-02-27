#! /usr/bin/env python
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib.figure import Figure
import matplotlib.animation as animation
from lofasm import parse_data as pdat
import sys
import numpy as np
import argparse
from tkFileDialog import askopenfilename
matplotlib.pyplot.ion()
from lofasm.filter import running_median
import time
#from matplotlib import style

import Tkinter as tk
import ttk

#############################################
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
results.file_name = '/Users/andrewdanford/Desktop/DataAnalysis/20140912_174502.lofasm'



#line=a.plot([],[])[0]


class LoFASMGUIapp(tk.Tk):

    def __init__(self, *args, **kwargs):
        
        tk.Tk.__init__(self, *args, **kwargs)

        #tk.Tk.iconbitmap(self, default="clienticon.ico")
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

        for F in (StartPage, PageOne, PageTwo, PageThree):

            frame = F(container, self)

            self.frames[F] = frame

            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame(PageThree)


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

        self.button2 = ttk.Button(self, text="Visit Page 2",
                            command=lambda: controller.show_frame(PageTwo))
        self.button2.pack()

        self.button3 = ttk.Button(self, text="Graph Page",
                            command=lambda: controller.show_frame(PageThree))
        self.button3.pack()
class PageOne(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        label = tk.Label(self, text="Page One!!!")
        label.pack(pady=10,padx=10)

        button1 = ttk.Button(self, text="Back to Home",
                            command=lambda: controller.show_frame(StartPage))
        button1.pack()

        button2 = ttk.Button(self, text="Page Two",
                            command=lambda: controller.show_frame(PageTwo))
        button2.pack()
class PageTwo(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        label = tk.Label(self, text="Page Two!!!")
        label.grid(row=0 , column=0)

        button1 = ttk.Button(self, text="Back to Home",
                            command=lambda: controller.show_frame(StartPage))
        button1.grid(row=1 , column=0)

        button2 = ttk.Button(self, text="Page One",
                            command=lambda: controller.show_frame(PageOne))
        button2.grid(row=1 , column=1)
class PageThree(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.freqs = np.linspace(0, 200, 2048)
        self.crawler = pdat.LoFASMFileCrawler(results.file_name)
        self.create_figure()
        self.populate_page()
        self.play=True

    def populate_page(self):
        '''
        this creates the button, fields, and canvas. also grids them
        '''


        #Gui Row 0
        self.file_name_label=tk.Label(master=self, text='File Name:')
        self.file_name_label.grid(row=0, column=0,sticky='E')
        self.current_file_name_label=tk.Label(master=self, text=results.file_name)
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
        self.l3=tk.Label(master=self, text="Lower Frequency:")
        self.l3.grid(row=2,column=0,sticky='E')
        self.lfEntry = tk.Entry(master=self)
        self.lfEntry.grid(row=2, column=1)
        self.l7=tk.Label(master=self, text=str(results.lower_freq)+' MHz')
        self.l7.grid(row=2, column=2,sticky='E')

        #Gui Row 3
        self.l4=tk.Label(master=self, text="Upper Frequency:")
        self.l4.grid(row=3,column=0,sticky='E')
        self.ufEntry = tk.Entry(master=self)
        self.ufEntry.grid(row=3, column=1)
        self.l8=tk.Label(master=self, text=str(results.upper_freq)+' MHz')
        self.l8.grid(row=3, column=2,sticky='E')



        #Gui Row 4
        self.l5=tk.Label(master=self, text="Upper Power:")
        self.l5.grid(row=4,column=0,sticky='E')
        self.upEntry = tk.Entry(master=self)
        self.upEntry.grid(row=4, column=1)
        self.l10=tk.Label(master=self, text=str(results.upper_power)+' dBm')
        self.l10.grid(row=5, column=2,sticky='E')


        #Gui Row 5
        self.l6=tk.Label(master=self, text="Lower Power:")
        self.l6.grid(row=5,column=0,sticky='E')
        self.lpEntry = tk.Entry(master=self)
        self.lpEntry.grid(row=5, column=1)
        self.l9=tk.Label(master=self, text=str(results.lower_power)+' dBm')
        self.l9.grid(row=4, column=2,sticky='E')

        #Gui Row 6
        self.button_help = tk.Button(self,text='help').grid(row=6,column=0,sticky=tk.W+tk.E+tk.N+tk.S)#make the help button taller
        plot_runningmedian = tk.StringVar()
        plot_runningmedian.set("L") # initialize
        radiobutton_median = tk.Radiobutton(self, text='plot running median',variable=plot_runningmedian)
        radiobutton_median.grid(row=6,column=1)
        self.button_get  = tk.Button(self,text='get',command=lambda: self.get()).grid(row=6,column=2)

        #Gui Row 7
        
        self.button_plot = tk.Button(self,text='plot',command=lambda: self.plot()).grid(row=7, column=1, columnspan=2, rowspan=1,sticky=tk.W+tk.E+tk.N+tk.S)
        #self.button_quit = tk.Button(self,text='quit').grid(row=7,column=0)

        self.button_home = tk.Button(self,text='Home',command=lambda: controller.show_frame(StartPage)).grid(row=7 , column=0,sticky=tk.W+tk.E+tk.N+tk.S)
        #Gui Row 8
        tk.Button(self,text='newfunc').grid(row=8,column=0,sticky=tk.W+tk.E+tk.N+tk.S)

        #Create canvas's for the matplotlib figures
        canvas = FigureCanvasTkAgg(self.fig, self)
        canvas.show()
        canvas.get_tk_widget().grid(row=0 , column=3,rowspan=11)#.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)
        '''
        canvas2 = FigureCanvasTkAgg(f2 , self)
        canvas2.show()
        canvas2.get_tk_widget().grid(row=11 , column=0 , columnspan=4)
        
        
        toolbar = NavigationToolbar2TkAgg(canvas, self)
        toolbar.update()
        canvas._tkcanvas.grid(row=1 , column=3)#pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        '''

    def create_figure(self):
        '''
        create matplotlib figures
        '''
        self.fig = Figure(figsize=(4,3), dpi=100)
        self.pow_spec_plot = self.fig.add_subplot(111)
        self.pow_spec_plot.set_xlim(0,100)
        self.pow_spec_plot.set_ylim(0,100)
        self.line, = self.pow_spec_plot.plot([1,2,3],[1,2,3])
        #line.set_ydata([1,2,3])
        self.line.set_data(self.freqs,np.zeros(len(self.freqs)))
        print "figure got created"
        '''
        f2 = Figure(figsize=(7.5,3) , dpi=100)
        a2 = f.add_subplot(111)
        '''

    def get(self):
        '''
        retrieve values 
        '''
        if self.correlation_variable.get():
            results.current_correlation = self.correlation_variable.get()
            self.current_correlation_label.configure(text=results.current_correlation)
        if self.lfEntry.get():                   # If the Entry field is not empty 
            results.lower_freq = self.lfEntry.get() # Get the new value
            self.l7.configure(text=str(results.lower_freq)+' MHz') # update label
        if self.ufEntry.get():                   # If the Entry field is not empty 
            results.upper_freq = self.ufEntry.get() # Get the new value
            self.l8.configure(text=str(results.upper_freq)+' MHz') # update label
        if self.upEntry.get():                   # If the Entry field is not empty 
            results.upper_power = self.upEntry.get() # Get the new value
            self.l9.configure(text=str(results.upper_power)+' dBm') # update label
        if self.lpEntry.get():                   # If the Entry field is not empty 
            results.lower_power = self.lpEntry.get() # Get the new value
            self.l10.configure(text=str(results.lower_power)+' dBm') # update label

    def _open(self): 
        results.file_name = askopenfilename(filetypes=[("allfiles","*"),("binary files","*.dat"),("FITS files","*.fits"),("LoFASM Data Files","*.lofasm")]) #open data file, currently .lofasm
        
        tk.Label(master=self,text=results.file_name.split('/')[-1][:20]+'...').grid(row=0, column=1)
        
    def animate(self,i):
        power = 10*np.log10(self.crawler.autos[results.current_correlation])
        print "animate DID get run"

        if self.play == True:
            print 'i should be plotting'
            #self.pow_spec_plot.clear()
            #line.set_data(x,y)
            #self.pow_spec_plot.plot(self.freqs , power , linewidth=0.3)
            print len(self.freqs)
            print len(power)
            self.line.set_ydata(power)
            #self.pow_spec_plot.xlim=(int(results.lower_freq) , int(results.upper_freq))
            #self.pow_spec_plot.ylim=(int(results.lower_power) , int(results.upper_power))

            #self.pow_spec_plot.plot(self.freqs, 10*np.log10(running_median(crawler.autos[results.current_correlation],results.running_median_window)),'r')
            #a.xlim=(int(results.lower_freq) , int(results.upper_freq))
            #a.ylim=(int(results.lower_power) , int(results.upper_power))
            #a2.plot()
            self.crawler.forward()
            return self.line,
            
        else:
            pass

    def plot(self):
        '''
        '''
        if self.play == False:
            self.play = True
            print 'playing'
        else:
            self.play = False
            print "paused" 
if __name__ == '__main__':
    try:
        app = LoFASMGUIapp()
        anim = animation.FuncAnimation(app.frames[PageThree].fig , app.frames[PageThree].animate, init_func=None,frames=10000, interval=83, blit=False)
        app.mainloop()
    except KeyboardInterrupt:
        exit()






