---
title: Partitioning the Dutch national flag
date: 2013-03-06 14:00:08
programming/languages:
- HTML
- JavaScript
- Racket
- Scheme
programming/sources:
- Programming Praxis
programming/topics:
- Sorting
- Web Development
---
<a title="Dutch National Flag" href="http://programmingpraxis.com/2013/03/05/dutch-national-flag/">Yesterday's post</a> from Programming Praxis asks us to solve a problem known as the Dutch National Flag problem (attributed to {{< wikipedia "Edsgar Dijkstra" >}}): *sort an array of red, white and blue symbols so that all reds come together, followed by all whites, followed finally by all blues*.

<!--more-->

For once, the first algorithm to come to mind was actually the correct one. This doesn't always happen quite so nicely, but it is pleasant when it does. The basic idea is similar to the in-place partition often used with quicksorts ((This is actually more of a partitioning problem than a sorting one)): Start with labels at the beginning and end of the array; advance the labels towards each other, swapping elements on the wrong side of the pivot.

In this case, there are three labels (one for each color), but that doesn't actually change the algorithm much at all. Here are the basic steps:


* Start with three labels Lr = 0, Lw = 0, Lb = |data| - 1
* While Lw < Lb, check the element at Lw: 
* Red: Swap Lr and Lr and increment Lr and Lw
* White: Increment Lw
* Blue: Swap Lw and Lb and decrement Lb


That's all there is to it. Here's how you might translate that into Racket:

```scheme
(define (vector-swap! v i j)
  (define temp (vector-ref v i))
  (vector-set! v i (vector-ref v j))
  (vector-set! v j temp))

(define (partition-flag! flag)
  (let loop ([r 0] [w 0] [b (- (vector-length flag) 1)])
    (cond
      [(> w b) flag]
      [(eq? (vector-ref flag w) 'red)
       (vector-swap! flag r w)
       (loop (+ r 1) (+ w 1) b)]
      [(eq? (vector-ref flag w) 'white)
       (loop r (+ w 1) b)]
      [(eq? (vector-ref flag w) 'blue)
       (vector-swap! flag w b)
       (loop r w (- b 1))])))
```

Since the code is relative straight forward, I went ahead off the deep end and worked out a visualization that will run in your web browser. If everything works as it should, clicking 'Run Demo' below should show you exactly what happens when partitioning a 50-element vector.

<script type="text/javascript">
jQuery(function($) {
	// Context to draw with
	var canvas = $('#canvas')[0];
	var context = canvas.getContext('2d');
	var progress = $('#progress');

	// Various constants
	var demo_size = 50;
	var demo_step = 250;
	var left_offset = canvas.width / 10;
	var top_offset = canvas.height / 6;
	var block_width = 4/5 * canvas.width / demo_size;
	var block_height = 1/3 * canvas.height;
	var label_width = 3;
	var label_height = block_height / 3;

	// Data for the simulation
	var styles = new Array('red', 'white', 'blue');
	var labels = new Array(0, 0, 0);
	var data = new Array();
	var tick = 0;
	var comparisons = 0;
	var swaps = 0;

	// Logging function
	function log(msg) {
		progress.html(
			'Step ' + tick + ':<br />' +
			msg + '<br /><br />' +
			'So far:<br />' +
			comparisons + ' comparisons<br />' +
			swaps + ' swaps<br />' +
			demo_size + ' elements'
		);
	}

	// Run the entire demo
	function showDemo() {
		// Generate a new set of data
		data = new Array(demo_size);
		for (var i = 0; i < data.length; i++) {
			data[i] = Math.floor(Math.random() * 3);
		}

		// Reset the arrays to left, left, and right
		labels = new Array(0, 0, data.length - 1);

		// Clear progress and raw everything the first time
		progress.text('');
		draw();

		// Run the update functions
		comparisons = 0;
		swaps = 0;
		tick = 0;
		function simStep() {
			tick += 1;

			if (step())
				setTimeout(simStep, demo_step);
			else
				log("finished");

			draw();
		}
		setTimeout(simStep, demo_step);
	}

	// Swap two data points
	function swap(i, j) {
		swaps += 1;
		var temp = data[i];
		data[i] = data[j];
		data[j] = temp;
	}

	// Take a single step of the sorting function
	function step() {
		// Stop when the white and blue pointers cross
		if (labels[1] > labels[2]) {
			return false;
		}

		// On red: swap to red and increment red and white
		else if (data[labels[1]] == 0) {
			log('red, swap to red and increment red and white');
			swap(labels[0], labels[1]);
			labels[0] += 1;
			labels[1] += 1;
		}

		// On white: increment white
		else if (data[labels[1]] == 1) {
			log('white, increment white');
			labels[1] += 1;
		}

		// On blue: swap to blue and decrement blue
		else if (data[labels[1]] == 2) {
			log('blue, swap to blue and decrement blue');
			swap(labels[1], labels[2]);
			labels[2] -= 1;
		}

		// Done, signify that we took a step
		comparisons += 1;
		return true;
	}

	// Draw the blocks and labels
	function draw() {
		// Clear the screen
		context.clearRect(0, 0, canvas.width, canvas.height);

		// Draw blocks
		context.lineWidth = 1;
		context.strokeStyle = 'black';
		for (var i = 0; i < data.length; i++) {
			context.beginPath();
			context.rect(
				left_offset + i * block_width,
				top_offset,
				block_width,
				block_height
			);
			context.fillStyle = styles[data[i]];
			context.fill();
			context.stroke();
		}

		// Draw labels
		var center_x = 0, center_y = 0;
		for (var i = 0; i < labels.length; i++) {
			center_x = left_offset + labels[i] * block_width + block_width / 3;
			center_y = 2 * top_offset + block_height + i * label_height;
			context.beginPath();
			context.rect(
				center_x - label_width / 2,
				center_y - label_height / 2,
				label_width,
				label_height
			);
			context.fillStyle = styles[i];
			context.fill();
			context.stroke();
		}
	}

	$('#run').click(showDemo);

	$('#source').hide();
	$('#viewsource').click(function() {
		$('#progress').html('');
		$('#source').toggle();
	});
});
</script>

