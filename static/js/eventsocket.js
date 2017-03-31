const RCV_DATA = /(.+)((?:\{|\[).+)/

function EventSocket(url) {

    this.listeners = {};

    var esock = this;

    this.ws = new WebSocket(url);

    this.ws.onopen = function() {
        esock.triggerEvent('websocket_connected');
    };

    this.ws.onmessage = function(event) {
        var match = RCV_DATA.exec(event.data);
        var event_name = match[1];
        var encoded_data = match[2];
        esock.triggerEvent(event_name, encoded_data);
    };

    this.ws.onerror = function(event) {
        esock.triggerEvent('websocket_error');
    };

    this.ws.onclose = function() {
        esock.triggerEvent('websocket_closed');
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
        this.listeners[event_name](JSON.parse(encoded_data));
        console.log('Handling event ' + event_name);
    } else {
        console.log('No listener for event ' + event_name + ', ignoring');
    }
};