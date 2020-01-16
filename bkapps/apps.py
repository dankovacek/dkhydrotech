# based on: https://github.com/bokeh/bokeh/blob/0.12.16/examples/howto/server_embed/flask_embed.py
try:
    import asyncio
except ImportError:
    raise RuntimeError("This example requries Python3 / asyncio")

import os
import sys

from django.apps import AppConfig
from django.conf import settings

from bokeh.server.server import Server, BaseServer
from bokeh.application import Application
from bokeh.application.handlers import FunctionHandler
from bokeh.server.tornado import BokehTornado
from bokeh.server.util import bind_sockets

from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop

# from tornado.ioloop import IOLoop

path = os.path.abspath(os.path.dirname(__file__))
if not path in sys.path:
    sys.path.append(path)

from sliders import bk_sliders
import bk_config

from flood_msmt import msmt_sim_app


# import the logging library
import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)

def bk_worker():
    # Note: num_procs must be 1; see e.g. flask_gunicorn_embed.py for num_procs>1

    bk_address = bk_config.server['address']
    bk_port = bk_config.server['port']
    ws_origin = 'dkhydrotech.com:8000'
    x_headers = True

    logging.error('starting Bokeh server...')
    asyncio.set_event_loop(asyncio.new_event_loop())
    if settings.DEBUG:
        # server = Server({'/bk_sliders_app': bk_sliders.app,
        #                 '/msmt_error_simulation': msmt_sim_app.app},
        #                 io_loop=IOLoop(),
        #                 allow_websocket_origin=['127.0.0.1:8000'],
        #                 num_procs=3
        # )

        bokeh_tornado = BokehTornado({'/bk_sliders_app': bk_sliders.app,
                                      '/msmt_error_simulation': msmt_sim_app.app},
                                      extra_websocket_origins=['127.0.0.1:8000'])
        bokeh_http = HTTPServer(bokeh_tornado)
        bokeh_http.add_sockets(sockets)

        server = BaseServer(IOLoop.current(), bokeh_tornado, bokeh_http)
        server.start()
        server.io_loop.start()
    else:    
        # server = Server({'/bk_sliders_app': bk_sliders.app},
        #                 io_loop=IOLoop(),
        #                 address=bk_config.server['address'],
        #                 port=bk_config.server['port'],
        #                 allow_websocket_origin=["www.dkhydrotech.com"],
        #                 use_xheaders=x_headers
        #                 )
        ws_origins = ['www.dkhydrotech.com', 'dkhydrotech.com']
        # patterns = []
        bokeh_tornado = BokehTornado({'/bk_sliders_app': bk_sliders.app,
                                      '/msmt_error_simulation': msmt_sim_app.app},
                                      prefix='http://127.0.0.1:5006',
                                      extra_patterns='http://127.0.0.1:5006'
                                      extra_websocket_origins=ws_origins,
                                      )

        bokeh_http = HTTPServer(bokeh_tornado)
        bokeh_http.add_sockets(sockets)

        server = BaseServer(IOLoop.current(), 
                            bokeh_tornado, 
                            bokeh_http)
        server.start()
        server.io_loop.start()

        logging.info('######## Server started...            +++++++++++')

    try:
        server.start()
        server.io_loop.start()
        logging.error('Bokeh server started')
    except Exception as e:
        logging.error('Bokeh Server Exception:')
        logging.error(e)

class BokehApps(AppConfig):
    name = 'bkapps'
    def read(self):
        # For development, django provides autoreload, which results
        # in ready() being called twice on startup.  We only want one
        # bokeh server, though. Trying to start a second bokeh server
        # just produces an error that's skipped over (port already in
        # use). Alternatively, using "python manage.py runserver
        # --noreload" avoids the problem. Otherwise, could add some
        # kind of lock...
        # from threading import Thread
        # Thread(target=bk_worker).start()

        # can't use shortcuts here, since we are passing to low level BokehTornado
        # bkapp = Application(FunctionHandler(msmt_sim_app.app))
        bkapp = Application(FunctionHandler(bk_sliders.app))
        

        # This is so that if this app is run using something like "gunicorn -w 4" then
        # each process will listen on its own port
        sockets, port = bind_sockets("127.0.0.1", 0)
        print('#####################')
        print('#####################')
        print('#####################')
        print('#####################')
        print('')
        print(sockets, port)
        print('')
        print('#####################')

        t = Thread(target=bk_worker)
        t.daemon = True
        t.start()

# class Sliders(AppConfig):
#     name = 'bkapps'
#     def ready(self):
#         # For development, django provides autoreload, which results
#         # in ready() being called twice on startup.  We only want one
#         # bokeh server, though. Trying to start a second bokeh server
#         # just produces an error that's skipped over (port already in
#         # use). Alternatively, using "python manage.py runserver
#         # --noreload" avoids the problem. Otherwise, could add some
#         # kind of lock...
#         from threading import Thread
#         Thread(target=bk_worker).start()
