---
title: Line art with an HTML5 canvas
date: 2012-09-26 14:00:16
programming/languages:
- HTML
- JavaScript
programming/topics:
- Mathematics
- Web Development
slug: line-art-with-html5-canvas
---
Let's play with <a href="http://www.w3schools.com/html/html5_canvas.asp" title="W3 Schools: HTML5 canvas">HTML5 canvas</a> elements!

Basically, I want to draw some simple line diagrams. Go from top to bottom on one side while going from right to left along the top or bottom. It sounds complicated, but perhaps it's easier to explain with a drawing:

<!--more-->

<canvas id="canvas0" width="200" height="200" style="border: 1px solid black;"></canvas>

The code for that is actually surprisingly simple:

```javascript
jQuery(function($) {
  var c = $("#canvas0")[0].getContext('2d');
  var w = $("#canvas0").width();
  var h = $("#canvas0").height();

  c.lineWidth = 1;
  c.strokeStyle = col;

  c.beginPath();
  for (var i = 0; i <= d; i++) {
    c.moveTo(0, i * h / d);
    c.lineTo(w - i * w / d, 0);
  }
  c.stroke();
}
```

That was easy enough, but what if we want to generalize out to something more like these:

<canvas id="canvas1" width="200" height="200" style="border: 1px solid black;"></canvas> <canvas id="canvas2" width="200" height="200" style="border: 1px solid black;"></canvas>

What additional variables do we want? It would be nice to be able to draw how many lines we're going to use, the rectangle we're drawing in (x, y, width, height), the color of the line, and the orientation. Combine all of that and you have something like this:

```javascript
function drawGrid(id, x, y, w, h, d, col, which) {
  var c = $("#canvas")[0].getContext('2d');

  c.lineWidth = 1;
  c.strokeStyle = col;

  c.beginPath();
  for (var i = 0; i <= d; i++) {
    if (which == "tl") {
  	  c.moveTo(x, y + i * h / d);
	  c.lineTo(x + w - i * w / d, y);
    } else if (which == "tr") {
	  c.moveTo(x + w, y + i * h / d);
	  c.lineTo(x + i * w / d, y + 0);
    } else if (which == "bl") {
	  c.moveTo(x, y + i * h / d);
	  c.lineTo(x + i * w / d, y + h);
    } else if (which == "br") {
	  c.moveTo(x + w, y + i * h / d);
	  c.lineTo(x + w - i * w / d, y + h);
    }
  }
  c.stroke();
}
```

Here is the source for the more complicated images:

```javascript
// outer border
drawGrid("#canvas1", 0, 0, 100, 100, 25, "green", "tl");
drawGrid("#canvas1", 100, 0, 100, 100, 25, "blue", "tr");
drawGrid("#canvas1", 0, 100, 100, 100, 25, "green", "bl");
drawGrid("#canvas1", 100, 100, 100, 100, 25, "blue", "br");

// inner border
drawGrid("#canvas2", 0, 0, 100, 100, 25, "red", "br");
drawGrid("#canvas2", 100, 0, 100, 100, 25, "green", "bl");
drawGrid("#canvas2", 0, 100, 100, 100, 25, "blue", "tr");
drawGrid("#canvas2", 100, 100, 100, 100, 25, "black", "tl");
```

Now the fun part, you can play with the settings:

<table class="table table-striped">
<tr>
  <td>left</td>
  <td><input id="drawGrid-x" name="drawGrid-x" style="width: 200px;" value="0" /></td>
  <td class="warning" id="drawGrid-x-warning"></td>
</tr>
<tr>
  <td>top</td>
  <td><input id="drawGrid-y" name="drawGrid-y" style="width: 200px;" value="0" /></td>
  <td class="warning" id="drawGrid-y-warning"></td>
</tr>
<tr>
  <td>width</td>
  <td><input id="drawGrid-width" name="drawGrid-width" style="width: 200px;" value="400" /></td>
  <td class="warning" id="drawGrid-width-warning"></td>
</tr>
<tr>
  <td>height</td>
  <td><input id="drawGrid-height" name="drawGrid-height" style="width: 200px;" value="400" /></td>
  <td class="warning" id="drawGrid-height-warning"></td>
</tr>
<tr>
  <td>lines</td>
  <td><input id="drawGrid-lines" name="drawGrid-lines" style="width: 200px;" value="10" /></td>
  <td class="warning" id="drawGrid-lines-warning"></td>
</tr>
<tr>
  <td>color</td>
  <td><input id="drawGrid-color" name="drawGrid-color" style="width: 200px;" value="black" /></td>
  <td class="warning" id="drawGrid-color-warning"></td>
