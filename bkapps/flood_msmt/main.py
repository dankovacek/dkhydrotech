import os
import sys
import math

import numpy as np
import pandas as pd
import time
import param

import scipy.special
import scipy.stats as st

from multiprocessing import Pool

from bokeh.layouts import row, column
from bokeh.models import CustomJS, Slider, Band, Spinner
from bokeh.plotting import figure, curdoc, ColumnDataSource
from bokeh.models.widgets import AutocompleteInput, Div, Toggle

path = os.path.abspath(os.path.dirname(__file__))
if not path in sys.path:
    sys.path.append(path)

from get_station_data import get_daily_UR, get_annual_inst_peaks

from stations import IDS_AND_DAS, STATIONS_DF, IDS_TO_NAMES, NAMES_TO_IDS



def get_stats(data, param):
    mean = data[param].mean()
    var = np.var(data[param])
    stdev = data[param].std()
    skew = st.skew(data[param])
    return mean, var, stdev, skew

def calculate_Tr(data, param, correction_factor=None):
    if correction_factor is None:
        correction_factor = 1

    data.loc[:, 'rank'] = data[param].rank(ascending=False, method='first')
    data.loc[:, 'logQ'] = list(map(math.log, data[param]))

    data.loc[:, 'Tr'] = (len(data) + 1) / \
        data['rank'].astype(int).round(1).copy()

    data = data.sort_values(by='rank', ascending=False)

    return data 

def norm_ppf(x):
    if x == 1.0:
        x += 0.001
    return st.norm.ppf(1-(1/x))

def update_UI_text_output(n_years):
    ffa_info.text = """Mean of {} simulations of a sample size {} \n
    out of a total {} years of record.  \n
    Coloured bands represent the 67 and 95 per cent confidence intervals, respectively.""".format(
        simulation_number_input.value, n_years, n_years)

    error_info.text = ""

def randomize_measurement_error(data):
    """
    Using the reported measured values as base points,
    and using the specified measurement error,
    generate a randomized resampling of the data 
    points accounting for the level of measurement
    error. 
    Note that the error is assumed constant across
    all data points.
    """
    msmt_error = msmt_error_input.value / 100.

    multipliers = np.random.uniform(low=1. - msmt_error, 
                                            high=1. + msmt_error, 
                                            size=len(data))

    data['peak_sim'] = np.multiply(data['PEAK'], multipliers)

    return data[['peak_sim']]


def set_up_model(df):
    log_skew = st.skew(np.log10(df['PEAK']))
    model = pd.DataFrame()
    model['Tr'] = np.linspace(1.01, 200, 500)
    model.set_index('Tr', inplace=True)
    model['z'] = list(map(norm_ppf, model.index.values))

    # # z_model = np.array(list(map(norm_ppf, df.index.values)))
    # z_empirical = np.array(list(map(norm_ppf, model.index)))

    lp3_model = 2 / log_skew * \
        (np.power((model['z'] - log_skew / 6) * log_skew / 6 + 1, 3) - 1)

    model['lp3_quantiles_model'] = np.power(10, np.mean(
        np.log10(df['PEAK'])) + lp3_model*np.std(np.log10(df['PEAK'])))

    return model


def run_ffa_simulation(model, data, target_param, n_simulations):
    # reference:
    # https://nbviewer.jupyter.org/github/demotu/BMC/blob/master/notebooks/CurveFitting.ipynb

    for i in range(n_simulations):

        # sample_set = data.sample(
        #     sample_size_input.value, replace=False)

        # For the measurement uncertainty simulation, use all points
        # instead of sampling from sample subset
        sample_set = randomize_measurement_error(data)

        selection = calculate_Tr(sample_set, target_param)

        # log-pearson distribution
        log_skew = st.skew(np.log10(selection[target_param]))

        lp3 = 2 / log_skew * \
            (np.power((model['z'] - log_skew / 6) * log_skew / 6 + 1, 3) - 1)

        lp3_model = np.power(10, np.mean(
            np.log10(selection[target_param])) + lp3 * np.std(np.log10(selection[target_param])))

        model[i] = lp3_model
    return model


