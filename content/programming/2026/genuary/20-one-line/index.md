---
title: "Genuary 2026.20: One line"
date: "2026-01-20"
programming/languages:
- JavaScript
programming/topics:
- Generative Art
- Procedural Content
- p5js
series:
- Genuary 2026
cover: gen26.20.png
---
One line... that repeatedly splits, albeit without (mostly) crossing itself. 

Fractal trees GO!

* `splitChance` controls how quickly the line branches
* `minChildren` / `maxChildren` controls branching
* `angleRange` is how many radians the new branches can change by
* `randomizeAngles` controls if child angles are random/evenly spaced
* `spacing` is roughly how spread out the tree is
* `pauseOnResetFor` / `stopOnReset` controls what happens when a tree is done
* `colorMode` changes drawing colors
* `anchor` changes where the tree starts

It does get a bit sluggish, especially if you have a high number of children. 

<!--more-->

{{<p5js width="600" height="500">}}
const MAX_DEPTH = 12;
const TICKS_PER_FRAME = 10;

let gui;
let params = {
  splitChance: 0.05, splitChanceMin: 0, splitChanceMax: 1, splitChanceStep: 0.01,
  minChildren: 2, minChildrenMin: 1, minChildrenMax: 10,
  maxChildren: 4, maxChildrenMin: 1, maxChildrenMax: 10,
  angleRange: Math.PI / 2, angleRangeMin: 0, angleRangeMax: Math.PI, angleRangeStep: 0.01,
  randomizeAngles: true,
  spacing: 5, spacingMin: 1, spacingMax: 10,
  pauseOnResetFor: 500, pauseOnResetForMin: 0, pauseOnResetForMax: 2000,
  stopOnReset: false,
  colorMode: [
    "black-and-white",
    "inverted",
    "flame",
    "rainbow",
    "random",
    "gradient",
  ],
  anchor: [
    "bottom",
    "bottom-left",
    "center",
    "top",
    "left",
    "random",
  ],
};

let tree;
let lastParams;
let pauseStartTime = null;
let gradientHue1, gradientHue2;

class TreeNode {
  constructor(x, y, angle, parent=null) {
    this.id = TreeNode.nextId ? ++TreeNode.nextId : TreeNode.nextId = 1;

    this.x = x;
    this.y = y;
    this.length = 1; 
    this.angle = angle;
    this.parent = parent;
    this.depth = parent ? parent.depth + 1 : 0;

    this.growing = true;
    this.children = [];
  }

  update() {
    this.children.map((c) => c.update());
    
    if (!this.growing) return;

    // If we would intersect another branch within 'spacing' steps, stop growing
    if (this.willIntersect()) {
      this.growing = false;
      return;
    }
    
    // Keep growing, maybe split
    this.length += 1;

    if (this.length >= params.spacing && random() < params.splitChance) {
      this.growing = false;

      if (this.depth >= MAX_DEPTH) return;
      
      let tip = {
        x: this.x + this.length * cos(this.angle),
        y: this.y + this.length * sin(this.angle),
      };

      if (tip.x < 0 || tip.x > width || tip.y < 0 || tip.y > height) {
        return; // Don't grow new branches outside the canvas
      }

      let childCount = floor(random() * (params.maxChildren - params.minChildren)) + params.minChildren;
      if (childCount < 1) return;

      for (let i = 0; i < childCount; i++) {
        let newAngle = this.angle;

        if (params.randomizeAngles) {
          newAngle = this.angle + random(-params.angleRange / 2, params.angleRange / 2);
        } else if (childCount > 1) {
          newAngle = this.angle - params.angleRange / 2 + i * params.angleRange / (childCount - 1);
        }

        this.children.push(new TreeNode(tip.x, tip.y, newAngle, this));
      }
    }
  }

  draw() {
    this.children.map((c) => c.draw());

    if (params.colorMode === "black-and-white") {
      stroke("white");
    } else if (params.colorMode === "inverted") {
      stroke("black");
    } else if (params.colorMode === "flame") {
      let t = this.depth / MAX_DEPTH;
      let hue = lerp(60, 0, t);
      let lightness = lerp(80, 30, t) + random(-10, 10);
      stroke(hue, 100, lightness);
    } else if (params.colorMode === "rainbow") {
      let hue = (this.depth / MAX_DEPTH) * 360;
      stroke(hue, 100, 50);
    } else if (params.colorMode === "random") {
      stroke(random(360), 100, 50);
    } else if (params.colorMode === "gradient") {
      let t = this.depth / MAX_DEPTH;
      let hue = lerp(gradientHue1, gradientHue2, t);
      stroke(hue, 100, 50);
    }
    
    strokeWeight(1);
    line(
      this.x,
      this.y,
      this.x + this.length * cos(this.angle),
      this.y + this.length * sin(this.angle),
    )
  }

