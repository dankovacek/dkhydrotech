import numpy as np
import pandas as pd

from bokeh.plotting import figure
from bokeh.models import Band 
from bokeh.models import BoxSelectTool, LassoSelectTool


def create_vhist(peak_source, p):
    # create the vertical histogram
    LINE_ARGS = dict(color="#3A5785", line_color=None)

    data = peak_source.data['PEAK']
    vhist, vedges = np.histogram(data, bins='auto')
    vzeros = np.zeros(len(vedges)-1)
    vmax = max(vhist)*1.1

    pv = figure(toolbar_location=None, plot_width=175, 
                plot_height=p.height, x_range=(0, vmax),
                y_range=p.y_range, min_border=10, 
                y_axis_location="right")
    pv.ygrid.grid_line_color = None
    pv.xaxis.major_label_orientation = np.pi/4
    pv.background_fill_color = "#fafafa"

    pv.quad(left=0, bottom=vedges[:-1], top=vedges[1:], right=vhist, 
            color="blue", alpha=0.25, line_color="#3A5785")
    vh1 = pv.quad(left=0, bottom=vedges[:-1], top=vedges[1:], 
                  right=vzeros, alpha=0.5, **LINE_ARGS)
    vh2 = pv.quad(left=0, bottom=vedges[:-1], top=vedges[1:], 
                  right=vzeros, alpha=0.1, **LINE_ARGS)

    return vedges, vzeros, vh1, vh2, pv


def create_ts_plot(peak_source, peak_sim_source, peak_flagged_source):
    ts_plot = figure(title="Annual Maximum Flood",
                     width=750,
                     height=250,
                     output_backend="webgl",
                     tools='box_select,lasso_select,reset,box_zoom,pan')

    ts_plot.xaxis.axis_label = "Year"
    ts_plot.yaxis.axis_label = "Flow [m³/s]"


    # add the simulated measurement error points
    ts_plot.triangle('YEAR', 'PEAK', source=peak_sim_source, 
                     legend_label='Sim. Msmt. Error', size=3, 
                     color='red', alpha=0.5)

    # add the recorded measurement values
    ts_plot.circle('YEAR', 'PEAK', source=peak_source, legend_label="Measured Data", size=4)
    ts_plot.circle('YEAR', 'PEAK', source=peak_flagged_source, color="orange",
                   legend_label="(QA/QC Flag)", size=4)

    ts_plot.legend.location = "top_left"
    ts_plot.legend.click_policy = 'hide'
    ts_plot.toolbar_location = 'above'
    ts_plot.select(BoxSelectTool).select_every_mousemove = False
    ts_plot.select(LassoSelectTool).select_every_mousemove = False
    return ts_plot


def create_ffa_plot(peak_source, peak_sim_source, peak_flagged_source, 
                    distribution_source, sim_distribution_source):
    # create a plot for the Flood Frequency Values and style its properties
    ffa_plot = figure(title="Flood Frequency Analysis Explorer",
                      x_range=(0.9, 2E2),
                      x_axis_type='log',
                      width=700,
                      height=550,
                      output_backend="webgl",
                      tools="pan,box_zoom,wheel_zoom,reset,lasso_select")

    ffa_plot.xaxis.axis_label = "Return Period (Years)"
    ffa_plot.yaxis.axis_label = "Flow (m³/s)"

    # add the simulated measurement error points
    ffa_plot.triangle('Tr', 'PEAK', source=peak_sim_source, 
                      legend_label='Sim. Msmt. Error', size=3, 
                      color='red', alpha=0.5)

    ffa_plot.circle('Tr', 'PEAK', source=peak_source, legend_label="Measured Data")
    ffa_plot.circle('Tr', 'PEAK', source=peak_flagged_source, color="orange",
                    legend_label="Measured Data (QA/QC Flag)")
    ffa_plot.line('Tr', 'theoretical_quantiles', color='blue',
                  source=distribution_source,
                  legend_label='Log-Pearson3 (Measured Data)')

    ffa_plot.line('Tr', 'mean', color='navy',
                  line_dash='dotted',
                  source=distribution_source,
                  legend_label='Mean Simulation')

    ffa_plot.line('Tr', 'expected_value', color='green',
                  source=distribution_source,
                  legend_label='Expected Value')

    ffa_plot.line('Tr', 'theoretical_quantiles', color='red',
                  line_dash='dotted',
                  source=sim_distribution_source,
                  legend_label='Simulated Error Fit')

    # plot the error bands as shaded areas
    ffa_2_sigma_band = Band(base='Tr', lower='lower_2s_bound', upper='upper_2s_bound', level='underlay',
                            fill_alpha=0.25, fill_color='#1c9099',
                            source=distribution_source)
    ffa_1_sigma_band = Band(base='Tr', lower='lower_1s_bound', upper='upper_1s_bound', level='underlay',
                            fill_alpha=0.65, fill_color='#a6bddb', 
                            source=distribution_source)

    ffa_plot.add_layout(ffa_2_sigma_band)
    ffa_plot.add_layout(ffa_1_sigma_band)

    ffa_plot.legend.location = "top_left"
    ffa_plot.legend.click_policy = "hide"
    ffa_plot.toolbar_location = 'above'

    return ffa_plot


def create_qq_plot(peak_source):
    # min_emp, max_emp = min(peak_source.data['PEAK']), max(peak_source.data['PEAK'])
    # prepare a Q-Q plot
    
    qq_plot = figure(title="Q-Q Plot",
                     width=275,
                     height=275,
                     output_backend="webgl",
                     tools='reset,wheel_zoom,pan',
                     y_axis_location="right")

    qq_plot.xaxis.axis_label = "Empirical Flow [m³/s]"
    qq_plot.yaxis.axis_label = "Theoretical Flow [m³/s]"

    qq_plot.circle('PEAK', 'theoretical_quantiles', source=peak_source)
    qq_plot.line('PEAK', 'PEAK', legend_label='1:1', source=peak_source,
                 line_dash='dashed', color='green')

    qq_plot.legend.location = 'top_left'
    qq_plot.toolbar_location = 'above'
    return qq_plot


def create_pp_plot(peak_source):
    # prepare a P-P plot
    pp_plot = figure(title="P-P Plot",
                     width=275,
                     height=275,
                     output_backend="webgl",
                     tools='reset,wheel_zoom,pan',
                     y_axis_location="right")

    pp_plot.xaxis.axis_label = "Empirical P(x)"
    pp_plot.yaxis.axis_label = "Theoretical P(x)"

    pp_plot.circle('empirical_cdf', 'theoretical_cdf', source=peak_source)
    pp_plot.line((0, 1), (0, 1), legend_label='1:1', 
                 line_dash='dashed', color='green')

    pp_plot.legend.location = 'top_left'
    pp_plot.toolbar_location = 'above'
    return pp_plot
