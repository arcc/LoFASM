#methods to simulate LoFASM signals
import numpy as np
from scipy import signal

def square_wave(f, fsamp=11.92, T=1.0, offset=0):
	'''
	return numpy array with square wave
	
	usage: s, t = square_wave(f, fsamp, T, offset)
	
	f is the frequency of the signal in Hz.
	
	fsamp is the sampling frequency in Hz.
	
	T is the length of the data in seconds.
	
	offset is the phase offset in radians.
	'''

	t = np.linspace(0, T, fsamp * T, endpoint=False)

	return signal.square(2*np.pi*f*t + offset), t
