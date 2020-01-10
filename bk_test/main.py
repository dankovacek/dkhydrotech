#   Regularized Linear Regression and Bias-Variance
#   Applied to Streamflow Data

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

import math
import os
import sys
import time

import bokeh
import numpy as np
import pandas as pd

from bokeh.io import curdoc
from bokeh.layouts import row, column, widgetbox
from bokeh.models import ColumnDataSource, Range1d, LinearAxis, Spacer, Band
from bokeh.models import LassoSelectTool, BoxSelectTool, Legend, LegendItem
from bokeh.models import Label
from bokeh.models.widgets import PreText, Select, Slider
from bokeh.plotting import figure
from bokeh.palettes import Spectral11, Viridis11

from helper_functions import load_data
from helper_functions import apply_poly, getRandomChronSets
from helper_functions import SITES, Site

# Define data folders
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')

VARS = {}
VARS['proportion'] = {}
VARS['proportion']['p_train'] = 0.6
VARS['proportion']['p_test'] = (1 - VARS['proportion']['p_train']) / 2
VARS['proportion']['p_val'] = (1 - VARS['proportion']['p_train']) / 2
VARS['poly_order'] = 1

start_time = time.time()

# set up data sources for bokeh plotting
source = ColumnDataSource(data=dict())
source_static = ColumnDataSource(data=dict())
train_source = ColumnDataSource(data=dict())
val_source = ColumnDataSource(data=dict())
test_source = ColumnDataSource(data=dict())
# gradDesc_source_static = ColumnDataSource(data=dict())
learningCurve_source = ColumnDataSource(data=dict())
polyLearningCurve_source = ColumnDataSource(data=dict())
lamLearningCurve_source = ColumnDataSource(data=dict())
poly_curves_source = ColumnDataSource(data=dict())
output_regression_source = ColumnDataSource(data=dict())
model_performance_source = ColumnDataSource(data=dict())
# data_breakdown_source = ColumnDataSource(data=dict())

results_text = PreText(text="")


@lru_cache()
def get_data(site_1, site_2):
    s1 = Site(SITES[site_1])
    s2 = Site(SITES[site_2])

    df1 = load_data(**s1)
    df2 = load_data(**s2)
    # load all data and concatenate series for concurrent days
    all_data = pd.concat([df1, df2], axis=1, join='inner')
    return s1, s2, all_data


s1, s2, all_data = get_data('lillooet', 'squamish')
load_data_time = time.time() - start_time
print('time to load data = ', load_data_time)

VARS['len_dataset'] = len(all_data)

# initialize a colour pallette for plotting multiple lines
mypalette = Viridis11

TOOLS = "pan,wheel_zoom,box_select,lasso_select,reset"

# test fig is the plot of daily UR ratio by day of the year
test_fig = figure(plot_width=500, plot_height=300)

test_fig.title.text = 'Ratio of Daily UR (Training Set)'
test_fig.xaxis.axis_label = 'Day of Year'
test_fig.yaxis.axis_label = '{} to {} Daily UR Ratio [-]'.format(
    s1.name, s2.name)
test_fig.xaxis.axis_label_text_font_size = '10pt'
test_fig.yaxis.axis_label_text_font_size = '10pt'
test_fig.xaxis.major_label_text_font_size = '10pt'
test_fig.yaxis.major_label_text_font_size = '10pt'

test_fig.scatter('day_of_year', 'ur_ratio', source=train_source, legend="UR Ratio",
                 size=3, color=mypalette[7], alpha=0.4)


equal_ur = dict()
equal_ur['date_norm'] = [1, 365]
equal_ur['ur'] = [1, 1]
equal_ur_source = ColumnDataSource(data=equal_ur)
test_fig.line('date_norm', 'ur', source=equal_ur_source, legend="Equal UR",
              line_dash='dashed', line_color=mypalette[3], line_width=3)

# get all data
# add a 'day of year' column and normalize to be between 1 and 365
all_data['day_of_year'] = all_data.index.dayofyear

# add a column to represent the ratio of runoff in the two catchments
ur_s1 = all_data['daily_ur_{}'.format(s1.name)]
ur_s2 = all_data['daily_ur_{}'.format(s2.name)]

