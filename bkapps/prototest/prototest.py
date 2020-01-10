import os
import pandas as pd

from jinja2 import Environment, FileSystemLoader

from bokeh.layouts import column
from bokeh.models import ColumnDataSource, Slider
from bokeh.plotting import figure
from bokeh.server.server import Server
from bokeh.palettes import Spectral4


from bokeh.sampledata.sea_surface_temperature import sea_surface_temperature

server = None

ROOT_DIR = os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(ROOT_DIR, 'plant_data/')


def convert_bin_dict(d):
    return {k: v[0].decode('UTF-8') for (k, v) in d.items()}


def get_data(params):
    '''
    This is a temporary workaround before we build a database connection.
    Otherwise, probably use an API endpoint do call for data to allow for
    filtering, date range selection, etc.
    '''
    print('aasdf;lkasjdf')
    print('aasdf;lkasjdf')
    print('aasdf;lkasjdf')
    print('aasdf;lkasjdf')
    print('aasdf;lkasjdf')
    print('aasdf;lkasjdf')
    params = convert_bin_dict(params)
    filenames = [file for file in os.listdir(
        DATA_DIR) if file.endswith('.csv')]

    select_file = [f for f in filenames if params['facilityId'] in f]

    if len(select_file) == 1:
        f = select_file[0]

    path = os.path.join(DATA_DIR, f)
    df = pd.read_csv(path, parse_dates=[
                     'DateTime'], infer_datetime_format=True)

    all_cols = df.columns.values

    try:
        cols = [e for e in all_cols if params['unitId'] in e]
    except Exception:
        print('{} was not found in cols ({})'.format(params['unitId'], cols))
        return None

    try:
        targets = ['Head', 'Hn']
        head_label = [e for e in cols if any(
            z in e for z in targets)][0]
    except Exception:
        print('{} was not found in cols ({})'.format(
            'Head_Pressure or Hn', cols))
        return None
    try:
        flow_label = [e for e in cols if 'Flow' in e][0]
    except Exception:
        print('{} was not found in cols ({})'.format(
            'Flow', cols))
    try:
        power_label = [e for e in cols if 'MW' in e][0]
    except Exception:
        print('{} was not found in cols ({})'.format(
            'MW', cols))

    all_labels = ['DateTime', head_label, flow_label, power_label]

    df = df[all_labels]

    name_mapper = {flow_label: 'Flow',
                   head_label: 'Head',
                   power_label: 'Power'}

    df.rename(name_mapper, inplace=True, axis='columns')

    return df, params['facilityId'], params['unitId']


def modify_doc(doc):
    df, stn, unitId = get_data(doc.session_context.request.arguments)

    print(df.head())
    print(df.columns.values)

    source = ColumnDataSource(df)

    power_plot = figure(x_axis_type='datetime',
                        title="Unit {} at {}".format(unitId, stn),
                        width=800, height=300)
    power_plot.line('DateTime', 'Power', source=source,
                    color=Spectral4[1], legend='Power [MW]')
    power_plot.line('DateTime', 'Flow', source=source,
                    color=Spectral4[0], legend='Flow [cms]')
    power_plot.line('DateTime', 'Head', source=source,
                    color=Spectral4[3], legend='Head [m WC]')

    def callback(attr, old, new):
        if new == 0:
            data = df
        else:
            data = df.rolling('{0}D'.format(new)).mean()
        source.data = ColumnDataSource(data=data).data

    slider = Slider(start=0, end=30, value=0, step=1,
                    title="Smoothing by N Days")
    slider.on_change('value', callback)

    doc.add_root(column(slider, power_plot))


# The `static/` end point is reserved for Bokeh resources, as specified in
# bokeh.server.urls. In order to make your own end point for static resources,
# add the following to the `extra_patterns` argument, replacing `DIR` with the desired directory.
# (r'/DIR/(.*)', StaticFileHandler, {'path': os.path.normpath(os.path.dirname(__file__) + '/DIR')})

# note the absence of a trailing slash here.
# server = Server({'/prototest': modify_doc}, io_loop=ioloop.IOLoop.instance(), extra_patterns=[('/', IndexHandler)])


def run(ioloop_instance):
    """
    Runs the app
    :param ioloop_instance: an instance of Tornado IOLoop.
    :type ioloop_instance:
    :return:
    :rtype:
    """
    return Server({'/prototest': modify_doc}, io_loop=ioloop_instance)
