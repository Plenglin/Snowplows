var drawingCanvas, bufferCanvas, ctx, bctx, playerImg;

const OPENING = 0;
const GAME = 1;
const CLOSING = 2;

const ENEMY_COLORS = ['blueviolet', 'crimson', 'darkcyan', 'darkorange', 'darkorchid', 'firebrick', 'saddlebrown', 'salmon', 'thistle'];
const FRIENDLY_COLOR = 'darkgreen';
const SELF_COLOR = 'cornflowerblue';
const DEAD_COLOR = 'black';

function Player(team, id, isUser) {
	this.team = team;
	this.id = id;
	this.pos = {x: 0, y: 0};
	this.direction = 0;
	this.isUser = isUser;
}

Player.prototype.setTransform = function(x, y, direction) {
	this.pos.x = x;
	this.pos.y = y;
	this.direction = direction;
	return this;
};

Player.prototype.getColor = function() {
	return this.isUser ? SELF_COLOR : this.team.color;
};

Player.prototype.draw = function(ctx) {
	ctx.save();
	// Rotate around center
	ctx.translate(this.pos.x, this.pos.y);
	ctx.rotate(this.direction);
	ctx.translate(-this.pos.x, this.pos.y);

	drawImgWithTint(ctx, playerImg, this.getColor(), 0.5, this.x, this.y, playerImg.width, playerImg.height);
	ctx.restore();

};

function Team(color) {
	this.color = color;
	this.players = {};
}

Team.prototype.createPlayer = function(id) {
	var p = new Player(this, id);
	this.players[id] = p;
	return p;
};

Team.prototype.getPlayer = function(id) {
	return this.players[id];
};


var game = {
	socket: null,
	socketstate: null,
	playerId: '',
	playerTeamId: '',
	teams: {}
};

$(function() {
	drawingCanvas = $('#gameCanvas')[0];
	ctx = drawingCanvas.getContext('2d');

	drawingCanvas.width = $(window).width();
	drawingCanvas.height = $(window).height();

	bufferCanvas = $('#bufferCanvas')[0];
	bctx = bufferCanvas.getContext('2d');

	var token = $('head').data('token');

	console.log('loading playerImg');
	playerImg = new Image();
	playerImg.src = '/static/img/truck.png';

	console.log('opening socket');
	game.socket = new WebSocket(websocketUrl($('head').data('socket-url')));
	
	async.parallel([
		function (cb) {  // Wait for image to load
			playerImg.onload = function() {
				console.log('playerImg finished loading');
				cb(null);
			};
		},
		function (cb) {  // Wait for socket to connect
			game.socket.onopen = function() {
				console.log('socket finished opening');
				cb(null);
			};
		}
	], function(err, results) {  // Finally, send our token through the socket to begin the game
    	console.log('sending token', token);
    	game.socketstate = OPENING;
		game.socket.send(JSON.stringify({
			token: token
		})); 
	});

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

function drawGame() {
	game.teams.foreach(function(team) {
		team.foreach(function(player) {
			player.draw();
		});
	});
}

function drawImgWithTint(ctx, img, tint, alpha, x, y, w, h) {
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
    bctx.fillStyle = '#FFCC00';
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
