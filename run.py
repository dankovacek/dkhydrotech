#!/usr/bin/env python3


import sys
import os
import logging
from tornado.options import options, define, parse_command_line
import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.wsgi

from bkapps import bkapp_control

from django.core.wsgi import get_wsgi_application

logger = logging.getLogger(__name__)

define('port', type=int, default=8000)

# if __name__ == "__main__":
#     os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mainsite.settings")
#     try:
#         from django.core.management import execute_from_command_line
#     except ImportError as exc:
#         raise ImportError(
#             "Couldn't import Django. Are you sure it's installed and "
#             "available on your PYTHONPATH environment variable? Did you "
#             "forget to activate a virtual environment?"
#         ) from exc
#     execute_from_command_line(sys.argv)

class HelloHandler(tornado.web.RequestHandler):
    """
    Test endpoint. Issue GET to localhost/hello-tornado to test if it's running.
    """

    def get(self):
        self.write('Hello from tornado')


def main():
    os.environ['DJANGO_SETTINGS_MODULE'] = 'mainsite.settings'
    # sys.path.append('./inemonitoring/inemonitoring') # path to your project if needed

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


    parse_command_line()

    # use the django wsgi application and wire it into a tornado application container.
    wsgi_app = get_wsgi_application()
    container = tornado.wsgi.WSGIContainer(wsgi_app)

    tornado_app = tornado.web.Application(
        [
            ('/hello-tornado/*', HelloHandler),
            ('.*', tornado.web.FallbackHandler, dict(fallback=container)),
        ])

    tornado_http_server = tornado.httpserver.HTTPServer(tornado_app)
    tornado_http_server.listen(options.port)

    # start the bokeh apps.
    bkapp_control.startapps(tornado.ioloop.IOLoop.instance())

    logger.info("Starting Bokeh Test App.")

    tornado.ioloop.IOLoop.instance().start()


if __name__ == '__main__':
    main()