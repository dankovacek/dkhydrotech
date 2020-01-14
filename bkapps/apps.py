# based on: https://github.com/bokeh/bokeh/blob/0.12.16/examples/howto/server_embed/flask_embed.py

from django.apps import AppConfig
from django.conf import settings

from bokeh.server.server import Server

from tornado.ioloop import IOLoop

from . import bk_sliders
from . import bk_config

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
    if settings.DEBUG:
        server = Server({'/bk_sliders_app': bk_sliders.app},
                        io_loop=IOLoop(),
                        allow_websocket_origin=['127.0.0.1:8000']
        )
    else:    
        server = Server({'/bk_sliders_app': bk_sliders.app},
                        io_loop=IOLoop(),
                        address=bk_config.server['address'],
                        port=bk_config.server['port'],
                        allow_websocket_origin=["www.dkhydrotech.com"],
                        use_xheaders=x_headers
                        )

    logging.info('starting server ...')

    try:
        server.start()
        server.io_loop.start()
        logging.error('Bokeh server started')
    except Exception as e:
        logging.error('Bokeh Server Exception:')
        logging.error(e)

class Sliders(AppConfig):
    name = 'bkapps'
    def ready(self):
        # For development, django provides autoreload, which results
        # in ready() being called twice on startup.  We only want one
        # bokeh server, though. Trying to start a second bokeh server
        # just produces an error that's skipped over (port already in
        # use). Alternatively, using "python manage.py runserver
        # --noreload" avoids the problem. Otherwise, could add some
        # kind of lock...
        from threading import Thread
        Thread(target=bk_worker).start()
