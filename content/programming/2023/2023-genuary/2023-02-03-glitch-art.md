---
title: "Genuary 2023.03: Glitch art"
date: 2023-02-03
draft: True
programming/languages:
- JavaScript
programming/topics:
- Generative Art
- Procedural Content
- Colors
- HSL Color Space
- p5js
series:
- Genuary 2023
---
[Genuary](https://genuary.art/)! 

Spend a month making one beautiful thing per day, given a bunch of prompts. A month late, but as they say, 'the second best time is now'.  

Let's do it!

## 3) Glitch Art

<!--more-->

Wikipedia: {{<wikipedia "Glitch Art">}}

This one took longer than I'd like to admit. The basic idea is that I want to take a region of the image, split into into red/green/blue channels and then offset the red left and the blue right. 

That's harder than I expected. I went through a bunch of direct `loadPixels` manipulation and a bunch of `tint` exploration, before realizing that it's easier than I was making it. Literally use the `blendMode(DIFFERENCE)` to remove the red, then `blendMode(ADD)` to put the red back. 

Good times. 

Note: this relies on https://picsum.photos/ so may take a moment to load. 

{{<p5js width="400" height="420">}}
let original;

function index(x, y, w, h, c) {
  return constrain(
    parseInt((y * w + x) * 4 + c),
    0,
    w * h * 4
  );
}

function preload() {
  console.log('Loading...');
  original = loadImage("https://picsum.photos/400");
  console.log("done");
}

function setup() {
  createCanvas(400, 400);
  frameRate(2);
  image(original, 0, 0);
}

function draw() {
  original.loadPixels();
  
  let maxOffset = 40;
  
  let x, y, w, h, offset;
  
  while (true) {
    let x1 = random(maxOffset, width - maxOffset);
    let x2 = random(maxOffset, width - maxOffset);
    let y1 = random(0, height);
    let y2 = random(0, height);

    x = min(x1, x2);
    w = max(x1, x2) - x;

    y = min(y1, y2);
    h = max(y1, y2) - y;

    offset = random(10, maxOffset);
  
    if (offset < w / 4) break;
  }
  
  let slice = original.get(x, y, w, h);
  
  // Remove red
  blendMode(DIFFERENCE);
  noStroke(); 
  fill(255, 0, 0, 255);
  rect(x - offset, y, w, h);
  
  // Add offset red
  blendMode(ADD);
  tint(255, 0, 0, 255);
  image(slice, x - offset, y);
  
  // Remove blue
  blendMode(DIFFERENCE);
  noStroke(); 
  fill(0, 0, 255, 255);
  rect(x + offset, y, w, h);
  
  // Add offset blue
  blendMode(ADD);
  tint(0, 0, 255, 255);
  image(slice, x + offset, y);
}
{{</p5js>}}

## 4) Intersections

This actually came about a lot from the previous one. I was working with `blendMode` and found that `ADD` is a good way to draw intersections. So we have:

{{<p5js width="400" height="420">}}
function setup() {
  createCanvas(400, 400);
  rectMode(CENTER);
  noStroke();
}

function draw() {
  push();
  {
    blendMode(ADD);
    translate(200, 200);
    rotate(TWO_PI / random(360));
    scale(random(100) / 100.0 - 0.5);

    fill(
      random(255),
      random(255),
      random(255),
    )
    rect(0, 0, 400, 400);
  }
  pop();
}
{{</p5js>}}

## 5) Debug view

I like {{<wikipedia "Boids">}}. Here are some Boids with debug vectors drawn showing the three forces acting on them (red to stay away from one another, green to move in the same direction as their friends, blue to move towards the center of their friends). 

Use the 'toggle clear' button to clear the screen between each frames to see the simulation versus not to get some twisty spaghetti 'art'. :smile:

Also, the forces for each are randomized each time. Click 'reload' to get new random values. 

{{<p5js width="400" height="420">}}
let BOID_COUNT = 100;
let MAX_SPEED = 3.0;

let VISION_DISTANCE = 50.0;

let NOISE_FORCE = 1.0;
let WALL_AVOIDANCE_FORCE = 1.0;
let SEPARATION_FORCE = 1.0;
let ALIGNMENT_FORCE = 1.0;
let COHESION_FORCE = 1.0;

let DRAW_BACKGROUND = false;
let boids;

class Boid {
  constructor(p) {
    this.position = p || createVector(
      VISION_DISTANCE + random(width - VISION_DISTANCE * 2),
      VISION_DISTANCE + random(height - VISION_DISTANCE * 2)
    );
    this.velocity = p5.Vector.random2D().mult(MAX_SPEED * random());
  }
  
  update() {
    // Apply noise
    this.velocity.add(p5.Vector.random2D().mult(NOISE_FORCE));

    // Avoid the walls
    if (this.position.x < VISION_DISTANCE) { 
      this.velocity.x += WALL_AVOIDANCE_FORCE;
    }
    if (this.position.x > width - VISION_DISTANCE) { 
      this.velocity.x -= WALL_AVOIDANCE_FORCE;
    }
    if (this.position.y < VISION_DISTANCE) { 
      this.velocity.y += WALL_AVOIDANCE_FORCE;
    }
    if (this.position.y > height - VISION_DISTANCE) { 
      this.velocity.y -= WALL_AVOIDANCE_FORCE;
    }
    
    // Actual BOID forces
    this.separation_force = createVector(0, 0);
    this.alignment_force = createVector(0, 0);
    this.cohesion_force = createVector(0, 0);

    // Calculate average of local neighborhood
    this.friend_count = 0;
    this.friend_position = createVector(0, 0);
    this.friend_velocity = createVector(0, 0);
    
    // Check all boids, ignore those not close enough
    for (let other of boids) {
      if (this == other) continue;
      
      let v = p5.Vector.sub(
        other.position,
        this.position
      ).normalize();
      let d = v.mag();
      if (d > VISION_DISTANCE) continue;
      
      // Add separation force
      this.separation_force.add(
        p5.Vector.mult(v, -1.0 * 0.01 / d * SEPARATION_FORCE)
      );
      
      // Alignment and cohesion
      this.friend_count += 1;
      this.friend_position.add(other.position);
      this.friend_velocity.add(other.velocity);      
    }
    
    this.velocity.add(this.separation_force);
    
    if (this.friend_count > 0) {
      // Alignment force, move towards local heading
      this.friend_velocity.mult(1 / this.friend_count);
      this.alignment_force = p5.Vector.mult(
        this.friend_velocity,
        ALIGNMENT_FORCE
      );
      this.velocity.add(this.alignment_force);

      // Cohesion force, move towards center of local group
      this.friend_position.mult(1 / this.friend_count);
      this.cohesion_force = p5.Vector.mult(
        p5.Vector.sub(
          this.friend_position,
          this.position
        ).normalize(),
        COHESION_FORCE
      );
      this.velocity.add(this.cohesion_force);
    }
    
    // Clamp to maximum speed
    if (this.velocity.mag() > MAX_SPEED) {
      this.velocity = this.velocity.normalize().mult(MAX_SPEED);
    } 
    
    // Update position based on current velocity
    this.position = this.position.add(this.velocity);
    
    if (this.position.x < 0) {
      this.position.x = 0;
      this.velocity.x = abs(this.velocity.x);
    }
    
    if (this.position.x > width) {
      this.position.x = width;
      this.velocity.x = -1 * abs(this.velocity.x);
    } 
    
    if (this.position.y < 0) {
      this.position.y = 0;
      this.velocity.y = abs(this.velocity.y);
    }
    
    if (this.position.y > width) {
      this.position.y = height;
      this.velocity.y = -1 * abs(this.velocity.y);
    }
  }
  
  draw() {
    stroke(0);
    circle(this.position.x, this.position.y, 5);
    
    stroke(255, 0, 0);
    line(
      this.position.x,
      this.position.y,
      this.position.x + 100.0 * this.separation_force.x,
      this.position.y + 100.0 * this.separation_force.y
    )
    
    stroke(0, 255, 0);
    line(
      this.position.x,
      this.position.y,
      this.position.x + 100.0 * this.alignment_force.x,
      this.position.y + 100.0 * this.alignment_force.y
    )
    
    stroke(0, 0, 255);
    line(
      this.position.x,
      this.position.y,
      this.position.x + 100.0 * this.cohesion_force.x,
      this.position.y + 100.0 * this.cohesion_force.y
    )
  }
}

function setup() {
  NOISE_FORCE = random() / 5.0;
  WALL_AVOIDANCE_FORCE = random() / 5.0;
  SEPARATION_FORCE = 0.1 + random() / 5.0;
  ALIGNMENT_FORCE = random() / 5.0;
  COHESION_FORCE = random() / 5.0;
  
  createCanvas(400, 400);
  createButton("toggle clear").mousePressed(() => {
    DRAW_BACKGROUND = !DRAW_BACKGROUND;
  });
  
  boids = [];
  for (let i = 0; i < BOID_COUNT; i++) {
    boids.push(new Boid());
  }
  
  background(255);
}

function draw() {
  if (DRAW_BACKGROUND) {
    background(255);
  }
  
  for (let boid of boids) {
    boid.update();
  }
  
  for (let boid of boids) {
    boid.draw();
  }
}
{{</p5js>}}


## 6) Steal Like An Artist

Cool. Let's do the [picsum](https://picsum.photos/) thing again and then randomly draw some nice curvy brush strokes over it. 

Now with parameterization!

{{<p5js width="600" height="420">}}
let gui;
let params = {
  iterationCount: 100, iterationCountMin: 1,
  maximumDistance: 10.0, maximumDistanceMax: 100.0,
  brush: 3, brushMin: 1, brushMax: 10,
  characterSet: [
    'latin'
  ]
};

let original;

function preload() {
  console.log('Loading...');
  original = loadImage("https://picsum.photos/400");
  console.log("done");
}

function setup() {
  createCanvas(400, 400);

  gui = createGuiPanel('params');
  gui.addObject(params);
  gui.setPosition(420, 0);
}

function draw() {
  for (let i = 0; i < params.iterationCount; i++) {
    drawOne();
  }
}

function drawOne() {
  let points = [];
  points.push(createVector(
    random(width),
    random(height)
  ));
  
  for (let i = 1; i <= 4; i++) {
    points.push(p5.Vector.add(
      points[points.length - 1],
      p5.Vector.random2D().mult(random() * params.maximumDistance)
    ));
  }
  
  let r = 0, g = 0, b = 0;
  
  for (let p of points) {
    let c = original.get(parseInt(p.x), parseInt(p.y));
    r += c[0];
    g += c[1];
    b += c[2];
  }
  
  r /= points.length;
  g /= points.length;
  b /= points.length;
  
  strokeWeight(params.brush);
  stroke(
    parseInt(r),
    parseInt(g),
    parseInt(b),
    255
  );
  noFill();
  
  curve(
    points[0].x, points[0].y,
    points[1].x, points[1].y,
    points[2].x, points[2].y,
    points[3].x, points[3].y
  );
}
{{</p5js>}}


## 7) Sample a color palette from your favorite movie/album cover

I'll do more than that! I'll sample the entire Matrix character scroll thing. Super paramaterizable. Whee!

{{<p5js width="600" height="420">}}
let params = {
  letterCount: 10,
  letterSize: 12, letterSizeMin: 1, letterSizeMax: 48,
  letterSizeVariance: 0.0, letterSizeVarianceMin: 0.0, letterSizeVarianceMax: 1.0, letterSizeVarianceStep: 0.01,
  
  speed: 0.5, speedMin: 0.1, speedMax: 4.0, speedStep: 0.01,
  speedVariance: 0.0, speedVarianceMin: 0.0, speedVarianceMax: 10.0, speedVarianceStep: 0.01,
  
  color: '#0fff00',
  
  fadeRate: 0.1, fadeRateMin: 0, fadeRateMax: 0.3, fadeRateStep: 0.01,
  
  characterSet: [
    'unknown',
  ]
};
let letters;

let characterSets = [
  ['latin', 'A', 'Z'],
  ['cjk', '一', '龯'],
  // ['cuneiform', '𒀀', '𒎙'],
  ['runic', 'ᚠ', 'ᛪ'],
  ['greek', 'α', 'ω'],
];

function randomChar(min, max) {

}

function randomLetter() {
  for (let [name, min, max] of characterSets) {
    if (params.characterSet == name) {
      return String.fromCharCode(
        random(
          min.charCodeAt(0),
          max.charCodeAt(0) + 1
        )
      );
    }
  }
       
  return '☹️';
}

class Letter {
  constructor(c, x, s) {
    this.x = x; 
    this.y = -1 * random(height);
    this.c = c;
    this.s = s + (
      s
      * (random() + 0.5)
      * params.letterSizeVariance
    );
    this.sv = (random() - 0.5) * params.speedVariance;
  }
  
  update() {
    this.y += (
      this.s * params.speed
      + this.sv * params.speed
    );
  }
  
  draw() {
    textSize(this.s);
    noStroke();
    fill(params.color);
    text(this.c, this.x, this.y);
  }
}

class Letters {
  constructor() {
    this.letters = [];
  }
  
  update() {
    while (this.letters.length < params.letterCount) {
      this.letters.push(new Letter(
        randomLetter(),
        random(width),
        params.letterSize
      ));
    }
    
    for (let letter of this.letters) {
      letter.update();
    }
    
    for (let i = 0; i < this.letters.length; i++) {
      if (this.letters[i].y > height && random() > 0.95) {
        this.letters.splice(i, 1);
        i--;
      }
    }
  }
  
  draw() {
    for (let letter of this.letters) {
      letter.draw();
    }
  }
}

function setup() {
  createCanvas(400, 400);
  background(0);
  
  params.characterSet = [];
  for (let [name, min, max] of characterSets) {
    params.characterSet.push(name);
  }
  
  gui = createGuiPanel('params');
  gui.addObject(params);
  gui.setPosition(420, 0);

  letters = new Letters();
}

function draw() {
  background(0, parseInt(255 * params.fadeRate));
  
  letters.update();
  letters.draw();
}
{{</p5js>}}

## 8) Signed Distance Functions

Wikipedia: {{<wikipedia "Signed Distance Functions">}}

* [Piter explains how to SDFs](https://genuary.art/wtsdf)
* [2D distance functions by Inigo Quilez](https://iquilezles.org/articles/distfunctions2d/)
* [2D distance functions by Inigo Quilez](https://iquilezles.org/articles/distfunctions/)

## 9) Plants

## 10) {{<wikipedia title="Aleatoric music" text="Generative music">}}

## 11) Suprematism

Wikipedia: {{<wikipedia "Suprematism">}}


## 12) Tessellation

Wikipedia: {{<wikipedia "Tessellation">}}
 ({{<wikipedia title="List of Tesselations" text="List">}})

## 13) Something you’ve always wanted to learn


## 14) Asemic writing

Wikipedia: {{<wikipedia "Asemic writing">}}



## 15) Sine waves

> [Fun with sine waves: 1D wobbly noise](https://www.desmos.com/calculator/nhbzwkhij3)

## 16) Reflection of a reflection

## 17) A grid inside a grid inside a grid

## 18) Definitely not a grid

## 19) Black and white

## 20) Art Deco

Wikipedia: {{<wikipedia "Art Deco">}}


## 21) Persian carpet

Wikipedia: {{<wikipedia "Persian carpet">}}


## 22) Shadows

## 23) Moiré

Wikipedia: {{<wikipedia "Moiré">}}


## 24) Textile

## 25) Yayoi Kusama

Wikipedia: {{<wikipedia "Yayoi Kusama">}}


## 26) My kid could have made that

## 27) In the style of {{<wikipedia "Hilma Af Klint">}}

## 28) Generative poetry

## 29) Maximalism

## 30) Minimalism

## 31) Deliberately break one of your previous images, take one of your previous works and ruin it. Alternatively, remix one of your previous works.

{{< taxonomy-list "series" "Genuary 2023" >}}