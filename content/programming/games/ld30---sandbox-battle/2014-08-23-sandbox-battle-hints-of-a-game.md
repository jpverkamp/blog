---
title: 'Ludum Dare 30: Hints of a game'
date: 2014-08-23 12:00:00
programming/languages:
- HTML
- JavaScript
programming/sources:
- Ludum Dare
programming/topics:
- Cellular Automata
- Games
series:
- Ludum Dare 30
---
We're getting there. 18 hours in and I have the first hints of what might actually be a game...

<!--more-->

{{< figure src="/embeds/2014/screenshot.png" >}}

(I'll include a demo at the bottom of the post)

Basically, I went with allowing each box to be controlled individually by the keyboard. There will be some problems with having that many people on the keyboard at once, but we'll deal with that later (if we can).

One additional thing I wanted (and mostly figured out) is somewhat 'loose' controls. Basically, rather than explicitly dealing with moving only when a key is down, we'll accelerate when the key is down, preserving velocity even after  keys are raised. There will be some small amount of friction as well, to make sure that eventually pieces will slow down.

It's actually not too hard to implement a system like this:

First, load in the keybindings from the interface you can see in the screenshot above:

```javascript
// Load key bindings
var loadKeyBindings = function() {
  keys = {};

  console.log('Loading key bindings...');

  $('#controls table').each(function(i, eli) {
    var player = parseInt($(eli).attr('data-player'));

    console.log('loading controls for player ' + player);

    $(eli).find('input').each(function(j, elj) {
      var command = $(elj).attr('name');
      var key = $(elj).val();

      keys[key] = [player, command, false];
    });
  });
};
```

This will put everything into the `key` array, indexed by key name and storing the player it refers to, the direction you are going (one of `left`, `right`, `up`, or `down`), and if that key is currently active (pressed down). If I can, I may add additional key bindings (such as rotation or powerups), otherwise, that's pretty good for the moment.

Next, we'll add a function to tell when keys are active:

```javascript
var onkey = function(event) {
  switch (event.keyCode) {
    case  37: key = 'LEFT'; break;
    case  38: key = 'UP'; break;
    case  39: key = 'RIGHT'; break;
    case  40: key = 'DOWN'; break;
    case  97: key = 'NUM1'; break;
    case  98: key = 'NUM2'; break;
    case  99: key = 'NUM3'; break;
    case 100: key = 'NUM4'; break;
    case 101: key = 'NUM5'; break;
    case 102: key = 'NUM6'; break;
    case 103: key = 'NUM7'; break;
    case 104: key = 'NUM8'; break;
    case 105: key = 'NUM9'; break;
    default: key = String.fromCharCode(event.keyCode).toUpperCase();
  }

  if (key in keys) {
    if (event.type == 'keydown') {
      keys[key][2] = true;
    } else if (event.type == 'keyup') {
      keys[key][2] = false;
    }
  }
};
```

Longer than I wanted, but it correctly deals with both the numpad and arrow keys, which is kind of necessary if you want to support 4 human players all at the same time. Perhaps I'll implement AIs, but until I do, we're going to have to allow for a bunch of players...

Okay, so what do we do with all of this information? Well, just like before, we have a `tick` function:

```javascript
var tick = function(event) {
  $.each(keys, function(i, el) {
    var player = el[0];
    var command = el[1];
    var active = el[2];

    $game = $('#tiles');
    $tile = $('#tiles *[data-player="' + player + '"]');

    // Update velocity
    ...

    // Use friction to slow each box down over time
    ...

    // Cap velocity so we don't go too fast
    ...

    // Update the current position based on velocity
    ...

    // Bounce off the edges of the screen
    ...

    // Finally, update the position
    $tile.css({'top': top, 'left': left});
  });

  if (running) {
    setTimeout(tick, 1000/30);
  }
};
```

Oof. That's a heck of a function. Luckily, the individual parts aren't *that* bad. First, we want to update the velocity. This is where the `active` parameter (the third in each key definition) comes into play:

```javascript
// Update velocity
if (active) {
  if (command == 'up') {
    vel[player][1] -= PER_TICK_ACCELERATION;
  } else if (command == 'down') {
    vel[player][1] += PER_TICK_ACCELERATION;
  } else if (command == 'left') {
    vel[player][0] -= PER_TICK_ACCELERATION;
  } else if (command == 'right') {
    vel[player][0] += PER_TICK_ACCELERATION;
  }
}
```

That's simple enough. As before, we have to decide that `up` and `down` are inverted (they almost always are when it comes to computers), but once you've decided that's easy enough.

Now, outside of that black, the next thing we'll do is apply friction. This way the boxes will slow down over time, forcing players both to pay attention and to let them bounce around like madmen.

```javascript
// Use friction to slow each box down over time
// If we're close enough to zero that friction will accelerate us, just stop
if (Math.abs(vel[player][0]) < PER_TICK_FRICTION) {
  vel[player][0] = 0;
} else {
  vel[player][0] += (vel[player][0] > 0 ? -PER_TICK_FRICTION : PER_TICK_FRICTION);
}

if (Math.abs(vel[player][1]) < PER_TICK_FRICTION) {
  vel[player][1] = 0;
} else {
  vel[player][1] += (vel[player][1] > 0 ? -PER_TICK_FRICTION : PER_TICK_FRICTION);
}

// Cap velcity so we don't go too fast
vel[player][0] = Math.min(VELOCITY_CAP, Math.max(-VELOCITY_CAP, vel[player][0]));
vel[player][1] = Math.min(VELOCITY_CAP, Math.max(-VELOCITY_CAP, vel[player][1]));
```

Also at the end there, we make sure we don't keep accelerating indefinitely. That both helps keep the game a little easier to play and prevents edge cases (such as moving further in one tick than we're allowed).

