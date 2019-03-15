import qcodes as qc
from numpy.random import randint
from itertools import product
from qdev_wrappers.automated_tuneup.readout_fidelity_alazar import calculate_fidelity
from qdev_wrappers.fitting.fitter import Fitter
import qdev_wrappers.fitting.least_squares_models as lsm
import numpy as np


class ReadoutFidelityOptimization:

    def __init__(self, *params, get_data, max_attempts=20, runid=None, from_saved_data=False):
        # get_data: pwa.alazar_channels.data
        # ToDo: figure out better solution for step size?
        # ToDo: I think params just go in the optimize function, instead of in the model, so model just needs get_data
        self.params = [item for item in params if isinstance(item, qc.Parameter) or isinstance(item, str)]
        self.step_size = [item for item in params if isinstance(item, float)]
        self.measured_params = {'readout_fidelity': {'label': 'Readout Fidelity', 'unit': ''}}
        self.max_attempts = max_attempts
        self.get_data = get_data
        self.from_saved_data = from_saved_data
        self.runid = runid

    def check_next(self, current_location):
        """Takes current location in parameter space, decides next coordinates to measure
            Returns a list of dictionaries, one for each location, with parameters (both variable
            and measured) and their values"""
        pass
        # return next_results

    def select_next_location(self, next_results, current_location):
        """Takes next coordinates and measurements from check_next, and the current
         best value found from the optimization, uses them to decide where to go next.
         Returns parameters and a measurement for next location"""
        pass
        # return next_location

    def measurement_function(self, **kwargs):
        """defines what to call to measure"""
        if self.from_saved_data:
            max_separation = self.get_data(self.runid, self.measured_params.keys(), **kwargs)[0]
        else:
            results = self.get_data()
            no_pi_real = results[0][:, 0]
            no_pi_im = results[1][:, 0]
            pi_real = results[0][:, 1]
            pi_im = results[1][:, 1]

            fidelity_info = calculate_fidelity(no_pi_real, no_pi_im, pi_real, pi_im)
            max_separation = fidelity_info.max_separation

        return [max_separation]

    def stopping_condition(self, num_attempts):
        if num_attempts >= self.max_attempts:
            return True
        else:
            return False

    def cost_val(self, measurement):
        if isinstance(measurement, dict):
            measurement = [measurement[key] for key in self.measured_params]
        if len(measurement) != 1:
            raise RuntimeError(f"Expected 1 value from measurement and got {len(measurement)}")

        val = float(measurement[0])

        return 1-val


class Rabis:

    def __init__(self, *params, get_data, max_attempts=20):
        # get_data = pwa.alazar_channels.data
        # ToDo: figure out better solution for step size?
        self.params = [item for item in params if isinstance(item, qc.Parameter)]
        self.step_size = [item for item in params if isinstance(item, float) or isinstance(item, int)]
        self.measured_params = {'pi_pulse_duration': {'label': 'Pi pulse duration', 'unit': 's'}}
        self.max_attempts = max_attempts
        self.get_data = get_data

    def check_next(self, current_location):
        """Takes current location in parameter space, decides next coordinates to measure
            Returns a list of dictionaries, one for each location, with parameters (both variable
            and measured) and their values"""
        pass
        # return next_results

    def select_next_location(self, next_results, current_location):
        """Takes next coordinates and measurements from check_next, and the current
         best value found from the optimization, uses them to decide where to go next.
         Returns parameters and a measurement for next location"""
        pass
        # return next_location

    def measurement_function(self):
        """defines what to call to measure"""
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

    def stopping_condition(self, num_attempts):
        if num_attempts >= self.max_attempts:
            return True
        else:
            return False

    def cost_val(self, measurement):
        if isinstance(measurement, dict):
            measurement = [measurement[key] for key in self.measured_params]
        if len(measurement) != 1:
            raise RuntimeError(f"Expected 1 value from measurement and got {len(measurement)}")

        val = measurement[0]

        if val is None:
            return 1e15
        else:
            if len(self.params) > 1:
                raise RuntimeError(f"Trying to optimize {self.params}, but you haven't set this one up to do multiple parameters at once!")
            param = self.params[0]
            # if scanning frequency, find maximum pi-pulse duration (frequency center)
            if param.name == 'frequency':
                return 1/val
            # if scanning power, find power that puts pi pulse duration closest to 50 ns
            elif param.name == 'power':
                return np.abs(50e-9-val)
            else:
                raise RuntimeError(f"I don't know how to optimize {param.full_name} based on pi pulse duration, "
                                   f"because it is not included in the cost_val function")


