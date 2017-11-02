# This is module to simulate time series
import numpy as np
import copy

class SeriesGen(object):
    """
       This a base class for series generation. Each type of series generator
       should be defined as a subclass.
    """
    def __init__(self):
        self.required_params = ['amp', ]

    def generate(self, t, **params):
        """
           This is a wrapper method to generate the time series. It wraps around
           the .gen_func method. Since .gen_func is assumed at amplitude 1.0,
           this method requires the amplitude as an input arguement.
        """
        for rp in self.required_params:
            if rp not in params:
                raise ValueError("Parameter '%s' is required to generate this time"
                                 " series."% rp)
        info = params
        return params['amp'] * self.gen_func(t, **params), info

    def gen_func(self, t, **params):
        """
           This is an abstract method for implement the time series generation.
           the out put time series amplitude is assumed to be 1.0.
        """
        raise NotImplementedError('Please use SeriesGen subclass to generate'
                                  ' the time series.')

class DCgen(SeriesGen):
    """ This class is for generate a DC signal
    """
    def __init__(self):
        super(DCgen, self).__init__()
    def gen_func(self, t, **params):
        return np.ones(len(t))

class WhiteNoiseGen(SeriesGen):
    """This class is for generate white noise.
    """
    def __init__(self):
        super(WhiteNoiseGen, self).__init__()
    def gen_func(self, t, mu, sigma, **params):
        return np.random.normal(mu, sigma, len(t))


class TimeSeries(object):
    """
       A class for holds a time series. The time is measured in seconds.
       Parameter
       ---------
       fs : float
           Sampling Rate.
       time_length : float
           Time lenght of the time series.
    """
    def __init__(self, name, fs, time_length, start_time=0.0, series_generator=None):
        self.name = name
        self.fs = fs
        self.time_length = time_length
        self.start_time = start_time
        self.end_time = self.start_time + self.time_length
        self.time_array = np.arange(self.start_time, self.end_time, 1.0/self.fs)
        self.num_bins = len(self.time_array)
        self.info = {}
        self.info[name] = {'amp':0.0, 'start_time': self.start_time, 'end_time': self.end_time}
        self.series_generator = series_generator
        self.data = np.zeros(self.num_bins)

    def __str__(self):
        out_str = 'Time Series %s Parameters:\n' % self.name
        out_str += 'Sampling Frequency    %s\n' % self.fs
        for k,v in zip(self.info[self.name].keys(), self.info[self.name].values()):
            out_str += k + '    ' + str(v) + '\n'
        out_str += 'It contains components of : \n['
        for k in self.info.keys():
            if k != self.name:
                out_str += k + ', '
        out_str += ']'
        return out_str

    def __add__(self, other):
        """
           This is a function to add two time series together. If the two time
           axis are not over lap, the time axis will be combined together.
        """
        if other.fs != self.fs:
            raise ValueError("Can not add two time series with different sampling rate.")
        new_name = 'total'

        if ((self.time_array == other.time_array)) and (self.time_array == other.time_array).all():
            new_start_time = self.start_time
            new_time_length = self.time_length
            new_series = TimeSeries(new_name, self.fs, new_time_length, new_start)
            new_series.data += self.data + other.data
            new_series.info.update(self.info)
            new_series.info.update(other.info)

        else: # match the time series.
            time_limits = np.array([self.start_time, self.end_time, other.start_time, other.end_time])
            new_start = time_limits.min()
            new_end = time_limits.max()
            new_time_length = new_end - new_start
            new_series = TimeSeries(new_name, self.fs, new_time_length, new_start)
            start_time_idx = np.zeros(2, dtype=int)
            for ii, t in enumerate(time_limits[[0,2]]):
                start_time_idx[ii] = (np.abs(new_series.time_array - t)).argmin()
            new_series.data[start_time_idx[0]:start_time_idx[0]+self.num_bins] += self.data
            new_series.data[start_time_idx[1]:start_time_idx[1]+other.num_bins] += other.data
            new_series.info.update(self.info)
            new_series.info.update(other.info)
            new_series.info[new_series.name]['amp'] = np.abs(new_series.data).max()
        return new_series

    def __neg__(self):
        new_series = TimeSeries('neg_'+self.name, self.fs, self.time_length, self.start_time)
        new_series.info[new_series.name].update(self.info[self.name])
        new_series.info[new_series.name]['amp'] = -new_series.info[new_series.name]['amp']
        new_series.data = -self.data
        return new_series

    def __sub__(self, other):
        return self.__add__(other.__neg__())

    def __mul__(self, number):
        new_series = TimeSeries(self.name + '_mul', self.fs, self.time_length, self.start_time)
        new_series.info[new_series.name].update(self.info[self.name])
        new_series.data = self.data * number
        new_series.info[new_series.name]['amp'] = new_series.data.max()
        new_series.info.update(self.info)
        return new_series

    def __div__(self, number):
        new_series = TimeSeries(self.name + '_div', self.fs, self.time_length, self.start_time)
        new_series.info[new_series.name].update(self.info[self.name])
        new_series.data = self.data / number
        new_series.info[new_series.name]['amp'] = new_series.data.max()
        new_series.info.update(self.info)
        return new_series

    def __imul__(self, number):
        self.data *= number
        self.info[self.name]['amp'] = self.data.max()
        return self

    def __idiv__(self, number):
        self.data /= number
        self.info[self.name]['amp'] = self.data.max()
        return self

    def __iadd__(self, other):
        if other.fs != self.fs:
            raise ValueError("Can not add two time series with different sampling rate.")

        if ((self.time_array == other.time_array)) and (self.time_array == other.time_array).all():
            new_start_time = self.start_time
            new_time_length = self.time_length
            self.data += other.data
            self.info.update(other.info)

        else: # match the time series.
            time_limits = np.array([self.start_time, self.end_time, other.start_time, other.end_time])
            new_start = time_limits.min()
            new_end = time_limits.max()
            self.time_length = new_end - new_start
            self.start_time = new_start
            self.end_time = new_end
            self.time_array = np.arange(new_start, new_end, 1.0/self.fs)
            new_num_bins = len(self.time_array)
            new_data = np.zeros(new_num_bins)
            start_time_idx = np.zeros(2, dtype=int)
            for ii, t in enumerate(time_limits[[0,2]]):
                start_time_idx[ii] = (np.abs(self.time_array - t)).argmin()
            new_data[start_time_idx[0]:start_time_idx[0]+self.num_bins] += self.data
            new_data[start_time_idx[1]:start_time_idx[1]+other.num_bins] += other.data
            # updata self
            self.data = new_data
            self.num_bins = new_num_bins
            self.info[self.name].update({'start_time': self.start_time, 'end_time': self.end_time})
            self.info.update(other.info)
            self.info[self.name]['amp'] = np.abs(self.data).max()
        return self

    def __isub__(self, other):
        return self.__iadd__(other.__neg__())

    def gen_time_series(self, **params):
        """
           This is method to generate a specific time series. It will rewrite the data.
        """
        self.data, par_info = self.series_generator().generate(self.time_array, **params)
        self.info[self.name].update(par_info)
