import numpy as np
from ..bbx.bbx import LofasmFile as lfbbx
import abc
import six
#from astropy import log


class DataGenMeta(abc.ABCMeta):
    """
    This is a Meta class for filter bank data generator registeration. In order
    ot get a data generator registered, a member called 'register' has to be set
    true in the FilterBankGen subclass.
    """
    def __init__(cls, name, bases, dct):
        regname = '_data_gen_list'
        if not hasattr(cls,regname):
            setattr(cls,regname,{})
        if 'register' in dct:
            if cls.register:
                getattr(cls,regname)[name] = cls
        super(DataGenMeta, cls).__init__(name, bases, dct)


@six.add_metaclass(DataGenMeta)
class FilterBankGen(object):
    """This is a class to generate filter bank data.
    """
    full_name = ''
    @classmethod
    def data_gen_help(cls, detail=False):
        if hasattr(cls, '__name__'):
            result = "Class '%s' is a '%s' simulator.\n" % (cls.__name__, cls.full_name)
        else:
            result = "Object '%s' is a '%s' simulator.\n" % (cls.__class__.__name__, \
                    cls.full_name)
        if detail:
            result += cls.gen_func.__doc__
        return result


    def __init__(self, resolution_time, time_bin, resolution_freq, freq_bin):
        self.resolution_time = resolution_time
        self.time_bin = int(time_bin)
        self.resolution_freq = resolution_freq
        self.freq_bin = int(freq_bin)


    def gen_func(self, **kwarg):
        raise NotImplementedError

class UniformDataGen(FilterBankGen):
    """This is a class to generate filter bank data.
    """
    register = True
    full_name = 'Filter bank uniformed data generator'
    category = 'noise'
    def __init__(self, resolution_time, time_bin, resolution_freq, freq_bin):
        super(UniformDataGen, self).__init__(resolution_time, time_bin, resolution_freq,\
                                             freq_bin)
    def gen_func(self, amp=1.0,**kwarg):
        """
        Parameter
        ---------
        amp: float, optional
            The amplitude of uniformed data.
        """
        data = amp * np.ones((self.freq_bin, self.time_bin))
        return data

class FBWhiteNoiseGen(FilterBankGen):
    """This is a class to generate filter bank data.
    """
    register = True
    full_name = 'Filter bank white noise generator'
    category = 'noise'
    def __init__(self, resolution_time, time_bin, resolution_freq, freq_bin):
        super(FBWhiteNoiseGen, self).__init__(resolution_time, time_bin, resolution_freq,\
                                              freq_bin)
    def gen_func(self, amp=1.0, offset=0.0, **kwarg):
        """
        This is a filter bank white noise generator.
        Parameter
        ---------
        amp: float, optional
            Amplitude of white noise.
        offset: float, optional
            DC offset from zero
        """
        data = amp * np.random.randn(self.freq_bin, self.time_bin) + offset
        return data

class GaussianPulseGen(FilterBankGen):
    """This is a class to generate Gaussian pulse in filter bank data.
    """
    register = True
    full_name = 'Filter bank gussian pulse generator'
    category = 'signal'
    def __init__(self, resolution_time, time_bin, resolution_freq, freq_bin):
        super(GaussianPulseGen, self).__init__(resolution_time, time_bin, resolution_freq,\
                                              freq_bin)

    def gen_func(self, amp=1.0, center_time_bin=0, center_freq_bin=0,\
                 std_time=1, std_freq=1, **kwarg):
        """
        This is a filter bank gussian signal generator. The signal will be a
        gaussian shape in both frequency and time.
        Parameter
        ---------
        amp: float
            Amplitude of the signal.(The peak value of the signal)
        center_time_bin: int
            The signal peak bin in time.
        center_freq_bin: int
            The signal peak bin in frequency
        std_time: float
            Standard deviation in time
        std_freq: float
            Standard deviation in frequency
        """
        time_axis = np.arange(0, self.resolution_time * self.time_bin, self.resolution_time)
        freq_axis = np.arange(0, self.resolution_freq * self.freq_bin, self.resolution_freq)
        center_t = time_axis[int(center_time_bin)]
        center_f = freq_axis[int(center_freq_bin)]
        g_data = np.zeros((self.freq_bin, self.time_bin))
        for ii, tt in enumerate(time_axis):
            for jj, ff in enumerate(freq_axis):
                exponent = -(tt - center_t)**2/(2 * std_time**2) - \
                            (ff - center_f)**2/(2 * std_freq**2)
                #g_data[ii,jj] = 1.0/(2.0*np.pi*std_time*std_freq) * np.exp(exponent)
                g_data[jj,ii] = np.exp(exponent)
        return amp * g_data

