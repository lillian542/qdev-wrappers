

import sqlite3
import dill
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


def fit_to_SQL(fit):    #it would be an improvement if it were able to get the fitclass from the fit information

    fitclass_pckl = fit['estimator']['dill']
    fitclass = dill.loads(fitclass_pckl)

    est_values = fit['estimate']['values']
    est_name = '{}_estimate'.format(fit['estimate']['name'])
    est_label = fit['estimate']['label']
    est_unit = fit['estimate']['unit']
    param_values = fit['estimate']['parameters']

    dim = fit['inferred_from']['dimensions']

    if dim == 1:
        param_units = [fit['parameters'][param]['unit'] for param in list(fitclass.p_labels)]
    elif dim == 2:
        setpoints = [key for key in fit.keys()]
        param_units = [fit[setpoints[0]]['parameters'][param]['unit'] for param in list(fitclass.p_labels)]


    tablename = 'analysis_{}_{}'.format(fit['inferred_from']['run_id'], fitclass.name)
    

    table_columns = [est_name]
    for parameter in fitclass.p_labels:
        table_columns.append(parameter)

    table_rows = []
    if dim == 1:
        for estimate, params in zip(est_values, param_values):
            id_nr = est_values.index(estimate) + 1
            row = (id_nr, estimate, *params)
            table_rows.append(row)
    elif dim == 2:
        for estimate, parameters in zip(est_values, param_values):
            id_nr = est_values.index(estimate) + 1
            row = (id_nr, estimate, *parameters)
            table_rows.append(row)



    data_run_id = fit['inferred_from']['run_id']
    exp_id = fit['inferred_from']['exp_id']
    predicts = est_name.strip("estimate").strip("_")
    estimator = "{}, {}".format(fit['estimator']['method'], fit['estimator']['type'])
    analysis = fit['estimator']['function used']
    dill_obj = fit['estimator']['dill']
    parameters = fitclass.p_labels
    param_labels = fitclass.p_names


    conn = sqlite3.connect('experiments.db')  # should this go in a separate analysis database, or just go in experiments.db?
    cur = conn.cursor()

    #Alternative: have a separate function that sets up the general analysis database with tables, so that this doesn't have to be here
    if not is_table('analyses', cur):
        cur.execute('''CREATE TABLE analyses
                        (data_run_id INTEGER, exp_id INTEGER, run_id INTEGER, analysis_table_name TEXT,
                        predicts TEXT, estimator TEXT, function TEXT, dill TEXT)''')




    table = make_table(tablename, cur)

    for column in table_columns:
        cur.execute('ALTER TABLE {} ADD {}'.format(table, column))

    num_cols = len(table_rows[0])
    placeholder = ('?,' * num_cols).strip(',')

    cur.executemany('INSERT INTO {} VALUES ({})'.format(table, placeholder), table_rows)





    sql_analyses = 'INSERT INTO analyses VALUES (?,?,?,?,?,?,?,?)'

    run_id = 1
    max_id = cur.execute('SELECT MAX(run_id) FROM layouts').fetchone()[0]
    if max_id != None:
        run_id += max_id

    cur.execute(sql_analyses, (data_run_id, exp_id, run_id, table, predicts, estimator, analysis, dill_obj))




    sql_layout = 'INSERT INTO layouts VALUES (?,?,?,?,?,?)'

    layout_id = 1
    max_id = cur.execute('SELECT MAX(layout_id) FROM layouts').fetchone()[0]
    if max_id != None:
        layout_id += max_id

    layout_rows = []
    for parameter, label, unit in zip(parameters, param_labels, param_units):
        row = (layout_id, run_id, parameter, label, unit, "inferred_from")
        layout_rows.append(row)
        layout_id += 1
    layout_rows.append((layout_id, run_id, est_name, est_label, est_unit, "inferred_from"))

    cur.executemany(sql_layout, (layout_rows))




    sql_runs = 'INSERT INTO runs VALUES (?,?,?,?,?,?,?,?,?,?)'
    cur.execute(sql_runs, (run_id, exp_id, 'analysis', table, "", "", "", 1, "", ""))




    conn.commit()
    conn.close()

    print("Table {} created".format(table))
