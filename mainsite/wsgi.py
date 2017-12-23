"""
WSGI config for mainsite project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/2.0/howto/deployment/wsgi/
"""

import os
import sys

path = os.path.expanduser('/home/protected/django/')
if path not in sys.path:
    sys.path.append(path)

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mainsite.settings")

from django.contrib.staticfiles.handlers import StaticFilesHandler

application = StaticFilesHandler(get_wsgi_application())
