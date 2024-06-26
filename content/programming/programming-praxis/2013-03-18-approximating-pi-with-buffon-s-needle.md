---
title: Approximating Pi with Buffon's Needle
date: 2013-03-18 14:00:14
programming/languages:
- HTML
- JavaScript
programming/sources:
- Programming Praxis
programming/topics:
- Mathematics
- Trigonometry
- Web Development
---
I'm a bit late for Pi Day, but Programming Praxis had <a href="http://programmingpraxis.com/2013/03/15/buffons-needle/" title="Buffon's Needle">a neat problem on Friday</a> that I wanted to check out:

> Suppose we have a floor made of parallel strips of wood, each the same width, and we drop a needle onto the floor. What is the probability that the needle will lie across a line between two strips?

<!--more-->

It turns out (as you might have guessed from the title) that the probability ends up being equal to 2/pi. How can we show that? Well in this case, I have a nice JavaScript simulation for you (down at the end of the post). The code is actually really straight forward:

```javascript
// Drop a bunch of needles
var x1, y1, theta, x2, y2;
for (var i = 0; i < numberToDrop; i++) {
	// Drop a new needle
	x1 = (Math.random() * (width - 2 * needleLength)) + needleLength;
	y1 = (Math.random() * (height - 2 * needleLength)) + needleLength;
	theta = Math.random() * 2 * Math.PI;

	x2 = x1 + needleLength * Math.cos(theta);
	y2 = y1 + needleLength * Math.sin(theta);

	// Check if it crosses a line
	// Yes, this isn't the best way to do this
	var crossesLine = false;
	for (var x = needleLength / 2; x <= canvas.width; x += needleLength) {
		if ((x1 <= x && x <= x2) || (x2 <= x && x <= x1))
			crossesLine = true;
	}

	// Record the toss
	tossed += 1;
	if (crossesLine) crossed += 1;
}

console.log("pi ~ " + (2 * tossed / crossed));
```

I know that there are better ways to figure out if a needle crosses the line, but this works well enough. Plus, I wanted to make a really neat visualization. Speaking of which (note: red needles are crossing the line, blue are not):

<script type="text/javascript">
jQuery(function($) {
	// Context to draw with
	var canvas = $('#canvas')[0];
	var context = canvas.getContext('2d');
	var progress = $('#progress');

	// Experiment parameters
	var drawEnabled = true;
	var pendingDrop = false;
	var tickTime = 1000000;
	var speedBoost = 1;
	var roundingDigits = 1000000;
	var maxBufferSize = 10;
	var needleBuffer = [];
	var needleLength = canvas.width / 20;
	var tossed = 0;
	var crossed = 0;

	// Draw lines
	function drawLines() {
		for (var x = needleLength / 2; x <= canvas.width; x += needleLength) {
			context.beginPath();
			context.strokeStyle = 'black';
			context.moveTo(x, 0);
			context.lineTo(x, canvas.height);
			context.stroke();
		}
	}

	// Drop a single needle on the canvas
	function dropNeedle() {
		var x1, y1, theta, x2, y2;
		// In accelerated mode, do multiple at a time
		for (var i = 0; i < speedBoost; i++) {
			// Drop a new needle
			x1 = (Math.random() * (canvas.width - 2 * needleLength)) + needleLength;
			y1 = (Math.random() * (canvas.height - 2 * needleLength)) + needleLength;
			theta = Math.random() * 2 * Math.PI;

			x2 = x1 + needleLength * Math.cos(theta);
			y2 = y1 + needleLength * Math.sin(theta);

			// Check if it crosses a line
			// Yes, this isn't the best way to do this
			var crossesLine = false;
			for (var x = needleLength / 2; x <= canvas.width; x += needleLength) {
				if ((x1 <= x && x <= x2) || (x2 <= x && x <= x1))
					crossesLine = true;
			}

			// Record the toss
			tossed += 1;
			if (crossesLine)
				crossed += 1;
		}

		// Potentially disable drawing
		if (drawEnabled) {
			// Buffer the drawn needles to erase them later
			needleBuffer.push([x1, y1, x2, y2])

			// Draw the needle
			context.beginPath();
			context.strokeStyle = (crossesLine ? 'red' : 'blue');
			context.moveTo(x1, y1);
			context.lineTo(x2, y2);
			context.stroke();

			// Fade out old needles
			if (needleBuffer.length >= maxBufferSize) {
				var toErase = needleBuffer.shift();

				context.beginPath();
				context.strokeStyle = 'white';
				context.moveTo(toErase[0], toErase[1]);
				context.lineTo(toErase[2], toErase[3]);
				context.stroke();
			}
		}

		// Update the progress (slowly if draw is disabled)
		progress.html(
			'Needles tossed: ' + tossed + ', ' +
			'crossing lines: ' + crossed + '. <br />' +
			'Current approximation: ' + (Math.round(roundingDigits * 2 * tossed / crossed) / roundingDigits)
		);

		// Call the next function
		pendingDrop = setTimeout(dropNeedle, tickTime);
	}

	// Update the simulation speed
	$('input[name="speed"]').click(function() {
		tickTime = parseInt($(this).val());
		drawEnabled = true;
		speedBoost = 1;

		if (tickTime <= -1) {
			speedBoost = Math.abs(tickTime);
			drawEnabled = false;
			tickTime = 0;
		}

		if (tickTime == 0) {
			var next = $(this).val() * 10;
			if (next == 0) next = -10;
			$('input[value="' + next + '"]').parent().show();
		}

		if (pendingDrop) clearTimeout(pendingDrop);
		pendingDrop = setTimeout(dropNeedle, tickTime);
	});

	// Reset the simulation
	$('input[name="reset"]').click(function() {
		tossed = 0;
		crossed = 0;

		context.clearRect(0, 0, canvas.width, canvas.height);
		drawLines();
		if (pendingDrop) clearTimeout(pendingDrop);
		pendingDrop = setTimeout(dropNeedle, tickTime);
	});

	// Start with the super fast speeds hidden
	$('.hide').hide();

	// Start the simulation
	drawLines();
});
</script>

### Demo
<canvas id="canvas" width="400" height="400" style="border: 1px solid black;"></canvas><br />
<input type="button" name="reset" value="Reset" />


### Results
<p id="progress"></p>



### Simulation speed
<input type="radio" name="speed" value="1000000" checked="checked">stopped <br />
<input type="radio" name="speed" value="1000">slow (1.0 Hz)<br />
<input type="radio" name="speed" value="500">normal (0.5 Hz)<br />
<input type="radio" name="speed" value="100">fast (0.1 Hz)<br />
<input type="radio" name="speed" value="10">very fast (0.01 Hz)<br />
<input type="radio" name="speed" value="0">as fast as possible<br />
<span class="hide"><input type="radio" name="speed" value="-10">even faster<br /></span>
<span class="hide"><input type="radio" name="speed" value="-100">light speed<br /></span>
<span class="hide"><input type="radio" name="speed" value="-1000">ludicrous speed<br /></span>
<span class="hide"><input type="radio" name="speed" value="-10000">...<br /></span>

<br /><br />
