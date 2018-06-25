

import sqlite3
from qdev_wrappers.fitting.Fitclasses import T1, T2


def is_table(tablename, cursor):  # Checks if table already exists. Assumes database connection and cursor already established

    table_count = "SELECT count(*) FROM sqlite_master WHERE type = 'table' AND name='{}'".format(tablename)
    execute = cursor.execute(table_count)
    count = execute.fetchone()[0]

    if count == 0:
        return False

    if count == 1:
        return True


def make_table(tablename, cursor):
    name = tablename
    n = 0

    while is_table(name, cursor):
        n += 1
        name = "{}_{}".format(tablename, n)
    else:
        cursor.execute('CREATE TABLE {} (id INTEGER)'.format(name))

    return name


def fit_to_SQL(data, fitclass, fit):    #it would be an improvement if it were able to get the fitclass from the fit information 

    if fit['estimator']['type'] != fitclass.name:       #maybe this should be more general in this function, like 'analysis_class? - so it makes sense e.g. in the case of Baysian inference
        raise RuntimeError('The data given was analyzed using {}. This does not seem to match {} specified in this function'.format(fit['estimator']['type'], fitclass.name))
    
    dim = 1
    if 'zdata' in fit['inferred_from'].keys():
        dim = 2
    
    xname = fit['inferred_from']['xdata']
    xdata = data[xname]['data']
    
    yname = fit['inferred_from']['ydata']
    ydata = data[yname]['data']
    
    est = []    #estimated/predicted value for the measured data given the fitted parameters
    est_name = '{}_estimate'.format(yname)
    
    p_values = []
    
    if dim == 2:
        zname = fit['inferred_from']['zdata']
        zdata = data[zname]['data'] 
        est_name = '{}_estimate'.format(zname)
        
    
    #make array of estimated values based on parameters and model used
    if dim == 1:
    
        params = list(fitclass.p_labels) 
        for index, parameter in enumerate(params):
            if parameter not in fit['parameters']:
                raise KeyError('The list of parameters for the fitclass {} contains a parameter, {}, which is not present in the fit dictionary.'.format(fitclass.name, parameter))
            params[index] = fit['parameters'][parameter]['value']  
    
        for datapoint in xdata:
            y = fitclass.fun(datapoint, *params)
            est.append(y)
            p_values.append(params)
            
    if dim == 2:
        
        for xpoint, ypoint in zip(xdata, ydata):
        
            if xpoint in fit.keys():
                setpoint = xpoint
                datapoint = ypoint
            elif ypoint in fit.keys():
                setpoint = ypoint
                datapoint = xpoint
        
            params = list(fitclass.p_labels)
            for index, parameter in enumerate(params):
                if parameter not in fit[setpoint]['parameters']:
                    raise KeyError('The list of parameters for the fitclass {} contains a parameter, {}, which is not present in the fit dictionary.'.format(fitclass.name, parameter))
                params[index] = fit[setpoint]['parameters'][parameter]['value']
        
            z = fitclass.fun(datapoint, *params)
            est.append(z)
            p_values.append(params)



    tablename = 'data_{}_{}'.format(data['data_id'], fitclass.name)
    

    table_columns = [est_name]
    for parameter in fitclass.p_labels:
        table_columns.append(parameter)
       
    table_rows = []
    if dim == 1:
        for estimate in est:
            id_nr = est.index(estimate) + 1
            row = (id_nr, estimate, *params)
            table_rows.append(row)
    elif dim == 2:
        for estimate, parameters in zip(est, p_values):
            id_nr = est.index(estimate) + 1
            row = (id_nr, estimate, *parameters)
            table_rows.append(row)



    conn = sqlite3.connect('analysis.db')  # should this go in a separate analysis database, or just go in experiments.db?
    cur = conn.cursor()

    table = make_table(tablename, cur)
 
    for column in table_columns:
        cur.execute('ALTER TABLE {} ADD {}'.format(table, column))
    
    num_cols = len(table_rows[0])
    placeholder = ('?,'*num_cols).strip(',')

    cur.executemany('INSERT INTO {} VALUES ({})'.format(table, placeholder), table_rows)

    conn.commit()
    conn.close()