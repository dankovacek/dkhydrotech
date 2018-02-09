"""
Investigate how battery depletion rate depends upon
air temperature (and day of year).
"""

import numpy as np
import pandas as pd
import math
import re
import os
import sys
import base64
import time
import utm
import datetime
from html.parser import HTMLParser

from django.core.mail import send_mail
from django.conf import settings

# from helper_functions import color_negative_red, col_shade, set_up_bokeh_ts_figure
# from helper_functions import load_data, find_newest_message

import statsmodels.api as sm
import scipy

from bokeh.io import curdoc
from bokeh.layouts import row, column, widgetbox
from bokeh.models import ColumnDataSource, Range1d, LinearAxis, Spacer, Band
from bokeh.models import LassoSelectTool, BoxSelectTool, Legend, LegendItem
from bokeh.models import Label
from bokeh.models.widgets import PreText, Select, Slider, Div, Paragraph, Button
from bokeh.plotting import figure, output_file, show
from bokeh.palettes import Spectral11, Spectral6, Viridis11
from bokeh.resources import CDN
from bokeh.embed import file_html

try:
    from functools import lru_cache
except ImportError:
    # Python 2 does stdlib does not have lru_cache so let's just
    # create a dummy decorator to avoid crashing
    print("WARNING: Cache for this example is available on Python 3 only.")

    def lru_cache():
        def dec(f):
            def _(*args, **kws):
                return f(*args, **kws)
            return _
        return dec


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data/')
IMG_DIR = os.path.join(BASE_DIR, "images/")
REPORT_DIR = os.path.join(BASE_DIR, "reports/")

FILENAME = 'Neon_Test_Site.csv'


@lru_cache()
def load_data():
    fname = os.path.join(DATA_DIR, FILENAME)
    df = pd.read_csv(fname, header=0)

    df['DateTime'] = pd.to_datetime(
        df['Date'] + ' ' + df['Time'], dayfirst=True)

    # make sure values are ascending -- not default by Unidata website output
    df = df.sort_values(['DateTime'], ascending=True)

    df = df.drop(['Date', 'Time'], axis=1)

    # check for invalid entries
    # print('# of null entries: ', df.isnull().sum())
    return df


def resample_data(df, sample_period):
    """
    Takes in a dataframe and a sample period (in minutes).
    Returns a dataframe resampled to the specified sample period.
    """
    time_resolution = sample_period  # resample time in minutes

    time_start = df['DateTime'].iloc[0]
    time_end = df['DateTime'].iloc[-1]

    new_index = pd.date_range(str(time_start), str(
        time_end), freq='{}min'.format(time_resolution))

    # df = df.resample('{}min'.format(time_resolution),
    #                  on='DateTime').mean()
    # df.reset_index(inplace=True)

    df.reindex(index=new_index)

    df['External Supply(AVG) (V )'] = df['External Supply(AVG) (mV )'] / 1000

    df = df.drop(['External Supply(AVG) (mV )'], axis=1)

    # add a column representing the battery voltage delta over a timestep
    df['batt_delta'] = (df['External Supply(AVG) (V )'] -
                        df['External Supply(AVG) (V )'].shift(1))

    df['timedelta'] = df['DateTime'] - df['DateTime'].shift(1)

    # add column for timedelta between steps
    df['timedelta'] = df['timedelta'] / np.timedelta64(1, 's')

    # add a column representint elapsed time
    df['elapsed_time'] = df['timedelta'].cumsum()

    # get rid of noninteger battery values
    df = df[np.isfinite(df['batt_delta'])]

    # add column for day of year
    df['day_of_year'] = df['DateTime'].apply(
        lambda x: x.timetuple().tm_yday)

    return df


########################################
#  Functions for OLS best-fit
########################################