def fit_LP3(df):
    ### 
    # First, fit an LP3 to the raw measured data.
    # This will be our basis of comparison
    # plot the log-pearson fit to the entire dataset
    log_skew = st.skew(np.log10(df['PEAK']))
    z_model = np.array(list(map(norm_ppf, df.index.values)))
    z_empirical = np.array(list(map(norm_ppf, df['Tr'])))

    lp3_model = 2 / log_skew * \
        (np.power((z_model - log_skew / 6) * log_skew / 6 + 1, 3) - 1)

    lp3_empirical = 2 / log_skew * \
        (np.power((z_empirical - log_skew/6)*log_skew/6 + 1, 3) - 1)

    df['lp3_quantiles_model'] = np.power(10, np.mean(
        np.log10(df['PEAK'])) + lp3_model*np.std(np.log10(df['PEAK'])))

    df['lp3_quantiles_theoretical'] = np.power(10, np.mean(
        np.log10(df['PEAK'])) + lp3_empirical*np.std(np.log10(df['PEAK'])))

    # pearson_fit_params = st.pearson3.fit(np.log(data['PEAK']))

    # reverse the order for proper plotting on P-P plot
    df['theoretical_cdf'] = st.pearson3.cdf(z_empirical, skew=log_skew)[::-1]

    # need to remember why I've added 1 to the denominator
    # has to do with sample vs. population?
    df['empirical_cdf'] = df['rank'] / (len(df) + 1)

    df['Mean'] = np.mean(df['PEAK'])

    return df


def get_data_and_initialize_dataframe():
    station_name = station_name_input.value.split(':')[-1].strip()

    df = get_annual_inst_peaks(
        NAMES_TO_IDS[station_name])

    if len(df) < 2:
        error_info.text = "Error, insufficient data in record (n = {}).  Resetting to default.".format(
            len(df))
        station_name_input.value = IDS_TO_NAMES['08MH016']
        update()

    df = calculate_Tr(df, 'PEAK')

    df = fit_LP3(df)
    
    return df


def update():
    
    df = get_data_and_initialize_dataframe()

    ###
    # Now simulate error on the measured data
    # set the target param to PEAK to extract peak annual values 
    # target_param = 'PEAK'

    model = set_up_model(df)

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

    data = df.copy()
    target_param = 'peak_sim'
    time0 = time.time()
    model = run_ffa_simulation(model, data, target_param, n_simulations)
    time_end = time.time()

    print("Time for {:.0f} simulations = {:0.2f} s".format(
        n_simulations, time_end - time0))

    # update the peak flow data source
    # peak_data_reorg
    peak_source.data = peak_source.from_df(data)
    peak_sim_source.data = peak_sim_source.from_df(data)
    data_flag_filter = data[~data['SYMBOL'].isin([None, ' '])]
    peak_flagged_source.data = peak_flagged_source.from_df(data_flag_filter)

    # plot the simulation error bounds
    model['lower_1s_bound'] = model.apply(lambda row: np.percentile(row, 33), axis=1)
    model['upper_1s_bound'] = model.apply(lambda row: np.percentile(row, 67), axis=1)
    model['lower_2s_bound'] = model.apply(lambda row: np.percentile(row, 5), axis=1)
    model['upper_2s_bound'] = model.apply(lambda row: np.percentile(row, 95), axis=1)
    model['expected_value'] = model.apply(lambda row: np.percentile(row, 50), axis=1)
    model['mean_value'] = model.apply(lambda row: row.mean(), axis=1)

    simulation = {'Tr': model.index,
                'lower_1_sigma': model['lower_1s_bound'],
                'upper_1_sigma': model['upper_1s_bound'],
                'lower_2_sigma': model['lower_2s_bound'],
                'upper_2_sigma': model['upper_2s_bound'],
                'mean': model['mean_value'],
                'EV': model['expected_value'],
                'lp3_model': model['lp3_quantiles_model']
                }    

    distribution_source.data = simulation
    
    update_UI_text_output(n_years)


def update_station(attr, old, new):
    update()


def update_n_simulations(attr, old, new):
    if new > 1000:
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


def update_simulation_sample_size(attr, old, new):
    update()


def update_sim(foo):
    data = get_data_and_initialize_dataframe()

    data['peak_sim'] = randomize_measurement_error(data)

    data = calculate_Tr(data, 'peak_sim')

    data.sort_values('Tr', inplace=True)
    # print(data[['Tr', 'peak_sim']])
    
    peak_sim_source.data = data

# configure Bokeh Inputs, data sources, and plots
autocomplete_station_names = list(STATIONS_DF['Station Name'])
peak_source = ColumnDataSource(data=dict())
peak_flagged_source = ColumnDataSource(data=dict())
peak_sim_source = ColumnDataSource(data=dict())
distribution_source = ColumnDataSource(data=dict())
qq_source = ColumnDataSource(data=dict())


station_name_input = AutocompleteInput(
    completions=autocomplete_station_names, title='Enter Station Name (ALL CAPS)',
    value=IDS_TO_NAMES['08MH016'], min_characters=3)

simulation_number_input = Spinner(
    high=1000, low=1, step=1, value=50, title="Number of Simulations",
)

sample_size_input = Spinner(
    high=200, low=2, step=1, value=10, title="Sample Size for Simulations"
)

