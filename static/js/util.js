// global $

function websocketUrl(path) {
	return 'ws://' + $(location).attr('host') + '/' + path
}