def update_temp_best_fit(df, x_param, y_param):

    # fit the depletion based on time vs. delta V
    lin_best_fit = scipy.stats.linregress(df[x_param], df[y_param])

    min_x_param = df[x_param].min()
    max_x_param = df[x_param].max()

    timestep = (max_x_param - min_x_param) / len(df.index.values)

    x_param_domain = np.arange(min_x_param, max_x_param, timestep)

    def linear_eqn(x): return lin_best_fit[0] * x + lin_best_fit[1]

    y_param_range = [linear_eqn(e) for e in x_param_domain]

    reg_df = pd.DataFrame({x_param: x_param_domain,
                           y_param: y_param_range,
                           'DateTime': df['DateTime']})

    return lin_best_fit, reg_df


def update_time_best_fit(df, x_param, y_param):
    # fit the depletion based on time vs. delta V

    lin_best_fit = scipy.stats.linregress(df[x_param], df[y_param])

    time_start = df['elapsed_time'].iloc[0]
    time_end = df['elapsed_time'].iloc[-1]

    min_x_param = time_start  # df[x_param].min()
    # elapsed_time.seconds  # df[x_param].max()
    max_x_param = time_end

    timestep = (max_x_param - min_x_param) / len(df.index.values)

    x_param_domain = np.arange(min_x_param, max_x_param, timestep)
    #x_param_domain = np.linspace(min_x_param, max_x_param)

    def linear_eqn(x): return lin_best_fit[0] * x + lin_best_fit[1]

    y_param_range = [linear_eqn(e) for e in x_param_domain]

    reg_df = pd.DataFrame({y_param: y_param_range,
                           'DateTime': df['DateTime']})

    return lin_best_fit, reg_df


###################################
# Bokeh functions for interactivity
###################################
temp_results_text = Div(text='', width=550)
time_results_text = Div(text='', width=550)

source = ColumnDataSource(data=dict())
source_static = ColumnDataSource(data=dict())

temp_reg_source = ColumnDataSource(data=dict())
time_reg_source = ColumnDataSource(data=dict())


def callback(attrname, old, new):
    update()


resample_slider = Slider(start=5, end=2880, value=5, step=1,
                         title="Resample Rate [minutes]")

resample_slider.on_change('value', callback)

reset_button = Button(label="Reset Selection", button_type="warning")
reset_button.on_click(callback)


def selection_change(attrname, old, new):
    data = load_data()
    data = resample_data(data, resample_slider.value)
    selected = source.selected['1d']['indices']
    if selected:
        data = data.iloc[selected, :]
        data.sort_index(inplace=True)
        update_regression_and_stats(data)


def calculate_depletion_time(df, fit_fn):
    if resample_slider.value < 30:
        last_batt_level = df['External Supply(AVG) (V )'].iloc[-3:].mean()
    else:
        last_batt_level = df['External Supply(AVG) (V )'].iloc[-1]
    print('last battery level = ', last_batt_level)
    batt_low_limit = 12.1
    if last_batt_level < batt_low_limit:
        return 0
    else:
        remaining_batt = last_batt_level - batt_low_limit
        return remaining_batt / fit_fn[0]


def update_regression_and_stats(df):
    temp_best_fit_fn, temp_reg_df, = update_temp_best_fit(
        df, 'Temperature(RAW) (Deg C )', 'batt_delta')

    time_best_fit_fn, time_reg_df = update_time_best_fit(
        df, 'elapsed_time', 'External Supply(AVG) (V )')

    depletion_time = calculate_depletion_time(df, time_best_fit_fn)

    update_time_stats(time_best_fit_fn, depletion_time)
    update_temp_stats(temp_best_fit_fn, depletion_time)

    source.data = source.from_df(df)
    source_static.data = source.data

    temp_reg_source.data = temp_reg_source.from_df(temp_reg_df)
    time_reg_source.data = time_reg_source.from_df(time_reg_df)


def update():
    raw_df = load_data()
    df = resample_data(raw_df, resample_slider.value)
    update_regression_and_stats(df)


