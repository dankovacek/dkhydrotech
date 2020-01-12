from django import template
from django.utils.safestring import mark_safe

from bokeh.resources import CDN

register = template.Library()


@register.simple_tag()
def bokeh_css():
    return mark_safe(CDN.render_css())


@register.simple_tag()
def bokeh_js():
    return mark_safe(CDN.render_js())
