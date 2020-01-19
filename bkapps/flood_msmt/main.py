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
from bokeh.models import CustomJS, Slider, Band, Spinner, RangeSlider
from bokeh.plotting import figure, curdoc, ColumnDataSource
from bokeh.models.widgets import AutocompleteInput, Div, Toggle
from bokeh.models.widgets import DataTable, TableColumn

from figures import *

path = os.path.abspath(os.path.dirname(__file__))
if not path in sys.path:
    sys.path.append(path)

from get_station_data import get_daily_UR, get_annual_inst_peaks

from skew_calc import calculate_skew

from stations import IDS_AND_DAS, STATIONS_DF, IDS_TO_NAMES, NAMES_TO_IDS


def calculate_sample_statistics(x):
    return (np.mean(x), np.var(x), np.std(x), st.skew(x))


def norm_ppf(x):
    if x == 1.0:
        x += 0.001
    if x < 0.001:
        x = 0.001
    return st.norm.ppf(1-(1/x))


norm_ppf_vector_func = np.vectorize(norm_ppf)


def update_UI_text_output(n_years):
    ffa_info.text = """
    Simulated measurement error is assumed to be a linear function of flow. 
    Coloured bands represent the 67 and 95 % confidence intervals of the 
    curve fit MCMC simulation.  The LP3 shape parameter is the generalized skew.
    """.format()
    error_info.text = ""


def set_up_model(df):
    mean, variance, stdev, skew = calculate_sample_statistics(np.log10(df['PEAK']))
    model = pd.DataFrame()
    model['Tr'] = np.linspace(1.01, 200, 500)
    model['theoretical_cdf'] = 1 / model['Tr']
    log_q = st.pearson3.ppf(1 - model['theoretical_cdf'], abs(skew),
                            loc=mean, scale=stdev)
    model['theoretical_quantiles'] = np.power(10, log_q)
    return model


def randomize_msmt_err(val, msmt_err_params):
    msmt_error = val * msmt_err_params[0] + msmt_err_params[1]
    return val * np.random.uniform(low=1. - msmt_error, 
                             high=1. + msmt_error)


def LP3_calc(data, exceedance):
    # calculate the log-pearson III distribution
    mean, variance, stdev, skew = calculate_sample_statistics(np.log10(data))
    lp3_model = st.pearson3.ppf(exceedance, abs(skew), loc=mean, scale=stdev)
    return np.power(10, lp3_model)


def calculate_measurement_error_params(data):
    """
    Assume measurement error is a linear function
    of magnitude of flow.
    """
    min_e, max_e = np.divide(msmt_error_input.value, 100.)
    min_q, max_q = min(data), max(data)
    m = (max_e - min_e) / (max_q - min_q)
    b = min_e - m * min_q
    print(m, b)
    return (m, b)


def run_ffa_simulation(data, n_simulations):
    # reference:
    # https://nbviewer.jupyter.org/github/demotu/BMC/blob/master/notebooks/CurveFitting.ipynb

    peak_values = data[['PEAK']].to_numpy().flatten()
    years = data[['YEAR']].to_numpy().flatten
    flags = data[['SYMBOL']].to_numpy().flatten

    data = calculate_distributions(peak_values, years, flags)
    model = set_up_model(data)

    simulation_matrix = np.tile(peak_values, (n_simulations, 1))

    msmt_error_params = calculate_measurement_error_params(peak_values)

    simulated_error = np.apply_along_axis(randomize_msmt_err, 1,
                                          simulation_matrix,
                                          msmt_err_params=msmt_error_params)

    exceedance = 1 - model['theoretical_cdf'].values.flatten()

    simulation = np.apply_along_axis(LP3_calc, 1,
                                     simulated_error,
                                     exceedance=exceedance)

    # print(simulation)
    # print(simulation.shape)
    # print('')
    
    model['lower_1s_bound'] = np.apply_along_axis(np.percentile, 0, simulation, q=33)
    model['upper_1s_bound'] = np.apply_along_axis(np.percentile, 0, simulation, q=67)
    model['lower_2s_bound'] = np.apply_along_axis(np.percentile, 0, simulation, q=5)
    model['upper_2s_bound'] = np.apply_along_axis(np.percentile, 0, simulation, q=95)
    model['expected_value'] = np.apply_along_axis(np.percentile, 0, simulation, q=50.)
    model['mean'] = np.apply_along_axis(np.mean, 0, simulation)
    # print(model[['lower_2s_bound', 'upper_2s_bound', 'lower_1s_bound', 'upper_1s_bound']])

    return model