VARS['max_UR'] = max(ur_s1.max(), ur_s2.max())

all_data['ur_ratio'] = ur_s1.divide(ur_s2).astype(float)

# select the proportion (%) of data to use as the validation set
# and the same for the testing set.  The remainder will be the training set

# set up domain for plotting fit curves and other derived line series
N = 500

# train_data is the bulk of data that will be used for model learning
# test_data is for evaluating performance
# val_data is the cross validation set
# for determining the cross validation parameter


def initialize_data_sets():
    p_train = VARS['proportion']['p_train']
    p_test = VARS['proportion']['p_test']
    p_val = VARS['proportion']['p_val']
    # for now, use equal lengths for test and validation sets
    pval, ptest = p_test, p_test

    train_data, test_data, val_data = getRandomChronSets(
        p_train, p_val, p_test, all_data)

    VARS['idx'] = {}
    VARS['idx']['train'] = [train_data.index[0],
                            train_data.index[-1],
                            len(train_data)]
    VARS['idx']['test'] = [test_data.index[0],
                           test_data.index[-1],
                           len(test_data)]
    VARS['idx']['val'] = [val_data.index[0],
                          val_data.index[-1],
                          len(val_data)]

    train_source.data = train_source.from_df(train_data)
    val_source.data = val_source.from_df(val_data)
    test_source.data = test_source.from_df(test_data)

    return train_data, test_data, val_data


def filter_df_by_date(df, ixs):
    mask_df = df[df.index > ixs[0]]
    mask_df = mask_df.iloc[0:int(ixs[2]), :]
    return mask_df


def update_data_sets():
    # p_train = VARS['proportion']['p_train']
    # p_test = VARS['proportion']['p_test']
    # p_val = VARS['proportion']['p_val']
    # # for now, use equal lengths for test and validation sets
    # pval, ptest = p_test, p_test

    train_ixs = VARS['idx']['train']
    test_ixs = VARS['idx']['test']
    val_ixs = VARS['idx']['val']

    train_data = filter_df_by_date(all_data, train_ixs)
    test_data = filter_df_by_date(all_data, test_ixs)
    val_data = filter_df_by_date(all_data, val_ixs)

    train_source.data = train_source.from_df(train_data)
    val_source.data = val_source.from_df(val_data)
    test_source.data = test_source.from_df(test_data)

    return train_data, test_data, val_data


# Initialize the training, test, and validation sets
train_data, test_data, val_data = initialize_data_sets()
initialize_time = time.time() - start_time
print('time to initialize datasets = ', initialize_time)

# =========== Feature Mapping for Polynomial Regression =============
#  Map each example to its powers to investigate
# polynomial regression performance
#
# poly_error is the order of polynomial to test modeling error with


poly_lc_df = pd.DataFrame()

poly_curves_df = pd.DataFrame()
poly_curves_df['x_poly_date'] = np.linspace(1, 365, 500)

poly_x_df = pd.DataFrame()

# ============= Apply Model =====================================
# Apply the polynomial functions to the test data set to
# plot against measured data

# ur ration is defined as s1 / s2 or param1 / param2
# for our test, let's predict s1 as a function of s2
# s1 = Fmodel(day) * s2

hyd_fig_labels = []
hydrograph = figure(plot_width=1200, plot_height=350,
                    tools=TOOLS + ',box_zoom', toolbar_location="above",
                    toolbar_sticky=False, x_axis_type="datetime")


hydrograph.title.text = 'Daily Runoff Measured vs. Predicted (Test Set)'
hydrograph.xaxis.axis_label = 'Date'
hydrograph.yaxis.axis_label = 'Daily Avg. UR [L/s/km^2]'
hydrograph.xaxis.axis_label_text_font_size = '10pt'
hydrograph.yaxis.axis_label_text_font_size = '10pt'
hydrograph.xaxis.major_label_text_font_size = '10pt'
hydrograph.yaxis.major_label_text_font_size = '10pt'

results_df = pd.DataFrame()


