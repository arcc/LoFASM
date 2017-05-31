import filter_bank_simulate as fbs
import numpy as np

def get_freq_from_time(freq_high, time_resolution, dm):
    """ This is a function returns the required frequency from dm and time
    resolution
    freq_high : Reference high frequency in the unit of MHz
    time_resolution : Time resolution in the unit of second
    """
    if dm == 0.0:
        return 0.0
    freq = 1.0/np.sqrt(time_resolution/4.15e3/dm + 1.0/(freq_high**2))
    return freq

def dm_delay(dm, f, f_ref):
    "The frequency unit is in MHz"
    dt = 4.15e3 * dm * (f**-2 - f_ref**-2)
    return dt

def disperse_filterbank(dm, filter_bank_data, full_result=False):
    freqs = filter_bank_data.freq_axis/1e6 # convert to the units of MHz
    freq_res = filter_bank_data.freq_resolution/1e6
    extra_low = (filter_bank_data.freq_axis[0] - filter_bank_data.freq_resolution)/1e6
    extra_time_delay = dm_delay(dm, extra_low, freqs[-1])
    last_time_delay = dm_delay(dm, freqs[0], freqs[-1])
    last_time_span = extra_time_delay - last_time_delay
    max_smear = int(last_time_span / filter_bank_data.time_resolution) + 3

    # Get a finer resolution of frequency
    fine_freqs = np.zeros((len(filter_bank_data.freq_axis), max_smear))
    fine_times = np.zeros((len(filter_bank_data.freq_axis), max_smear))
    # First We need a finer time resolution
    delay_prim = dm_delay(dm, freqs, freqs[-1])
    delay_prim_index = delay_prim/filter_bank_data.time_resolution
    delay_prim_index = delay_prim_index.astype(int)
    index_time = delay_prim_index * filter_bank_data.time_resolution
    freq_enter_time = delay_prim - index_time
    # construct a finer time resolution
    fine_times.fill(filter_bank_data.time_resolution)
    fine_times[:, 0] = filter_bank_data.time_resolution - freq_enter_time
    # get_finer_freq
    back_freqs = np.append(freqs[::-1], extra_low)
    end_freqs = np.delete(back_freqs, 0)
    for ii, f in enumerate(back_freqs[0:-1]):
        f_high = f
        f_low = f
        itr = 0
        fine_freqs[fine_freqs.shape[0] - ii - 1 ] = end_freqs[ii]
        fine_freqs[fine_freqs.shape[0] - ii - 1 ][itr] = f
        while True:
            itr += 1
            res_time = fine_times[fine_freqs.shape[0] - ii - 1][itr-1]
            f_low = get_freq_from_time(f_low, res_time, dm)
            if f_low < back_freqs[ii + 1]:
                break
            fine_freqs[fine_freqs.shape[0] - ii -1][itr] = f_low
    # Get fine_freqs powers.
    power_distr = np.zeros((len(freqs), max_smear - 1))
    for ii in range(max_smear - 1):
        power_distr[:, ii] = (fine_freqs[:,ii] - \
                  fine_freqs[:,ii+1])/freq_res

    if not full_result:
        dispersed = fbs.FilterBank(filter_bank_data.name + '_dispersed',
                               num_time_bin=filter_bank_data.num_time_bin, \
                               num_freq_bin=filter_bank_data.num_freq_bin, \
                               freq_resolution=filter_bank_data.freq_resolution, \
                               freq_start=filter_bank_data.freq_start,  \
                               time_resolution=filter_bank_data.time_resolution, \
                               time_start=filter_bank_data.time_start,
                               data_gen=fbs.UniformDataGen)
    else:
        add_time_bin = int(extra_time_delay/filter_bank_data.time_resolution)
        dispersed = fbs.FilterBank(filter_bank_data.name + '_dispersed',
                               num_time_bin=filter_bank_data.num_time_bin + add_time_bin, \
                               num_freq_bin=filter_bank_data.num_freq_bin, \
                               freq_resolution=filter_bank_data.freq_resolution, \
                               freq_start=filter_bank_data.freq_start,  \
                               time_resolution=filter_bank_data.time_resolution, \
                               time_start=filter_bank_data.time_start,
                               data_gen=fbs.UniformDataGen)
    dispersed.generate_data(amp=0.0)
    for ii in range(filter_bank_data.num_time_bin):
        powers = power_distr * filter_bank_data.data[:, ii][:,np.newaxis]
        for jj in range(filter_bank_data.num_freq_bin):
            target_time_idx = ii + delay_prim_index[jj]
            changed_idx = np.arange(target_time_idx, target_time_idx+powers.shape[1])
            d_idx = dispersed.num_time_bin - changed_idx
            effect = changed_idx[np.where(d_idx>0)[0]]
            dispersed.data[jj, effect] += powers[jj, 0:len(effect)]
    return dispersed
