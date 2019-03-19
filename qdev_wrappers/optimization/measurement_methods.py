from qdev_wrappers.automated_tuneup.readout_fidelity_alazar import calculate_fidelity
from qdev_wrappers.fitting.fitter import Fitter
import qdev_wrappers.fitting.least_squares_models as lsm
import numpy as np


class MeasurementMethod:

    def __init__(self, param_name='None'):
        super(MeasurementMethod, self).__init__()
        self.measured_params = {param_name: {'label': '', 'unit': ''}}

    def measurement_function(self, **kwargs):
        """calls get_data function to retrieve data,
        finds value of interest to optimization
        (fx. max separation, pi pulse duration)"""
        pass

    def stopping_condition(self, num_attempts):
        if num_attempts >= self.max_attempts:
            return True
        else:
            return False

    def cost_val(self, measurement):
        """Takes measurement results (fx. max separation,
        pi pulse duration) as list or dictionary, returns
        cost val for the corresponding location in param space"""
        pass


class ReadoutFidelityOptimization(MeasurementMethod):

    def __init__(self, param_name='readout_fidelity'):
        super(ReadoutFidelityOptimization, self).__init__()
        self.measured_params = {param_name: {'label': 'Readout Fidelity', 'unit': ''}}

    def measurement_function(self, **kwargs):
        # get_data could fx be: pwa.alazar_channels.data or get_measured_data
        """defines what to call to measure"""
        if self.from_runid:
            measured_params = [key for key in self.measured_params.keys()]
            max_separation = self.get_data(self.from_runid, *measured_params, **kwargs)[0]
        else:
            results = self.get_data()
            no_pi_real = results[0][:, 0]
            no_pi_im = results[1][:, 0]
            pi_real = results[0][:, 1]
            pi_im = results[1][:, 1]

            fidelity_info = calculate_fidelity(no_pi_real, no_pi_im, pi_real, pi_im)
            max_separation = fidelity_info.max_separation

        return [max_separation]

    def cost_val(self, measurement):
        if isinstance(measurement, dict):
            measurement = [measurement[key] for key in self.measured_params]
        if len(measurement) != 1:
            raise RuntimeError(f"Expected 1 value from measurement and got {len(measurement)}")

        val = float(measurement[0])

        return 1-val


class Rabis(MeasurementMethod):

    def __init__(self):
        super(Rabis, self).__init__()
        self.measured_params = {'pi_pulse_duration': {'label': 'Pi pulse duration', 'unit': 's'}}

    def measurement_function(self, **kwargs):
        """defines what to call to measure"""
        if self.from_runid:
            pulse_dur = self.get_data(self.from_runid, 'alazar_controller_pulse_duration', **kwargs)[0]
            data = self.get_data(self.from_runid, 'alazar_controller_ch_0_r_records_data', **kwargs)[0]
        # get_data could fx be: pwa.alazar_channels.data or get_measured_data
        else:
            pulse_dur = self.get_data.setpoints[0][0]
            data = self.get_data()[0]

        fitter = Fitter(lsm.CosineModel())
        fit = fitter.fit(data, x=pulse_dur)

        if fit[0] is None:
            pi_pulse_duration = None
        else:
            omega = fit[0]['w']
            pi_pulse_duration = np.pi / omega
        return [pi_pulse_duration]

    def cost_val(self, measurement):
        if isinstance(measurement, dict):
            measurement = [measurement[key] for key in self.measured_params]
        if len(measurement) != 1:
            raise RuntimeError(f"Expected 1 value from measurement and got {len(measurement)}")

        val = measurement[0]

        if val is None:
            return 1e15
        else:
            if len(self.params) != 1:
                raise RuntimeError(f"Trying to optimize {len(self.params)} parameters. Method expects 1 parameter.")
            param = self.params[0]
            if self.from_runid:
                param_name = param
            else:
                param_name = param.full_name
            # if scanning frequency, find maximum pi-pulse duration (frequency center)
            if 'frequency' in param_name:
                return 1/val
            # if scanning power, find power that puts pi pulse duration closest to 50 ns
            elif 'power' in param_name:
                return np.abs(50e-9-val)
            else:
                raise RuntimeError(f"I don't know how to optimize {param_name} based on pi pulse duration, "
                                   f"because it is not included in the cost_val function")
