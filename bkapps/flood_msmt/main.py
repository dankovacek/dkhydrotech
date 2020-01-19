import os
import sys
import math

import numpy as np
import pandas as pd
import time
import param

from functools import lru_cache

import scipy.special
import scipy.stats as st

from numba import jit

from bokeh.layouts import row, column
from bokeh.models import CustomJS, Slider, Band, Spinner
from bokeh.plotting import figure, curdoc, ColumnDataSource
from bokeh.models.widgets import AutocompleteInput, Div, Toggle
from bokeh.models.widgets import DataTable, TableColumn

from figures import *

path = os.path.abspath(os.path.dirname(__file__))
if not path in sys.path:
    sys.path.append(path)

from get_station_data import get_daily_UR, get_annual_inst_peaks

from stations import IDS_AND_DAS, STATIONS_DF, IDS_TO_NAMES, NAMES_TO_IDS


def norm_ppf(x):
    if x == 1.0:
        x += 0.001
    if x < 0.001:
        x = 0.001
    return st.norm.ppf(1-(1/x))

def calculate_sample_statistics(x):
    return (np.mean(x), np.var(x), np.std(x), st.skew(x))

def update_UI_text_output(n_years):
    ffa_info.text = """Mean of {} simulations of a sample size {} \n
    out of a total {} years of record.  \n
    Coloured bands represent the 67 and 95 per cent confidence intervals, respectively.""".format(
        simulation_number_input.value, n_years, n_years)
    error_info.text = ""


def set_up_model(df):
    log_skew = st.skew(np.log10(df['PEAK']))
    model = pd.DataFrame()
    model['Tr'] = np.linspace(1.01, 200, 500)
    model['z'] = list(map(norm_ppf, model['Tr']))
    model.set_index('Tr', inplace=True)    
    model['lp3_quantiles_theoretical'] = LP3_calc(df['PEAK'], model['z'])
    return model


def randomize_msmt_err(val):
    msmt_error = msmt_error_input.value / 100.
    return val * np.random.uniform(low=1. - msmt_error, 
                             high=1. + msmt_error)


def log_mapper(val):
    return math.log(val)


def LP3_calc(data, z_array):
    # calculate the log-pearson III distribution
    log_skew = st.skew(np.log10(data))
    lp3 = 2 / log_skew * \
        (np.power((z_array - log_skew / 6) * log_skew / 6 + 1, 3) - 1)
    lp3_model = np.power(10, np.mean(
        np.log10(data)) + lp3 * np.std(np.log10(data)))
    return lp3_model

def fit_LP3(df):
    ### 
    # First, fit an LP3 to the raw measured data.
    # This will be our basis of comparison
    # plot the log-pearson fit to the entire dataset

    z_theoretical = np.array(list(map(norm_ppf, (len(df) + 1) / df['rank'])))
    z_empirical = np.array(list(map(norm_ppf, df['Tr'])))

    df['lp3_quantiles_theoretical'] = LP3_calc(df['PEAK'], z_theoretical)
    df['lp3_quantiles_empirical'] = LP3_calc(df['PEAK'], z_empirical)

    # print(df[['lp3_quantiles_empirical', 'lp3_quantiles_theoretical']])

    # reverse the order for proper plotting on P-P plot
    log_skew = st.skew(np.log10(df['PEAK'].values.flatten()))
    df['theoretical_cdf'] = st.pearson3.cdf(z_theoretical, skew=log_skew)

    # need to remember why I've added 1 to the denominator
    # has to do with sample vs. population (degrees of freedom)?
    df['empirical_cdf'] = df['rank'] / (len(df) + 1)

    df['Mean'] = np.mean(df['PEAK'])

    return df


def calculate_Tr(peak_values, years, flags, correction_factor=None):
   
    data = pd.DataFrame()
    data['PEAK'] = peak_values

    msmt_error = msmt_error_input.value / 100.
    data['YEAR'] = years
    data['SYMBOL'] = flags

    if correction_factor is None:
        correction_factor = 1

    data['rank'] = data['PEAK'].rank(ascending=False, method='first')

    log_func_mapper = np.vectorize(log_mapper)

    data['log_Q'] = log_func_mapper(peak_values)

    n_sample = len(peak_values)

    data['Tr'] = (n_sample + 1) / data['rank'].values.flatten()
    data['z'] = np.array(list(map(norm_ppf, data['Tr'])))

    return data

