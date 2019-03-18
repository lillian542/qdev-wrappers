from qcodes.dataset.measurements import Measurement
import numpy as np
from qdev_wrappers.optimization.optimization_from_completed_data import get_measured_data


class Optimization:
    def __init__(self, method, start=None, runid=None):
        self.method = method
        self.num_attempts = 0
        self.from_runid = runid
        self.parameters = None
        self.step_size = None
        self.measured_parameters = None

        if runid:
            self.start = start
        else:
            self.start = {param.full_name: param() for param in self.params}

        self.current = self.start.copy()
        initial_measurement = method.measurement_function(**start)
        for i, param in enumerate(method.measured_params):
            self.current[param] = initial_measurement[i]

        self.best_cost_val = method.cost_val(self.current)
        self.best = self.current.copy()
