from django.shortcuts import render
from django.conf import settings

from django.views.generic import ListView, View, TemplateView

from bokeh.embed import server_document
from bokeh.util.token import generate_session_id
from bokeh.embed import server_session

from . import bk_config

import logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


# Inspired by: https://panel.pyviz.org/user_guide/Django_Apps.html

class BokehView(TemplateView):
    # model = Entry
    template_name = "dkht/bokeh_post.html"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)

        helper_image = None
    
        app_ID = self.kwargs['app_ID']

        if app_ID == 'flood_msmt':
            header_info = 'Flood Measurement Explorer'
        elif app_ID == 'sliders':
            header_info = 'Bokeh Demo App'
        elif app_ID == 'recognition_heuristic':
            header_info = 'Recognition Heuristic Visualization'
            helper_image = 'static/gigenrenzer_fn.jpg'
        
        try:
            if settings.DEBUG:
                bk_url = 'http://127.0.0.1:5006/' + app_ID
                bk_script = server_session(url=bk_url,
                                            relative_urls=False,
                                            session_id=generate_session_id(),
                                            )
            else:
                bk_script = server_session(url='/bokeh/' + app_ID,
                                           relative_urls=True,
                                           resources=None,
                                           session_id=generate_session_id(),
                                           )

            context['bk_script'] = bk_script
            context['header_info'] = header_info
            context['helper_image'] = helper_image

        except Exception as e:
            msg = "Uh oh.  Richard, whatja do??: {}".format(e)
            logger.error(msg)

        return context

