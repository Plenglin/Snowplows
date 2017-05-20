// Gamemode 'enum'

const DUEL = 'duel';

const FFA_3 = 'ffa3';
const FFA_6 = 'ffa6';
const FFA_10 = 'ffa10';

const TDM_3 = 'tdm3';
const TDM_5 = 'tdm5';

const CUSTOM = 'custom';

function onButtonClicked(param) {
	sequence.begin({gamemode: param})
}

var socket, sequence, mmId;

$(function() {

    socket = new EventSocket(websocket_path('socket/matchmaking'));
    socket.on('websocket_connected', function() {

	    sequence = new Sequence('test', socket, [
	    	function(data) {
	    		mmId = data.playerId;
	    		console.log('Recieved id: ' + mmId);
	    		return;
	    	},
	    ]).register();

	});

});