def calculate_distributions(peak_values, years, flags, correction_factor=None):
   
    n_sample = len(peak_values)
    data = pd.DataFrame()
    data['PEAK'] = peak_values
    data['log_Q'] = np.log10(peak_values)
    data['YEAR'] = years
    data['SYMBOL'] = flags
    mean, variance, stdev, skew = calculate_sample_statistics(np.log10(peak_values))
    print('skew = {:.2f}'.format(skew))
    skew = abs(skew)

    data['Tr'] = (n_sample + 1) / data['PEAK'].rank(ascending=False)

    data['empirical_pdf'] = st.pearson3.pdf(np.log10(peak_values), skew, loc=mean, scale=stdev)
    data['empirical_cdf'] = st.pearson3.cdf(np.log10(peak_values), skew, loc=mean, scale=stdev)
    data['theoretical_cdf'] = 1 - 1 / data['Tr']
    data['theoretical_quantiles'] = np.power(10, st.pearson3.ppf(data['theoretical_cdf'], 
                                                    skew, loc=mean, scale=stdev))
    data['mean'] = np.mean(peak_values)
    data = data.sort_values('Tr', ascending=False)

    return data


def get_data_and_initialize_dataframe():
    station_name = station_name_input.value.split(':')[-1].strip()

    peak_source.selected.indices = []
    
    df = get_annual_inst_peaks(
        NAMES_TO_IDS[station_name])

    if len(df) < 2:
        error_info.text = "Error, insufficient data in record (n = {}).  Resetting to default.".format(
            len(df))
        station_name_input.value = IDS_TO_NAMES['08MH016']
        update_sim(1)
        return update()

    df = calculate_distributions(df['PEAK'].values.flatten(),
                      df['YEAR'].values.flatten(),
                      df['SYMBOL'].values.flatten())

    return df

def update():
    
    df = get_data_and_initialize_dataframe()

    update_data_table(df['PEAK'].values.flatten())

    # prevent the sample size from exceeding the length of record
    n_years = len(df)
    if n_years < sample_size_input.value:
        sample_size_input.value = n_years - 1

    # Run the FFA fit simulation on a sample of specified size
    # number of times to run the simulation
    n_simulations = simulation_number_input.value

    time0 = time.time()
    model = run_ffa_simulation(df, n_simulations)
    time_end = time.time()

    # print(model[['Tr', 'theoretical_quantiles', 'theoretical_cdf']].head())
    # print(model.columns)

    print("Time for {:.0f} simulations = {:0.2f} s".format(
        n_simulations, time_end - time0))

    # update the data sources  
    peak_source.data = peak_source.from_df(df)
    peak_source.selected
    peak_sim_source.data = peak_sim_source.from_df(df)
    data_flag_filter = df[~df['SYMBOL'].isin([None, ' '])]
    peak_flagged_source.data = peak_flagged_source.from_df(data_flag_filter)

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
    update_sim(1)


def update_msmt_error(attr, old, new):
    update()
    update_sim(1)


def update_simulation_sample_size(attr, old, new):
    update()


