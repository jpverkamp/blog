---
title: Elementary cellular automaton
date: 2012-10-03 14:00:47
programming/languages:
- HTML
- JavaScript
programming/topics:
- Cellular Automata
- Mathematics
- Web Development
---
Today we're going to be playing with an HTML5 canvas again (previously we made [line art]({{< ref "2012-09-26-line-art-with-an-html5-canvas.md" >}}) and [bugs]({{< ref "2012-09-27-html5-bugs.md" >}})). This time, the goal is to make a tool where you can explore <a href="http://mathworld.wolfram.com/ElementaryCellularAutomaton.html" title="Wolfram Mathworld: Elementary Cellular Automaton">elementary cellular automaton</a>.

<!--more-->

(If you just want to jump to the toy, <a href="#thecanvas">click here</a>. There's also a much larger version available <a href="http://apps.jverkamp.com/small-projects/cellular/" title="jverkamp apps: Cellular">here</a>.)

Essentially, you can think of an elementary cellular automaton as a function on a series of rooms. Each room has a light and the ability to see their neighbor's lights as well as their own. Now if you take that those three inputs, there are 8 cases to consider:


| left | me  | right |
|------|-----|-------|
| off  | off |  off  |
| off  | off |  on   |
| off  | on  |  off  |
| off  | on  |  on   |
|  on  | off |  off  |
|  on  | off |  on   |
|  on  | on  |  off  |
|  on  | on  |  on   |


For each of those eight inputs, there are two possible outputs. I can either turn my light on or turn it off. This in turn will be seen by my neighbors who might the adjust their own lights and so on.

What gets more interesting is when you show a picture of the changing lights over time. Imagine a series of rows where each row is the state of all of the lights at one moment in time. So if the rule is that whenever either neighbor's light is on to turn your own on, you'll see a spreading wave of lights turning on as you move down the picture (rule 222).

So how does this all work in practice? It turns out, it's actually pretty simple.

First, we'll initialize two arrays. I've included a number of initial conditions including all off, all on, half and half, random, and a single point.

```javascript
var oldRow = new Array(width);
var newRow = new Array(width);

for (var i = 0; i < width; i++) {
  if (initial == "random")
    oldRow[i] = (Math.random() > 0.5 ? 1 : 0);
  else if (initial == "5050")
    oldRow[i] = (i < width / 2 ? 0 : 1);
  else if (initial == "point")
    oldRow[i] = (i == Math.floor(width / 2) ? 1 : 0);
  else if (initial == "black")
    oldRow[i] = 1;
  else if (initial == "white")
    oldRow[i] = 0;
  else
    oldRow[i] = 0;

  newRow[i] = 0;
}
```

Why two arrays? So that we can update one without the updates themselves having an effect on the row we're working on. You could actually do that just as well, but it wouldn't be the simulation we're trying to do.

In any case, the next step we need is run the actual simulation. Basically, work from top to bottom making each row based off of the previous one.

```javascript
var index = 0;
for (var row = 0; row < height; row++) {
  for (var col = 0; col < width; col++) {
    if (oldRow[col] == 1)
      c.fillRect(col, row, 1, 1);

    index = oldRow[col == 0 ? 0 : col - 1] * 4 + oldRow[col] * 2 + oldRow[col == width - 1 ? width - 1 : col + 1];
    newRow[col] = setTo[index];
  }

  for (var col = 0; col < width; col++) {
    oldRow[col] = newRow[col];
  }
}
```

One interesting bit there is the calculation and use of the variable `index`. Basically, `index` treats the values to the left, right, and at the given point as a binary number 0-8. These values are each decoded in another part of the code:

```javascript
var setTo = [0, 0, 0, 0, 0, 0, 0, 0];
for (var i = 0; i < 8; i++)
  setTo[i] = (rule >> i) & 1;
```

That may look like black magic, but all it's doing is turning a number in the range [0, 255] into a set of rules for the automaton. Here's how that works:

First, convert the number into binary:
Rule 30 = 00011110

Then, go through the 8 possibilies for off/on patterns we discussed earlier. Assign each bit to each pattern in order, treating 0 as off and 1 as on:


| left | me  | right |   bit   |
|------|-----|-------|---------|
| off  | off |  off  | 0 = off |
| off  | off |  on   | 0 = 0ff |
| off  | on  |  off  | 0 = off |
| off  | on  |  on   | 1 = on  |
|  on  | off |  off  | 1 = on  |
|  on  | off |  on   | 1 = on  |
|  on  | on  |  off  | 1 = on  |
|  on  | on  |  on   | 0 = off |


Then, we can interpret the table by finding the row that corresponds to what we currently see and adjusting our lights accordingly. So if our light is on and so is our left neighbor but the right is out, that means we are in the second last row and should keep our light on. If our right neighbor turns their light on though, that puts us in the last row so we should turn our light off. That then means we're in the 6th row, so we should turn it back on (and thus we alternate between the 6th and 8th rows until one of our neighbors turns their light off). Isn't it neat how you get oscillating behavior like that from such a simple set of rules?

In any case, that's about enough from me for the time being. Why don't you try out the demo below? You can choose any of the 256 possible rules with 5 initial conditions I mentioned above or you can try out the interesting cases mentioned in the <a href="http://mathworld.wolfram.com/ElementaryCellularAutomaton.html" title="Wolfram Mathworld: Elementary Cellular Automaton">Wolfram Mathworld</a> article mine is based on.

If you have any questions / comments / suggestions, feel free to drop me a line below.

If you would like to try this in a larger, resizable version, you can do so <a href="http://apps.jverkamp.com/small-projects/cellular/" title="jverkamp apps: Cellular">here</a>.

Have fun!

<a name="thecanvas">
<canvas style="border: 1px solid black;" id="canvas" width="400" height="200"></canvas>
</a>


<table class="table table-striped">
  <tr><td>Rule</td><td><input class="update" id="inputRule" type="text" value="30" /></td><td class="warning" id="inputRuleWarning"></td></tr>
  <tr><td>Scale</td><td><input class="update" id="inputScale" type="text" value="1" /></td><td class="warning" id="inputScaleWarning"></td></tr>
  <tr><td>Initial condition</td>
    <td>
      <select class="update" id="inputInitial">
        <option value="point">Point</option>
        <option value="random">Random</option>
        <option value="5050">50/50 Split</option>
        <option value="black">Black</option>
        <option value="white">White</option>
      </select>
    </td><td></td>
  </tr>
  <tr><td>Interesting rules</td>
  <td>
<select id="inputInteresting">
  <option value=""></option>
  <option value="30">30</option>
  <option value="54">54</option>
  <option value="60">60</option>
  <option value="62">62</option>
  <option value="90">90</option>
  <option value="94">94</option>
  <option value="102">102</option>
  <option value="110">110</option>
  <option value="122">122</option>
  <option value="126">126</option>
  <option value="150">150</option>
  <option value="158">158</option>
  <option value="182">182</option>
  <option value="188">188</option>
  <option value="190">190</option>
  <option value="220">220</option>
  <option value="222">222</option>
  <option value="250">250</option>
</select>
</td><td></td></tr>
</table>

<button id="drawButton">Draw</button> <button id="saveButton">Save</button>

<p style="color: red;" id="warning"></p>

If you'd like, you can download the source here: <a href="https://github.com/jpverkamp/small-projects/blob/master/blog/cellular-automaton.js" title="Cellular automaton source">cellular automaton source code</a>

<script>
jQuery(function($) {
  function div(a, b) {
    return Math.floor(a / b);
  }

  function drawRule(rule, initial, scale) {
    var c = $("#canvas")[0].getContext('2d');
    c.lineWidth = 1;
    c.fillStyle = "black";

    var width = $("#canvas").width();
    var height = $("#canvas").height();

    var scaleWidth = div(width, scale);
    var scaleHeight = div(height, scale);

    c.clearRect(0, 0, width, height);

    var setTo = [0, 0, 0, 0, 0, 0, 0, 0];
    for (var i = 0; i < 8; i++)
      setTo[i] = (rule >> i) & 1;

    var oldRow = new Array(scaleWidth);
    var newRow = new Array(scaleWidth);

    for (var i = 0; i < scaleWidth; i++) {
      if (initial == "random")
        oldRow[i] = (Math.random() > 0.5 ? 1 : 0);
      else if (initial == "5050")
        oldRow[i] = (i < scaleWidth / 2 ? 0 : 1);
      else if (initial == "point")
        oldRow[i] = (i == div(scaleWidth, 2) ? 1 : 0);
      else if (initial == "black")
        oldRow[i] = 1;
      else if (initial == "white")
        oldRow[i] = 0;
      else
        oldRow[i] = 0;

      newRow[i] = 0;
    }

    var index = 0;
    for (var row = 0; row < scaleHeight; row++) {
      for (var col = 0; col < scaleWidth; col++) {
        if (oldRow[col] == 1)
          c.fillRect(col * scale, row * scale, scale, scale);

        index = oldRow[col == 0 ? 0 : col - 1] * 4 + oldRow[col] * 2 + oldRow[col == scaleWidth - 1 ? scaleWidth - 1 : col + 1];
        newRow[col] = setTo[index];
      }

      for (var col = 0; col < scaleWidth; col++) {
        oldRow[col] = newRow[col];
      }
    }
  }

  $(".warning").css("color", "red");

  function doUpdate() {
    $(".warning").empty();

    var rule = parseInt($("#inputRule").val());
    if (isNaN(rule) || rule < 0 || rule > 255) {
      $("#inputRuleWarning").html('Rule must be an integer in the range [0, 255]');
      return;
    }

    var scale = parseInt($("#inputScale").val());
    if (isNaN(scale) || scale < 1 || scale > 10) {
      $("#inputScaleWarning").html('Rule must be an integer in the range [1, 10]');
      return;
    }

    var initial = $("#inputInitial").val();
    drawRule(rule, initial, scale);
  };

  $(".update").change(doUpdate);
  $("#drawButton").click(doUpdate);

  $("#inputInteresting").change(function() {
    if ($("#inputInteresting").val() != "") {
      $("#inputRule").val($("#inputInteresting").val());
      $("#inputInitial").val("point");
      $("#inputInteresting").val("");
      doUpdate();
    }
  });

  doUpdate();

  function doSave() {
    window.open(jQuery("#canvas")[0].toDataURL());
  }
  $("#saveButton").click(doSave);
});
</script>
