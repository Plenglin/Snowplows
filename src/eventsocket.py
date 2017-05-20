"""
Websockets, but a bit neater. It's greatly based on Socket.io, but only supports websockets. It will have events.
No namespaces or rooms. Those would be handled by the websocket url.

It takes in data in the form of:

event{json}

However, json must be an array or object.

Examples:
    memes{"foo": "bar"}
    #!@c["test", {"is": ["a", 4], "success"}]
Non-examples:
    {"yer": 4}
    [dsa
    asdf"hohoho"
"""
import json
import logging
import re

from tornado import websocket

_logger = logging.getLogger('eventsocket')


class EventSocketRouter:
    """
    Controls all the eventsockets.
    """

    def __init__(self):
        self.listeners = {}
        self.sockets = []
        self._next_sid = 0
        self.on_open = lambda s: _logger.warning('Socket open event undefined, not triggering it')
        self.on_close = lambda s: _logger.warning('Socket close event undefined, not triggering it')

    def __repr__(self):
        return 'EventSocketRouter({})'.format(hash(self))

    def get_socket_by_id(self, id):
        try:
            return self.sockets[id]
        except IndexError:
            return None

    def register_listener(self, event: str, listener: callable):
        """
        Register a listener to listen to an event.
        :param event: the event name. Must be alphanumeric.
        :param listener: the callback called when the event is detected.
        :return: 
        """
        self.listeners[event] = listener

    def register_socket(self, socket):
        self.sockets.append(socket)
        self._next_sid += 1
        return self._next_sid - 1

    def on(self, arg):
        """
        A shorthand for register_listener. It can be used as a function or a decorator. If arg is a string, 
        it registers that as the listener. Without any args, it is a decorator that takes the name of the function 
        and uses that as the event name. Example of usage: 
        
        :Example:
        
        @router.on
        def event():
            ...
        # is equivalent to
        @router.on('event')
        def listener():
            ....
        
        :param arg: a string or function
        
        :return: a decorator function or a regular function depending on input
        """
        if type(arg) == str:  # Take-in-argument mode
            def decorator(func):
                self.register_listener(arg, func)
                return func
            return decorator

        elif callable(arg):  # Decorator mode
            self.register_listener(arg.__name__, arg)
            return arg

        else:
            raise TypeError

    def on_received_message(self, event, data, socket):
        try:
            self.listeners[event](data, socket)
        except KeyError or IndexError:
            _logger.warning('No listener was found for event "%s"', event)

    def broadcast(self, event, data):
        for socket in self.sockets:
            socket.emit(event, data)


class EventSocketHandler(websocket.WebSocketHandler):

    def __repr__(self):
        return 'EventSocketHandler(router={}, id={})'.format(self.router, self.id)

    # noinspection PyMethodOverriding
    def initialize(self, router: EventSocketRouter):
        self.router = router
        self.id = None
        self.url_param = None
        self.count = 0

    def open(self, url_param=''):
        _logger.info('new connection established with url_param: %s', url_param)
        self.add_to_router()
        self.url_param = url_param

    def add_to_router(self):
        self.id = self.router.register_socket(self)
        _logger.info('registered socket #%s', self.id)
        self.router.on_open(self)

    def on_message(self, message):
        _logger.debug('socket #%s recieved message #%s: %s', self.id, self.count, message)
        try:
            match = re.match(r'([\w]+)([{\[].+)', message)  # Ensure that it matches the described format
            event = match.group(1)
            encoded_data = match.group(2)
            data = json.loads(encoded_data)  # Ensure that it's a valid JSON
            self.router.on_received_message(event, data, self)
            _logger.info('socket #%s triggered event "%s" by message #%s', self.id, self.count, event)
        except json.decoder.JSONDecodeError:
            # Do nothing because it's not valid JSON
            _logger.warning('socket #%s dropped message #%s due to improper format: %s', self.id, self.count,
                            message)

        self.count += 1

    def on_close(self):
        self.router.sockets.remove(self)
        self.router.on_close(self)
        _logger.info('Disconnected')

    def emit(self, event: str, data):
        to_send = '{event}{json}'.format(event=event, json=json.dumps(data))
        self.write_message(to_send)


class Sequence:
    """
    A sequence of messages sent back and forth between the server and client. Good for handshakes or any sort of 
    "request" type of communication. 
     
    The messages are sent like this:
    {message: [current message], data: [data being sent, or null for stop message]}
    
    Create a new instance for every new sequence.
    """

    def __init__(self, event_name: str, socket: EventSocketHandler, listeners, shared_data=None):
        """
        Create a new ReceivingSequence. 
        
        :param event_name: The name of the event to be used when sending messages back. 
        
        :param listeners: A list of callables that take in 2 dicts (first contains the raw socket data, second can be 
        modified and shared between each callback) and return a list, dict, or None. If it returns a list or dict, 
        that will be sent and the sequence continues. The sequence stops when a listener returns None or the number 
        of messages exceeds the number of listeners supplied. 
        """
        self.event_name = event_name
        self.socket = socket
        self.listeners = iter(listeners)
        if shared_data is None:
            shared_data = {}
        self.shared_data = shared_data

        self.messages = 0
        self.on_stop = lambda d: _logger.warning('%s stopped, no callback defined.', self)

    def __repr__(self):
        return 'Sequence(event={}, socket={})'.format(self.event_name, self.socket)

    def _listener(self, data, socket):
        if socket == self.socket:
            if data['data'] is not None:
                try:
                    next_listener = next(self.listeners)
                    self._send_data(next_listener(data['data'], self.shared_data))
                except StopIteration:
                    self._send_data(None)
                    self.on_stop(data)
                self.messages += 1
            else:
                self.on_stop(data)

    def register(self):
        """
        Registers this sequence.
        
        :return: itself, for method chaining
        """
        self.socket.router.register_listener(self.event_name, self._listener)
        return self

    def begin(self, data):
        """
        Begin the transmission with a socket if the server is meant to start the sequence. If the client is supposed 
        to begin, do NOT use this method! 
        
        :param data: The initial data to send.
        
        :param socket: The socket to send through.
        
        :return: None
        """
        self._send_data(data)

    def _send_data(self, data):
        self.socket.emit(self.event_name, {'count': self.messages, 'data': data})


if __name__ == '__main__':
    pass