def update_sim(foo):
    data = get_data_and_initialize_dataframe()

    msmt_error_params = calculate_measurement_error_params(data['PEAK'])

    peak_sim = [randomize_msmt_err(v, msmt_error_params) for v in data['PEAK']]

    data = calculate_distributions(peak_sim,
                        data['YEAR'].values.flatten(),
                        data['SYMBOL'].values.flatten())

    # Fit LP3 to simulated data
    model = set_up_model(data)
  
    peak_sim_source.data = data
    sim_distribution_source.data = model


def update_pv_plot(data, inds):
    if len(inds) == 0 or len(inds) == len(data):
        vhist1, vhist2 = vzeros, vzeros
    else:
        neg_inds = np.ones_like(data, dtype=np.bool)
        neg_inds[inds] = False
        vhist1, _ = np.histogram(data[inds], bins=vedges)
        vhist2, _ = np.histogram(data[neg_inds], bins=vedges)

    vh1.data_source.data["right"] = vhist1
    vh2.data_source.data["right"] = -vhist2


def update_ffa_plot(data, inds):
    if len(inds) > 2:
        pass


def update_figs(attr, old, new):
    inds = new

    # update the datatable only if at least three points are selected
    if len(inds) > 2:
        data = peak_source.data['PEAK']
        update_pv_plot(data, inds)
        update_ffa_plot(data, inds)
        stats = [round(e, 2) for e in calculate_sample_statistics(data[inds])]
        datatable_source.data['value_selection'] = [stats[0], stats[2], stats[3], len(data[inds])]


def update_data_table(data):
    """
    order of stats is mean, var, stdev, skew
    """
    df = pd.DataFrame()
    stats = calculate_sample_statistics(data)
    df['parameter'] = ['Mean', 'Standard Deviation', 'Skewness', 'Sample Size']
    df['value_all'] = np.round([stats[0], stats[2], stats[3], len(data)], 2)
    df['value_selection'] = np.round([stats[0], stats[2], stats[3], len(data)], 2)
    datatable_source.data = dict(df)


# configure Bokeh Inputs, data sources, and plots
autocomplete_station_names = list(STATIONS_DF['Station Name'])
peak_source = ColumnDataSource(data=dict())
peak_flagged_source = ColumnDataSource(data=dict())
peak_sim_source = ColumnDataSource(data=dict())
distribution_source = ColumnDataSource(data=dict())
sim_distribution_source = ColumnDataSource(data=dict())
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

msmt_error_input = RangeSlider(
    start=0, end=100., value=(10, 35), 
    step=2, title="Measurement Uncertainty [%]",
    callback_policy="mouseup"
)

toggle_button = Toggle(label="Simulate Measurement Error", button_type="success")

ffa_info = Div(width=550,
    text="Mean of {} simulations for a sample size of {}.".format('x', 'y'))

error_info = Div(text="", style={'color': 'red'})


# Set up data table for summary statistics
datatable_columns = [
    TableColumn(field="parameter", title="Parameter"),
    TableColumn(field="value_all", title="All Data"),
    TableColumn(field="value_selection", title="Selected Data"),
]

data_table = DataTable(source=datatable_source, columns=datatable_columns,
                       width=450, height=125, index_position=None)

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

peak_source.selected.on_change('indices', update_figs)

vedges, vzeros, vh1, vh2, pv = create_vhist(peak_source, ts_plot)

ffa_plot = create_ffa_plot(peak_source, peak_sim_source, peak_flagged_source,
                           distribution_source, sim_distribution_source)

qq_plot = create_qq_plot(peak_source)

pp_plot = create_pp_plot(peak_source)

input_layout = row(column(simulation_number_input,
                          msmt_error_input,
                          ffa_info, 
                          toggle_button),
                   column(station_name_input,
                          data_table),
                   sizing_mode='scale_both')

# create a page layout
layout = column(input_layout,
                error_info,
                row(ts_plot, pv),
                row(ffa_plot, column(pp_plot, qq_plot))
                )

curdoc().add_root(layout)
