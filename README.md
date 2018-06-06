## Get Bokeh server running and embedded in site.

##### To run bokeh server:

Check the shell script to run bokeh server and gunicorn

```
#!/bin/sh
. /home/protected/django/env/bin/activate
exec gunicorn mainsite.wsgi &
exec bokeh serve bk_test/ --address 127.0.0.1 --port 5006 --use-xheaders &
```

#### TODO:

1.