class BestNeighbour(ReadoutFidelityOptimization):

    def check_next(self, current_location):
        """Takes current location in parameter space, decides next coordinates to measure
            Returns a list of dictionaries, one for each location, with parameters (both variable
            and measured) and their values"""
        next_param_vals = {}
        next_locations = []

        for i, param in enumerate(self.params):
            # select randomly to go anywhere from 1-10 steps
            step = randint(1, 11) * self.step_size[i]
            if self.from_saved_data:
                param_name = param
            else:
                param_name = param.full_name
            next_param_vals[param_name] = [current_location[param_name] - step,
                                           current_location[param_name] + step]

        param_combinations = product(*[set(v) for v in next_param_vals.values()])

        for combination in param_combinations:
            if self.from_saved_data:
                d = {}
                for i, param in enumerate(self.params):
                    d[param] = combination[i]
                measurement = self.measurement_function(**d)
                for i, measured_param in enumerate(self.measured_params):
                    d[measured_param] = measurement[i]
                next_locations.append(d)
            else:
                d = {}
                for i, param in enumerate(self.params):
                    param(combination[i])
                    d[param.full_name] = combination[i]
                measurement = self.measurement_function()
                for i, measured_param in enumerate(self.measured_params):
                    d[measured_param] = measurement[i]
                next_locations.append(d)

        return next_locations

    def select_next_location(self, next_locations, current_location):
        # If any of the new locations are better than the current, return the new current location.
        # Otherwise, return the current location.
        for candidate in next_locations:
            if self.cost_val(candidate) < self.cost_val(current_location):
                current_location = candidate
        return current_location


class BestNeighbourPiPulse(Rabis):

    def check_next(self, current_location):
        """Takes current location in parameter space, decides next coordinates to measure
            Returns a list of dictionaries, one for each location, with parameters (both variable
            and measured) and their values"""
        next_param_vals = {}
        next_locations = []

        for i, param in enumerate(self.params):
            # select randomly to go anywhere from 1-10 steps
            step = randint(1, 11) * self.step_size[i]
            next_param_vals[param.full_name] = [current_location[param.full_name] - step,
                                                current_location[param.full_name] + step]

        param_combinations = product(*[set(v) for v in next_param_vals.values()])

        for combination in param_combinations:
            d = {}
            for i, param in enumerate(self.params):
                param(combination[i])
                d[param.full_name] = combination[i]
            measurement = self.measurement_function()
            for i, measured_param in enumerate(self.measured_params):
                d[measured_param] = measurement[i]
            next_locations.append(d)

        return next_locations

    def select_next_location(self, next_locations, current_location):
        # If any of the new locations are better than the current, return the new current location.
        # Otherwise, return the current location.
        for candidate in next_locations:
            if self.cost_val(candidate) < self.cost_val(current_location):
                current_location = candidate
        return current_location


class WeightedMovement(ReadoutFidelityOptimization):

    def check_next(self, optimization):
        """Takes current location in parameter space, decides next coordinates to measure
            Returns a list of dictionaries, one for each location, with parameters (both variable
            and measured) and their values"""
        next_param_vals = {}
        next_locations = []

        # Todo: make this a property of the method, so that it actually goes down with each repetition of the function
        step_multiplier = 10

        for i, param in enumerate(self.params):
            step = step_multiplier * self.step_size[i]
            # Todo: this makes no sense here, unless it is a property of the method
            step_multiplier -= 1
            next_param_vals[param.full_name] = [optimization.current[param.full_name] - step,
                                                optimization.current[param.full_name] + step]

        param_combinations = product(*[set(v) for v in next_param_vals.values()])

        for combination in param_combinations:
            d = {}
            for i, param in enumerate(self.params):
                param(combination[i])
                d[param.full_name] = combination[i]
            measurement = self.measurement_function()
            for i, measured_param in enumerate(self.measured_params):
                d[measured_param] = measurement[i]
            next_locations.append(d)

        return next_locations

    def select_next_location(self, next_locations, optimization):
        # go to new location based on weighted
        current_location = optimization.current
        delta_params = {param.full_name: 0 for param in self.params}

        for candidate in next_locations:
            cv = self.cost_val(candidate)
            for param in self.params:
                d = candidate[param.full_name] - current_location[param.full_name]
                delta_params[param.full_name] += d/cv

        for param in self.params:
            current_location[param.full_name] += delta_params[param.full_name]
            param(current_location[param.full_name])
        measurement = self.measurement_function()
        for i, measured_param in enumerate(self.measured_params):
            current_location[measured_param] = measurement[i]

        return current_location


class PendulumSearch:
    pass