def update_temp_stats(best_fit_fn, depletion_time):
    time_step = resample_slider.value
    temp_results_text.text = """
    <h4>R^2 = {:2.2f}</h4>
    <h4>Power Supply Discharge Rate:</h4>
    <p>{:2.2f} V / (degree Celsius) / ({:4.0f} minute timestep)</p>
    <p>{}</p>
    <h4>Projected time to low-battery threshold:</h4>
    {} days
    """.format(best_fit_fn[2], best_fit_fn[0], time_step, best_fit_fn, depletion_time)


def update_time_stats(best_fit_fn, depletion_time):
    time_step = resample_slider.value
    time_results_text.text = """
    <h4>R^2 = {:2.2f}</h4>
    <h4>Power Depletion Rate: </h4>
    <p>{:2.2f} V / ({:4.0f} minute timestep)</p>
    <p>{}</p>
    <h4>Projected time to low-battery threshold:</h4>
    {} days
    """.format(best_fit_fn[2], best_fit_fn[0], time_step, best_fit_fn, depletion_time)


source.on_change('selected', selection_change)


update()


###########################
#  Bokeh Figure Plotting & UI params
###########################
batt_series_name = 'External Supply(AVG) (V )'
batt_delta_series_name = 'batt_delta'
temp_series_name = 'Temperature(RAW) (Deg C )'

TOOLS = "pan,wheel_zoom,box_zoom,box_select,lasso_select,reset"

# figure for battery level
battery_level_fig = figure(plot_width=500, plot_height=300,
                           tools=TOOLS, toolbar_location="above",
                           toolbar_sticky=False, x_axis_type="datetime")

battery_level_fig.xaxis.axis_label = "Date"
battery_level_fig.yaxis.axis_label = "Voltage [V]"

# Setting the second y axis range name and range
battery_level_fig.extra_y_ranges = {
    temp_series_name: Range1d(start=-10, end=30)}

# Adding the second axis to the plot.
battery_level_fig.add_layout(LinearAxis(
    y_range_name=temp_series_name, axis_label='Air Temp [C]'), 'right')


# battery_level_fig.title.text = 'Battery'
battery_level_fig.line('DateTime', batt_series_name, source=source_static,
                       legend='Battery Voltage [V]', line_color=Spectral11[8], line_width=2)

battery_level_fig.line('DateTime', temp_series_name, source=source_static,
                       legend='Air Temp [C]', line_color=Spectral11[2],
                       y_range_name=temp_series_name, line_width=1)

battery_level_fig.circle('DateTime', batt_series_name, source=source, size=2,
                         color=Spectral11[8], selection_color='orange',
                         fill_alpha=0.2, selection_alpha=0.8)

battery_level_fig.line('DateTime', batt_series_name,
                       source=time_reg_source, legend='Best Fit',
                       line_color=Spectral11[0], line_width=2)

battery_level_fig.legend.location = "top_left"
battery_level_fig.legend.click_policy = "hide"

battery_regression_fig = figure(plot_width=500, plot_height=300,
                                tools=TOOLS, toolbar_location="above",
                                toolbar_sticky=False)

battery_regression_fig.xaxis.axis_label = "Air Temp [C]"
battery_regression_fig.yaxis.axis_label = "Voltage delta [V]"
battery_regression_fig.title.text = "delta Battery [V] vs. Temperature [C]"


# add a series corresponding to the line at 12.1 V
battery_regression_fig.circle(temp_series_name, batt_delta_series_name, source=source,
                              color=Spectral11[2], size=4,
                              selection_color='orange', fill_alpha=0.6)


battery_regression_fig.line(temp_series_name, batt_delta_series_name,
                            source=temp_reg_source, legend='Best Fit',
                            line_color=Spectral11[0], line_width=2)

battery_level_fig.legend.location = "top_left"
battery_level_fig.legend.click_policy = "hide"
time_fig_row = row(battery_level_fig, column(
    resample_slider, time_results_text))  # reset_button
temp_fig_row = row(battery_regression_fig, temp_results_text)

layout = column(time_fig_row, temp_fig_row)

curdoc().add_root(layout)
curdoc().title = "Battery Example"
