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

from helper_functions import color_negative_red, col_shade, set_up_bokeh_ts_figure
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
    allMessages[site] = {}
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

    # retrieve the csv attachment data in the form of a dataframe
    df = get_mail.GetMessageAttachment(service,
                                       newestMessage[site]['msg'],
                                       email,
                                       newestMessage[site]['id'])

    # resample dataframe to 30 minutes for performance
    df = df.resample('30min', on='DateTime').mean()
    df.reset_index(inplace=True)
    siteData[site] = df


#####################################################################
# Add Basic Data Checks for battery level, water level, transmission
#####################################################################

battery_series_name = 'External Supply(AVG) (mV )'
wl_series_name = 'Water Level(RAW) (m)'
low_battery_series_name = 'Low Battery Threshold (V)'

siteFlags = {}

for site in SITES:
    siteFlags[site] = {'battery': False,
                       'water_level': False,
                       'transmission': False}

    # set low battery column in dataframe
    siteData[site][low_battery_series_name] = 12.1

    # convert battery voltage from mV to V
    siteData[site][battery_series_name] = siteData[site][battery_series_name] / 1000.0
    # check for low battery condition and set flag
    siteData[site]['Battery Flag'] = np.where(siteData[site][battery_series_name] < 12.1,
                                              "**Flag -- Low Battery", "")

    try:
        siteFlags[site]['battery'] = float(
            siteData[site][battery_series_name].iloc[-1])
    except ValueError as err:
        print("Last battery voltage reading is not a valid number")
        print(err)
        siteFlags[site]['battery'] = "NaN"

    # check for negative water level
    siteData[site]['WL Flag'] = np.where(siteData[site][wl_series_name] < 0.0,
                                         '**Flag -- Negative Water Level', "")
    # set a flag for negative water level or non-numeric value transmissions
    if siteData[site][wl_series_name].min() < 0:
        siteFlags[site]['water_level'] = siteData[site][wl_series_name].min()
    elif siteData[site][wl_series_name].isnull().values.any():
        siteFlags[site]['water_level'] = '**Bad Stage Data**'
    else:
        try:
            siteFlags[site]['water_level'] = float(
                siteData[site][wl_series_name].iloc[-1])
        except ValueError as err:
            print("Latest WL voltage reading is not a valid number")
            print(err)
            siteFlags[site]['water_level'] = "NaN"

    # check time differential between the last logger entry
    # and the time the email was received
    # print('')
    # print(' Last datetime entry: ')
    latest_logger_entry = siteData[site]['DateTime'].iloc[-1]
    message_received = pd.to_datetime(
        datetime.datetime.fromtimestamp(time.mktime(newestMessage[site]['datetime'])))
    # print('check message time difference from received time')
    # print('latest logger entry  at {} = '.format(site), latest_logger_entry)
    # print('message received from {} at '.format(site), message_received)
    # print(message_received > latest_logger_entry)
    # print('time diff: ')
    # print(message_received - latest_logger_entry)
    time_diff = message_received - latest_logger_entry
    siteFlags[site]['transmission'] = time_diff


#####################################################################
# Initialization for plotting and UI elements
#####################################################################

# wl_figs = {}
# battery_figs = {}
# results_flags_text = {}
site_data_rows = []

