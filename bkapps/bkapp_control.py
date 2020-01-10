from .prototest import prototest

apps = [
    prototest
]

servers = []

def startapps(ioloop_instance):
    """
    Starts all apps listed above.
    The assumption is made that every app has a "run" function that accepts an IO loop, make sure you add one.
    :param ioloop_instance:
    :type ioloop_instance:
    :return:
    :rtype:
    """
    for app in apps:
        servers.append(app.run(ioloop_instance))


def stopapps():
    """
    This is probably unnecessary, but it looks nice.
    :return:
    :rtype:
    """
    for server in servers:
        server.stop()
