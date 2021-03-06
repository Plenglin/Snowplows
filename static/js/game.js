var game, drawing, inputManager, drawingCanvas, bufferCanvas, playerImg, drawingTask, inputTask;

const DRAW_PERIOD = 50;
const INPUT_PERIOD = 100;
const ARENA_THICKNESS = 10;
const EXTRA_SCALE_FACTOR = 0.75;

const OPENING = 0;
const GAME = 1;
const CLOSING = 2;

const ENEMY_COLORS = ['blueviolet', 'crimson', 'darkcyan', 'darkorange', 'darkorchid', 'firebrick', 'saddlebrown', 'salmon', 'thistle'];
const FRIENDLY_COLOR = 'darkgreen';
const SELF_COLOR = 'blue';
const DEAD_COLOR = 'black';


function debugDot(ctx, x, y) {
	ctx.beginPath();
	ctx.arc(x, y, 5, 0, 2*Math.PI);
	ctx.fill();
}

function PlayerControl() {
	this.pos = new util.Vec2(0, 0);
}

PlayerControl.prototype.getCallback = function() {
	var self = this;
	return function (event) {
		self.pos.x = event.clientX;
		self.pos.y = event.clientY;
	};
};

function Camera() {
	this.scale = 0;
	//this.rotate = 0;
	this.translate = new util.Vec2(0, 0);
}

Camera.prototype.applyToCanvas = function(ctx) {
	ctx.scale(this.scale, this.scale);
	//ctx.rotate(this.rotate);
	ctx.translate(this.translate.x, this.translate.y);
};

Camera.prototype.getPointOnScreen = function(p) {
	// Takes the point relative to (0, 0) on the untransformed canvas and maps it to a point on the camera after transforms.
	return new util.Vec2(
		util.linMap(p.x, 0, 1, this.translate.x, this.scale*(this.translate.x + 1)),
		util.linMap(p.y, 0, 1, this.translate.y, this.scale*(this.translate.y + 1))
	);
	/*return new util.Vec2(
		util.linMap(p.x, 0, 1, 0, this.scale*(1)),
		util.linMap(p.y, 0, 1, 0, this.scale*(1))
	);*/
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
	if (this.arenaDims.width < this.arenaDims.height) {
		this.cam.scale = this.canvas.width / this.arenaDims.width;
	} else {
		this.cam.scale = this.canvas.height / this.arenaDims.height;
	}
	this.cam.scale *= EXTRA_SCALE_FACTOR;
};

Drawing.prototype.drawImgWithTint = function(img, tint, alpha, x, y, w, h) {
	if (w == undefined) {
		w = img.width;
	}
	if (h == undefined) {
		h = img.height;
	}

	// rest of function shamelessly copied from stackoverflow
	this.buffer.width = w;
    this.buffer.height = h;

    // fill offscreen buffer with the tint color
    this.bctx.fillStyle = tint;
    this.bctx.fillRect(0, 0, w, h);

    // destination atop makes a result with an alpha channel identical to img, but with all pixels retaining their original color *as far as I can tell*
    this.bctx.globalCompositeOperation = "destination-atop";
    this.bctx.drawImage(img, 0, 0, w, h);

    // to tint the image, draw it first
    this.ctx.drawImage(img, x, y, w, h);

    //then set the global alpha to the amound that you want to tint it, and draw the buffer directly on top of it.
    this.ctx.globalAlpha = alpha;
    this.ctx.drawImage(this.buffer, x, y);
};

Drawing.prototype.drawGame = function(gameObj) {
	
	var self = this;

	// Clear the screen
	this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

	// Apply the camera to the canvas
	this.ctx.save();
	this.updateCam();
	console.log(this.cam.scale);
	//this.cam.scale = 0.25;
	this.cam.applyToCanvas(this.ctx);

	// Render background
	this.ctx.strokeStyle = "black";
	this.ctx.lineWidth = ARENA_THICKNESS;
	this.ctx.strokeRect(
		ARENA_THICKNESS/2, 
		ARENA_THICKNESS/2, 
		this.arenaDims.width + ARENA_THICKNESS*2, 
		this.arenaDims.height + ARENA_THICKNESS*2);

	debugDot(this.ctx, 400, 100);

	// Render players
	gameObj.forEachPlayer(function (player) {
		self.drawPlayer(player);
	});

	// Reset scaling and stuff
	this.ctx.restore();

};

