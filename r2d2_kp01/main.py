"""
Retrieve latest email from r2d2_data_wrangler@dkhydrotech.com
mail account.  Parse the email attachment, format a report,
send report on set schedule.
Trigger 'notification alarm' report on any flagged condition met.
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
settings.configure()

from helper_functions import color_negative_red, col_shade
from helper_functions import load_data, find_newest_message

from bokeh.io import curdoc
from bokeh.layouts import row, column, widgetbox
from bokeh.models import ColumnDataSource, Range1d, LinearAxis, Spacer, Band
from bokeh.models import LassoSelectTool, BoxSelectTool, Legend, LegendItem
from bokeh.models import Label
from bokeh.models.widgets import PreText, Select, Slider, Div, Paragraph
from bokeh.plotting import figure, output_file, show
from bokeh.palettes import Spectral11, Spectral6, Viridis11
from bokeh.resources import CDN
from bokeh.embed import file_html

import pdfkit

import gmail_api
import get_mail

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data/')
IMG_DIR = os.path.join(BASE_DIR, "images/")
REPORT_DIR = os.path.join(BASE_DIR, "reports/")

# set up service token
service = gmail_api.create_service_instance()

SITES = ['SITE_1', 'SITE_2', 'SITE_3', 'SITE_4']

search_query = '('
# create a search string to retrieve messages for all stations
for site in SITES:
    search_query += site + ' OR '
search_query = search_query[:-4]
search_query += ')'


# retrieve gmail with specific label
email = 'r2d2_data_wrangler@dkhydrotech.com'

allMessages = {}
newestMessage = {}
siteData = {}

#####################################################################
# Retrieve Messages and Load into Separate DataFrames
#####################################################################

# iterate through all sites, and find the newest message for each site
for site in SITES:
    # retrieve all the messages with subject containing a
    # station name listed in our STATION parameter
    allMessages[site]['msg_list'] = get_mail.ListMessagesMatchingQuery(
        service, email, site)

    allMessages[site]['mail_objs'] = []
    # using message IDs from previous msg_list query
    # retrieve the associated message objects
    for msg in allMessages[site]['msg_list']:
        allMessages[site]['mail_objs'] += [
            get_mail.GetMessage(service, email, msg['id'])]

    # find and store only the latest message for each site
    newestMessage[site] = find_newest_message(allMessages[site]['mail_objs'])

    print('newest message found: ')
    print(newestMessage[site])

    # retrieve the csv attachment data in the form of a dataframe
    siteData[site] = get_mail.GetMessageAttachment(service,
                                                   newest_message['msg'],
                                                   email,
                                                   newest_message['id'])


#####################################################################
# Basic Data Checks for battery level, water level, last transmission
#####################################################################

battery_series_name = 'External Supply(AVG) (mV )'
wl_series_name = 'Water Level(RAW) (m)'

# as well as negative water level values
for site in SITES:
    # check for low battery condition
    siteData[site]['Batt. Flag'] = np.where(siteData[site][battery_series_name] < 12100,
                                            "**Flag -- Low Battery", "")

    siteData[site]['W.L. Flag'] = np.where(siteData[site][wl_series_name] < 0.0,
                                           '**Flag -- Negative Water Level', "")

# check time differential between the last logger entry
# and the time the email was received
print('')
print(' Last datetime entry: ')
latest_logger_entry = df['DateTime'].iloc[-1]
message_received = pd.to_datetime(
    datetime.datetime.fromtimestamp(time.mktime(newest_message['datetime'])))
print('check message time difference from received time')
print('latest logger entry = ', latest_logger_entry)
print('message received', message_received)
print(message_received > latest_logger_entry)

# check for last data transmission

# for f in filenames:
#     if d in f:
#         df = pd.read_csv(ec_base_url + f, header=0, parse_dates=[0])
#         cols = df.columns.tolist()
#         transmit_time_start = cols[0].find('TRANSMIT') + len('TRANSMIT.')
#         transmit_time_end = cols[0].find('.xml')
#         header_line = re.split("[, \-!?:;|]+", cols[0])
#         # cols[0].split('|')[0].strip()
#         station_name_en = header_line[0].strip()
#         station_name_fr = header_line[1].strip()
#
#         # get just the transmission time for the datetime column header
#         transmit_time_str = cols[0][transmit_time_start:transmit_time_end - 1]
#         x_series_names += [transmit_time_str]
#         # use the shortened transmission time for the datetime header
#         df = df.rename(index=str, columns={
#                        cols[0]: transmit_time_str, cols[1]: temp_series_name})
#         # drop the -9999 invalid number text.  -200 is fine as a filter
#         df = df[df[temp_series_name] > -200]
#         df = df[df[transmit_time_str] < date + datetime.timedelta(days=3)]
#         df['Flag'] = np.where(df[temp_series_name] < 0,
#                               "**Flag -- Low Air Temp", "")
#         # df.set_index(transmit_time_str, inplace=True)
#         frames += [df]
#
# # initialize data sources for bokeh plotting
# sources = []
# for f in filenames:
#     sources += [ColumnDataSource(data=dict())]
#
# # update plotting sources with retrieved data
# for i in range(len(sources)):
#     sources[i].data = sources[i].from_df(frames[i])
#

source = ColumnDataSource(data=dict())
source.data = source.from_df(df)
wl_series_title =
TOOLS = "pan,wheel_zoom,box_select,lasso_select,reset"

water_level_fig = figure(plot_width=700, plot_height=400,
                         tools=TOOLS + ',box_zoom', toolbar_location="above",
                         toolbar_sticky=False, x_axis_type="datetime")

water_level_fig.title.text = 'Water Level'
water_level_fig.xaxis.axis_label = 'Date'
water_level_fig.yaxis.axis_label = 'Water Level [m]'
water_level_fig.xaxis.axis_label_text_font_size = '10pt'
water_level_fig.yaxis.axis_label_text_font_size = '10pt'
water_level_fig.xaxis.major_label_text_font_size = '10pt'
water_level_fig.yaxis.major_label_text_font_size = '10pt'
water_level_fig.line('DateTime', wl_series_title, source=source, legend=site_name,
                     line_color=Spectral6[1], line_width=2)

battery_level_fig = figure(plot_width=700, plot_height=400,
                           tools=TOOLS + ',box_zoom', toolbar_location="above",
                           toolbar_sticky=False, x_axis_type="datetime")

battery_level_fig.title.text = 'Battery'
battery_level_fig.xaxis.axis_label = 'Date'
battery_level_fig.yaxis.axis_label = 'Battery Voltage [mV]'
battery_level_fig.xaxis.axis_label_text_font_size = '10pt'
battery_level_fig.yaxis.axis_label_text_font_size = '10pt'
battery_level_fig.xaxis.major_label_text_font_size = '10pt'
battery_level_fig.yaxis.major_label_text_font_size = '10pt'
battery_level_fig.line('DateTime', battery_series_name, source=source, legend=site_name,
                       line_color=Spectral6[4], line_width=2)

# i = 0
# n = 0
# palette_n = int((len(Spectral11) - 1) / len(x_series_names))
# for s in x_series_names:
#     forecast_fig.line(s, temp_series_name, source=sources[n], legend=s,
#                       line_dash='dashed', line_color=Spectral11[i], line_width=3)
#     i += palette_n
#     n += 1

##############
# Data and Layout for Report
##############

# format the filename
date = datetime.datetime.now()
d = str(date.date())
t = 'T' + str(date.hour) + '-' + str(date.minute) + '-03Z_'

# dkht logo parameters
dkht_logo_path = os.path.join(IMG_DIR, "dkhydrotech_green.jpg")

# with open(dkht_logo_path) as svg_file:
#     data = svg_file.read()
#     encoded_string = base64.b64encode(data.encode('utf-8'))
#     b64 = encoded_string.decode('utf-8')

logo_h = 83
logo_w = 80

# logo_str = '''<img src="data:image/svg+xml;base64,'''.format(
#     dkht_logo_path) + b64 + '''" />'''
# logo_str += '''" width={} height={} style="padding: 0 5px 0 5px;">'''.format(
# logo_w, logo_h)

logo_str = '''<svg src="{}" width="{}" height="{}">'''.format(
    dkht_logo_path, logo_w, logo_h)

logo_img = Div(text=logo_str, width=logo_w, height=logo_h)

logo_text = Div(
    text="""<h4 style="padding: 0 5px 0 5px;">DK Hydrotech</h4>""", width=100, height=25)

report_title = Div(
    text="""<h1>Automated Neon Telemetry Report</h1>""", width=600, height=25)

report_subtitle = Div(
    text="""<h4>Air temperature forecast for {} at {}</h5>""".format(
        d, site_name),
    width=600, height=60)

# header = row(column(logo_img, logo_text),
#              column(report_title, report_subtitle))
header = row(column(report_title, report_subtitle))

body_text = Div(text="""The above plot represents the output from Unidata's Neon Telemetry Service.
The data are presented as-is, and are not modified or reviewed by the author of this intermediary software.
""", width=700)

footer = Div(
    text="""Automated analysis and reporting by DKHydrotech<br>
    Dan Kovacek, P.Eng.<r>
    dan@dkhydrotech.com | 604-842-0619<br>
    <a href="https://www.dkhydrotech.com">www.dkhydrotech.com</a> """, width=700, height=100)

# inline_table = Div(text=frames[0].style.applymap(
#     color_negative_red, subset=[temp_series_name]).render(), width=700)

# layout = column(header, forecast_fig, inline_table, body_text, footer)
layout = column(header, water_level_fig, battery_level_fig, body_text, footer)

# show the report in a browser
show(layout)

# Convert the layout to an html document for sending as email and converting to pdf for document
# html = file_html(layout, CDN, "Automated Report from DKHydrotech")

#
# # only include the first table in the frame
# frame = frames[0]
#
# frame = (
#     frame.style.applymap(color_negative_red, subset=[
#         temp_series_name]).render()
# )
# # remove borders from auto-generated table html
# table_html += frame
# table_html += '<br><br>'


email_html = '''
<h1>Automated Station Summary Report</h1>
<h3>Air temperature forecast for {} at {}</h3>
\n
{}
\n\n
<p style="width: 600px;">The above table summarizes the official forecast values issued by Environment
and Climate Change Canada. The data presented in this report are retrieved from the
<a href="http://dd.weather.gc.ca/about_dd_apropos.txt">http://dd.weather.gc.ca/about_dd_apropos.txt</a> (MSC HTTP Data Server -- meteocode).
The data are presented as-is, and are not modified or reviewed by the author of this intermediary software.
</p>
\n\n
<table>
<thead></thead>
<tbody>
<tr>
    <td>
        <img src="cid:img_logo" width="{}" height="{}">
        <h5 style="padding: 0 0 0 5px; margin: 0;">DK Hydrotech</h5>
    <td>
    <td>
        <p>Automated analysis and reporting by DKHydrotech<br>
        Dan Kovacek, P.Eng. <br>
        <a href="https://www.dkhydrotech.com">www.dkhydrotech.com</a><br>
        dan@dkhydrotech.com | 604-842-0619</p>
    </td>
</tr>
'''.format(d, site_name, table_html, logo_w, logo_h)

# Conver the layout for sending pdf attachment with email
# report_pdf = pdfkit.from_string(html, False)
#
# # pdfkit.from_string(html, os.path.join(REPORT_DIR, 'report_{}'.format(d)))
#
# # email parameters: separate multiple recipients by comma
# recipient = 'dan@dkhydrotech.com'
# subject = "Automated Neon Telemetry Report from DKHydrotech"
# message_text_html = email_html
# message_text_plain = "Images cannot be displayed in email body, please refer to the attached pdf for the 72 hour forecast report for {} at {}.".format(
#     d, station_name_en)
# attached_file = report_pdf
#
# f_name = 'NEON_Telemetry_Report_{}'.format(d)

# send the report!
# gmail_api.send_email_report(
#     recipient, subject, message_text_plain, message_text_html, attached_file, f_name, dkht_logo_path)
