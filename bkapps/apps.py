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
    if settings.DEBUG:
        bk_port = 5007
        bk_address = '127.0.0.1'
        ws_origin = '127.0.0.1:8000'
        x_headers = False
    else:
        bk_address = bk_config.server['address']
        bk_port = bk_config.server['port']
        ws_origin = 'dkhydrotech.com'
        x_headers = True

    server = Server({'/bk_sliders_app': bk_sliders.app},
                    io_loop=IOLoop(),
                    address='http://www.dkhydrotech.com',
                    port=5007,
                    allow_websocket_origin=[ws_origin],
                    use_xheaders=x_headers
                    )

    logging.error('starting server ...')

    try:
        server.start()
        server.io_loop.start()
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
