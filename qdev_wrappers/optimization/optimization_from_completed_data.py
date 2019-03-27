import numpy as np
from qcodes.dataset.data_export import load_by_id


def get_measured_data(runid, *data_names, **variable_parameters):
    """Takes runid and variable param values, returns a corresponding cut or point
    in the data.

    args:
        dataname from saved data (fx. 'max_separation')
        variable parameter values (fx. frequency=5.5e9, power=-12)"""
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


