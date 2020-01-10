from django.shortcuts import render

from django.views.generic import ListView, View, TemplateView

from bokeh.embed import server_document

from . import bk_config

def sliders(request):
    print('')
    print('')
    print('hahahahahah')
    print('')
    print('')
    return render(request, 'base.html', {
        "server_script": server_document('http://%s:%s/bk_sliders_app'%(bk_config.server['address'],
                                                                        bk_config.server['port']))})



class DataVizDetail(TemplateView):
    # model = Entry
    template_name = "dkht/bokeh_post.html"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        # dataviz_url = 'https://www.dkhydrotech.com/' + context['viz_url']
        # dataviz_url = 'wss://dkhydrotech.com:5000/bokeh/' + context['viz_url']

        # sec_key = settings.BOKEH_SECRET_KEY
        # session_id = session_id.generate_session_id(sec_key)
        
        try:
            print('')
            print('made it into pull session!')
            bk_script = server_document('http://%s:%s/bk_sliders_app'%(bk_config.server['address'],
                                                                        bk_config.server['port']))
            # bk_script = server_session(url=dataviz_url, session_id=generate_session_id())
            print(bk_script)
            print('')
            print('')
            context['bk_script'] = bk_script

        except Exception as e:
            msg = "Uh oh.  Richard, whatja do??: {}".format(e)
            logger.error(msg)

        return context
