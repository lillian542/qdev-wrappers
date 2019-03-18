import qcodes as qc
from qcodes.dataset.measurements import Measurement
from qdev_wrappers.optimization.optimization import Optimization


def make_optimization_method(meas_method,
                             search_method,
                             get_data,
                             max_attempts=20):

    class OptimizationMethod(meas_method, search_method):

        def __init__(self):
            super(OptimizationMethod, self).__init__()
            self.params = []
            self.step_size = []
            self.max_attempts = max_attempts
            self.get_data = get_data
            self.from_runid = None

        def optimize(self, *params, start=None, runid=None):

            self.from_runid = runid

            opt = Optimization(self, start, runid=runid)
            opt.params = self.params = [item for item in params if isinstance(item, qc.Parameter) or isinstance(item, str)]
            opt.step_size = self.step_size = [item for item in params if isinstance(item, float)]
            opt.measured_params = self.measured_params

            meas = Measurement()

            setpoints = []
            if opt.from_runid:
                for parameter in opt.params:
                    setpoints.append(parameter)
                    meas.register_custom_parameter(name=parameter,
                                                   label=parameter)
            else:
                for parameter in opt.params:
                    setpoints.append(parameter.full_name)
                    meas.register_parameter(parameter)
            for parameter, param_info in self.measured_params.items():
                meas.register_custom_parameter(name=parameter,
                                               label=param_info['label'],
                                               unit=param_info['unit'],
                                               setpoints=tuple(setpoints))

            with meas.run() as datasaver:
                run_id = datasaver.run_id
                opt.run_id = run_id

                res = [(param, val) for param, val in opt.current.items()]
                datasaver.add_result(*res)

                while not self.stopping_condition(opt.num_attempts):
                    # check new parameter settings, select one to move to
                    next_results = self.check_next(opt)
                    opt.num_attempts += 1

                    for result in next_results:
                        res = []
                        for param, val in result.items():
                            if val is not None:
                                res.append((param, val))
                        datasaver.add_result(*res)

                    next_location = self.select_next_location(next_results, opt)

                    if next_location not in next_results:
                        res = []
                        for param, val in next_location.items():
                            res.append((param, val))
                        datasaver.add_result(*res)

                    opt.current = next_location
                    if self.cost_val(next_location) < opt.best_cost_val:
                        opt.best = opt.current
                        opt.best_cost_val = self.cost_val(next_location)

            print(f"Best: {opt.best}")
            return opt

    method = OptimizationMethod()

    return method




