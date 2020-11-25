---
title: Backtracking Worm Coral
date: 2020-11-20
programming/topics:
- Cellular Automata
- Generative Art
- Procedural Content
- p5js
programming/languages:
- JavaScript
---
Let's take [yesterday's Worm Coral]{{< ref "03-worm-coral" >}} and turn it up to 11!

Now we have:

* Whenever a worm gets stuck, it will 'backtrack': it will instead expand from the previous position recursively 

That means that the initial 10 worms should always be able to fill the entire world! Even if one closes off an area, that one can eventually fill it up:

{{< figure src="/embeds/2020/backtracking-worm-full.png" >}}

I like how occiasionally you get one spindly bit (usually early in the run) that another goes through. It reminds me of [Blokus](https://boardgamegeek.com/boardgame/2453/blokus) It does take a while.

In addition, I wanted to play a bit with simulationism:

* Worms can potentially `changeColor` each frame
* Every `framesPerGeneration` check if each worm dies `deathChance` or spawns a child worm (`spawnChance`)
* If a worm dies, it is removed from the simulation
* If a worm spawns, it creates a new child at it's current location
  * If `spawnIncludesHistory` is set, the child can backtrack into the parent's history
  * If `spawnVariesColor` is set, the child will (potentially, it's random) have a slightly different color

Let's check it out!

<!--more-->

{{< p5js width="600" height="420" >}}
let gui;
let params = {
  minimumWormCount: 10,
  minimumWormCountMin: 1,
  colorChange: false,
  framesPerGeneration: 10,
  deathChance: 0.0,
  deathChanceMin: 0,
  deathChanceMax: 1,
  deathChanceStep: 0.01,
  spawnChance: 0.0,
  spawnChanceMin: 0,
  spawnChanceMax: 1,
  spawnChanceStep: 0.01,
  spawnIncludesHistory: true,
  spawnVariesColor: false,
};

let visited;
let worms;

class Worm {
  constructor() {
    this.points = [{
      x: int(random(width)),
      y: int(random(height))
    }];

    this.color = color(
      random(256),
      random(256),
      random(256)
    );
    
    this.age = 0;
  }

  update() {
    this.age++;
    
    // Dead point (should be removed)
    if (this.points.length == 0) {
      return;
    }
    
    var oldX = this.points[this.points.length - 1].x;
    var oldY = this.points[this.points.length - 1].y;
    
    // Calculate available points
    var possible = [];
    for (var newX = oldX - 1; newX <= oldX + 1; newX++) {
      for (var newY = oldY - 1; newY <= oldY + 1; newY++) {
        if (newX < 0 || newX >= width || newY < 0 || newY >= height) {
          continue;
        } else if (!visited[newX][newY]) {
          possible.push({x: newX, y: newY});
        }
      }
    }
    
    // If we have none, we are stuck; backtrack and try to move again
    if (possible.length == 0) {
      this.points.pop();
      this.update();
      return;
    }
    
    // Otherwise, move to one of them
    var target = possible[Math.floor(random() * possible.length)];
    this.points.push(target);
    visited[target.x][target.y] = true;
    
    // Update color if requested
    if (params.colorChange) {
      this.color = color(
        red(this.color) + random(-10, 10),
        green(this.color) + random(-10, 10),
        blue(this.color) + random(-10, 10)
      );
    }
  }

  draw() {
    var p = this.points[this.points.length - 1];
    fill(this.color);
    noStroke();
    rect(p.x, p.y, 1, 1);
  }
  
  spawn() {
    var child = new Worm();

    if (params.spawnIncludesHistory) {
      child.points = [...this.points];
    } else {
      child.points = [this.points[this.points.length - 1]];
    }

    if (params.spawnVariesColor) {
      child.color = color(
        red(this.color) + random(-10, 10),
        green(this.color) + random(-10, 10),
        blue(this.color) + random(-10, 10)
      );
    } else {
      child.color = this.color; 
    }
    
    return child;
  }
}

function setup() {
  createCanvas(400, 400);
  gui = createGuiPanel();
  gui.addObject(params);
  gui.setPosition(420, 0);

  background(0);
  reset();
}

function reset() {
  background(0); 

  visited = [];
  for (var x = 0; x < width; x++) {
    visited[x] = [];
    for (var y = 0; y < height; y++) {
      visited[x][y] = false;
    }
  }

  worms = [];
}

function draw() {
  while (worms.length < params.minimumWormCount) {
    worms.push(new Worm());
  }
  
  worms.forEach((worm) => worm.update());
  
  worms = worms.filter((worm) => worm.points.length > 0);
  
  if (frameCount % params.framesPerGeneration == 0) {
    worms = worms.filter((worm) => random() > params.deathChance);
    worms.forEach((worm) => {
      if (random() < params.spawnChance) {
        worms.push(worm.spawn());
      }
    });
  }
  
  worms.forEach((worm) => worm.draw());  
  
  // If all points are visited, stop the simulation
  if (visited.every((row) => row.every((el) => el))) {
    noLoop();
  }
}
{{< /p5js >}}

There are a few particular settings I'm a fan of:

`spawnChance` = 1 is basically a {{< wikipedia "flood fill" >}} and makes something close to a {{< wikipedia "voronoi diagram" >}}. 

{{< figure src="/embeds/2020/backtracking-worm-spawn1.png" >}}

High `spawnChance` with color change is basically beautiful spaghetti:

{{< figure src="/embeds/2020/backtracking-worm-tangle.png" >}}

Setting the `minimumWormCount` to 1 and spawning new, colorful worms is delightlful to look at. You can also tell where they started (bottom left):

{{< figure src="/embeds/2020/backtracking-worm-1parent.png" >}}

Setting `deathChance` = 1 means that each worm goes exactly the `framesPerGeneration` count (unless it gets stuck). Tons of small worms! 

{{< figure src="/embeds/2020/backtracking-worm-immediate-death.png" >}}

And setting both death and spawn is fun to watch, it's like it's grabbing out for you! (I need to figure out how to do gifs). 

{{< figure src="/embeds/2020/backtracking-worm-tendrils.png" >}}

Also, I've added the ability to save/share settings to the `p5js` shortcode I'm writing by way of the {{< wikipedia "URI fragment" >}}. Every time you change a setting, it saves:

```javascript
if (typeof params !== "undefined") {
    for (var el of document.querySelectorAll('input')) {
        if (el.id && el.id.startsWith('qs_')) {
            el.addEventListener('change', () => {
                parent.location.hash = btoa(JSON.stringify(params));
            });
        }
    }
}
```

And whenever you load the page, it loads the fragment (if present):

```javascript
setup = () => {
    // Load saved settings from the browser's hash fragment
    if (parent.location.hash && typeof params !== "undefined") {
        try {
            var settings = JSON.parse(atob(parent.location.hash.substring(1)));
            Object.keys(params).forEach((key) => params[key] = settings[key] || params[key]);
        } catch(ex) {
        }
    }

    oldSetup();

    ...
}
```

It loads first so it runs before the original `setup`, otherwise the settings will be loaded but the GUI will not automatically refresh. 

Pretty cool, no? 