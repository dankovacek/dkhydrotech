from django.shortcuts import render
from django.conf import settings

from django.views.generic import ListView, View, TemplateView

from bokeh.embed import server_document
from bokeh.util import session_id

from . import bk_config

import logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


# Inspired by: https://panel.pyviz.org/user_guide/Django_Apps.html

class DataVizDetail(TemplateView):
    # model = Entry
    template_name = "dkht/bokeh_post.html"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)

        app_ID = '/' + self.kwargs['app_ID']

        try:
            # bk_url = '/bk_sliders_app'

            if settings.DEBUG:
                bk_url = 'http://127.0.0.1:5006' + app_ID
                bk_script = server_document(url=bk_url)
            else:
                bk_url = app_ID
                bk_script = server_document(url=bk_url, relative_urls=True, 
                                            resources=None)

            logging.info('views url = {}'.format(bk_url))
            logging.error('Server document generated...')

            context['bk_script'] = bk_script

        except Exception as e:
            msg = "Uh oh.  Richard, whatja do??: {}".format(e)
            logger.error(msg)

        return context
