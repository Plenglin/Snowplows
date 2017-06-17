var drawingCanvas, bufferCanvas, ctx, bctx;

const OPENING = 0;
const GAME = 1;
const CLOSING = 2;

const ENEMY_COLORS = ['blueviolet', 'crimson', 'darkcyan', 'darkgreen', 'darkorange', 'darkorchid', 'firebrick', 'saddlebrown', 'salmon', 'thistle', 'teal'];
const FRIENDLY_COLOR = 'cornflowerblue';
const DEAD_COLOR = 'black';

function ServerData(input) {
	this.players = [];
	for (var i=0; i < input.teams.length; i++) {
		this.players = this.players.concat(t.players);
	}
}

var game = {
	socket: null,
	socketstate: null,
	playerId: '',
	playerTeamId: '',
	teams: {}
};

$(function() {
	/*
	drawingCanvas = $('#gameCanvas')[0];
	ctx = drawingCanvas.getContext('2d');

	drawingCanvas.width = $(window).width();
	drawingCanvas.height = $(window).height();

	bufferCanvas = $('#bufferCanvas')[0];
	bctx = bufferCanvas.getContext('2d');
	img = new Image();
	img.onload = function() {
		drawImgWithTint(this, '#FF0000', 1, 0, 0);
	}
	img.src = '/static/img/truckBase.svg';
	*/
	game.socket = new WebSocket(websocketUrl($('head').data('socket-url')));
	game.socket.onopen = function() {
    	game.socketstate = OPENING;
    	var token = $('head').data('token');
    	console.log('sending token', token);
		game.socket.send(JSON.stringify({
			token: token
		}));  // send our token
	};
	game.socket.onmessage = function(event) {

		var data = JSON.parse(event.data);
		console.log('RECEIVED:', data);

		switch (game.socketstate) {
		case OPENING:
			if (data.valid) {
			    console.log('token acknowledged, decoding data');

			    game.playerId = data.id;
			    game.playerTeamId = data.playerTeamId;

			    console.log('player id is', game.playerId);
			    console.log('player is on team', game.playerTeamId);

			    console.log('assigning colors to the teams...');
			    for (var i = data.teamIds.length - 1; i >= 0; i--) {
			    	var id = data.teamIds[i];
			    	var color = id == game.playerTeamId ? FRIENDLY_COLOR : choice(ENEMY_COLORS);
			    	game.teams[id] = color;
			    	console.log('assigned', color, 'to', id);
			    }

			    game.socketstate = GAME;
			} else {
				console.log('token not acknowledged, closing socket');
				socket.close();
			}
			break;
		case GAME:

			break;

		case CLOSING:
			break;

		default:
			console.log('state machine derped pls fix');
			break;
		}
	};

});

function drawPlayer(argument) {
	// body...
}

function drawImgWithTint(img, tint, alpha, x, y, w, h) {
	if (w == undefined) {
		w = img.width;
	}
	if (h == undefined) {
		h = img.height;
	}

	// rest of function shamelessly copied from stackoverflow
	bufferCanvas.width = w;
    bufferCanvas.height = h;

    // fill offscreen buffer with the tint color
    bctx.fillStyle = '#FFCC00'
    bctx.fillRect(0, 0, w, h);

    // destination atop makes a result with an alpha channel identical to img, but with all pixels retaining their original color *as far as I can tell*
    bctx.globalCompositeOperation = "destination-atop";
    bctx.drawImage(img, 0, 0);

    // to tint the image, draw it first
    ctx.drawImage(img, 0, 0);

    //then set the global alpha to the amound that you want to tint it, and draw the buffer directly on top of it.
    ctx.globalAlpha = alpha;
    ctx.drawImage(bufferCanvas, 0, 0);
}