  intersects(other) {
    // Tests if this segment intersects with another segment
    let x1 = this.x;
    let y1 = this.y;
    let x2 = this.x + this.length * cos(this.angle);
    let y2 = this.y + this.length * sin(this.angle);

    let x3 = other.x;
    let y3 = other.y;
    let x4 = other.x + other.length * cos(other.angle);
    let y4 = other.y + other.length * sin(other.angle);

    // Exact endpoint matches are fine
    if ((x1 == x3 && y1 == y3) || (x1 == x4 && y1 == y4) || (x2 == x3 && y2 == y3) || (x2 == x4 && y2 == y4)) {
      return false;
    }

    let denom = (y4 - y3) * (x2 - x1) - (x4 - x3) * (y2 - y1);
    if (denom == 0) {
      return false; // parallel lines
    }

    let ua = ((x4 - x3) * (y1 - y3) - (y4 - y3) * (x1 - x3)) / denom;
    let ub = ((x2 - x1) * (y1 - y3) - (y2 - y1) * (x1 - x3)) / denom;

    return (ua >= 0 && ua <= 1 && ub >= 0 && ub <= 1);
  }

  intersectsAnyOther(other, ignore = null) {
    if (other !== ignore && this.intersects(other)) {
      return true;
    }
    return other.children.some((c) => this.intersectsAnyOther(c, ignore));
  }

  willIntersect() {
    this.length += params.spacing;
    let result = this.intersectsAnyOther(tree, this);
    this.length -= params.spacing;
    return result;
  }
  
  anyGrowing() {
    if (this.growing) return true;
    return this.children.some((c) => c.anyGrowing());
  }
}

function setup() {
  createCanvas(400, 400);
  pixelDensity(1);
  colorMode(HSL, 360, 100, 100);

  gui = createGuiPanel("params");
  gui.addObject(params);
  gui.setPosition(420, 0);

  reset();
}

function reset() {
  let anchorX, anchorY, angle;
  switch (params.anchor) {
    case "bottom":
      anchorX = width / 2;
      anchorY = height;
      angle = -PI / 2;
      break;
    case "bottom-left":
      anchorX = 0;
      anchorY = height;
      angle = -PI / 4;
      break;
    case "center":
      anchorX = width / 2;
      anchorY = height / 2;
      angle = -PI / 2;
      break;
    case "top":
      anchorX = width / 2;
      anchorY = 0;
      angle = PI / 2;
      break;
    case "left":
      anchorX = 0;
      anchorY = height / 2;
      angle = 0;
      break;
    case "random":
      anchorX = random(width);
      anchorY = random(height);
      angle = random(TWO_PI);
      break;
    default:
      anchorX = width / 2;
      anchorY = height;
      angle = -PI / 2;
  }

  tree = new TreeNode(anchorX, anchorY, angle);
  gradientHue1 = random(360);
  gradientHue2 = (gradientHue1 + random(120, 240)) % 360;
}

function draw() {
  if (lastParams == undefined || Object.keys(params).some((k) => params[k] !== lastParams[k])) {
    reset();
    lastParams = { ...params };
  }

  if (params.colorMode === "inverted") {
    background("white");
  } else {
    background("black");
  }
  for (let i = 0; i < TICKS_PER_FRAME; i++) {
    tree.update();
  }
  tree.draw();

  if (!tree.anyGrowing()) {
    if (params.stopOnReset) {
      // Don't reset, just stop
    } else {
      // Pause for pauseOnResetFor milliseconds before resetting
      if (pauseStartTime === null) {
        pauseStartTime = millis();
      }
      if (millis() - pauseStartTime >= params.pauseOnResetFor) {
        reset();
        pauseStartTime = null;
      }
    }
  }
}
{{</p5js>}}

## Examples

### [Hard Angles](?randomizeAngles=false&colorMode=rainbow)

![](hard-angles.png)

### [Streets](?angleRange=3.14&randomizeAngles=false&anchor=center)

![](streets.png)

### [Roots](?maxChildren=2&angleRange=3.14&spacing=10&colorMode=gradient&anchor=top)

![](roots.png)

### [Fireball](?splitChance=1&minChildren=3&maxChildren=5&angleRange=3.14&spacing=10&colorMode=flame&anchor=center)

![](fireball.png)

### [Shattered](?splitChance=0.01&minChildren=1&maxChildren=5&angleRange=3.14&spacing=1)

![](shattered.png)

Or you can [turn maxChildren up to 10](?splitChance=0.01&minChildren=1&maxChildren=10&angleRange=3.14&spacing=1)!

![](shattered-10.png)

### [Fan](?splitChance=0.01&minChildren=4&maxChildren=10&angleRange=0.57&randomizeAngles=false&spacing=1)

![](fan.png)

### [Stained Glass](?splitChance=0.01&minChildren=4&angleRange=3.14&randomizeAngles=false&spacing=1&colorMode=rainbow)

![](stained-glass.png)