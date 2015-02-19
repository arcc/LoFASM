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
matplotlib.pyplot.ion()
#from matplotlib import style

import Tkinter as tk
import ttk


LARGE_FONT= ("Verdana", 12)
#style.use("ggplot")



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

parser.add_argument('-cr', '--correlation', action='store', dest='correlation',
default = 'AA', help='Which correlation do you want to plot?')

parser.add_argument('--version', action='version', version='%(prog)s 1.0')

results = parser.parse_args()

f = Figure(figsize=(5,5), dpi=100)
a = f.add_subplot(111)


global play , crawler , x
play = False
crawler = pdat.LoFASMFileCrawler(results.file_name)
x = np.linspace(0, 200, 2048)

#line=a.plot([],[])[0]

def animate(i):
    global play , x
    

    y = 10*np.log10(crawler.autos[results.correlation])
    if play == True:
        a.clear()
        #line.set_data(x,y)
        a.plot(x , y , linewidth=0.3)
        a.xlim=(int(results.lower_freq) , int(results.upper_freq))
        a.ylim=(int(results.lower_power) , int(results.upper_power))
        crawler.forward()
        
    else:
        pass

    

    
            

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
        filemenu.add_command(label="Save settings", command=lambda: popupmsg('Not supported just yet!'))
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=quit)
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

    def plot(self):
        '''
        '''
        global play
        if play == False:
            play = True
        else:
            play = False
            print "stopped"

 

        
class StartPage(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self,parent)
        label = tk.Label(self, text="Start Page", font=LARGE_FONT)
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
        label = tk.Label(self, text="Page One!!!", font=LARGE_FONT)
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
        label = tk.Label(self, text="Page Two!!!", font=LARGE_FONT)
        label.grid(row=0 , column=0)#pack(pady=10,padx=10)

        button1 = ttk.Button(self, text="Back to Home",
                            command=lambda: controller.show_frame(StartPage))
        button1.grid(row=1 , column=0)

        button2 = ttk.Button(self, text="Page One",
                            command=lambda: controller.show_frame(PageOne))
        button2.grid(row=1 , column=1)


class PageThree(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)


        #Buttons
        self.button_open = tk.Button(self,text='open').grid(row=0,column=2)
        self.button_plot = tk.Button(self,text='plot',
            command=lambda: controller.plot()).grid(row=6,column=0)
        self.button_help = tk.Button(self,text='help').grid(row=6,column=1)
        self.button_get  = tk.Button(self,text='get',
            command = self.get).grid(row=6,column=2)
        self.button_quit = tk.Button(self,text='quit').grid(row=7,column=0)
        self.button_home = tk.Button(self,text='Home',
            command=lambda: controller.show_frame(StartPage)).grid(row=7 , column=1)

        #Labels
        self.l1=tk.Label(master=self, text='File Name:')
        self.l1.grid(row=0, column=0,sticky='E')

        self.l2=tk.Label(master=self, text=results.file_name)
        self.l2.grid(row=0, column=1)

        self.l3=tk.Label(master=self, text="Lower Frequency:")
        self.l3.grid(row=1,column=0,sticky='E')

        self.l4=tk.Label(master=self, text="Upper Frequency:")
        self.l4.grid(row=2,column=0,sticky='E')

        self.l5=tk.Label(master=self, text="Upper Power:")
        self.l5.grid(row=3,column=0,sticky='E')

        self.l6=tk.Label(master=self, text="Lower Power:")
        self.l6.grid(row=4,column=0,sticky='E')

        self.l7=tk.Label(master=self, text=str(results.lower_freq)+' MHz')
        self.l7.grid(row=1, column=2,sticky='E')

        self.l8=tk.Label(master=self, text=str(results.upper_freq)+' MHz')
        self.l8.grid(row=2, column=2,sticky='E')

        self.l9=tk.Label(master=self, text=str(results.lower_power)+' dBm')
        self.l9.grid(row=3, column=2,sticky='E')

        self.l10=tk.Label(master=self, text=str(results.upper_power)+' dBm')
        self.l10.grid(row=4, column=2,sticky='E')


        #entry fields
        self.lfEntry = tk.Entry(master=self)
        self.lfEntry.grid(row=1, column=1)
        self.ufEntry = tk.Entry(master=self)
        self.ufEntry.grid(row=2, column=1)
        self.upEntry = tk.Entry(master=self)
        self.upEntry.grid(row=3, column=1)
        self.lpEntry = tk.Entry(master=self)
        self.lpEntry.grid(row=4, column=1)


        canvas = FigureCanvasTkAgg(f, self)
        canvas.show()
        canvas.get_tk_widget().grid(row=0 , column=3,rowspan=1000)#.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)
        '''
        toolbar = NavigationToolbar2TkAgg(canvas, self)
        toolbar.update()
        canvas._tkcanvas.grid(row=1 , column=3)#pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        '''

    def get(self):
        '''
        '''
        if self.lfEntry.get():                   # If the Entry field is not empty 
            results.lower_freq = self.lfEntry.get() # Get the new value
            self.l7.configure(text=str(results.lower_freq)+' MHz') # update label
            print "The new Lower Frequency is ",results.lower_freq #print to terminal for shits and gigs

            
        

    

  
            


app = LoFASMGUIapp()
ani = animation.FuncAnimation(f, animate, interval=50,init_func=None,blit=False)
app.mainloop()