msmt_error_input = Spinner(
    high=100, low=0., step = 5, value=20, title="Measurement Uncertainty [%]"
)

toggle_button = Toggle(label="Simulate Measurement Error", button_type="success")

ffa_info = Div(
    text="Mean of {} simulations for a sample size of {}.".format('x', 'y'))

error_info = Div(text="", style={'color': 'red'})

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

# widgets
ts_plot = figure(title="Annual Maximum Flood",
                width=800,
                height=250,
                output_backend="webgl")

ts_plot.xaxis.axis_label = "Year"
ts_plot.yaxis.axis_label = "Flow [m³/s]"


# add the simulated measurement error points
ts_plot.triangle('YEAR', 'peak_sim', source=peak_sim_source, 
                legend_label='Sim. Msmt. Error', size=3, 
                color='red', alpha=0.5)

# add the recorded measurement values
ts_plot.circle('YEAR', 'PEAK', source=peak_source, legend_label="Measured Data", size=4)
ts_plot.circle('YEAR', 'PEAK', source=peak_flagged_source, color="orange",
            legend_label="(QA/QC Flag)", size=4)


ts_plot.line('YEAR', 'Mean', source=peak_source, color='red',
            legend_label='Mean Annual Max', line_dash='dashed')

ts_plot.legend.location = "top_left"
ts_plot.legend.click_policy = 'hide'

# create a plot for the Flood Frequency Values and style its properties
ffa_plot = figure(title="Flood Frequency Analysis Explorer",
                x_range=(0.9, 2E2),
                x_axis_type='log',
                width=800,
                height=500,
                output_backend="webgl")

ffa_plot.xaxis.axis_label = "Return Period (Years)"
ffa_plot.yaxis.axis_label = "Flow (m³/s)"

# add the simulated measurement error points
ffa_plot.triangle('Tr', 'peak_sim', source=peak_sim_source, 
                legend_label='Sim. Msmt. Error', size=3, 
                color='red', alpha=0.5)

ffa_plot.circle('Tr', 'PEAK', source=peak_source, legend_label="Measured Data")
ffa_plot.circle('Tr', 'PEAK', source=peak_flagged_source, color="orange",
                legend_label="Measured Data (QA/QC Flag)")
ffa_plot.line('Tr', 'lp3_model', color='red',
            source=distribution_source,
            legend_label='Log-Pearson3 (Measured Data)')

ffa_plot.line('Tr', 'mean', color='navy',
            line_dash='dotted',
            source=distribution_source,
            legend_label='Mean Simulation')

ffa_plot.line('Tr', 'EV', color='orange',
            line_dash='dashed',
            source=distribution_source,
            legend_label='Expected Value')


# plot the error bands as shaded areas
ffa_2_sigma_band = Band(base='Tr', lower='lower_2_sigma', upper='upper_2_sigma', level='underlay',
                        fill_alpha=0.25, fill_color='#1c9099',
                        source=distribution_source)
ffa_1_sigma_band = Band(base='Tr', lower='lower_1_sigma', upper='upper_1_sigma', level='underlay',
                        fill_alpha=0.65, fill_color='#a6bddb', 
                        source=distribution_source)

ffa_plot.add_layout(ffa_2_sigma_band)
ffa_plot.add_layout(ffa_1_sigma_band)

ffa_plot.legend.location = "top_left"
ffa_plot.legend.click_policy = "hide"

# prepare a Q-Q plot
qq_plot = figure(title="Q-Q Plot",
                width=400,
                height=300,
                output_backend="webgl")

qq_plot.xaxis.axis_label = "Empirical"
qq_plot.yaxis.axis_label = "Theoretical"

qq_plot.circle('PEAK', 'lp3_quantiles_theoretical', source=peak_source)
qq_plot.line('PEAK', 'PEAK', source=peak_source, legend_label='1:1',
            line_dash='dashed', color='green')

qq_plot.legend.location = 'top_left'

# prepare a P-P plot
pp_plot = figure(title="P-P Plot",
                width=400,
                height=300,
                output_backend="webgl")

pp_plot.xaxis.axis_label = "Empirical"
pp_plot.yaxis.axis_label = "Theoretical"

pp_plot.circle('empirical_cdf', 'theoretical_cdf', source=peak_source)
pp_plot.line('empirical_cdf', 'empirical_cdf', source=peak_source, legend_label='1:1',
            line_dash='dashed', color='green')

pp_plot.legend.location = 'top_left'

# create a page layout
layout = column(station_name_input,
                # sample_size_input,
                row(simulation_number_input, msmt_error_input, toggle_button),
                ffa_info,
                error_info,
                ts_plot,
                ffa_plot,
                row(qq_plot, pp_plot)
                )

curdoc().add_root(layout)
