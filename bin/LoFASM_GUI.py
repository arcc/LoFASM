#! /usr/bin/env python
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib.figure import Figure
import matplotlib.animation as animation
from lofasm import parse_data as pdat
import matplotlib.pyplot as plt
import sys
import numpy as np
import argparse
from tkFileDialog import askopenfilename
plt.ion()
from lofasm.filter import running_median
import time
import Tkinter as tk
import ttk
import thread
import struct
plt.rcParams['animation.ffmpeg_path'] = '/Users/andrewdanford/Desktop/ffmepg/ffmpeg'
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
default = 1, help='How many frames do you want to accumulate into each plot?')

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
        self.filter_bank_data = np.zeros((2048,64))
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

        self.fig = Figure(figsize=(13,11), dpi=75)

        self.populate_page()
        self.forward = True
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
        self.accumulation_stride_entry = tk.Entry(master=self)
        self.accumulation_stride_entry.grid(row=6, column=1)
        self.l12=tk.Label(master=self, text=str(results.accumulation_stride)+' integrations')
        self.l12.grid(row=6, column=2,sticky='E')

        #gui Row 7
        self.label_start_time=tk.Label(master=self, text="Start Time:")
        self.label_start_time.grid(row=7,column=0,sticky='E')
        self.start_time_entry = tk.Entry(master=self)
        self.start_time_entry.grid(row=7, column=1)
        self.l11=tk.Label(master=self, text='T+'+str(results.start_frame)+'sec')
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

        #Gui Row 10
        tk.Button(self,text='newfunc').grid(row=10,column=0,sticky=tk.W+tk.E+tk.N+tk.S)
        self.button_plot2 = tk.Button(self,text='colorplot').grid(row=10, column=1, columnspan=2, rowspan=1)#,sticky=tk.W+tk.E+tk.N+tk.S)
        self.button_save_movie  = tk.Button(self,text='save movie',command=lambda: self.save_movie()).grid(row=10,column=2)


        #pause play step button

        tk.Button(self,text='step back',command=lambda: self.step_backward()).grid(row=0,column=3,sticky=tk.W+tk.E)
        tk.Button(self,text='reverse').grid(row=0,column=4,sticky=tk.W+tk.E)
        tk.Button(self,text='play/pause',command=lambda: self.plot()).grid(row=0,column=5,sticky=tk.W+tk.E)
        tk.Button(self,text='step forward',command=lambda: self.step_forward()).grid(row=0,column=6,sticky=tk.W+tk.E)


        #Create canvas for the matplotlib figures
        canvas = FigureCanvasTkAgg(self.fig, self)
        canvas.show()
        canvas.get_tk_widget().grid(row=1 , column=3,rowspan=20,columnspan=4)#.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)


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
        #Create power spectrum subplot
        self.pow_spec_plot = self.fig.add_subplot(3,1,1)
        self.pow_spec_plot.set_xlim(0,100)
        self.pow_spec_plot.set_ylim(0,100)
        self.pow_spec_plot.set_ylabel('Power (dBm)')
        self.pow_spec_plot.set_xlabel('Frequency (MHz)')
        self.pow_spec_plot.set_title(self.file_date_string+'\n ' +self.file_time_string)
        self.line, = self.pow_spec_plot.plot([],[],linewidth=0.3)
        self.line.set_data(self.freqs,np.zeros(len(self.freqs)))



        #Create 'colorplot'
        self.filter_bank_plot = self.fig.add_subplot(3,1,(2,3))
        self.im = self.filter_bank_plot.imshow(self.filter_bank_data, aspect='auto',interpolation='none', cmap='spectral', extent=[(-63*0.083),(64*0.083),200,0])
        self.filter_bank_plot.set_ylim(0,100)
        self.filter_bank_plot.axvline(x=0, color='r',ymin=0, ymax=.5)
        self.filter_bank_plot.axvline(x=0, color='r',ymin=.5, ymax=1)
        self.filter_bank_plot.set_xlabel('Time (Seconds)')
        self.filter_bank_plot.set_ylabel('Frequency (MHz)')
        self.fig.colorbar(self.im, orientation='vertical')

    def step_forward(self):
        '''
        This function steps forward one integration.
        only use while paused
        '''
        if self.forward == False:
            for i in range(127):
                self.crawler_front.forward()
            self.forward = True
        corr=list(results.current_correlation)
        if corr[0]==corr[1]:
            data_to_average = []
            for i in range(int(results.accumulation_stride)):
                data_to_average.append(10*np.log10(self.crawler_front.autos[results.current_correlation]))
                self.crawler_front.forward()
            self.lofasm_data = np.average(data_to_average, axis=0)
        else:
            power_mid = 10*np.log10(self.crawler_mid.cross[results.current_correlation])
            power_front = 10*np.log10(self.crawler_front.autos[results.current_correlation])

        self.line.set_ydata(self.filter_bank_data[:,64])
        self.filter_bank_data = np.hstack((self.filter_bank_data,(self.lofasm_data).reshape((2048,1))))
        self.filter_bank_data = np.delete(self.filter_bank_data,0,1)
        self.im.set_data(self.filter_bank_data)
        self.update_time()
        self.pow_spec_plot.set_title(self.file_date_string+'\n ' +self.file_time_string)


    def step_backward(self):
        '''
        This function steps back one integration.
        only use while paused
        '''
        if self.forward == True:
            for i in range(127):
                print "going back" + str(i)
                self.crawler_front.backward()
            self.forward = False
        
        corr=list(results.current_correlation)
        if corr[0]==corr[1]:
            data_to_average = []
            for i in range(int(results.accumulation_stride)):
                data_to_average.append(10*np.log10(self.crawler_front.autos[results.current_correlation]))
                self.crawler_front.backward()
            self.lofasm_data = np.average(data_to_average, axis=0)
        else:
            power_mid = 10*np.log10(self.crawler_mid.cross[results.current_correlation])
            power_front = 10*np.log10(self.crawler_front.autos[results.current_correlation])

        self.line.set_ydata(self.filter_bank_data[:,63])
        self.filter_bank_data = np.hstack(((self.lofasm_data).reshape((2048,1)),self.filter_bank_data))
        self.filter_bank_data = np.delete(self.filter_bank_data,127,1)
        self.im.set_data(self.filter_bank_data)
        self.pow_spec_plot.set_title('T+'+str(round(self.t/(1/0.086),2)))
        self.t-=1

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
            self.pow_spec_plot.set_xlim(int(results.lower_freq),int(results.upper_freq))
            #print "```````````````````````````"+str(int(results.lower_freq)*(1/0.086))
            self.filter_bank_plot.set_ylim(int(results.lower_freq),int(results.upper_freq))

        if self.ufEntry.get():                   # If the Entry field is not empty 
            results.upper_freq = self.ufEntry.get() # Get the new value
            self.l8.configure(text=str(results.upper_freq)+' MHz') # update label
            self.pow_spec_plot.set_xlim(int(results.lower_freq),int(results.upper_freq))
            self.filter_bank_plot.set_ylim(int(results.lower_freq),int(results.upper_freq))

        if self.upEntry.get():                   # If the Entry field is not empty 
            results.upper_power = self.upEntry.get() # Get the new value
            self.l9.configure(text=str(results.upper_power)+' dBm') # update label
            self.pow_spec_plot.set_ylim(int(results.lower_power),int(results.upper_power))

        if self.lpEntry.get():                   # If the Entry field is not empty 
            results.lower_power = self.lpEntry.get() # Get the new value
            self.l10.configure(text=str(results.lower_power)+' dBm') # update label
            self.pow_spec_plot.set_ylim(int(results.lower_power),int(results.upper_power))

        if self.accumulation_stride_entry.get():                   # If the Entry field is not empty 
            results.accumulation_stride = self.accumulation_stride_entry.get() # Get the new value
            self.l12.configure(text=str(results.accumulation_stride)+' Integrations') # update label

        if self.start_time_entry.get():                   # If the Entry field is not empty 
            results.start_frame = self.start_time_entry.get() # Get the new value
            self.l11.configure(text='T+'+str(results.start_frame)+'sec')

    def load_file(self):
        '''
        Load lofil file into memory
        '''
        raw_lofil_data = self.lofil_file.read(2048*4*int(self.spec_amount))
        data_format = ">"+str(int(self.spec_amount)*2048)+"L"
        self.lofil_data_array = struct.unpack(data_format,raw_lofil_data)

    def get_file_info(self):
        '''
        retrieve information such as file data , time, and type
        '''
        #Get time info
        self.file_time_info = results.file_name.split('.')[0].split('/')[-1]
        self.file_year = self.file_time_info[0:4]
        self.file_month_number = self.file_time_info[4:6]
        months = ['January','February','March','April','May','June','July','August','September','October','November','December']
        self.file_month_name = months[int(self.file_month_number)]
        self.file_day = self.file_time_info[6:8]

        #this is the month day and year of the obs as a string
        self.file_date_string = self.file_month_name+' '+self.file_day+', '+self.file_year

        self.file_hour = self.file_time_info[9:11]
        self.file_minute =self.file_time_info[11:13]
        self.file_second = self.file_time_info[13:15]

        self.file_time_string = self.file_hour+':'+self.file_minute+':'+self.file_second


        #Get file type
        self.file_type = results.file_name.split('.')[1]
        print "this is the file type "+self.file_type

    def average_data(self):
        data_to_average = []
        for i in range(int(results.accumulation_stride)):
            data_to_average.append(10*np.log10(self.crawler_front.autos[results.current_correlation]))
            self.crawler_front.forward()
        self.lofasm_data = np.average(data_to_average, axis=0)


    def _open(self): 
        '''
        Opens file
        Currently supported file types: *.lofasm, *.lofil
        '''
        results.file_name = askopenfilename(filetypes=[("allfiles","*"),("binary files","*.dat"),("FITS files","*.fits"),("LoFASM Data Files","*.lofasm"),("LoFASM Data Files","*.lofil")]) #open data file, currently .lofasm
        self.get_file_info()
        tk.Label(master=self,text=results.file_name.split('/')[-1][:20]+'...').grid(row=0, column=1) #update file name into Gui


        if self.file_type == "lofasm":
            self.crawler_front = pdat.LoFASMFileCrawler(results.file_name)
            self.crawler_front.open()

            #change start time
            for i in range(int(float(results.start_frame)*(1/0.086))):
                self.crawler_front.forward()
                self.update_start_time()

            #read in first 64 integrations to populate the colorplot
            for i in range(63):
                if results.accumulation_stride == 1:
                    self.lofasm_data = 10*np.log10(self.crawler_front.autos[results.current_correlation])
                    self.crawler_front.forward()
                elif results.accumulation_stride > 1:
                    self.average_data()
                self.filter_bank_data = np.hstack((self.filter_bank_data, self.lofasm_data.reshape((2048,1))))
            print np.shape(self.filter_bank_data)

            self.create_figure()
            self.line.set_ydata(self.filter_bank_data[:,63])
            self.openedfile = True

        elif self.file_type == "lofil":
            self.lofil_file = open(results.file_name,'rb')
            self.lofil_file.read(30)
            self.spec_amount = self.lofil_file.read(10)
            self.lofil_file.read(70)
            print 'number of spectrum is '+str(int(self.spec_amount))
            self.load_file()
            self.lofil_file.seek(110)

            for self.current_spectrum in range(63):
                self.lofil_spectrum = self.lofil_data_array[(self.current_spectrum*2048):((self.current_spectrum+1)*2048)]
                self.lofil_spectrum = 10*np.log10(self.lofil_spectrum)
                self.filter_bank_data = np.hstack((self.filter_bank_data, self.lofil_spectrum.reshape((2048,1))))
                print self.current_spectrum
            self.create_figure()
            self.openedfile = True

    def update_start_time(self):
        self.file_hour = int(self.file_hour)
        self.file_minute =int(self.file_minute)
        self.file_second = float(self.file_second)
        self.file_second += 0.086

        if self.file_second >= 60:
            self.file_minute += 1
            self.file_second -= 60
        if self.file_minute >= 60:
            self.file_hour +=1
            self.file_minute -= 60
        self.file_time_string = str(self.file_hour)+':'+str(self.file_minute)+':'+str(self.file_second)

    def update_time(self):
        self.file_hour = int(self.file_hour)
        self.file_minute =int(self.file_minute)
        self.file_second = float(self.file_second)
        self.file_second += round((int(results.accumulation_stride)/(1/0.086)),2)

        while self.file_second >= 60:
            self.file_minute += 1
            self.file_second -= 60
        while self.file_minute >= 60:
            self.file_hour +=1
            self.file_minute -= 60
        self.file_time_string = str(self.file_hour)+':'+str(self.file_minute)+':'+str(self.file_second)

    def animate(self,i):

        #wait for a lofasm file to be opened
        if not self.openedfile:
            return

        if self.file_type == "lofasm":

            #check if auto or cross correlation
            corr=list(results.current_correlation)
            if corr[0]==corr[1]:
                self.average_data()
            else:
                power_front = 10*np.log10(self.crawler_front.cross[results.current_correlation])

            #Animate if play button has been presses
            if self.play == True:
                self.line.set_ydata(self.filter_bank_data[:,63])
                self.crawler_front.forward()
                self.filter_bank_data = np.hstack((self.filter_bank_data,(self.lofasm_data).reshape((2048,1))))
                self.filter_bank_data = np.delete(self.filter_bank_data,0,1)
                self.im.set_data(self.filter_bank_data)
                self.update_time()
                self.pow_spec_plot.set_title(self.file_date_string+'\n ' +self.file_time_string)
                #self.t+=int(results.accumulation_stride)

            else:
                pass

        elif self.file_type == "lofil":
            if self.play == True:
                self.current_spectrum+=1
                #print 'plotting spectrum number'+str(self.current_spectrum)
                self.line.set_ydata(self.lofil_spectrum)
                self.lofil_spectrum = self.lofil_data_array[(self.current_spectrum*2048):((self.current_spectrum+1)*2048)]
                self.lofil_spectrum = 10*np.log10(self.lofil_spectrum)
                self.filter_bank_data = np.hstack((self.filter_bank_data,(self.lofil_spectrum).reshape((2048,1))))
                self.filter_bank_data = np.delete(self.filter_bank_data,0,1)
                self.im.set_data(self.filter_bank_data)
                self.pow_spec_plot.set_title('T+'+str(round(self.current_spectrum/(1/0.086),2))+ '\n' +str(self.current_spectrum))
                

            else:
                pass

    def init(self):
        self.pow_spec_plot = []
        self.lofil_spectrum = []
        self.filter_bank_data = []
        return self.lofil_spectrum , self.filter_bank_data, self.pow_spec_plot

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

    def save_movie(self):
        FFwriter = animation.FFMpegWriter()
        anim.save('basic_animation.mp4', writer = FFwriter, fps=30, extra_args=['-vcodec', 'libx264'])

if __name__ == '__main__':
    try:
        app = LoFASMGUIapp()

        anim = animation.FuncAnimation(app.frames[GraphPage].fig,
            app.frames[GraphPage].animate,
            init_func=None,
            frames=10000, interval=125, blit=False)

        app.mainloop()

    except KeyboardInterrupt:
        exit()