### Demo
<canvas id="canvas" width="400" height="100" style="border: 1px solid black;">

</canvas>

<button id="run" type="button">Run demo</button>
<button id="viewsource" type="button">Show demo source</button>







```javascript
jQuery(function($) {
	// Context to draw with
	var canvas = $('#canvas')[0];
	var context = canvas.getContext('2d');
	var progress = $('#progress');

	// Various constants
	var demo_size = 50;
	var demo_step = 250;
	var left_offset = canvas.width / 10;
	var top_offset = canvas.height / 6;
	var block_width = 4/5 * canvas.width / demo_size;
	var block_height = 1/3 * canvas.height;
	var label_width = 3;
	var label_height = block_height / 3;

	// Data for the simulation
	var styles = new Array('red', 'white', 'blue');
	var labels = new Array(0, 0, 0);
	var data = new Array();
	var tick = 0;
	var comparisons = 0;
	var swaps = 0;

	// Logging function
	function log(msg) {
		progress.html(
			'Step ' + tick + ':<br />' +
			msg + '<br /><br />' +
			'So far:<br />' +
			comparisons + ' comparisons<br />' +
			swaps + ' swaps<br />' +
			demo_size + ' elements'
		);
	}

	// Run the entire demo
	function showDemo() {
		// Generate a new set of data
		data = new Array(demo_size);
		for (var i = 0; i < data.length; i++) {
			data[i] = Math.floor(Math.random() * 3);
		}

		// Reset the arrays to left, left, and right
		labels = new Array(0, 0, data.length - 1);

		// Clear progress and raw everything the first time
		progress.text('');
		draw();

		// Run the update functions
		comparisons = 0;
		swaps = 0;
		tick = 0;
		function simStep() {
			tick += 1;

			if (step())
				setTimeout(simStep, demo_step);
			else
				log("finished");

			draw();
		}
		setTimeout(simStep, demo_step);
	}

	// Swap two data points
	function swap(i, j) {
		swaps += 1;
		var temp = data[i];
		data[i] = data[j];
		data[j] = temp;
	}

	// Take a single step of the sorting function
	function step() {
		// Stop when the white and blue pointers cross
		if (labels[1] > labels[2]) {
			return false;
		}

		// On red: swap to red and increment red and white
		else if (data[labels[1]] == 0) {
			log('red, swap to red and increment red and white');
			swap(labels[0], labels[1]);
			labels[0] += 1;
			labels[1] += 1;
		}

		// On white: increment white
		else if (data[labels[1]] == 1) {
			log('white, increment white');
			labels[1] += 1;
		}

		// On blue: swap to blue and decrement blue
		else if (data[labels[1]] == 2) {
			log('blue, swap to blue and decrement blue');
			swap(labels[1], labels[2]);
			labels[2] -= 1;
		}

		// Done, signify that we took a step
		comparisons += 1;
		return true;
	}

	// Draw the blocks and labels
	function draw() {
		// Clear the screen
		context.clearRect(0, 0, canvas.width, canvas.height);

		// Draw blocks
		context.lineWidth = 1;
		context.strokeStyle = 'black';
		for (var i = 0; i < data.length; i++) {
			context.beginPath();
			context.rect(
				left_offset + i * block_width,
				top_offset,
				block_width,
				block_height
			);
			context.fillStyle = styles[data[i]];
			context.fill();
			context.stroke();
		}

		// Draw labels
		var center_x = 0, center_y = 0;
		for (var i = 0; i < labels.length; i++) {
			center_x = left_offset + labels[i] * block_width + block_width / 3;
			center_y = 2 * top_offset + block_height + i * label_height;
			context.beginPath();
			context.rect(
				center_x - label_width / 2,
				center_y - label_height / 2,
				label_width,
				label_height
			);
			context.fillStyle = styles[i];
			context.fill();
			context.stroke();
		}
	}

	$('#run').click(showDemo);
});
```


