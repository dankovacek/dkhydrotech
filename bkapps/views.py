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

class BokehView(TemplateView):
    # model = Entry
    template_name = "dkht/bokeh_post.html"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)
    
        app_ID = self.kwargs['app_ID']

        print(app_ID)
        print(app_ID)
        print(app_ID)
        print(app_ID)
        logging.error('@@@@@@@@@@@ pp id = {}'.format(app_ID))
        
        try:

            if settings.DEBUG:
                bk_url = 'http://127.0.0.1:5006/' + app_ID
                bk_script = server_session(url=bk_url,
                                            relative_urls=False,
                                            session_id=session_id.generate_session_id(),
                                            )
            else:
                # bk_url = 'http://127.0.0.1:5006/bokehproxy' + app_ID
                # bk_url = context['base_uri'] + '/bokehproxy' + app_ID
                # bk_url = app_ID
                # bk_script = server_document(url=bk_url, relative_urls=True, 
                #                             resources=None)
                bk_script = server_session(url='http://127.0.0.1:5006/' + app_ID,
                                           relative_urls=False,
                                           resources=None,
                                           session_id=session_id.generate_session_id(),
                                           )

            context['bk_script'] = bk_script
            logging.info(bk_script)
            logging.info(bk_script)
            logging.info(bk_script)
            logging.info(bk_script)
            logging.info(bk_script)

        except Exception as e:
            msg = "Uh oh.  Richard, whatja do??: {}".format(e)
            logger.error(msg)

        return context