def get_info_bbx(bbx_cls):
    """
    This is function the get all the necessary information from bbx file.
    """
    hdr = bbx_cls.header
    meta = hdr['metadata']
    info = {}
    info['num_time_bin'] = int(meta['dim1_len'])
    info['time_resolution'] = float(hdr['dim1_span'])/info['num_time_bin']
    info['num_freq_bin'] = int(meta['dim2_len'])
    info['freq_resolution'] = float(hdr['dim2_span'])/info['num_freq_bin']
    if 'frequency_offset_DC' in hdr.keys():
        freq_off_set_DC = float(hdr['frequency_offset_DC'].split()[0])
    else:
        freq_off_set_DC = 0.0
    info['freq_start'] = float(hdr['dim2_start']) + float(freq_off_set_DC)
    if 'time_offset_J2000' in hdr.keys():
        time_off_J2000 = float(hdr['time_offset_J2000'].split()[0])
    else:
        time_off_J2000 = 0.0
    info['time_start'] = float(hdr['dim1_start']) + time_off_J2000
    info['time_end'] = info['time_start'] + float(hdr['dim1_span'])
    info['freq_end'] = info['freq_start'] + float(hdr['dim2_span'])
    info['time_axis'] = np.arange(info['time_start'], info['time_end'], info['time_resolution'])
    info['freq_axis'] = np.arange(info['freq_start'], info['freq_end'], info['freq_resolution'])
    return info

FILETYPE = {'bbx': (lfbbx, get_info_bbx)}

