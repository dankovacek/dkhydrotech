import numpy as np
import pandas as pd
import math
import os
import sys
import time
import utm
from datetime import datetime
from html.parser import HTMLParser
from django.core.mail import send_mail
from django.conf import settings
settings.configure()

from helper_functions import MyHTMLParser
from helper_functions import get_html_string

from bokeh.io import curdoc
from bokeh.layouts import row, column, widgetbox
from bokeh.models import ColumnDataSource, Range1d, LinearAxis, Spacer, Band
from bokeh.models import LassoSelectTool, BoxSelectTool, Legend, LegendItem
from bokeh.models import Label
from bokeh.models.widgets import PreText, Select, Slider
from bokeh.plotting import figure, output_file, show
from bokeh.palettes import Spectral11, Viridis11

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data/')

# all_data = pd.DataFrame()
#
# # for accessing data from dd.weather.gc.ca, filename format is as follows:
# # for SWOB:
# # YYYY-MM-DD-hhmm_XXXX_TYPE_CCz_swob.xml
# # for MeteoCode: example for Whistler region
# # 2018-01-04T13-00-02Z_FPVR50_rv12_TA.csv
#
# # format the filename
# date = datetime.now()
# d = str(date.date())
# t = 'T' + str(date.hour) + '-' + str(date.minute) + '-03Z_'
# station_code = 'FPVR50_rv12_'
# param_code = 'TA'
#
# filename = d + t + station_code + param_code + '.csv'
#
# ec_base_url = 'http://dd.weather.gc.ca/meteocode/pyr/csv/'
#
# html_string = get_html_string(ec_base_url)
#
# myParser = MyHTMLParser()
#
# myParser.feed(html_string)
#
# filenames = myParser.data
#
# # filter filenames for only those on the current date
# filenames = [f for f in filenames if d in f]
#
# frames = []
# x_series_names = []
# temp_series_name = "Air Temp. [Celsius]"
#
# for f in filenames:
#     if d in f:
#         df = pd.read_csv(ec_base_url + f, header=0, parse_dates=[0])
#         cols = df.columns.tolist()
#         transmit_time_start = cols[0].find('TRANSMIT')
#         transmit_time_end = cols[0].find('.xml')
#         # get just the transmission time for the datetime column header
#         transmit_time_str = cols[0][transmit_time_start:transmit_time_end - 1]
#         x_series_names += [transmit_time_str]
#         # use the shortened transmission time for the datetime heade
#         df = df.rename(index=str, columns={
#                        cols[0]: transmit_time_str, cols[1]: temp_series_name})
#         # drop the -9999 invalid number text.  -200 is fine as a filter
#         df = df[df[temp_series_name] > -200]
#         #df.set_index(transmit_time_str, inplace=True)
#         frames += [df]
#
# # set up data sources for bokeh plotting
# sources = []
# for f in filenames:
#     sources += [ColumnDataSource(data=dict())]
#
#
# for i in range(len(sources)):
#     sources[i].data = sources[i].from_df(frames[i])
#
# TOOLS = "pan,wheel_zoom,box_select,lasso_select,reset"
#
# forecast_fig = figure(plot_width=800, plot_height=400,
#                       tools=TOOLS + ',box_zoom', toolbar_location="above",
#                       toolbar_sticky=False, x_axis_type="datetime")
#
# forecast_fig.title.text = 'EC MeteoCast Forecast for {}'.format(
#     station_code[:-1])
# forecast_fig.xaxis.axis_label = 'Date'
# forecast_fig.yaxis.axis_label = 'Temperature [Celsius]'
# forecast_fig.xaxis.axis_label_text_font_size = '10pt'
# forecast_fig.yaxis.axis_label_text_font_size = '10pt'
# forecast_fig.xaxis.major_label_text_font_size = '10pt'
# forecast_fig.yaxis.major_label_text_font_size = '10pt'
#
# i = 0
# n = 0
# palette_n = int((len(Spectral11) - 1) / len(x_series_names))
# for s in x_series_names:
#     forecast_fig.line(s, temp_series_name, source=sources[n], legend=s,
#                       line_dash='dashed', line_color=Spectral11[i], line_width=3)
#     i += palette_n
#     n += 1
#
#
# show(forecast_fig)


try:
    send_mail(
        'Test auto-email',  # subject
        'Here is the message.',
        'dan@dkhydrotech.com',  # from e-mail
        ['dankovacek@gmail.com'],  # to e-mail
        fail_silently=False,
    )
except Exception as e:
    print('')
    print(e)
    print("")