def run_ffa_simulation(data, n_simulations):
    # reference:
    # https://nbviewer.jupyter.org/github/demotu/BMC/blob/master/notebooks/CurveFitting.ipynb

    peak_values = data[['PEAK']].to_numpy().flatten()
    years = data[['YEAR']].to_numpy().flatten
    flags = data[['SYMBOL']].to_numpy().flatten

    simulation_matrix = np.tile(peak_values, (n_simulations, 1))

    v_func = np.vectorize(randomize_msmt_err)

    vectorized_random_value_matrix = v_func(simulation_matrix)

    data = calculate_Tr(peak_values, years, flags)

    model = set_up_model(data)

    def calculate_percentile(row, p):
        return np.percentile(row, p)
    
    def calculate_mean(row):
        return np.mean(row)

    lp3_model = np.apply_along_axis(LP3_calc, 1,
                                    vectorized_random_value_matrix,
                                    z_array=model['z'].values.flatten())

    model['lower_1s_bound'] = np.apply_along_axis(calculate_percentile, 0, lp3_model, p=33.333)
    model['upper_1s_bound'] = np.apply_along_axis(calculate_percentile, 0, lp3_model, p=66.667)
    model['lower_2s_bound'] = np.apply_along_axis(calculate_percentile, 0, lp3_model, p=95.)
    model['upper_2s_bound'] = np.apply_along_axis(calculate_percentile, 0, lp3_model, p=5.)
    model['expected_value'] = np.apply_along_axis(calculate_percentile, 0, lp3_model, p=50.)
    model['mean'] = np.apply_along_axis(calculate_mean, 0, lp3_model)

    return model


def get_data_and_initialize_dataframe():
    station_name = station_name_input.value.split(':')[-1].strip()

    df = get_annual_inst_peaks(
        NAMES_TO_IDS[station_name])

    stats = calculate_sample_statistics(df['PEAK'].values.flatten())
    update_data_table(stats)

    if len(df) < 2:
        error_info.text = "Error, insufficient data in record (n = {}).  Resetting to default.".format(
            len(df))
        station_name_input.value = IDS_TO_NAMES['08MH016']
        update()

    df = calculate_Tr(df['PEAK'].values.flatten(),
                      df['YEAR'].values.flatten(),
                      df['SYMBOL'].values.flatten())

    df = fit_LP3(df)
    
    return df

def update():
    
    df = get_data_and_initialize_dataframe()

    ###
    # Now simulate error on the measured data
    # set the target param to PEAK to extract peak annual values 
    # target_param = 'PEAK'

    n_years = len(df)
    print('number of years of data = {}'.format(n_years))
    print("")

    # prevent the sample size from exceeding the
    # length of record
    if n_years < sample_size_input.value:
        sample_size_input.value = n_years - 1

    # Run the FFA fit simulation on a sample of specified size
    ## number of times to run the simulation
    n_simulations = simulation_number_input.value

    time0 = time.time()
    model = run_ffa_simulation(df, n_simulations)
    time_end = time.time()

    print("Time for {:.0f} simulations = {:0.2f} s".format(
        n_simulations, time_end - time0))

    # df = df.sort_values('PEAK')
    # update the data sources  
    peak_source.data = peak_source.from_df(df)
    peak_sim_source.data = peak_sim_source.from_df(df)
    data_flag_filter = df[~df['SYMBOL'].isin([None, ' '])]
    peak_flagged_source.data = peak_flagged_source.from_df(data_flag_filter)


    df = df.sort_values('lp3_quantiles_empirical')
    
    df['empirical_cdf'] = df['empirical_cdf'].values.flatten()[::-1]
    pp_source.data = pp_source.from_df(df)
    qq_source.data = qq_source.from_df(df)

    distribution_source.data = model
    
    update_UI_text_output(n_years)


def update_station(attr, old, new):
    update()
    update_sim(1)


def update_n_simulations(attr, old, new):
    if new > simulation_number_input.high:
        simulation_number_input.value = 500
        error_info.text = "Max simulation size is 500"
    update()

def update_msmt_error(attr, old, new):
    if new > 100:
        msmt_error_input.value = 100
        error_info.text = "Maximum measurement error is 100."
    if new < 0:
        msmt_error_input.value = 1
        error_info.text = "Minimum measurement error is 0."
    update()
    update_sim()


def update_simulation_sample_size(attr, old, new):
    update()