class FilterBank(object):
    """
    This is a class for holding filter bank data.
    A filter bank data is a two dimesion array.
    dim 1 (x-axis) : time second
    dim 2 (y-axis) : frequency Hz
    dim 3          : power. undefined unit
    """
    def __init__(self, name, from_file=False, time_resolution=0.0,  num_time_bin=0, \
                 freq_resolution=0.0, num_freq_bin=0, freq_start=0.0, time_start=0.0,\
                 data_gen=None, gap_filling=None, filename=None, filetype=None,
                 **kwarg):
        self.name = name
        self.info = {self.name:{},}
        self._data = None
        if from_file:
            if filetype is None or filename is None:
                raise ValueError('Please provide file name and file type to'
                                 ' input data from a file.')
            self.read_from_file(filename, filetype)
        else:
            self.time_resolution = time_resolution
            self.num_time_bin = int(num_time_bin)
            self.freq_resolution = freq_resolution
            self.num_freq_bin = int(num_freq_bin)
            self.freq_start = freq_start
            self.time_start = time_start
            self.time_end = time_start + time_resolution * num_time_bin
            self.freq_end = freq_start + freq_resolution * num_freq_bin
            self.time_axis = np.arange(self.time_start, self.time_end, time_resolution)
            self.freq_axis = np.arange(self.freq_start, self.freq_end, freq_resolution)
        if data_gen is not None:
            self.data_gen = data_gen(self.time_resolution, self.num_time_bin, \
                                     self.freq_resolution, self.num_freq_bin)
        else:
            self.data_gen = data_gen

        if gap_filling is None:
            self.gap_fill_fun = self.gap_fill_default

    @property
    def data(self):
        if self._data is None:
            print('Filter Bank data has not been generated yet.')
        return self._data

    @data.setter
    def data(self, val):
        self._data = val

    @property
    def time_start(self):
        return self._time_start
    @time_start.setter
    def time_start(self, value):
        self._time_start = value
        self.info[self.name]['time_start'] = value

    @property
    def time_end(self):
        return self._time_end
    @time_end.setter
    def time_end(self, value):
        self._time_end = value
        self.info[self.name]['time_end'] = value

    @property
    def freq_start(self):
        return self._freq_start
    @freq_start.setter
    def freq_start(self, value):
        self._freq_start = value
        self.info[self.name]['freq_start'] = value

    @property
    def freq_end(self):
        return self._freq_end
    @freq_end.setter
    def freq_end(self, value):
        self._freq_end = value
        self.info[self.name]['freq_end'] = value

    def __add__(self, other):
        """
        Define the operator for adding two filter bank data together.
        """
        if self.time_resolution != other.time_resolution:
            raise ValueError('Can only add two filter bank data with the same'
                             ' time resolution.')
        if self.freq_resolution != other.freq_resolution:
            raise ValueError('Can only add two filter bank data with the same'
                             ' frequency resolution.')

        if not np.array_equal(self.freq_axis, other.freq_axis):
            raise ValueError('Can only add two filter bank data with the same' \
                             ' freq range.')
        # Check time range.
        time_range = np.array([self.time_start, self.time_end, other.time_start, \
                               other.time_end])
        # find the min and max time
        new_start = time_range.min()
        new_end = time_range.max()
        new_time_bin = int((new_end - new_start)/self.time_resolution)
        new_flt_data = FilterBank('total', time_resolution=self.time_resolution,
                                  num_time_bin=new_time_bin,\
                                  freq_resolution=self.freq_resolution,
                                  num_freq_bin=self.num_freq_bin, \
                                  freq_start=self.freq_start,
                                  time_start=new_start, data_gen=UniformDataGen)
        new_flt_data.generate_data(amp=0.0)
        new_start_idx = np.array([0,0])
        for st in [self.time_start, other.time_start]:
            new_start_idx[0] = np.abs(st - new_flt_data.time_axis).argmin()
        new_end_idx = new_start_idx + np.array([self.num_time_bin, other.num_time_bin])
        # prevent index over flow.
        excd = np.where(new_end_idx >= new_flt_data.num_time_bin)[0]
        new_start_idx[excd] -= 1
        new_flt_data.data[new_start_idx[0]:new_end_idx[0], :] += self.data
        new_flt_data.data[new_start_idx[1]:new_end_idx[1], :] += other.data
        # Check gap
        diff = np.array([new_start_idx[0] - new_start_idx[1], \
                         new_end_idx[0] - new_end_idx[1]], \
                         new_end_idx[0] - new_start_idx[1], \
                         new_start_idx[0] - new_end_idx[1])
        if np.all(np.greater(diff, [0,0,0,0])):
            new_flt_data.info[new_flt_data.name]['gap'] = new_start_idx[0] - new_end_idx[1]
        elif np.all(np.less(diff, [0,0,0,0])):
            new_flt_data.info[new_flt_data.name]['gap'] = new_start_idx[1] - new_end_idx[0]
        new_flt_data.info.updata(self.info)
        new_flt_data.info.updata(other.info)
        return new_flt_data

    def __neg__(self,):
        new_flt_data = FilterBank('neg_' + self.name, self.time_resolution, self.num_time_bin,\
                                  self.freq_resolution, self.num_freq_bin, \
                                  self.freq_start, self.time_start)
        new_flt_data.data /= -1
        return new_flt_data

    def __sub__(self, other):
        self.__add__(other.__neg__())

    def __iadd__(self, other):
        """
        Define the operator for adding two filter bank data together.
        """
        if self.time_resolution != other.time_resolution:
            raise ValueError('Can only add two filter bank data with the same'
                             ' time resolution.')
        if self.freq_resolution != other.freq_resolution:
            raise ValueError('Can only add two filter bank data with the same'
                             ' frequency resolution.')

        if not np.array_equal(self.freq_axis, other.freq_axis):
            raise ValueError('Can only add two filter bank data with the same'
                             'freq range.')
        # Check time range.
        time_range = np.array([self.time_start, self.time_end, other.time_start, \
                               other.time_end])
        # find the min and max time
        new_start = time_range.min()
        new_end = time_range.max()
        new_time_bin = int((new_end - new_start)/self.time_resolution)
        if new_start == self.time_start and new_end == self.time_end:
            self.data += other.data
        else:
            # resize time axis
            self.time_axis = np.arange(new_start, new_end, self.time_resolution)
            # resize data
            temp = np.zeros((new_time_bin, self.num_freq_bin))
            new_start_idx = np.array([0,0])
            for st in [self.time_start, other.time_start]:
                new_start_idx[0] = np.abs(st - new_flt_data.time_axis).argmin()
            new_end_idx = new_start_idx + np.array([self.num_time_bin, other.num_time_bin])
            # prevent index over flow.
            excd = np.where(new_end_idx >= new_flt_data.num_time_bin)[0]
            new_start_idx[excd] -= 1
            temp[new_start_idx[0]:new_end_idx[0], :] += self.data
            temp[new_start_idx[1]:new_end_idx[1], :] += other.data
            # Check gap
            diff = np.array([new_start_idx[0] - new_start_idx[1], \
                         new_end_idx[0] - new_end_idx[1]], \
                         new_end_idx[0] - new_start_idx[1], \
                         new_start_idx[0] - new_end_idx[1])
            if np.all(np.greater(diff, [0,0,0,0])):
                self.info[self.name]['gap'] = new_start_idx[0] - new_end_idx[1]
            elif np.all(np.less(diff, [0,0,0,0])):
                self.info[self.name]['gap'] = new_start_idx[1] - new_end_idx[0]
        self.time_start = new_start
        self.time_end = new_end
        self.num_time_bin = new_time_bin
        self.info.update(other.info)
        return self

    def generate_data(self, **kws):
        self.data = self.data_gen.gen_func(**kws)

    def gap_fill_default(self, gap):
        """
        This a function that determine what to fill into the filter bank data
        gap.
        """
        gap = np.zeros(gap.shape)
        return gap

    def get_info_from_file(self, filecls, filetype):
        info = FILETYPE[filetype][1](filecls)
        for k in info.keys():
            setattr(self, k, info[k])


    def read_from_file(self, filename, filetype, read_data=True):
        """
        This function is to read a filter bank data from a file.
        Parameter
        ---------
        filename: str
            The file name to be read in.
        type: str
            The type of the file. It will map to a file class from FILETYPE dict.
        """
        df = FILETYPE[filetype][0](filename)
        self.get_info_from_file(df, filetype)
        if read_data:
            df.read_data()
            self.data = df.data


    def write(self, filename, filetype, gz=True, extra_info={'station':'simulate',\
                                                             'channel':'simulate'}):
        filecls = FILETYPE[filetype][0](filename, mode='write', gz=gz)
        filecls.add_data(self.data)
        hdr = {}
        hdr['dim1_span'] = self.time_end - self.time_start
        hdr['dim2_span'] = self.freq_end - self.freq_start
        hdr['dim1_start'] = self.time_start
        hdr['dim2_start'] = self.freq_start
        hdr['station'] = extra_info['station']
        hdr['channel'] = extra_info['channel']

        for k, v in hdr.items():
            filecls.set(k, v)
        filecls.write()
        filecls.close()
