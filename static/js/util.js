// global $

function websocket_url(path) {
	return 'ws://' + $(location).attr('hostname') + '/' + path
}