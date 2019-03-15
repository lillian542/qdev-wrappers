import numpy as np
import matplotlib.pyplot as plt
from qcodes.dataset.data_export import load_by_id
from qdev_wrappers.fitting.fitter import Fitter
from qdev_wrappers.fitting.models import SimpleMinimum
from qcodes.dataset.plotting import plot_by_id



def get_unpushed_cavity_frequency(cavity, guess, pwa, span=50e6, step=1e6, measurement=False):
    cavity.power(-10)
    fitter = Fitter(SimpleMinimum())
    if measurement:
        runid = do1d(cavity_drive_frequency, guess-span/2, guess+span/2, span/step+1, 0, pwa.alazar_channels.ch_0_m.data)
        fit = fitter.fit_by_id(runid, 'alazar_controller_ch_0_m_data', x='cavity_drive_frequency', save_fit=False)
        cav_freq = fit.get_result()['param_values']['location']
        
    else:
        setpoints = np.linspace(guess-span/2, guess+span/2, int(span/step+1))
        results = []
        for freq in setpoints:
            cavity_drive_frequency.set(freq)
            results.append(pwa.alazar_channels.ch_0_m.data.get())
        cav_freq = fitter.fit(np.array(results), x=setpoints)[0]['location']

    print(f"Unpushed cavity frequency: {cav_freq}")

    return cav_freq


def get_pushed_cavity_settings(guess=None,
                               cavity=None,
                               pwa=None,
                               from_saved_data=False,
                               runid=None,
                               span=10e6, 
                               step=0.5e6,
                               power_start=-10,
                               power_stop=-45,
                               power_step=5):

    points = []
    slope = [0]

    power_setpoints = np.linspace(power_start, power_stop, int((power_start - power_stop) / power_step + 1))

    if from_saved_data:
        # adjust power_setpoints to the closest possible values in the completed meausrement
        measured_powers = np.array(load_by_id(runid).get_data('rs_vna_S21_power')).flatten()
        for i, power in enumerate(power_setpoints):
            power_setpoints[i] = measured_powers[np.argmin(np.abs(measured_powers - power))]
    else:
        freq_setpoints = np.linspace(guess - span / 2, guess + span / 2, int(span / step + 1))

    
    fitter = Fitter(SimpleMinimum())
    # ToDo: cavity fit model instead of simple minimum
    # ToDo: make this a measurement

    for power in power_setpoints:
        if from_saved_data:
            indices = np.argwhere(measured_powers == power).flatten()
            freq = np.array(load_by_id(runid).get_data('rs_vna_S21_S21_frequency')).flatten()[indices]
            mag = np.array(load_by_id(runid).get_data('rs_vna_S21_trace')).flatten()[indices]
            cav_freq = fitter.fit(mag, x=freq)[0]['location']
        else:
            cavity.power(power)
            results = []
            for freq in freq_setpoints:
                cavity_drive_frequency.set(freq)
                results.append(pwa.alazar_channels.ch_0_m.data.get())
            cav_freq = fitter.fit(np.array(results), x=freq_setpoints)[0]['location']
            
        points.append((power, cav_freq))

        if len(points) > 1:
            d_freq = points[-1][1] - points[-2][1]
            d_pow = points[-1][0] - points[-2][0]
            m = d_freq/d_pow
            slope.append(m)
        
        if np.abs(cav_freq-points[0][1]) > 1e6 and 0 <= m < 0.05e6:
            # ToDo: what if the pushed cavity frequency is below the unpushed frequency? -> useful error message
            break

    print(f"Pushed cavity frequency: {points[-2]}")
    print(f"Unpushed cavity frequency: {points[0]}")
    print(f"Push: {points[-2][1]-points[0][1]}")

    if from_saved_data:
        ax, clb = plot_by_id(runid)
        ax[0].scatter(*points[0])
        ax[0].scatter(*points[-2])
            
    return points[-2],


