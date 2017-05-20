// sprintf

var gamemodes, socket, mmId, state;

const INITIAL = 0;
const FINDING = 1;
const FILLING = 2;


$(function() {

	gamemodes = {};

	$('#gamemodes > button').each(function() {
		var code = $(this).data('code');
		var name = $(this).data('name');
		gamemodes[code] = {code: code, name: name};
	}).click(function() {
		var gm = gamemodes[$(this).data('code')];
		console.log(sprintf('selected gamemode %s', gm.code));
		
		state = INITIAL;
		socket = new WebSocket(websocket_url('socket/matchmaking'));
		socket.onopen = function() {
			socket.send(gm.code);
		};
		socket.onmessage = function(event) {
			switch (state) {
				case INITIAL:
				state = FINDING;
				mmId = event.data;
				console.log(sprintf('assigned id %s', mmId));
				break;
				case FINDING:

				break;
				case FILLING:

				break;
			}
		};
	});

	console.log('found gamemodes: ', gamemodes);

});