# Runs a Tornado web server with a django project
# Make sure to edit the DJANGO_SETTINGS_MODULE to point to your settings.py
#
# http://localhost:8080/hello-tornado
# http://localhost:8080/    # for index.html which runs the VueJS App
# http://localhost:5006/    # for bokeh

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


class HelloHandler(tornado.web.RequestHandler):
    """
    Test endpoint. Issue GET to localhost/hello-tornado to test if it's running.
    """

    def get(self):
        self.write('Hello from tornado')


def main():
    os.environ['DJANGO_SETTINGS_MODULE'] = 'inemonitoring.settings'
    # sys.path.append('./mainsite/') # path to your project if needed

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

    logger.info("Starting INE Performance Monitor.")

    tornado.ioloop.IOLoop.instance().start()


if __name__ == '__main__':
    main()