Drawing.prototype.drawPlayer = function(player) {
	this.ctx.save();
	// Rotate around center
	this.ctx.translate(
		player.pos.x, 
		player.pos.y);
	this.ctx.rotate(player.direction);

	var pSize = player.getSize();

	console.log(pSize);

	this.drawImgWithTint(
		playerImg, player.getColor(), 0.5, 
		-pSize.w/2, -pSize.h/2, 
		pSize.w, pSize.h);
	debugDot(this.ctx, 0, 0);

	this.ctx.restore();

};

Drawing.prototype.setCanvasDimensions = function() {
	console.log('setting canvas dims with arena dims', this.arenaDims, 'and window dims', $(window).width(), $(window).height());
	if ($(window).width() < $(window).height()) {
		console.log('window is vertical');
		this.canvas.width = $(window).width();
		this.canvas.height = $(window).width() * this.arenaDims.height / this.arenaDims.width;
	} else {
		console.log('window is horizontal');
		this.canvas.height = $(window).height();
		this.canvas.width = $(window).height() * this.arenaDims.width / this.arenaDims.height;		
	}
	console.log('final canvas dims:', this.canvas.width, this.canvas.height);

};

function Player(team, id, isUser, size) {
	this.team = team;
	this.id = id;
	this.pos = new util.Vec2(0, 0);
	this.direction = 0;
	this.isUser = isUser;
	this.size = size;
	this.living = true;
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

Player.prototype.getSize = function() {
	return {w: this.size, h: this.size};
};

function Team(id, color) {
	this.id = id;
	this.color = color;
	this.players = {};
}

Team.prototype.createPlayer = function(id, isUser, pSize) {
	var p = new Player(this, id, isUser, pSize);
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
	this.player = null;
	this.teams = {};
}

Game.prototype.initialize = function(data) {
    console.log('player id is', data.player.id);
    console.log('player is on team', data.player.team);

    this.arena = data.arena;
    console.log('arena dimensions', this.arena);

    console.log('assigning colors to the teams...');
    for (var i = data.teams.length - 1; i >= 0; i--) {
    	var teamData = data.teams[i];
    	var id = teamData.id;
    	
    	var color = (id === this.playerTeamId) ? FRIENDLY_COLOR : choice(ENEMY_COLORS);
    	var team = new Team(id, color);
    	this.teams[id] = team;
    	console.log('assigned', color, 'to', id);
    	
    	for (var j = teamData.players.length - 1; j >= 0; j--) {
    		var playerId = teamData.players[j];
    		console.log('creating player', playerId);
    		if (playerId === data.player.id) {
    			console.log('this.player');
	    		this.player = team.createPlayer(playerId, true, data.playerSize);
	    	} else {
	    		team.createPlayer(playerId, false, data.playerSize);
	    	}
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
			player.setTransform(pData.x, pData.y, pData.direction);
		});
	});
};

$(function() {

	game = new Game();

	drawingCanvas = $('#gameCanvas')[0];
	bufferCanvas = $('#bufferCanvas')[0];

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
			    drawing = new Drawing(game.arena, drawingCanvas, bufferCanvas);
				drawing.setCanvasDimensions();

			    console.log('starting drawing task');
		        drawingTask = setInterval(function() {
		        	drawing.drawGame(game);
		        	console.log(drawing, game);
		        }, DRAW_PERIOD);

		        console.log('starting mouse listener and client input');
		        inputManager = new PlayerControl();
		        $('#gameCanvas').mousemove(inputManager.getCallback());
		        inputTask = setInterval(function() {
		        	console.log('ipman', inputManager);
		        	var pointOnScreen = drawing.cam.getPointOnScreen(inputManager.pos);
		        	var playerPos = game.player.pos;
		        	pointOnScreen = pointOnScreen.add(new Vec2(ARENA_THICKNESS, ARENA_THICKNESS));
		        	debugDot(drawing.ctx, pointOnScreen.x, pointOnScreen.y);
		        	console.log(inputManager.pos, pointOnScreen, playerPos);
		        	game.socket.send(JSON.stringify({
		        		movement: pointOnScreen.sub(playerPos),
		        		events: []
		        	}));
		        }, INPUT_PERIOD);

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