for site in SITES:
    # results_flags_text[site] = {}
    # format the a column for site flags
    flag_text_bottom_margin = 10
    if siteFlags[site]['battery'] < 12.1:
        battery_flag_text = Div(text="""<p style="color: 'red'; margin-bottom:{}px;">**Low Battery**: <br>{} (mV)</p>""".format(
            flag_text_bottom_margin,
            siteFlags[site]['battery']),
            width=125, height=25)
    else:
        battery_flag_text = Div(
            text="""<p style="color: #3c763d; margin-bottom:{}px;">Battery OK: <br>{:3.1f} (V)</p>""".format(
                flag_text_bottom_margin,
                siteFlags[site]['battery']))

    if type(siteFlags[site]['water_level']) == 'string':
        wl_flag_text = Div(text="""<p style="color: 'red'; margin-bottom:{}px;">**Check WL**:<br> {} (m)</p>""".format(
            flag_text_bottom_margin,
            siteFlags[site]['water_level']),
            width=125, height=25)
    elif siteFlags[site]['water_level'] < 0:
        wl_flag_text = Div(text="""<p style="color: 'red'; margin-bottom:{}px;">**Check WL**: <br>{}</p>""".format(
            flag_text_bottom_margin,
            siteFlags[site]['water_level']),
            width=100, height=25)
    else:
        wl_flag_text = Div(text="""<p style="color: #3c763d; margin-bottom:{}px">WL OK: <br>{}</p>""".format(
            flag_text_bottom_margin,
            siteFlags[site]['water_level']),
            width=100, height=25)

    # check time elapsed since last reading
    time_diff = siteFlags[site]['transmission']
    time_diff_hours = int(time_diff.seconds / 3600)
    if time_diff.days > 2:
        time_diff_color = '#a94442;'
    else:
        time_diff_color = '#3c763d;'

    reading_text = """<p style="color: {}">{} d {}h <br> since last reading</p>""".format(
        time_diff_color, time_diff.days, time_diff_hours)
    latest_reading_text = Div(text=reading_text, width=125, height=25)

    # Set up figures
    wl_fig = set_up_bokeh_ts_figure(350, 250, 'Water Level [m]')
    # wl_fig.title.text = 'Water Level at {}'.format(site)
    wl_fig.line(siteData[site]['DateTime'], siteData[site][wl_series_name], legend='Stage [m]',
                line_color=Spectral6[0], line_width=2)

    # figure for battery level
    battery_level_fig = set_up_bokeh_ts_figure(
        350, 250, 'Battery Voltage [mV]')
    # battery_level_fig.title.text = 'Battery'
    battery_level_fig.line(siteData[site]['DateTime'], siteData[site][battery_series_name],
                           legend='Battery [V]', line_color=Spectral6[4], line_width=2)
    # add a series corresponding to the line at 12.1 V
    battery_level_fig.line(siteData[site]['DateTime'], siteData[site][low_battery_series_name],
                           legend='Low Batt.', line_color=Spectral6[5], line_width=2,
                           line_dash='dotted')

    # add figure to dedicated figure dicts
    # wl_figs[site] = water_level_fig
    # battery_figs[site] = batt_level_fig
    site_name_text = Div(text="""<h3>{}</h3>""".format(site),
                         width=125, height=25)

    # results_flags_text[site] = column([batt_flag_text, wl_flag_text])
    results_flags_text = column(
        [site_name_text, battery_flag_text, wl_flag_text, latest_reading_text], width=150)
    site_data_rows += [row(results_flags_text,
                           battery_level_fig, wl_fig)]


##########################################
# Layout for Email and PDF Report
##########################################

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

client_name = 'Knight Piesold:'

logo_str = '''<svg src="{}" width="{}" height="{}">'''.format(
    dkht_logo_path, logo_w, logo_h)

logo_img = Div(text=logo_str, width=logo_w, height=logo_h)

logo_text = Div(
    text="""<h4 style="padding: 0 5px 0 5px;">DK Hydrotech</h4>""", width=100, height=25)

report_title = Div(
    text="""<h1>Automated Neon Telemetry Report</h1>""", width=600, height=25)

report_subtitle = Div(
    text="""<h4>{} Station data report for {}</h5>""".format(
        client_name, d),
    width=600, height=60)

# header = row(column(logo_img, logo_text),
#              column(report_title, report_subtitle))
header = row(column(report_title, report_subtitle))

body_text = Div(text="""The above plot represents the output from Unidata's Neon Telemetry Service.
The data are presented as-is, and are not modified or reviewed by the author of this intermediary software.
""", width=850)

footer = Div(
    text="""Automated analysis and reporting by DKHydrotech<br>
    Dan Kovacek, P.Eng.<r>
    dan@dkhydrotech.com | 604-842-0619<br>
    <a href="https://www.dkhydrotech.com">www.dkhydrotech.com</a> """, width=850, height=100)

# inline_table = Div(text=frames[0].style.applymap(
#     color_negative_red, subset=[temp_series_name]).render(), width=700)
# site_info_rows=[]
# for site in SITES:
#     site_info_rows += row(results_flags_text[site],
#                           battery_figs[site], battery_figs[site])

# layout = column(header, forecast_fig, inline_table, body_text, footer)
layout = column(header, column(site_data_rows), body_text, footer)

# show the report in a browser
# show(layout)

# Convert the layout to an html document for sending as email and converting to pdf for document
html = file_html(layout, CDN, "Automated Report from DKHydrotech")

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
<h3>{} Station data report for {}</h3>
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
'''.format(client_name, d, logo_w, logo_h)

# Conver the layout for sending pdf attachment with email
# report_pdf = pdfkit.from_string(html, False)
#
pdfkit.from_string(html, os.path.join(REPORT_DIR, 'report_{}.pdf'.format(d)))
#
# # email parameters: separate multiple recipients by comma
# recipient = 'dan@dkhydrotech.com,tfurst@innergex.com'
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
