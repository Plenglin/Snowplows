const SUBDIRECTORY = 'eventsockets'
const DEFAULT_NAMESPACE = '/'
const RCV_DATA = /(.+)((?:\{|\[).+)/

function EventSocket(namespace) {

    ws = new WebSocket('ws://' + location.href.split( '/' )[2] + '/' + SUBDIRECTORY);
    this.ws = ws;
    this.namespace = namespace == null ? DEFAULT_NAMESPACE : namespace;
    this.listeners = {};

    var namespace = this.namespace;

    ws.onopen = function() {
        ws.send(namespace);  // Tell the server our namespace
        console.log(namespace);
    };

    ws.onmessage = function(event) {
        var match = RCV_DATA.exec(event.data);
        var event_name = match[1];
        var encoded_data = match[2];
        try {
            this.listeners[event_name](JSON.parse(encoded_data));
            console.log('Recieved ' + event_name);
        } catch(error) {
            console.log('Invalid event, pretending nothing happened');
        }
    };

    this.emit = function(event, data) {
        ws.send(event + JSON.stringify(data));
    };

    this.on = function(event, listener) {
        this.listeners[event] = listener;
    };

}