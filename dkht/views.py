from django.shortcuts import render, get_object_or_404, get_list_or_404
from django.views.generic.edit import FormView, UpdateView, CreateView, DeleteView
from django.views.generic import ListView, View, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.detail import DetailView, SingleObjectMixin
from .models import Entry, StationSearchTarget, ClimateStation, Donation
from .forms import EntryForm, ClimateScrapeForm
from django.urls import reverse_lazy, reverse
from django.conf import settings
from django.http import JsonResponse, HttpResponse, HttpResponseRedirect
from django.utils import timezone
from django.db import transaction
from django.forms.models import inlineformset_factory

from io import StringIO

from bokeh.embed import server_session
from bokeh.util import session_id

from climatescrape import station_search


import logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class Main(TemplateView):
    """
    View for default landing page.
    """
    template_name = 'dkht/frontpage.html'


class Contact(TemplateView):
    """
    View for default landing page.
    """
    template_name = 'dkht/contact.html'


class PaymentSuccess(TemplateView):
    """
    View for successful payment.
    """
    model = Donation
    template_name = 'dkht/payment-success.html'

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        print('transaction object pk = ', self.kwargs['pk'])
        context['donation'] = get_object_or_404(
            Donation, charge_id=self.kwargs['pk'])
        return context


class EntryList(ListView):
    """
    View for Project Entries (Work Portfolio List view)
    """
    model = Entry

    # def get_context_data(self, *args, **kwargs):
    #     context = super()

    def get_queryset(self):
        qs = super().get_queryset()
        qs = Entry.objects.order_by('-created')
        return qs


class EntryCreate(LoginRequiredMixin, CreateView):
    """
    Will need to change implementation of stations once
    organization and user are incorporated.
    """
    model = Entry
    fields = ['post_type', 'title', 'byline',
              'text_body', 'image', 'tags', 'video']

    def get_context_data(self, *args, **kwargs):
        context = super(EntryCreate, self).get_context_data(**kwargs)
        return context

    def get_success_url(self, **kwargs):
        return reverse_lazy('dkht:entry-list')

    def form_valid(self, form):
        # form.save(commit=True)
        return super(EntryCreate, self).form_valid(form)


class EntryDetail(DetailView):
    model = Entry

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        context['entry'] = get_object_or_404(Entry, id=self.kwargs['pk'])
        return context


class EntryUpdate(LoginRequiredMixin, UpdateView):
    """
    Will need to change implementation of stations once
    organization and user are incorporated.
    """
    model = Entry
    fields = ['post_type', 'title', 'byline',
              'text_body', 'image', 'tags', 'video']

    def get_context_data(self, *args, **kwargs):
        context = super(EntryUpdate, self).get_context_data(**kwargs)
        context['entry'] = get_object_or_404(Entry, id=self.kwargs['pk'])
        return context

    def get_success_url(self, **kwargs):
        return reverse_lazy('dkht:entry-detail', kwargs={
            'pk': self.kwargs['pk'],
        })


class EntryDelete(LoginRequiredMixin, DeleteView):
    """
    Will need to change implementation of stations once
    organization and user are incorporated.
    """
    model = Entry

    def get_success_url(self, *args, **kwargs):
        return reverse_lazy('dkht:entry-list')


class TagList(ListView):
    """
    Possibly redundant view.
    """
    model = Entry

    # def get_context_data(self, *args, **kwargs):
    #     context = super()

    def get_queryset(self):
        qs = super().get_queryset()
        # if self.request.user
        tag = self.kwargs['pk']
        qs = Entry.objects.filter(tags__contains=tag).order_by('created')
        return qs


class ClimateScrapeCreate(CreateView):
    model = StationSearchTarget
    template_name = "dkht/climatescrape_form.html"
    fields = ['lat', 'lon', 'search_radius']

    def get_context_data(self, *args, **kwargs):
        context = super(ClimateScrapeCreate, self).get_context_data(**kwargs)
        context['stripe_key'] = settings.STRIPE_PUBLIC_KEY
        return context

    def get_success_url(self, **kwargs):
        return reverse_lazy('dkht:climate-scrape-results', kwargs={'pk': self.object.id, })

    def form_valid(self, form):
        return super(ClimateScrapeCreate, self).form_valid(form)


class ClimateScrapeResults(DetailView):
    model = StationSearchTarget
    template_name = "dkht/climatescrape_list.html"
    fields = ['lat', 'lon', 'search_radius']

    def get_context_data(self, *args, **kwargs):
        context = super(ClimateScrapeResults, self).get_context_data(**kwargs)
        target = get_object_or_404(
            StationSearchTarget, id=self.kwargs['pk'])

        results = station_search.get_stations(
            target.lat, target.lon, target.search_radius)

        # now convert the output stations to a context object
        # that can be used in the templateview
        stations = []
        if len(results) > 0:
            for station in results:
                st = ClimateStation(**station)
                stations += [st]
            context['stations'] = stations
        else:
            context['stations'] = None

        context['stripe_key'] = settings.STRIPE_PUBLIC_KEY

        return context

    def get_success_url(self, **kwargs):
        return reverse_lazy('dkht:climate-scrape-results', kwargs={'pk': self.object.id, })

    def form_valid(self, form):
        # form.save(commit=True)

        return super(ClimateScrapeResults, self).form_valid(form)


def ClimateScrapeExport(request, station_ID, start_year, end_year):
    # def get(self, request), station_ID, start_year, end_year):
    # stn_id = request.GET.get('station_ID')
    # start_year = request.GET.get('start_year')
    # end_year = request.GET.get('end_year')
    # Create the HttpResponse object with the appropriate CSV header.

    data, filename = station_search.make_dataframe(
        station_ID, start_year, end_year)

    buff = StringIO()

    output = data.to_csv(buff, index=None)

    buff.seek(0)

    response = HttpResponse(buff, content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename={}'.format(
        filename)

    return response


class DataVizDetail(TemplateView):
    model = Entry
    template_name = "dkht/bokeh_post.html"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        data_viz_id = context['viz_url']
        dataviz_url = self.request.build_absolute_uri(
            location='/') + context['viz_url']
        print('')
        print('dataviz url = ', dataviz_url)
        print('')
        try:
            bk_script = server_session(
                None, session_id=session_id.generate_session_id(), url=dataviz_url)
            context['bk_script'] = bk_script
        except Exception as e:
            msg = "Uh oh.  Richard, whatja do??: {}".format(e)
            logger.error(msg)

        return context
