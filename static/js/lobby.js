// Gamemode 'enum'

const DUEL = 'duel';

const FFA_3 = 'ffa3';
const FFA_6 = 'ffa6';
const FFA_10 = 'ffa10';

const TDM_3 = 'tdm3';
const TDM_5 = 'tdm5';

const CUSTOM = 'custom';

function onButtonClicked(param) {
	var socket = new EventSocket($(location).attr('hostname'));
	socket.emit('joining', {gamemode: param});
}

var socket, sequence;

$(function() {

    socket = new EventSocket('ws://' + $(location).attr('hostname') + '/sockets/matchmaking/fsda');
    socket.on('websocket_connected', function() {

	    sequence = new Sequence('test', socket, [
	    	function(data) {
	    		console.log(data);
	    		return data;
	    	},
	    	function(data) {
	    		console.log(data);
	    		return data;
	    	},
	    	function(data) {
	    		console.log(data);
	    		return data;
	    	},
	    	function(data) {
	    		console.log(data);
	    		return data;
	    	},
	    ]).register();

	});

});