Next, we can finally update the position:

```javascript
// Update the current position based on velocity
var left = $tile[0].offsetLeft + vel[player][0];
var top = $tile[0].offsetTop + vel[player][1];

// Bounce off the edges of the screen
if (left < 0) {
  left = 0;
  vel[player][0] = Math.abs(vel[player][0]);
} else if (left > $game.width() - $tile.width()) {
  left = $game.width() - $tile.width();
  vel[player][0] = -1 * Math.abs(vel[player][0]);
}

if (top < 0) {
  top = 0;
  vel[player][1] = Math.abs(vel[player][1]);
} else if (top > $game.height() - $tile.height()) {
  top =  $game.height() - $tile.height();
  vel[player][1] = -1 * Math.abs(vel[player][1]);
}
```

Once again, we want to clip the positions. This time though, we're actually going to use the velocities we have rather than zeroing them out. Instead: bounce! It's nice, because it makes the game feel more 'realistic' (for some definitions of the word).

And that's about it. With that, we can have the boxes moving around and interacting as they did last night. We're actually starting to get a game going here. One other tweak is the control code:

```javascript
var tiles = new Tiles();
var controls = new Controls();

var MS_PER_GAME = 60 * 1000;
var startTime = new Date().getTime();
var running = true;

$(function() {
  controls.run();
});

function tick() {
  var soFar = new Date().getTime() - startTime;
  var remainingSec = Math.floor((MS_PER_GAME - soFar) / 1000);

  if (remainingSec > 0) {
    $('#tiles #countdown').text(remainingSec + ' sec remaining');
  } else {
    stop();
  }

  if (running) {
    setTimeout(tick, 1000/30);
  }
}

function run() {
  tiles.run();
  controls.run();

  startTime = new Date().getTime();
  running = true;
  tick();

  return false;
}

function stop() {
  tiles.stop();
  controls.stop();

  startTime = new Date().getTime() - MS_PER_GAME;
  running = false;
  $('#tiles #countdown').text('game over');

  return false;
}
```

Technically, it's not a gameloop, since everything is done asynchronously via `setTimeout` (and make **absolutely sure** that you don't use `setInterval`...), but it's close enough. What this does give us though is a strict time before the game ends. Otherwise, the boxes will eventually fill up, and where's the fun in that? (Although that might be an interesting alternative end condition).

After that, all I have to figure out is scoring. And I have another 6 hours until the one day mark. If I can make it by then, I'll feel pretty good--and can use all of the rest of the time for polish. I'm thinking some simple music, sound effects, a title screen (initial letters in sand?). Of course, I still have to figure out the scoring algorithm..

Same as yesterday, the entire source (warning: still ugly) if available on GitHub: <a href="https://github.com/jpverkamp/sandbox-battle">jpverkamp/sandbox-battle</a>

* * *

Demo:

<style>
#controls table {
  border: 1px solid black;
  display: inline-block;
  margin: 1em;
  padding: 0.5em;
  border-radius: 0.5em;

}

#controls table td {
  padding: 0.1em;
}

#controls table td:first-child {
  text-align: right;
}

#controls table input {
  width: 50px;
  text-align: center;
}

#tiles {
  position: relative;
  width: 600px;
  height: 400px;
  background: black;
  border: 1px solid black;
}

