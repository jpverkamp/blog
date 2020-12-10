---
title: Worm Coral
date: 2020-11-19
programming/topics:
- Cellular Automata
- Generative Art
- Procedural Content
- p5js
programming/languages:
- JavaScript
---
Today, I'm going to work on using [worms]({{< ref "2020-11-17-worms" >}}) to generate coral, similar to what I did way back when I was [generating omnichromatic images]({{< ref "2015-01-01-generating-omnichromatic-images" >}}). 

{{< figure src="/embeds/2020/worm-coral.png" >}}

In a nutshell:

* Spawn n worms
* On each tick:
  * Each worm tries to randomly move one direction
  * If it cannot, increment that worm's `stuck` counter
  * If it can, restart the `stuck` counter
  * If a worm is `stuck` long enough, kill it off and spawn a new worm

Eventually, we'll fill the entire space with colors that end up looking a bit like coral. I'll probably extend this later, since there are a lot of cool tweaks you can do with this general idea. 

<!--more-->

{{< p5js width="600" height="420" >}}
let gui;
let params = {
  pointCount: 10,
  maxAge: 0,
  maxStuck: 10,
};

let visited;
let points;

function setup() {
  createCanvas(400, 400);
  gui = createGuiPanel();
  gui.addObject(params);
  gui.setPosition(420, 0);

  reset();
}

function reset() {
  clear();
  background(0);
  
  visited = [];
  for (var x = 0; x < width; x++) {
    visited[x] = [];
    for (var y = 0; y < height; y++) {
      visited[x][y] = false;
    }
  }
  
  points = [];
}

function draw() {
  while (points.length < params.pointCount) {
    points.push({
      x: int(random(width)),
      y: int(random(height)),
      c: color(random(256), random(256), random(256)),
      age: 0,
      stuck: 0,
    })
  }

  for (var i = 0; i < points.length; i++) {
    var point = points[i];
    point.age++;
    
    fill(point.c);
    noStroke();
    rect(point.x, point.y, 1, 1);
    
    // Try to move each point
    var newX = point.x + random([-1, 0, 1]);
    var newY = point.y + random([-1, 0, 1]);
    
    if (newX == point.x && newY == point.y) {
      continue;
    } else if (newX < 0 || newX >= width || newY < 0 || newY >= height || visited[newX][newY]) {
      point.stuck++;
    } else {
      point.x = newX;
      point.y = newY;
      visited[newX][newY] = true;
    }
    
    // Remove old points
    if (params.maxAge > 0 && point.age > params.maxAge) {
      points.splice(i, 1);
      i--;
    }

    // Remove 'stuck' points
    if (params.maxStuck > 0 && point.stuck > params.maxStuck) {
      points.splice(i, 1);
      i--;
    }
  }
}
{{< /p5js >}}

Pretty cool!

I've also updated my `p5js` Hugo shortcode with a bit of a neat trick to add the save and clear buttons:

```html
{{ $additionalScript := `
var oldSetup = setup;
setup = () => {
    oldSetup();
    
    createButton("play/pause").mousePressed(() => {
      if (isLooping()) {
        noLoop();
      } else {
        loop();
      }
    });

    createButton("save").mousePressed(() => {
        saveCanvas('photo', 'png')
    });

    createButton("clear").mousePressed(() => {
        if (typeof reset !== 'undefined') {
            reset();
        } else {
            clear();
        }
    });
}
`}}

<iframe 
    width="{{ $width }}" height="{{ $height }}" frameBorder="0"
    srcdoc="{{ $header }}<script>{{ .Inner }}{{ $additionalScript }}</script>{{ $footer }}"
></iframe>
```

So after the script that I'm embedding I will be overwriting the script provided `setup` function with one that can add the buttons:

* `play/pause` will stop the p5js loop or start it again
* `save` will call the built in `saveCanvas` to generate a PNG and export it
* `clear` will call the custom `reset` function if defined (to do additional work, like resetting the worms in this case), the built in `clear` if not

And because I'm modifying the shortcode, this will apply to all previous sketches as well. Woot. 