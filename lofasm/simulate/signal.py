#methods to simulate LoFASM signals
import numpy as np
from scipy import signal

def square_wave(f, fsamp=11.92, T=1.0):
	'''
	return numpy array with square wave
	f is the frequency of the signal in Hz
	fsamp is the sampling frequency in Hz
	T is the length of the data in seconds
	'''

	t = np.linspace(0, T, fsamp * T, endpoint=False)

	return signal.square(2*np.pi*f*t) + 1, t
