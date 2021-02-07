var canvas, gl;
var shaderScript;
var shaderSource;
var vertexShader; 
var fragmentShader; 
var buffer;
var locationOfTime;
var locationOfResolution;
var startTime = new Date().getTime(); // Get start time for animating
var currentTime = 0;

function init() {
	// standard canvas setup here, except get webgl context
	canvas = document.getElementById('glscreen');
	gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
	canvas.width  = window.innerWidth;
	canvas.height = document.body.clientHeight;
	
	// give WebGL it's viewport
	gl.viewport(0, 0, gl.drawingBufferWidth, gl.drawingBufferHeight);
	buffer = gl.createBuffer();
	gl.bindBuffer(gl.ARRAY_BUFFER, buffer);
	gl.bufferData(
		gl.ARRAY_BUFFER, 
		new Float32Array([
			-1.0, -1.0, 
			1.0, -1.0, 
			-1.0,  1.0, 
			-1.0,  1.0, 
			1.0, -1.0, 
			1.0,  1.0]), 
		gl.STATIC_DRAW
	); 

	shaderScript = document.getElementById("2d-vertex-shader");
	shaderSource = shaderScript.text;
	vertexShader = gl.createShader(gl.VERTEX_SHADER); //create the vertex shader from script
	gl.shaderSource(vertexShader, shaderSource);
	gl.compileShader(vertexShader);

	shaderScript   = document.getElementById("2d-fragment-shader");
	shaderSource   = shaderScript.text;
	fragmentShader = gl.createShader(gl.FRAGMENT_SHADER); //create the fragment from script
	gl.shaderSource(fragmentShader, shaderSource);
	gl.compileShader(fragmentShader);

	program = gl.createProgram(); // create the WebGL program.  This variable will be used to inject our javascript variables into the program.
	gl.attachShader(program, vertexShader); // add the shaders to the program
	gl.attachShader(program, fragmentShader); // ^^
	gl.linkProgram(program);	 // Tell our WebGL application to use the program
	gl.useProgram(program); // ^^ yep, but now literally use it.
	
	
	locationOfResolution = gl.getUniformLocation(program, "u_resolution");
	locationOfTime = gl.getUniformLocation(program, "u_time");
	
	
	gl.uniform2f(locationOfResolution, canvas.width, canvas.height);
	gl.uniform1f(locationOfTime, currentTime);

	render();
}

function render() {
	var now = new Date().getTime();
	currentTime = (now - startTime) / 1000; // update the current time for animations
	
	
	gl.uniform1f(locationOfTime, currentTime); // update the time uniform in our shader

	window.requestAnimationFrame(render, canvas); // request the next frame

	positionLocation = gl.getAttribLocation(program, "a_position"); // do stuff for those vertex's
	gl.enableVertexAttribArray(positionLocation);
	gl.vertexAttribPointer(positionLocation, 2, gl.FLOAT, false, 0, 0);
	gl.drawArrays(gl.TRIANGLES, 0, 6);
}

window.addEventListener('load', function(event){
	init();
});

window.addEventListener('resize', function(event){	
	canvas.width  = window.innerWidth;
	canvas.height = window.innerHeight;
	gl.viewport(0, 0, window.innerWidth, window.innerHeight);
	locationOfResolution = gl.getUniformLocation(program, "u_resolution");
});

// https://codepen.io/darrylhuffman/pen/prrzVQ