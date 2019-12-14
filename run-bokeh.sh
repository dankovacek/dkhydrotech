#!/bin/sh
. /home/protected/django/env/bin/activate
cd "$(dirname "$0")"
exec bokeh serve bk_test --allow-websocket-origin=10.2.62.99 --port=80
