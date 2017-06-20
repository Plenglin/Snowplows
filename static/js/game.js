var game, drawingCanvas, bufferCanvas, ctx, bctx, playerImg, drawingTask, inputTask;

const DRAW_PERIOD = 50;
const INPUT_PERIOD = 100;
const ARENA_THICKNESS = 10;

const OPENING = 0;
const GAME = 1;
const CLOSING = 2;

const ENEMY_COLORS = ['blueviolet', 'crimson', 'darkcyan', 'darkorange', 'darkorchid', 'firebrick', 'saddlebrown', 'salmon', 'thistle'];
const FRIENDLY_COLOR = 'darkgreen';
const SELF_COLOR = 'cornflowerblue';
const DEAD_COLOR = 'black';

function Camera() {
	this.scale = 0;
	this.rotate = 0;
	this.translate = {x: 0, y: 0};
}

Camera.prototype.applyToCanvas = function(ctx) {
	ctx.scale(this.scale);
	ctx.rotate(this.rotate);
	ctx.translate(this.translate.x, this.translate.y);
};

function Drawing(arenaDims, canvas, bufferCanvas) {
	this.arenaDims = arenaDims;
	this.canvas = canvas;
	this.buffer = bufferCanvas;

	this.cam = new Camera();
	this.ctx = canvas.getContext('2d');
	this.bctx = this.buffer.getContext('2d');
}

Drawing.prototype.updateCam = function() {
	// Get the factor to multiply arena dimensions by
	if (arenaDims.width < arenaDims.height) {
		this.cam.scale = canvas.getWidth() / arenaDims.width;
	} else {
		this.cam.scale = canvas.getHeight() / arenaDims.getHeight;
	}
};

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

function Team(id, color) {
	this.id = id;
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

function Game() {
	this.socket = null;
	this.socketstate = null;
	this.arena = {width: 0, height: 0};
	this.playerId = '';
	this.playerTeamId = '';
	this.teams = {};
}

Game.prototype.initialize = function(data) {
    this.playerId = data.player.id;
    this.playerTeamId = data.player.team;

    console.log('player id is', this.playerId);
    console.log('player is on team', this.playerTeamId);

    this.arena = data.arena;
    console.log('arena dimensions', this.arena);

    console.log('assigning colors to the teams...');
    for (var i = data.teams.length - 1; i >= 0; i--) {
    	var teamData = data.teams[i];
    	var id = teamData.id;
    	
    	var color = id == this.playerTeamId ? FRIENDLY_COLOR : choice(ENEMY_COLORS);
    	var team = new Team(id, color);
    	this.teams[id] = team;
    	console.log('assigned', color, 'to', id);
    	
    	for (var j = teamData.players.length - 1; j >= 0; j--) {
    		var playerId = teamData.players[j];
    		team.createPlayer(playerId);
    	}
    }

};

Game.prototype.forEachPlayer = function(cb) {
	for (var teamId in this.teams) {
		var team = this.teams[teamId];
		for (var playerId in team.players) {
			cb(team.getPlayer(playerId));
		}
	}
};

Game.prototype.update = function(data) {
	var self = this;
	data.teams.forEach(function (tData) {
		var team = self.teams[tData.id];
		tData.players.forEach(function (pData) {
			var player = team.getPlayer(pData.id);
			player.pos.x = pData.x;
			player.pos.y = pData.y;
			player.direction = pData.direction;
		});
	});
};

Game.prototype.draw = function(ctx) {

	// Clear the screen
	ctx.clearRect(0, 0, gameCanvas.width, gameCanvas.height);

	// Render background
	ctx.strokeStyle = "black";
	ctx.lineWidth = 100;
	ctx.strokeRect(
		ARENA_THICKNESS/2, 
		ARENA_THICKNESS/2, 
		this.arena.width + ARENA_THICKNESS*2, 
		this.arena.height + ARENA_THICKNESS*2);

	// Render players
	this.forEachPlayer(function (player) {
		player.draw(ctx);
	});

};

$(function() {

	game = new Game();

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
			    game.initialize(data);
			    console.log('game object:', game);
			    console.log('starting drawing task');
		        drawingTask = setInterval(function() {
		        	game.draw(ctx);
		        }, DRAW_PERIOD);
				game.socketstate = GAME;
			} else {
				console.log('token not acknowledged, closing socket');
				game.socket.close();
			}
			break;
		case GAME:
			game.update(data);
			break;

		case CLOSING:
			break;

		default:
			console.log('state machine derped pls fix');
			break;
		}
	};

});

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