def update_poly_order():
    poly_start = time.time()
    try:
        # Select which feature(s) to use in analysis
        features = ['day_of_year', 'ur_ratio']

        # as an example, use s1 to predict s2 (lillooet to predict squamish)
        target = 'daily_ur_{}'.format(s2.name)

        train_data, test_data, val_data = update_data_sets()

        p = VARS['poly_order']

        X_train = train_data.loc[:, features]
        X_test = test_data.loc[:, features]
        X_val = val_data.loc[:, features]

        # m_* = Number of examples in each set
        m_train = len(train_data.index.values)
        m_test = len(test_data.index.values)
        m_val = len(val_data.index.values)

        y_train = train_data.loc[:, target].values.reshape((m_train, 1))
        y_test = test_data.loc[:, target].values.reshape((m_test, 1))
        y_val = val_data.loc[:, target].values.reshape((m_val, 1))

        # initialize theta = 1 for all features
        theta = np.mat(np.ones((len(features) + 1, 1)))

        tolerance = 1e-4

        X_train_adj = np.hstack((np.ones((m_train, 1)), X_train))
        X_val_adj = np.hstack((np.ones((m_val, 1)), X_val))
        # note that we need to make a new dataframe inside this function
        # when calling a dataframe from outside.

        # # Map X onto Polynomial Features and Normalize
        X_ur_train = polyFeatures(X_train, p)
        # X_poly_train = featureNormalize(X_poly_train)
        X_ur_train = np.hstack((np.ones((m_train, 1)), X_ur_train))
        X_ur_val = polyFeatures(X_val, p)
        X_ur_val = np.hstack((np.ones((m_val, 1)), X_ur_val))
        # X_poly_val = featureNormalize(X_poly_val)
        X_ur_test = polyFeatures(X_test, p)
        # X_poly_test = featureNormalize(X_poly_test)
        X_ur_test = np.hstack((np.ones((m_test, 1)), X_ur_test))

        y_ur_test = y_test
        y_ur_val = y_val
        y_ur_train = y_train

        # add polynomial curves for plotting on ur_ratio figure
        current_fit = np.polyfit(
            test_data['day_of_year'], test_data['ur_ratio'], p)[::-1]

        test_data[pred_series_label] = [apply_poly(
            current_fit, day) for day in test_data['day_of_year']]
        test_data[pred_series_label] = test_data[pred_series_label].multiply(
            test_data['daily_ur_{}'.format(s2.name)])

        max_runoff = float(
            (test_data[pred_series_label].max() +
             test_data[target_series_label].max()) / 2
        )

        bf_domain = np.linspace(0, max_runoff, N)

        # regression plot of modeled and measured data
        # get the equation for best fit line
        a1 = np.array(test_data[pred_series_label].astype(float))
        a2 = np.array(test_data[target_series_label].astype(float))

        model_fit = np.polyfit(a1, a2, 1)[:: -1]

        bf_range = [apply_poly(model_fit, e) for e in bf_domain]

        rmse = np.sqrt(np.mean((predictions-targets)**2))

        results_df['bf_domain'] = bf_domain
        results_df['bf_range'] = bf_range

        output_regression_source.data = output_regression_source.from_df(
            results_df)
        model_performance_source.data = model_performance_source.from_df(
            test_data)

        # add polynomial curves for plotting on ur_ratio figure
        current_fit, residuals = np.polyfit(
            train_data['day_of_year'], train_data['ur_ratio'], p, full=True)[::-1]

        r_value = 1 - residuals**2 / len(train_data)

        # plot the polynomial curve over the ur_ratio vs. normalized day scatter plot
        poly_curves_df['y_poly_date'] = [apply_poly(
            current_fit, day) for day in poly_curves_df['x_poly_date']]

        source.data = source.from_df(all_data)
        source_static.data = source_static.from_df(all_data)

        poly_curves_source.data = poly_curves_source.from_df(poly_curves_df)

        results_text.text = "\n\nR^2={:.3f}\n".format(r_value**2)
        results_text.text += "For polynomial order (p={})".format(p)

    except Exception as e:
        print('Blargh!!  Error: {}'.format(e))

    poly_order_init_time = time.time() - poly_start
    print('time to run poly order iteration = ', poly_order_init_time)


pred_series_label = 'predicted_{}'.format(s1.name)
target_series_label = 'daily_ur_{}'.format(s1.name)

