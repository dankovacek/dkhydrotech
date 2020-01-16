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
                                            relative_urls=False,
                                            session_id=session_id.generate_session_id(),
                                            )
            else:
                # bk_url = 'http://127.0.0.1:5006
                # bk_url = context['base_uri'] + '/bokehproxy' + app_ID
                bk_url = '/bokehproxy' + app_ID
                # bk_script = server_document(url=bk_url, relative_urls=True, 
                #                             resources=None)
                bk_script = server_session(url=bk_url,
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


def sliders_view(request):
    # Define bokeh endpoint url
    # bokeh_server_url = "%sbokehproxy/sliders" % (request.build_absolute_uri(location='/'))
    bokeh_server_url = 'http://127.0.0.1:5006/sliders'
    print('')
    print('')
    print('')
    print(request.build_absolute_uri(location='/'))
    print('')
    print('##############')
    print('')
    # Generate bokeh session token so user can access plot, this is done for all logged in users per the @login_required decorator
    # ensuring only logged in users can view plots

    # Using newer bokeh server_session method vs.  deprecated bokeh.embed.autoload_server
    # Note: session_id.generate_session_id() relies on the presence of BOKEH_SECRET_KEY defined in settings.py via an OS variable
    server_script = server_session(None,
                                   session_id=session_id.generate_session_id(),
                                   url=bokeh_server_url)

    # Tip: More elaborate permission checks can be made using Django's user system, to generate (or not) bokeh session accesss tokens:
    # if user.is_authenticated() and user.has_perm("bokehdash.change_plot"):
    #     server_session(None, session_id=....)
    # else:
    #     HttpResponseRedirect("You can't see this plot")
    # Tip2: More elaborate permissions checks can also be made with other method decorators @user_passes_test, @permission_required
    # (besides @login_reqired)

    # Proceed with context and response
    context = {
               "graphname":"Sliders",
               "bk_script": server_script,
               }
    # return render(request, 'bokehdash/bokeh_server.html', context)
    return render(request, 'dkht/bokeh_post.html', context)