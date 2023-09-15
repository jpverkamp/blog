---
title: 'Ludum Dare 30: Sandbox Battle'
date: 2014-08-22 23:00:00
programming/languages:
- HTML
- JavaScript
programming/sources:
- Ludum Dare
programming/topics:
- Cellular Automata
- Games
- Falling Sand
series:
- Ludum Dare 30
---
And here we are again. [Ludum Dare]({{< ref "2013-05-21-ludum-dare-26-vtanks-results.md" >}}). Taken directly from their about page...

> Ludum Dare is a regular accelerated game development Event.  Participants develop games from scratch in a weekend, based on a theme suggested by community.

More specifically, the goal is to make a game from scratch in 48 hours. You're allowed to use publicly available frameworks and code libraries, but no art or other assets. Previously, I missed the original start time. So although I made my game in 48 hours, it didn't qualify. This time around, I'm starting on time.

<!--more-->

The theme this time is <a href="http://www.ludumdare.com/compo/2014/08/16/ludum-dare-30-theme-voting-begins/">Connected Worlds</a>. I like that a lot more than many of the previous themes, so let's see what ideas we can come up with.

Taking about an hour at the start of the compo to both work out and think, I ended up basically going in two directions:


* A [[wiki:falling sand]]() style game, only with discrete 'bubbles' with different particles / physics
* A [[wiki:puzzle platformer|Platform_game#Puzzle_platformers]]() based around portals that split you into two realities you play at the same time


Of the two, the second has the advantages of 1) actually sounding like a game (that's always been my problem with falling sand style simulations) and 2) being much easier to code. I've worked on falling sand style games before ([Sandbox]({{< ref "2010-02-06-sandbox-it-s-alive.md" >}})) and they take a lot of tuning to get reasonable performance. Certainly worth doing... but not the best idea for a 48 hour time window.

So of course I'm going with option A. :smile:

About 6 hours in, and so far this is what I have:

{{< figure src="/embeds/2014/screenshot.png" >}}

* * *

Real-life demo! (Click run, then try dragging the boxes around)

<canvas id="frame1" width="100" height="100"></canvas>
<canvas id="frame2" width="100" height="100"></canvas>
<canvas id="frame3" width="100" height="100"></canvas>

<button id="runGame" type="button">Run!</button>

<style>
canvas { border: 1px solid black; }
</style>

<script>
$(function() {
  var maxFrames = 10000;

  // Assign an index to each canvas so we can order them
  $('canvas').each(function(index, canvas) {
     $(canvas).attr('data-index', index);
  });

  // Keep a list of the current z-ordering of the canvases
  var ordering = [];
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

  var allData = {};

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

      var count = 0;
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

              /*
              // We only want to run this once, so only for the frame on top
              // If we see the frame first, we're golden (break out of the loop)
              // If we see the other first, we're in the wrong order (stop processing)
              for (var i = 0; i < ordering.length; i++) {
                  if (ordering[i] == frameIndex) break;
                  if (ordering[i] == otherIndex) return;
              }
              */

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
                  }

                  imageData.data[i * 4 + 0] = r;
                  imageData.data[i * 4 + 1] = g;
                  imageData.data[i * 4 + 2] = b;
                  imageData.data[i * 4 + 3] = a;
              }
          }

          // Copy back to the GUI
          frame_ctx.putImageData(imageData, 0, 0);

          if (count < maxFrames) {
              count += 1;
              setTimeout(tick, 0);
          } else {
              end = new Date().getTime();
              console.log(
                  maxFrames + ' frames in ' +
                  (end - start) + ' ms = ' +
                  (maxFrames / ((end - start) / 1000)) + ' fps'
              );
          }
      }
      tick();
  }

  $('#runGame').click(function() {
    console.log('starting...');
    $('canvas').each(animate);
  });
});
</script>

You can click and drag the blocks around and the sand will from from box to box. At first, I was trying to figure out goals where you could--for example--use water in one box to put out fire in another. But right at the end, I had an even better idea (hopefully not just the long day talking): SANDBOX BATTLE! Basically, some sort of multiplayer / AI madness, where you are trying to steal the other box's sand before they can steal yours... I'm going to have to think about that...

