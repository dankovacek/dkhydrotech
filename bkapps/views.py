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

        sec_key = settings.BOKEH_SECRET_KEY
        s_id = session_id.generate_session_id(sec_key)
        
        try:
            print('')
            print('made it into pull session!')
            bk_script = server_document(url='https://{}:{}/bk_sliders_app'.format(bk_config.server['address'],
                                                                        bk_config.server['port']),
                                                                        session_id=s_id)
            # bk_script = server_session(url=dataviz_url, session_id=generate_session_id())
            print(bk_script)
            print('##')
            print('')
            context['bk_script'] = bk_script

        except Exception as e:
            msg = "Uh oh.  Richard, whatja do??: {}".format(e)
            logger.error(msg)

        return context
