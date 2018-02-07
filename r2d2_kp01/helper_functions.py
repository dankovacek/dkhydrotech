import os
import numpy as np
import pandas as pd
import math
import os
import sys
import time
import utm
import requests
from html.parser import HTMLParser

from bokeh.plotting import figure


def set_up_bokeh_ts_figure(width, height, y_label):
    TOOLS = "pan,wheel_zoom,box_zoom,box_select,lasso_select,reset"
    fig = figure(plot_width=width, plot_height=height,
                 tools=TOOLS, toolbar_location="above",
                 toolbar_sticky=False, x_axis_type="datetime")

    fig.xaxis.axis_label = 'Date'
    fig.yaxis.axis_label = y_label
    fig.xaxis.axis_label_text_font_size = '10pt'
    fig.yaxis.axis_label_text_font_size = '10pt'
    fig.xaxis.major_label_text_font_size = '10pt'
    fig.yaxis.major_label_text_font_size = '10pt'
    return fig


def load_data(attachment):
    """
    Takes in a message attachment from gmail.
    Returns the data in a pandas dataframe.
    """
    df = pd.DataFrame()
    df = pd.read_csv(attachment)
    return df


def find_newest_message(all_messages):
    """
    Takes in a list of messages
    and returns the most recent message object.
    Message keys correspond to the gmail message payload keys,
    with additional keys for 'id', 'datetime',
    and 'msg' <-- the entire message object
    (needed for retrieving attachment)
    """
    newestMessage = None
    for message in all_messages:
        current_message = {}
        # make a dict object of the massage payload
        for e in message['payload']['headers']:
            current_message[e['name']] = e['value']
        # get the datetime value of the message from string
        datetime_object = time.strptime(
            current_message['Date'], "%a, %d %b %Y %H:%M:%S -0800")
        current_message['datetime'] = datetime_object
        current_message['id'] = message['id']
        current_message['msg'] = message

        if newestMessage:
            # if the newest message has been set, check if
            # the current message is newer and update newest message
            if newestMessage['datetime'] < datetime_object:
                newestMessage = current_message
        else:
            # set the newest message initially
            newestMessage = current_message
    return newestMessage


def color_negative_red(val):
    """
    Takes a scalar and returns a string with
    the css property `'color: red'` for negative
    strings, black otherwise.
    """
    color = 'red' if val < 0 else 'black'
    return 'color: {}'.format(color)


def col_shade(s):
    """
    Takes a scalar and returns a string with
    the css property `'color: red'` for negative
    strings, black otherwise.
    """
    color = 'rgba(0,0,0,0.5)'
    return 'background-color: {}'.format(color)


def load_station_data(filename, DATA_DIR):
    fname = os.path.join(DATA_DIR, filename)
    data = pd.read_csv(fname, header=0)

    data.dropna(inplace=True, subset=['Latitude'])

    data.dropna(inplace=True, subset=['Longitude'])

    data[['Latitude', 'Longitude']] = data[[
        'Latitude', 'Longitude']].astype(float)

    data['dec_deg_latlon'] = data[['Latitude', 'Longitude']].values.tolist()

    # convert decimal degrees to utm and make new columns for UTM Northing and Easting
    data['utm_latlon'] = [utm.from_latlon(
        e[0], e[1]) for e in data['dec_deg_latlon']]

    data['utm_E'] = [e[0] for e in data['utm_latlon']]
    data['utm_N'] = [e[1] for e in data['utm_latlon']]

    return data


def load_flow_data(filename, DATA_DIR):
    fname = os.path.join(DATA_DIR, filename)
    data = pd.read_csv(fname, header=0)
    return data