#tiles canvas {
  position: absolute;
  border: 1px solid black;
}

#tiles canvas[data-player="0"] { border: 1px solid blue; }
#tiles canvas[data-player="1"] { border: 1px solid red; }
#tiles canvas[data-player="2"] { border: 1px solid green; }
#tiles canvas[data-player="3"] { border: 1px solid hotPink; }

#tiles #countdown {
  color: white;
}
</style>

<script>
function Tiles() {
  var running = false;
  var allData = {};
  var ordering = [];

  // Assign an index to each canvas so we can order them
  $('canvas').each(function(index, canvas) {
     $(canvas).attr('data-index', index);
  });

  // Keep a list of the current z-ordering of the canvases
  $('canvas').each(function(i) { ordering.push(i); });

  // Make them draggable, on drag udate the index
  $('canvas').draggable({
      stack: '*',
      drag: function(event, ui) {

      },
      stop: function(event, ui) {
          var i = parseInt($(event.target).attr('data-index'));
          var index = ordering.indexOf(i);
          ordering.splice(index, 1);
          ordering.unshift(i);
      }
  });

  // Make a 2D array initialized all to a given valu
  var make2DArray = function(width, height, def) {
      var array = new Array(width);
      for (var x = 0; x < width; x++) {
          array[x] = new Array(height);
          for (var y = 0; y < height; y++) {
              array[x][y] = def;
          }
      }
      return array;
  }

  // Update the given grid
  var update = function(data, buffer, width, height) {
      // Clear the buffer
      for (var x = 0; x < width; x++) {
          for (var y = 0; y < height; y++) {
              buffer[x][y] = 0;
          }
      }

      // Update the buffer with falling cells
      var r = 0, xt = 0, yt = 0;
      for (var y = height - 1; y >= 0; y--) {
          for (var x = 0; x < width; x++) {
              // Skip empty cells
              if (data[x][y] == 0) continue;
              xt = x;
              yt = y;

              // Determine which way it's going to fall
              r = Math.random();
              if (r < 0.5) { // Straight down
                  if (y > 0 && buffer[x][y - 1] == 0) { xt = x; yt = y - 1; }
              } else if (r < 0.7) { // Down left
                  if (x > 0 && y > 0 && buffer[x - 1][y - 1] == 0) { xt = x - 1; yt = y - 1; }
              } else if (r < 0.9) { // Down right
                  if (x < width - 1 && y > 1 && buffer[x + 1][y - 1] == 0) { xt = x + 1; yt = y - 1; }
              } else if (r < 0.95) { // Straight left
                  if (x > 0 && buffer[x - 1][y] == 0) { xt = x - 1; yt = y; }
              } else { // Straight right
                  if (x < width - 1 && buffer[x + 1][y] == 0) { xt = x + 1; yt = y; }
              }

              if (data[xt][yt] != 0) { xt = x; yt = y; }

              // Update the buffer
              buffer[xt][yt] = data[x][y];
          }
      }
  }

  // Animate a given frame
  var animate = function(frameIndex, frame) {
      var start = new Date().getTime();

      var frame_ctx = frame.getContext('2d');
      frame_ctx.imageSmoothingEnabled = false;

      var width = frame.width;
      var height = frame.height;

      var data = make2DArray(width, height, 0);
      var buffer = make2DArray(width, height, 0);
      var temp;
      var i = 0, r = 0, g = 0, b = 0, a = 0;

      allData[frameIndex] = data;
      var imageData = frame_ctx.createImageData(width, height);

      var tick = function() {
          // Debug: For add a pixel
          data[width / 2][height - 1] = frameIndex + 1;

          // Update from data to buffer; swap the arrays for the next iteration
          update(data, buffer, width, height);
          temp = data;
          data = buffer;
          buffer = temp;

          // Detect overlapping buffers, if so swap randomly
          $('canvas').each(function(otherIndex, other) {
              // If we're comparing to ourself, we'll always overlap, skip
              if (frame == other) return;

              // If the two canvases don't overlap, don't look at them
              var frameBounds = frame.getBoundingClientRect();
              var otherBounds = other.getBoundingClientRect();
              if (frameBounds.right < otherBounds.left ||
                  frameBounds.left > otherBounds.right ||
                  frameBounds.bottom < otherBounds.top ||
                  frameBounds.top > otherBounds.bottom) {
                  return;
              }

              // We only want this once, so give priority to whichever frame is 'lower' on the screen
              if (frameBounds.top < otherBounds.top) return;

              // Bail out if we haven't loaded the data yet
              if (!(frameIndex in allData && otherIndex in allData)) {
                return;
              }

              // TODO: Find the actual offset rather than looping over an entire image
              var otherX, otherY, temp;
              for (var frameY = 0; frameY < height; frameY++) {
                  for (var frameX = 0; frameX < width; frameX++) {
                      otherX = Math.floor(frameBounds.left - otherBounds.left + frameX);
                      otherY = Math.floor(otherBounds.top - frameBounds.top + frameY);

                      if (0 <= otherX && otherX < width && 0 <= otherY && otherY < height) {
                          if (allData[frameIndex][frameX][frameY] == 0
                              /* && allData[otherIndex][otherX][otherY] != 0*/) {
                              temp = allData[frameIndex][frameX][frameY];
                              allData[frameIndex][frameX][frameY] = allData[otherIndex][otherX][otherY];
                              allData[otherIndex][otherX][otherY] = temp;
                          }
                      }
                  }
              }
          });

          // Render to the image data
          for (var y = 0; y < height; y++) {
              for (var x = 0; x < width; x++) {
                  i = x + (height - y) * width;

                  r = g = b = 0;
                  a = 255;

                  if (data[x][y] == 0) {
                    a = 0;
                  } else if (data[x][y] == 1) {
                    b = 255;
                  } else if (data[x][y] == 2) {
                    r = 255;
                  } else if (data[x][y] == 3) {
                    g = 255;
                  } else if (data[x][y] == 4) {
                    r = 246;
                    g = 96;
                    b = 171;
                  }

                  imageData.data[i * 4 + 0] = r;
                  imageData.data[i * 4 + 1] = g;
                  imageData.data[i * 4 + 2] = b;
                  imageData.data[i * 4 + 3] = a;
              }
          }

          // Copy back to the GUI
          frame_ctx.putImageData(imageData, 0, 0);

          if (running) {
              setTimeout(tick, 1000/60);
          }
      }
      tick();
  };

  this.run = function() {
    running = true;
    $('canvas').each(animate);
  };

  this.stop = function() {
    running = false;
  };
};