surrogate_series_label = 'daily_ur_{}'.format(s2.name)
#
# hydrograph.line('Date', target_series_label, line_width=2,
#                 color=mypalette[8],
#                 legend=pred_series_label, alpha=0.4,
#                 source=source)

surrogate_measured = hydrograph.line('Date', surrogate_series_label, line_width=2,
                                     color=mypalette[6], alpha=0.6, source=source)

predicted_synth = hydrograph.line('Date', pred_series_label, line_width=2,
                                  color=mypalette[2], line_dash='dashed',
                                  source=model_performance_source)

target_measured = hydrograph.line('Date', target_series_label,
                                  source=model_performance_source,
                                  color=mypalette[2])

# add coloured bands to illustrate how the training, test, and validation sets
# are broken down within the whole dataset.
train_band = Band(base='Date', lower=VARS['max_UR'], upper=VARS['max_UR'] + 100,
                  source=train_source, level='underlay',
                  fill_alpha=1, fill_color=mypalette[-1])

val_band = Band(base='Date', lower=VARS['max_UR'], upper=VARS['max_UR'] + 100,
                source=val_source, level='underlay',
                fill_alpha=1, fill_color=mypalette[-3])

test_band = Band(base='Date', lower=VARS['max_UR'], upper=VARS['max_UR'] + 100,
                 source=test_source, level='underlay',
                 fill_alpha=1, fill_color=mypalette[-6])


train_citation = Label(x=950, y=240, x_units='screen', y_units='screen',
                       text='Training Set', render_mode='css', text_font="Helvetica",
                       border_line_color='Black', border_line_alpha=0,
                       background_fill_color=mypalette[-1], background_fill_alpha=0.8)

val_citation = Label(x=950, y=220, x_units='screen', y_units='screen',
                     text='Validation Set', render_mode='css',
                     border_line_color='Black', border_line_alpha=0,
                     background_fill_color=mypalette[-3], background_fill_alpha=0.8)

test_citation = Label(x=950, y=200, x_units='screen', y_units='screen',
                      text='Test Set', render_mode='css',
                      border_line_color='Black', border_line_alpha=0,
                      background_fill_color=mypalette[-6], background_fill_alpha=0.8)


hydrograph.add_layout(train_citation)
hydrograph.add_layout(test_citation)
hydrograph.add_layout(val_citation)
hydrograph.add_layout(train_band)
hydrograph.add_layout(test_band)
hydrograph.add_layout(val_band)


hydrograph_legend = Legend(items=[
    ("Measured {}".format(s2.name), [surrogate_measured]),
    ("Measured_{}".format(s1.name), [target_measured]),
    (pred_series_label, [predicted_synth]),
], location=(0, -30))

hydrograph.add_layout(hydrograph_legend, 'right')


test_fig.line('x_poly_date', 'y_poly_date', source=poly_curves_source,
              legend='polynomial prediction',
              line_color=mypalette[2], line_width=3)

x_label = 'num_examples'
ytrain_label = 'training_error'
yval_error_label = 'val_error'

# Add input for polynomial order
update_poly_order()


def check_proportion(new_val, component):
    old_m_train = int(VARS['idx']['train'][2])
    old_m_val = int(VARS['idx']['val'][2])
    old_m_test = int(VARS['idx']['test'][2])

    if component == 'p_train':
        new_vals = [new_val, old_m_val, old_m_test]
    elif component == 'p_test':
        new_vals = [old_m_train, new_val, new_val]

    if sum(new_vals) <= VARS['len_dataset']:
        VARS['idx']['train'][2] = new_vals[0]
        VARS['idx']['val'][2] = new_vals[1]
        VARS['idx']['test'][2] = new_vals[2]
        update_poly_order()
        return True
    else:
        return False


def update_poly_slider(attrname, old, new):
    VARS['poly_order'] = new
    update_poly_order()


def update_training_set_size(attrname, old, new):
    if not check_proportion(new, 'p_train'):
        training_set_slider.value = old
    else:
        test_set_slider.end = (
            VARS['len_dataset'] - VARS['idx']['train'][2] / 2)


def update_test_set_size(attrname, old, new):
    if not check_proportion(new, 'p_test'):
        test_set_slider.value = old
    else:
        training_set_slider.end = VARS['len_dataset'] - \
            2 * VARS['idx']['test'][2]


