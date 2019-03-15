import numpy as np
from qcodes.dataset.data_export import get_data_by_id
from numpy.random import randint
from qcodes.dataset.data_export import load_by_id


def get_measured_data(runid, data_names, **variable_parameters):
    dataset = load_by_id(runid)

    param_values = [val for val in variable_parameters.values()]
    param_data = [np.array(dataset.get_data(name)).flatten() for name in variable_parameters]

    measured_data = [np.array(dataset.get_data(name)).flatten() for name in data_names]

    nearest_measured_value = param_data[0][np.argmin(np.abs(param_data[0] - param_values[0]))]
    indices = set(np.argwhere(param_data[0] == nearest_measured_value).flatten())

    for data, val in zip(param_data, param_values):
        nearest_measured_value = data[np.argmin(np.abs(data - val))]
        new_indices = np.argwhere(data == nearest_measured_value).flatten()
        indices = indices.intersection(new_indices)

    data = [d[list(indices)] for d in measured_data]
    return data


def get_params_dict(run_id):
    all_data = get_data_by_id(run_id)
    variable_params = []
    measured_params = []

    for data in all_data:
        for param in data[0:-1]:
            param_info = param.copy()
            param_info['values'] = np.unique(param['data'])
            variable_params.append(param_info)
        param_info = data[-1]
        param_info['values'] = np.unique(data[-1]['data'])
        measured_params.append(param_info)

    return variable_params, measured_params


def get_results(variable_params, measured_params, coordinates):
    results = []
    for co, param in zip(coordinates, variable_params):
        results.append((param['name'], param['values'][co]))
    for param in measured_params:
        data = get_measurement_from_data(variable_params, measured_params, coordinates)
        results.append((param['name'], data))
    return results



def optimize_from_runid(run_id,
                        variable_params,
                        measured_params,
                        get_new_coordinates,
                        cost_val,
                        stopping_condition,
                        max_num_attempts=250):

    start = [randint(0, len(param['values'])) for param in params]
    current = start
    best = start
    num_attempts = 0
    checked = []

    while not stopping_condition(variable_params, best) \
            and not num_attempts == max_num_attempts:
        # check new parameter settings, select one to move to
        new_coordinates = get_new_coordinates(current, variable_params)
        num_attempts += 1

        for coordinates in new_coordinates:
            # add location to list of locations checked
            checked.append(coordinates)
            # ToDo: this is not general and needs to be separated out from the rest of it
            if cost_val(variable_params, measured_params, coordinates) < cost_val(variable_params, measured_params, current):
                current = coordinates

        if cost_val(variable_params, measured_params, current) < cost_val(variable_params, measured_params, best):
            best = current

    best_val = get_measurement_from_data(variable_params, measured_params, best)
    print(f"Best value {best_val} at {best}")
    return best_val, best, checked, num_attempts


def try_many(num_attempts,
             run_id,
             variable_params,
             measured_params,
             get_new_coordinates,
             cost_val,
             stopping_condition,
             success_condition=None):
    # success_condition: a function that takes the best_value and returns True for a success, otherwise False
    if success_condition is not None:
        successes = 0
    measurements_done = 0
    iterations = 0
    best_value = []
    best_coordinates = []
    starts = []

    for attempt in range(0, num_attempts):
        optimization = optimize_from_runid(run_id,
                                           variable_params,
                                           measured_params,
                                           get_new_coordinates,
                                           cost_val,
                                           stopping_condition,
                                           max_num_attempts=150)

        iterations += len(optimization.checked)
        measurements_done += len(np.unique(optimization.checked))
        starts.append(optimization.start)
        best_coordinates.append(optimization.best)

        value = get_measurement_from_data(variable_params, measured_params, optimization.best)
        best_value.append(value)
        if success_condition is not None:
            if success_condition(value):
                successes += 1

    avg_measurements = measurements_done / num_attempts
    avg_num_iterations = iterations / num_attempts

    # if num_attempts % 10 == 0:
    #     print(num_attempts)

    if success_condition is not None:
        return best_coordinates, best_value, starts, avg_measurements, avg_num_iterations, successes/num_attempts
    else:
        return best_coordinates, best_value, starts, avg_measurements, avg_num_iterations