function Controls() {
  var keys = {};
  var running = false;
  var PER_TICK_ACCELERATION = 0.1;
  var PER_TICK_FRICTION = 0.01;
  var VELOCITY_CAP = 10;

  var vel = {};

  // Load key bindings
  var loadKeyBindings = function() {
    keys = {};

    console.log('Loading key bindings...');

    $('#controls table').each(function(i, eli) {
      var player = parseInt($(eli).attr('data-player'));

      console.log('loading controls for player ' + player);

      $(eli).find('input').each(function(j, elj) {
        var command = $(elj).attr('name');
        var key = $(elj).val();

        keys[key] = [player, command, false];
      });
    });
  };

  var onkey = function(event) {
    switch (event.keyCode) {
      case  37: key = 'LEFT'; break;
      case  38: key = 'UP'; break;
      case  39: key = 'RIGHT'; break;
      case  40: key = 'DOWN'; break;
      case  97: key = 'NUM1'; break;
      case  98: key = 'NUM2'; break;
      case  99: key = 'NUM3'; break;
      case 100: key = 'NUM4'; break;
      case 101: key = 'NUM5'; break;
      case 102: key = 'NUM6'; break;
      case 103: key = 'NUM7'; break;
      case 104: key = 'NUM8'; break;
      case 105: key = 'NUM9'; break;
      default: key = String.fromCharCode(event.keyCode).toUpperCase();
    }

    if (key in keys) {
      if (event.type == 'keydown') {
        keys[key][2] = true;
      } else if (event.type == 'keyup') {
        keys[key][2] = false;
      }
    }
  };

  var tick = function(event) {
    $.each(keys, function(i, el) {
      var player = el[0];
      var command = el[1];
      var active = el[2];

      $game = $('#tiles');
      $tile = $('#tiles *[data-player="' + player + '"]');

      // Update velocity
      if (active) {
        if (command == 'up') {
          vel[player][1] -= PER_TICK_ACCELERATION;
        } else if (command == 'down') {
          vel[player][1] += PER_TICK_ACCELERATION;
        } else if (command == 'left') {
          vel[player][0] -= PER_TICK_ACCELERATION;
        } else if (command == 'right') {
          vel[player][0] += PER_TICK_ACCELERATION;
        }
      }

      // Use friction to slow each box down over time
      // If we're close enough to zero that friction will accelerate us, just stop
      if (Math.abs(vel[player][0]) < PER_TICK_FRICTION) {
        vel[player][0] = 0;
      } else {
        vel[player][0] += (vel[player][0] > 0 ? -PER_TICK_FRICTION : PER_TICK_FRICTION);
      }

      if (Math.abs(vel[player][1]) < PER_TICK_FRICTION) {
        vel[player][1] = 0;
      } else {
        vel[player][1] += (vel[player][1] > 0 ? -PER_TICK_FRICTION : PER_TICK_FRICTION);
      }

      // Cap velocity so we don't go too fast
      vel[player][0] = Math.min(VELOCITY_CAP, Math.max(-VELOCITY_CAP, vel[player][0]));
      vel[player][1] = Math.min(VELOCITY_CAP, Math.max(-VELOCITY_CAP, vel[player][1]));

      // Update the current position based on velocity
      var left = $tile[0].offsetLeft + vel[player][0];
      var top = $tile[0].offsetTop + vel[player][1];

      // Bounce off the edges of the screen
      if (left < 0) {
        left = 0;
        vel[player][0] = Math.abs(vel[player][0]);
      } else if (left > $game.width() - $tile.width()) {
        left = $game.width() - $tile.width();
        vel[player][0] = -1 * Math.abs(vel[player][0]);
      }

      if (top < 0) {
        top = 0;
        vel[player][1] = Math.abs(vel[player][1]);
      } else if (top > $game.height() - $tile.height()) {
        top =  $game.height() - $tile.height();
        vel[player][1] = -1 * Math.abs(vel[player][1]);
      }

      // Finally, update the position
      $tile.css({'top': top, 'left': left});
    });

    if (running) {
      setTimeout(tick, 1000/30);
    }
  };

  this.run = function() {
    // Reload keybindings in case they've changed
    loadKeyBindings();

    // Initialize velocities to zero
    $game = $('#tiles');
    $('#tiles canvas').each(function(i, eli) {
      vel[i] = [0, 0];
      $(eli).css({
        top: Math.random() * ($game.height() - $(eli).height()),
        left: Math.random() * ($game.width() - $(eli).width())
      });
    });

    // Add keybindings, we can use the same function since it can check type
    $(document).unbind('keydown').bind('keydown', onkey);
    $(document).unbind('keyup').bind('keyup', onkey);

    running = true;
    tick();
  }

  this.stop = function() {
    running = false;

    $(document).unbind('keydown');
    $(document).unbind('keyup');
  }
};

