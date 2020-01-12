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

        try:

            if settings.DEBUG:
                bk_url = 'http://127.0.0.1:5007/bk_sliders_app'
            else:
                bk_url = 'http://{}:{}/bk_sliders_app'.format(bk_config.server['address'],
                                                                        bk_config.server['port'])

            bk_script = server_document(url=bk_url)

            print(bk_script)
            print('##')
            print('')
            context['bk_script'] = bk_script

        except Exception as e:
            msg = "Uh oh.  Richard, whatja do??: {}".format(e)
            logger.error(msg)

        return context
