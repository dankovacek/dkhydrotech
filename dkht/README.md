# Basic Splash Page for DK Hydro / Tech Site #

## Starting and Restarting Gunicorn and Bokeh Servers

1. If you are incorporating changes to the UI, you may need to run collectstatic:
>`python manage.py collectstatic`

2.  If any database changes occurred:  
>`python manage.py makemigrations`
>`python manage.py migrate`


### Check status of gunicorn

`sudo systemctl status gunicorn`

### Update the Bokeh Server Service and Restart the Bokeh server

# edit the bokeh server service configuration
`sudo nano /etc/systemd/system/bokehserver.service`

# if config changed, reload the daemon
`sudo systemctl daemon-reload`

# check the bokeh server log
`sudo journalctl -u bokehserver`

# restart the bokeh server
`sudo systemctl restart bokehserver`

### Restart the webserver

`sudo systemctl restart gunicorn`

### Reload the Django Daemon

`sudo systemctl daemon-reload`

`sudo nano /etc/nginx/sites-available/mainsite`
