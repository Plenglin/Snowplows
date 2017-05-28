var drawingCanvas, bufferCanvas, ctx, bctx, socket, socketstate, playerId;

const OPENING = 0;
const GAME = 1;
const CLOSING = 2;

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
	socket = new WebSocket(websocketUrl($('head').data('socket-url')));
	socket.onopen = function() {
    	socketstate = OPENING;
		socket.send(JSON.stringify({
			token: $('head').data('token')
		}));
	}
	socket.onmessage = function(event) {

		var data = JSON.parse(event.data);
		console.log('received', data);
		switch (socketstate) {
		case OPENING:
			if (data.valid) {
			    playerId = data.id;
			    console.log('token acknowledged');
			    console.log(sprintf('player id is %s', playerId));
			    socketstate = GAME;
			}
			break;
		case GAME:
			break;
		case CLOSING:
			break;
		}
	}

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
