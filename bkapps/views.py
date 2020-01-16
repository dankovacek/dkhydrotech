from django.shortcuts import render
from django.conf import settings

from django.views.generic import ListView, View, TemplateView

from bokeh.embed import server_document
from bokeh.util import session_id
from bokeh.embed import server_session

from . import bk_config

import logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


# Inspired by: https://panel.pyviz.org/user_guide/Django_Apps.html

class FloodMsmtErrorSimulator(TemplateView):
    # model = Entry
    template_name = "dkht/bokeh_post.html"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        context['base_uri'] = self.request.build_absolute_uri("/").rstrip("/")
        logging.info('$$$$$$$ base uri = {}'.format(context['base_uri']))
        app_ID = '/flood_msmt'

        try:
            # bk_url = '/bk_sliders_app'

            if settings.DEBUG:
                bk_url = 'http://127.0.0.1:5006' + app_ID
                bk_script = server_session(url=bk_url,
                                            session_id=session_id.generate_session_id(),
                                            )
            else:
                # bk_url = 'http://127.0.0.1:5006
                bk_url = context['base_uri'] + '/bokehproxy' + app_ID
                # bk_script = server_document(url=bk_url, relative_urls=True, 
                #                             resources=None)
                bk_script = server_session(url='/bokehproxy/flood_msmt',#bk_url,
                                           relative_urls=True,
                                           resources=None,
                                           session_id=session_id.generate_session_id(),
                                           )

            logging.info('views url = {}'.format(bk_url))
            logging.error('Server document generated...')

            context['bk_script'] = bk_script

        except Exception as e:
            msg = "Uh oh.  Richard, whatja do??: {}".format(e)
            logger.error(msg)

        return context
