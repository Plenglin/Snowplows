// global $

function websocketUrl(path) {
	return 'ws://' + $(location).attr('host') + '/' + path;
}

function choice(array) {
	return array[Math.floor(Math.random() * array.length)];
}