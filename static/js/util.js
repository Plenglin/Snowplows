// global $

function websocket_url(path) {
	return 'ws://' + $(location).attr('host') + '/' + path
}