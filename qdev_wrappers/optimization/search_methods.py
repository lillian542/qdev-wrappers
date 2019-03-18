from numpy.random import randint
from itertools import product
from qdev_wrappers.optimization.measurement_methods import MeasurementMethod


class BestNeighbour(MeasurementMethod):

    def check_next(self, opt):
        """Takes optimization, gets current location in parameter space, decides next coordinates to measure
            Returns a list of dictionaries, one for each location, with parameters (both variable
            and measured) and their values"""
        next_param_vals = {}
        next_locations = []

        for i, param in enumerate(opt.params):
            # select randomly to go anywhere from 1-10 steps
            step = randint(1, 11) * opt.step_size[i]
            if opt.from_runid:
                param_name = param
            else:
                param_name = param.full_name
            next_param_vals[param_name] = [opt.current[param_name] - step,
                                           opt.current[param_name] + step]

        param_combinations = product(*[set(v) for v in next_param_vals.values()])

        for combination in param_combinations:
            if opt.from_runid:
                d = {}
                for i, param in enumerate(opt.params):
                    d[param] = combination[i]
                measurement = self.measurement_function(**d)
                for i, measured_param in enumerate(self.measured_params):
                    d[measured_param] = measurement[i]
                next_locations.append(d)
            else:
                d = {}
                for i, param in enumerate(opt.params):
                    param(combination[i])
                    d[param.full_name] = combination[i]
                measurement = self.measurement_function()
                for i, measured_param in enumerate(self.measured_params):
                    d[measured_param] = measurement[i]
                next_locations.append(d)

        return next_locations

    def select_next_location(self, next_locations, optimization):
        # If any of the new locations are better than the current, return the updated current location.
        # Otherwise, return the current location.
        current_location = optimization.current
        for candidate in next_locations:
            if self.cost_val(candidate) < self.cost_val(current_location):
                current_location = candidate
        return current_location


class WeightedMovement:

    def __init__(self):
        super(WeightedMovement, self).__init__()
        self.step_multiplier = 10

    def check_next(self, opt):
        """Takes optimization, gets current location in parameter space, decides next coordinates to measure
            Returns a list of dictionaries, one for each location, with parameters (both variable
            and measured) and their values"""
        next_param_vals = {}
        next_locations = []

        for i, param in enumerate(self.params):
            step = self.step_multiplier * self.step_size[i]
            self.step_multiplier -= 1
            if opt.from_runid:
                param_name = param
            else:
                param_name = param.full_name
            next_param_vals[param_name] = [opt.current[param_name] - step,
                                           opt.current[param_name] + step]

        param_combinations = ()
        for comb in param_combinations:
            print(comb)

        for combination in param_combinations:
            if opt.from_runid:
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

    def select_next_location(self, next_locations, opt):
        # go to new location based on weighted
        current_location = opt.current
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
