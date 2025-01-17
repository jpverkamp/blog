---
title: 'Ludum Dare 30: Programmer art and simple AI'
date: 2014-08-23 23:00:00
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
- Ludum Dare 
- Ludum Dare 30
---
A few hours later and we've already finished (or at least made good progress on) two of the goals that I was hoping for:


* AI players; at the very least one that moves randomly, but optimally several different kinds
* Pending the previous, a selector on the options screen that can turn each player either off, on, or to any of the current AIs
* Stylings around the page; probably some sort of thick border that bleeds a little in and out, looking different per player


<!--more-->

More specifically, here's how you can change the AIs:

{{< figure src="/embeds/2014/choose-ai.png" >}}

Those are the three AIs currently implemented. I've tied them into the same framework as the player movement. It's a bit hacky and could be in its own file, but for a 48 hour game, it works well enough.

The first, the `Wiggle`, is straight forward:

```javascript
// Randomly wiggle about, changing directions no slower than every second
case 'wiggle':
  ai['nextWiggle'] = ai['nextWiggle'] || new Date().getTime() + 1000 * Math.random();
  ai['xAccel'] = ai['xAccel'] || 0;
  ai['yAccel'] = ai['yAccel'] || 0;

  if (new Date().getTime() > ai['nextWiggle']) {
    ai['xAccel'] = (Math.floor(Math.random() * 3) - 1) * PER_TICK_ACCELERATION;
    ai['yAccel'] = (Math.floor(Math.random() * 3) - 1) * PER_TICK_ACCELERATION;

    ai['nextWiggle'] = new Date().getTime() + 1000 * Math.random();
  }

  vel[player][0] += ai['xAccel'];
  vel[player][1] += ai['yAccel'];

  break;
```

The other two (`Chicken` and `Shark`) are actually really similar. Enough so that they share almost all of their code. The only difference is that the former runs from the closest neighbor while the latter chases it. It's a bit of math, but it runs great:

```javascript
case 'chicken': // Run away from the nearest other tile
case 'shark':   // Run towards the nearest other tile
  $me = $('#tiles *[data-player="' + player + '"]');
  var myCenterX = $me.offset().left + $me.width() / 2;
  var myCenterY = $me.offset().top + $me.height() / 2;

  // Find the closest target
  var otherCenterX, otherCenterY, distance;
  var minimumDistance = +Infinity, $target;
  $('#tiles *[data-player]').each(function(otherPlayer, other) {
    $other = $(other);

    var otherCenterX = $other.offset().left + $other.width() / 2;
    var otherCenterY = $other.offset().top + $other.height() / 2;

    distance = (
      (myCenterX - otherCenterX) * (myCenterX - otherCenterX) +
      (myCenterY - otherCenterY) * (myCenterY - otherCenterY)
    );

    if (distance > 0 && distance < minimumDistance) {
      minimumDistance = distance;
      $target = $other;
    }
  });

  // Calculate the direction to that target
  var targetCenterX = $target.offset().left + $target.width() / 2;
  var targetCenterY = $target.offset().top + $target.height() / 2;

  // Get the length and normalized direciton
  var length = Math.sqrt(
    (targetCenterX - myCenterX) * (targetCenterX - myCenterX) +
    (targetCenterY - myCenterY) * (targetCenterY - myCenterY)
  );

  var directionX = (targetCenterX - myCenterX) / length;
  var directionY = (targetCenterY - myCenterY) / length;

  // If we're the chicken, invert that and run away rather than towards
  // Sharks also move away, once they've come in for the kill
  if (ai['type'] == 'chicken' || distance < 25) {
    directionX *= -1;
    directionY *= -1;
  }

  // Apply a force in that direction
  // Sharks and chickens accelerate more slowly or they'll stay right on the player
  vel[player][0] += directionX * PER_TICK_ACCELERATION * (Math.random() / 2 + 0.5);
  vel[player][1] += directionY * PER_TICK_ACCELERATION * (Math.random() / 2 + 0.5);

  break;
```

Shiny.

Up to date code: <a href="https://github.com/jpverkamp/sandbox-battle">jpverkamp/sandbox-battle</a>

Current demo:

{{< iframe height="440" width="660" src="/embeds/2014/demo.embed.htm" >}}
