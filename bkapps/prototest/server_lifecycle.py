import logging
logger = logging.getLogger(__name__)

def on_server_loaded(server_context):
    ''' If present, this function is called when the server first starts. '''
    logger.debug("Bokeh server started")


def on_server_unloaded(server_context):
    ''' If present, this function is called when the server shuts down. '''
    logger.debug("Bokeh server shutdown")

def on_session_created(session_context):
    ''' If present, this function is called when a session is created. '''
    logger.debug("Bokeh server session created")

def on_session_destroyed(session_context):
    ''' If present, this function is called when a session is closed. '''
    logger.debug("Bokeh server session closed")