</tr>
<tr>
  <td>corner</td>
  <td>
    <select id="drawGrid-which" name="drawGrid-which">
      <option value="tl">top left</option>
      <option value="tr">top right</option>
      <option value="bl">bottom left</option>
      <option value="br">bottom right</option>
    </select>
  </td>
  <td class="warning" id="drawGrid-which-warning"></td>
</tr>
</table>

<button id="drawGrid">Draw</button> <button id="clearGrid">Clear</button> <button id="saveGrid">Save</button>

<canvas id="canvas3" width="400" height="400" style="border: 1px solid black;"></canvas>

If you'd like to download the source, you can do so here: <a href="https://github.com/jpverkamp/small-projects/blob/master/blog/html5-line-art.js" title="html5-line-art source">html5-line-art</a>

<style>
.warning { color: red; }
</style>

<script type="text/javascript">
// id: canvas to draw on
// d: divisions
// col: the color to draw with
// which: the corner -- tl, tr, bl, br
jQuery(function($) {
  function drawGrid(id, x, y, w, h, d, col, which) {
    var c = $(id)[0].getContext('2d');

    c.lineWidth = 1;
    c.strokeStyle = col;

    c.beginPath();
    for (var i = 0; i <= d; i++) {
      if (which == "tl") {
        c.moveTo(x, y + i * h / d);
        c.lineTo(x + w - i * w / d, y);
      } else if (which == "tr") {
        c.moveTo(x + w, y + i * h / d);
        c.lineTo(x + i * w / d, y + 0);
      } else if (which == "bl") {
        c.moveTo(x, y + i * h / d);
        c.lineTo(x + i * w / d, y + h);
      } else if (which == "br") {
        c.moveTo(x + w, y + i * h / d);
        c.lineTo(x + w - i * w / d, y + h);
      }
    }
    c.stroke();
  }

  drawGrid("#canvas0", 0, 0, 200, 200, 20, "black", "tl");

  drawGrid("#canvas1", 0, 0, 100, 100, 25, "green", "tl");
  drawGrid("#canvas1", 100, 0, 100, 100, 25, "blue", "tr");
  drawGrid("#canvas1", 0, 100, 100, 100, 25, "green", "bl");
  drawGrid("#canvas1", 100, 100, 100, 100, 25, "blue", "br");

  drawGrid("#canvas2", 0, 0, 100, 100, 25, "red", "br");
  drawGrid("#canvas2", 100, 0, 100, 100, 25, "green", "bl");
  drawGrid("#canvas2", 0, 100, 100, 100, 25, "blue", "tr");
  drawGrid("#canvas2", 100, 100, 100, 100, 25, "black", "tl");

  function doDraw() {
    var failed = false;
    $(".warning").empty();

    var x = parseInt($("#drawGrid-x").val());
    if (isNaN(x) || x < 0 || x > 400) {
      $("#drawGrid-x-warning").text("Must be in the range [0, 400]");
      failed = true;
    }

    var y = parseInt($("#drawGrid-y").val());
    if (isNaN(y) || y < 0 || y > 400) {
      $("#drawGrid-y-warning").text("Must be in the range [0, 400]");
      failed = true;
    }

    var width = parseInt($("#drawGrid-width").val());
    if (isNaN(width) || width < 0 || width > 400) {
      $("#drawGrid-width-warning").text("Must be in the range [0, 400]");
      failed = true;
    }

    var height = parseInt($("#drawGrid-height").val());
    if (isNaN(height) || height < 0 || height > 400) {
      $("#drawGrid-height-warning").text("Must be in the range [0, 400]");
      failed = true;
    }

	var lines = parseInt($("#drawGrid-lines").val());
    if (isNaN(lines) || lines < 2 || lines > 100) {
      $("#drawGrid-lines-warning").text("Must be in the range [2, 100]");
      failed = true;
    }

    var color = $("#drawGrid-color").val();
    if (color == "")
	  color = "black";

	var which = $("#drawGrid-which").val();
	if (!($.inArray(which, new Array("tl", "tr", "bl", "br"))))
	  which = "tl";

    if (!failed) {
      drawGrid("#canvas3", x, y, width, height, lines, color, which);
    }
  }
  $("#drawGrid").click(doDraw);

  function doClear() {
    var c = $("#canvas3")[0].getContext('2d');
    var w = $("#canvas3").width();
    var h = $("#canvas3").height();
    c.clearRect(0, 0, w, h);
  }
  $("#clearGrid").click(doClear);

  function doSave() {
    window.open(jQuery("#canvas3")[0].toDataURL());
  }
  $("#saveGrid").click(doSave);
});
</script>