def update_sim(foo):
    data = get_data_and_initialize_dataframe()

    peak_sim = [randomize_msmt_err(v) for v in data['PEAK']]

    data = calculate_Tr(peak_sim,
                        data['YEAR'].values.flatten(),
                        data['SYMBOL'].values.flatten())

    # Fit LP3 to simulated data
    model = set_up_model(data)
   
    peak_sim_source.data = data
    sim_distribution_source.data = model

def update_pv(attr, old, new):
    data = peak_source.data['PEAK']
    inds = new
    if len(inds) == 0 or len(inds) == len(data):
        vhist1, vhist2 = vzeros, vzeros
    else:
        neg_inds = np.ones_like(data, dtype=np.bool)
        neg_inds[inds] = False
        vhist1, _ = np.histogram(data[inds], bins=vedges)
        vhist2, _ = np.histogram(data[neg_inds], bins=vedges)

    vh1.data_source.data["right"] = vhist1
    vh2.data_source.data["right"] = -vhist2

    if len(inds) > 2:
        stats = [round(e, 2) for e in calculate_sample_statistics(data[inds])]

        datatable_source.data['value_selection'] = [stats[0], stats[2], stats[3]]


def update_data_table(stats):
    """
    order of stats is mean, var, stdev, skew
    """
    df = pd.DataFrame()
    df['parameter'] = ['Mean', 'Standard Deviation', 'Skewness']
    df['value_all_data'] = np.round([stats[0], stats[2], stats[3]], 2)
    df['value_selection'] = np.round([stats[0], stats[2], stats[3]], 2)
    datatable_source.data = dict(df)


# configure Bokeh Inputs, data sources, and plots
autocomplete_station_names = list(STATIONS_DF['Station Name'])
peak_source = ColumnDataSource(data=dict())
peak_flagged_source = ColumnDataSource(data=dict())
peak_sim_source = ColumnDataSource(data=dict())
distribution_source = ColumnDataSource(data=dict())
sim_distribution_source = ColumnDataSource(data=dict())
pp_source = ColumnDataSource(data=dict())
qq_source = ColumnDataSource(data=dict())
datatable_source = ColumnDataSource(data=dict())


station_name_input = AutocompleteInput(
    completions=autocomplete_station_names, title='Enter Station Name (ALL CAPS)',
    value=IDS_TO_NAMES['08MH016'], min_characters=3)

simulation_number_input = Spinner(
    high=5000, low=100, step=1, value=500, title="Number of Simulations",
)

sample_size_input = Spinner(
    high=200, low=2, step=1, value=10, title="Sample Size for Simulations"
)

msmt_error_input = Spinner(
    high=100, low=0., step = 5, value=20, title="Measurement Uncertainty [%]"
)

toggle_button = Toggle(label="Simulate Measurement Error", button_type="success")

ffa_info = Div(width=400,
    text="Mean of {} simulations for a sample size of {}.".format('x', 'y'))

error_info = Div(text="", style={'color': 'red'})

# Set up data table for summary statistics
columns = [
    TableColumn(field="parameter", title="Parameter"),
    TableColumn(field="value_all_data", title="Value (All Data)"),
    TableColumn(field="value_selection", title="Value (Selection)"),
]

data_table = DataTable(source=datatable_source, columns=columns, 
                       width=400, height=100, index_position=None)

# callback for updating the plot based on a changes to inputs
station_name_input.on_change('value', update_station)
simulation_number_input.on_change('value', update_n_simulations)
msmt_error_input.on_change('value', update_msmt_error)
sample_size_input.on_change(
    'value', update_simulation_sample_size)
toggle_button.on_click(update_sim)

# see documentation for threading information
# https://docs.bokeh.org/en/latest/docs/user_guide/server.html

update()
update_sim(1)

# widgets
ts_plot = create_ts_plot(peak_source, peak_sim_source, peak_flagged_source)

vedges, vzeros, vh1, vh2, pv = create_vhist(peak_source, ts_plot)

# peak_source.selected.on_change('indices', update_pv)

ffa_plot = create_ffa_plot(peak_source, peak_sim_source, peak_flagged_source,
                            distribution_source, sim_distribution_source)

qq_plot = create_qq_plot(qq_source)

pp_plot = create_pp_plot(pp_source)

inputs_row = column(station_name_input, row(simulation_number_input, msmt_error_input, toggle_button))

# create a page layout
layout = column(inputs_row,
                row(data_table, ffa_info),
                error_info,
                row(ts_plot, pv),
                row(ffa_plot, column(qq_plot, pp_plot))
                )

curdoc().add_root(layout)