var tiles = new Tiles();
var controls = new Controls();

var MS_PER_GAME = 60 * 1000;
var startTime = new Date().getTime();
var running = true;

$(function() {
  controls.run();
});

function tick() {
  var soFar = new Date().getTime() - startTime;
  var remainingSec = Math.floor((MS_PER_GAME - soFar) / 1000);

  if (remainingSec > 0) {
    $('#tiles #countdown').text(remainingSec + ' sec remaining');
  } else {
    stop();
  }

  if (running) {
    setTimeout(tick, 1000/30);
  }
}

function run() {
  tiles.run();
  controls.run();

  startTime = new Date().getTime();
  running = true;
  tick();

  return false;
}

function stop() {
  tiles.stop();
  controls.stop();

  startTime = new Date().getTime() - MS_PER_GAME;
  running = false;
  $('#tiles #countdown').text('game over');

  return false;
}
</script>



| Player 1 - Blue |   |
|-----------------|---|
|       Up        |   |
|      Left       |   |
|      Right      |   |
|      Down       |   |



| Player 2 - Red |   |
|----------------|---|
|       Up       |   |
|      Left      |   |
|     Right      |   |
|      Down      |   |



| Player 3 - Green |   |
|------------------|---|
|        Up        |   |
|       Left       |   |
|      Right       |   |
|       Down       |   |



| Player 4 - Pink |   |
|-----------------|---|
|       Up        |   |
|      Left       |   |
|      Right      |   |
|      Down       |   |




  [ <a href="javascript:run()">Run!</a> ]
  [ <a href="javascript:stop()">Stop!</a> ]



  <div id="tiles">
    <p id="countdown"></p>
    <canvas data-player="0" width="100" height="100"></canvas>
    <canvas data-player="1" width="100" height="100"></canvas>
    <canvas data-player="2" width="100" height="100"></canvas>
    <canvas data-player="3" width="100" height="100"></canvas>
  
</div>

* * *

I'm sure there are bugs... And I'm working on it right at the moment. If you have any questions or comments though, feel free to drop me a line below.