Anyways, here are some of the interesting bits (in JavaScript for once!):

First, the core of the whole thing, the update function:

```javascript
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
```

The basic idea is two have two data arrays: `data` and `buffer`. We will trust the rest of the code to swap them the other way and spend all of the effort in this function creating buffer as the next frame. Specifically, we're going to loop through all of the tiles from bottom to top (because sand falls) then left to right. For each particle (non-`0` space), there are five possibilities:


* 50% chance of trying to move directly down
* 20% chance of trying to move down and left, 20% down and right
* 5% chance each of moving directly left or right


Sounds pretty good. It's the same sort of code I've written rather a lot of times... This time around, we're not going to do any optimizations. We'll deal with that later if we have time.

Next, we have to deal with the `tick` function:

```javascript
var tick = function() {
    // Debug: Add a pixel
    data[width / 2][height - 1] = frameIndex + 1;

    // Update from data to buffer; swap the arrays for the next iteration
    update(data, buffer, width, height);
    temp = data;
    data = buffer;
    buffer = temp;

    // Detect overlapping buffers, if so swap randomly
    ...

    // Render to the image data
    ...
}
```

So we start with pixels dumping in from the ceiling and we update the world. We have space for two more functions: copying between worlds (pretty much the core idea of the game :smile:) and rendering. Let's look at the latter first.

In order to render quickly, I'm going to use the `canvas` element's context's `createImageData` and `putImageData` to write data directly into the image. That will be a lot faster than setting pixels individually, especially since we're going to be changing rather a lot of pixels at the indiviual level. So... rendering:

```javascript
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
        }

        imageData.data[i * 4 + 0] = r;
        imageData.data[i * 4 + 1] = g;
        imageData.data[i * 4 + 2] = b;
        imageData.data[i * 4 + 3] = a;

    }
}

// Copy back to the GUI
frame_ctx.putImageData(imageData, 0, 0);
```

We've previously set up `imageData` using `createImageData` (we only have to do this once and then can reuse that same memory) and the `frame_ctx` as the context object of the canvas.

One interesting part that I changed right before this writeup was the transparency of empty cells. That way the page will shine through. I'm not entirely sure that's what I want, but it's an interesting effect, so I'll leave it for the time being.

And then last but not least, the combination function. This one is honestly kind of weird:

```javascript
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

    // TODO: Find the actual offset rather than looping over an entire image
    var otherX, otherY, temp;
    for (var frameY = 0; frameY < height; frameY++) {
        for (var frameX = 0; frameX < width; frameX++) {
            otherX = frameBounds.left - otherBounds.left + frameX;
            otherY = otherBounds.top - frameBounds.top + frameY;

            if (0 <= otherX && otherX < width && 0 <= otherY && otherY < height) {
                if (allData[frameIndex][frameX][frameY] == 0 ) {
                    temp = allData[frameIndex][frameX][frameY];
                    allData[frameIndex][frameX][frameY] = allData[otherIndex][otherX][otherY];
                    allData[otherIndex][otherX][otherY] = temp;
                }
            }
        }
    }
});
```

Theoretically the comments should be enough, but if not, the basic idea is to first find if we have two overlapping regions (the `frameIndex` and `otherIndex` will make more sense if you look at the full code). If you have one, then loop over the shared region and copy pixels to the lower of the two boxes. I'm going to have to figure out a better rule for that. I tried using z-index, but that didn't work much better... Essentially, we need to be able to move particles from one box to another, but we need to be careful to neither lose nor duplicate particles. There are a number of weird edges cases (as I'm sure you've found if you played with the simulation).

And, that's it. I have until 5pm Pacific on Sunday. I'm actually feeling pretty good about this. The best plan is to have a playable game after 24 hours and to spend the second day on polish. I'm not sure if I'll quite hit that... but maybe!

If you'd like to see the entire source (warning: ugly) and potentially spoilers, check it out here: <a href="https://github.com/jpverkamp/sandbox-battle">jpverkamp/sandbox-battle</a>
