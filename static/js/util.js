// global $

util = {};

function websocketUrl(path) {
	return 'ws://' + $(location).attr('host') + '/' + path;
}

function choice(array) {
	return array[Math.floor(Math.random() * array.length)];
}

util.linMap = function(x, a1, b1, a2, b2) {
	// Maps a number x between a1 and b1 to a number between a2 and b2.
	return (b2 - a2) * (x - a1) / (b1 - a1) + a2;
};

function Vec2(x, y) {
	this.x = x;
	this.y = y;
}

Vec2.prototype.add = function(other) {
	return new Vec2(this.x + other.x, this.y + other.y);
};

Vec2.prototype.sub = function(other) {
	return new Vec2(this.x - other.x, this.y - other.y);
};

Vec2.prototype.mul = function(other) {
	return new Vec2(this.x * other.x, this.y * other.y);
};

Vec2.prototype.scl = function(k) {
	return new Vec2(this.x * k, this.y * k);
};

Vec2.prototype.mag = function() {
	return Math.sqrt(this.x * this.x + this.y * this.y)
};

Vec2.prototype.unit = function() {
	return this.scl(1/this.mag);
};

Vec2.prototype.rot = function(a) {
	return new Vec2(this.x * Math.cos(a) - this.y * Math.sin(a), this.x * Math.sin(a) + this.y * Math.cos(a))
};

Vec2.prototype.div = function(other) {
	return new Vec2(this.x / other.x, this.y / other.y);
};

Vec2.prototype.dot = function(other) {
	return this.x * other.x + this.y * other.y;
};

util.Vec2 = Vec2;