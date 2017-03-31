const RCV_DATA = /(.+)((?:\{|\[).+)/

function EventSocket(url) {

    this.ws = new WebSocket(url);
    this.listeners = {};

    var esock = this;

    this.ws.onopen = function() {
        console.log('EventSocket connected to ' + url);
    };

    this.ws.onmessage = function(event) {
        var match = RCV_DATA.exec(event.data);
        var event_name = match[1];
        var encoded_data = match[2];
        if (event_name in esock.listeners) {
            esock.listeners[event_name](JSON.parse(encoded_data));
            console.log('Handling event ' + event_name);
        } else {
            console.log('No listener for event ' + event_name + ', ignoring');
        }
    };

}

EventSocket.prototype.emit = function(event, data) {
    this.ws.send(event + JSON.stringify(data));
};

EventSocket.prototype.on = function(event, listener) {
    this.listeners[event] = listener;
};