const RCV_DATA = /([\w]+)([{\[].+)/

function EventSocket(url) {

    this.listeners = {};

    var self = this;

    this.ws = new WebSocket(url);

    this.ws.onopen = function() {
        self.triggerEvent('websocket_connected');
    };

    this.ws.onmessage = function(event) {
        var match = RCV_DATA.exec(event.data);
        var event_name = match[1];
        var encoded_data = match[2];
        self.triggerEvent(event_name, encoded_data);
    };

    this.ws.onerror = function(event) {
        self.triggerEvent('websocket_error');
    };

    this.ws.onclose = function() {
        self.triggerEvent('websocket_closed');
    };

}

EventSocket.prototype.emit = function(event, data) {
    this.ws.send(event + JSON.stringify(data));
};

EventSocket.prototype.on = function(event, listener) {
    this.listeners[event] = listener;
};

EventSocket.prototype.triggerEvent = function(event_name, encoded_data) {
    if (event_name in this.listeners) {
        console.log('Handling event ' + event_name);
        var decoded_data;
        if (encoded_data == undefined) {
            this.listeners[event_name]()
        } else {
            this.listeners[event_name](JSON.parse(encoded_data));
        }
    } else {
        console.log('No listener for event ' + event_name + ', ignoring');
    }
};

function Sequence(event, socket, listeners) {
    this.event = event;
    this.socket = socket;
    this.listeners = listeners;

    this.messages = 0;
    this.sharedData = {};

    this.cbStop = function(data) {console.log('Sequence stopped')};

    var self = this;

    var sendData = function(data) {
        self.socket.emit(self.event, {
            count: self.messages,
            data: data
        });
    }

    var listener = function(data) {
        if (data.data != null) {
            var nextListener = self.listeners[self.messages];
            if (nextListener != undefined) {
                sendData(nextListener(data.data, self.sharedData));
            } else {
                sendData(null);
                self.cbStop();
            }
            self.messages++;
        } else {
            self.cbStop();
        }
    };

    this.begin = function(data) {
        sendData(data);
    };    

    this.register = function() {
        self.socket.on(self.event, listener);
        return self;
    };

    this.on = function(event, callback) {
        if (event == 'stop') {
            self.cbStop = callback;
        }
    };
}