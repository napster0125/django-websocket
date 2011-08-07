
import re


class EventError(Exception):
    pass

class Event(object):
    """
    Signal-like object for Socket.IO events that supports
    filtering on channels. Registering event handlers is
    performed by using the Event instance as a decorator::

        @on_message
        def message(request, socket, message):
            ...

    Event handlers can also be registered for particular
    channels using the channel keyword argument with a
    regular expression pattern::

        @on_message(channel="^room-")
        def message(request, socket, message):
            ...

    The ``on_connect`` event cannot be registered with a
    channel pattern since channel subscription occurs
    after a connection is established.
    """

    def __init__(self, supports_channels=True):
        self.supports_channels = supports_channels
        self.handlers = []

    def __call__(self, handler=None, channel=None):
        """
        Decorates the given handler. The event may be called
        with only a channel argument, in which case return a
        decorator with the channel argument bound.
        """
        if handler is None:
            def handler_with_channel(handler):
                return self.__call__(handler, channel)
            return handler_with_channel
        if channel:
            if not self.supports_channels:
                raise EventError("The %s event does not support channels so "
                                 "the handler `%s` could not be registered" %
                                 self.name, handler.__name__)
            channel = re.compile(channel)
        self.handlers.append((handler, channel))

    def send(self, request, socket, *args):
        """
        When an event is sent, run all relevant handlers. Relevant
        handlers are those without a channel pattern when the given
        socket is not subscribed to any particular channel, or the
        handlers with a channel pattern that matches any of the
        channels that the given socket is subscribed to.
        """
        for handler, channel_pattern in self.handlers:
            no_channel = channel_pattern is None and not socket.channels
            matched = [channel_pattern.match(c) for c in socket.channels]
            if no_channel or matched:
                handler(request, socket, *args)

on_connect      = Event(False)  # request, socket
on_message      = Event()       # request, socket, message
on_subscribe    = Event()       # request, socket, channel
on_unsubscribe  = Event()       # request, socket, channel
on_error        = Event()       # request, socket, exception
on_disconnect   = Event()       # request, socket
on_finish       = Event()       # request, socket

# Give each event a name attribute.
for k, v in globals().items():
    if isinstance(k, Event):
        setattr(v, "name", k)
