from qdev_wrappers.automated_tuneup.readout_fidelity_alazar import calculate_fidelity
from qdev_wrappers.fitting.fitter import Fitter
import qdev_wrappers.fitting.least_squares_models as lsm
import numpy as np


def readout_fidelity(get_data, runid=None, **kwargs):
    # get_data could fx be: pwa.alazar_channels.data or get_measured_data
    """Optimizes for best readout _fidelity (costval = 1-readout_fidelity)
        Returns [readout_fidelity, costval] """
    if runid:
        # ToDo?: this will not work for data that has a different name for the measured param
        # But maybe as long as it works with the example data we are using its fine?
        max_separation = get_data(runid, 'max_separation', **kwargs)[0]
    else:
        results = get_data()
        no_pi_real = results[0][:, 0]
        no_pi_im = results[1][:, 0]
        pi_real = results[0][:, 1]
        pi_im = results[1][:, 1]

        fidelity_info = calculate_fidelity(no_pi_real, no_pi_im, pi_real, pi_im)
        max_separation = fidelity_info.max_separation

    # returns measured value, cost_val (what if multiple things are measured? Should measured values be a list?)
    return [max_separation, 1-max_separation]


def rabis_vs_freq(get_data, runid=None, **kwargs):
    """ Optimizes for max pi_pulse_duration (costval = 1/pi_pulse_duration)
        Returns [pi_pulse_duration, costval]"""

    # get_data could fx be: pwa.alazar_channels.data or get_measured_data
    if runid:
        # ToDo?: this will not work for data that has a different name for the measured param
        # But maybe as long as it works with the example data we are using its fine?
        pulse_dur = get_data(runid, 'alazar_controller_pulse_duration', **kwargs)[0]
        data = get_data(runid, 'alazar_controller_ch_0_r_records_data', **kwargs)[0]

    else:
        pulse_dur = get_data.setpoints[0][0]
        data = get_data()[0]

    fitter = Fitter(lsm.CosineModel())
    fit = fitter.fit(data, x=pulse_dur)

    if fit[0] is None:
        pi_pulse_duration = None
    else:
        omega = fit[0]['w']
        pi_pulse_duration = np.pi / omega

    return [pi_pulse_duration, 1/pi_pulse_duration]


def rabis_vs_power(get_data, runid=None, **kwargs):
    """ Optimizes for pi_pulse_duration close to 50 ns (costval = np.abs(50e-9-pi_pulse_duration))
        Returns [pi_pulse_duration, costval]"""
    # get_data could fx be: pwa.alazar_channels.data or get_measured_data
    if runid:
        # ToDo?: this will not work for data that has a different name for the measured param
        # But maybe as long as it works with the example data we are using its fine?
        pulse_dur = get_data(runid, 'alazar_controller_pulse_duration', **kwargs)[0]
        data = get_data(runid, 'alazar_controller_ch_0_r_records_data', **kwargs)[0]

    else:
        pulse_dur = get_data.setpoints[0][0]
        data = get_data()[0]

    fitter = Fitter(lsm.CosineModel())
    fit = fitter.fit(data, x=pulse_dur)

    if fit[0] is None:
        pi_pulse_duration = None
    else:
        omega = fit[0]['w']
        pi_pulse_duration = np.pi / omega

    return [pi_pulse_duration, np.abs(50e-9-pi_pulse_duration)]