poly_order_slider = Slider(title="Polynomial Order",
                           start=1, end=7, step=1, value=1)

poly_order_slider.on_change('value', update_poly_slider)

training_set_slider = Slider(title="Training Set Size [days]",
                             start=365, end=VARS['idx']['train'][2],
                             step=30, value=VARS['idx']['train'][2])

training_set_slider.on_change('value', update_training_set_size)

test_set_slider = Slider(title="Test Set Size [days]",
                         start=10, end=VARS['idx']['test'][2],
                         step=10, value=VARS['idx']['test'][2])

test_set_slider.on_change('value', update_test_set_size)

output_forecast_fig = figure(plot_width=400, plot_height=300)

output_forecast_fig.circle('daily_ur_{}'.format(s1.name),
                           "predicted_{}".format(s1.name),
                           source=model_performance_source, size=3,
                           legend="Daily Avg. UR",
                           color=mypalette[2], selection_color="orange",
                           alpha=0.5, nonselection_alpha=0.01, selection_alpha=0.2)

output_forecast_fig.line('bf_domain', 'bf_range', source=output_regression_source,
                         legend="Best Fit)",
                         color=mypalette[6], line_dash='dashed')

output_forecast_fig.title.text = 'Test Data Set: Measured vs. Predicted'
output_forecast_fig.xaxis.axis_label = 'Measured Daily UR [L/s/km^2])'
output_forecast_fig.yaxis.axis_label = 'Predicted Daily UR [L/s/km^2])'
output_forecast_fig.xaxis.axis_label_text_font_size = '10pt'
output_forecast_fig.yaxis.axis_label_text_font_size = '10pt'
output_forecast_fig.xaxis.major_label_text_font_size = '10pt'
output_forecast_fig.yaxis.major_label_text_font_size = '10pt'

#######################################
# Dataset Breakdown Horizontal Bar Chart
# colors = ["#c9d9d3", "#718dbf", "#e84d60"]
# data_bdown_labels = ['p_train', 'p_val', 'p_test']
# data_breakdown_fig = figure(x_range=['dataset_proportion'],
#                             title="Dataset Breakdown", y_range=(0, 1.6),
#                             toolbar_location=None, tools="",
#                             width=150, height=325)
# bar_plot = data_breakdown_fig.vbar_stack(data_bdown_labels, x='groups',
#                                          color=colors, source=data_breakdown_source,
#                                          legend=data_bdown_labels,
#                                          width=75)
#
# # data_breakdown_fig.x_range.start = 0
# data_breakdown_fig.x_range.range_padding = 0.1
# # p.xgrid.grid_line_color = None
# data_breakdown_fig.axis.minor_tick_line_color = None
# data_breakdown_fig.outline_line_color = None


# polyLearningCurve_fig.add_layout(poly_learning_legend, 'right')
# poly_2 = polyLearningCurve_fig.line(x_label, yval_error_label,
#                                     color=mypalette[9], source=polyLearningCurve_source,
#                                     line_dash='dashed', line_width=3)
#
# poly_learning_labels.append(("Training Error", [poly_1]))
# poly_learning_labels.append(("Cross Validation Error", [poly_2]))

# Lay out the figures for the results document

control_box = column(results_text,
                     widgetbox(poly_order_slider, width=225),
                     widgetbox(training_set_slider, width=225),
                     widgetbox(test_set_slider, width=225),
                     )


row_1 = row(control_box)

layout = column(
    # learningCurve_fig,
    # seasonal_decomp_fig,
    # seasonal_resid_fig,
    row(control_box, output_forecast_fig, test_fig),
    row(hydrograph),
    # polyLearningCurve_fig,
    # row(contour_fig))
)
# row1 = row(all_regression_fig)#logger_series_fig, model_series_fig)#threcs_series_fig)

# row2 = row(gradDescent_fig, learningCurve_fig)
#
# row3 = row(polyLearningCurve_fig, lamLearningCurve_fig)
#
# row4 = row(results_fig)

# layout = column(row1)#, row2, row3, row4)

curdoc().add_root(layout)
curdoc().title = "Time Series Streamflow Regression"
