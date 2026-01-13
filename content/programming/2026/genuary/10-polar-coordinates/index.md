---
title: "Genuary 2026.10: Polar coordinates"
date: "2026-01-10"
programming/languages:
- JavaScript
programming/topics:
- Generative Art
- Procedural Content
- p5js
series:
- Genuary 2026
cover: gen26.10.png
---
## 10) Polar coordinates

CIrcles within circles within circles. 

<!--more-->

{{<p5js width="600" height="420">}}
let gui;
let params = {
  count: 3, countMin: 1, countMax: 10,
  children: 6, childrenMin: 0, childrenMax: 10,
  maxDepth: 1, maxDepthMin: 0, maxDepthMax: 4,
  iKnowWhatImDoing: false,
  fade: true,
  fadeStrength: 0.1, fadeStrengthMin: 0, fadeStrengthMax: 1, fadeStrengthStep: 0.1,
};

class Bug {
  constructor(depth=0) {
    this.radius = 0;
    this.dradius = random();

    this.theta = 0;
    this.dtheta = random();
    
    this.size = random(10);
    this.dsize = random();
    
    this.hue = random(360);
    this.dhue = random();
    
    this.alpha = random(50, 100);
    
    this.children = [];
    if (depth < params.maxDepth) {
      for (let i = 0; i < params.maxDepth; i++) {
        this.children.push(new Bug(depth + 1));
      }
    }
  }
  
  update() {
    if (!this.isValid()) return;
    
    this.dradius += random() - 0.5;
    this.dtheta += random() - 0.5;
    this.dsize += random() - 0.5;
    this.dhue += random() - 0.5;
    
    this.radius += this.dradius;
    this.theta += this.dtheta;
    this.size += this.dsize;
    this.hue += this.dhue;
    
    this.children = this.children.filter(c => c.isValid());
    for (let c of this.children) c.update();
  }
  
  isValid() {
    return (
      Math.abs(this.radius) < min(width, height) &&
      this.size > 1 &&
      this.size < 100
    );
  }
  
  draw() {
    if (!this.isValid()) return;
    
    let x = this.radius * cos(this.theta);
    let y = this.radius * sin(this.theta);
    
    push();
    {
      translate(x, y);
      stroke("black");
      fill(this.hue, 100, 100, this.alpha);
      circle(0, 0, this.size);
      
      for (let c of this.children) c.draw();
    }
    pop();
  }
}

let bugs = [];

function setup() {
  createCanvas(400, 400);
  noStroke();
  colorMode(HSB, 360, 100, 100, 100);
  
  background("black");

  gui = createGuiPanel("params");
  gui.addObject(params);
  gui.setPosition(420, 0);
}

function draw() {
  frameRate(30);
  
  if (Math.pow(params.count * params.children, params.maxDepth) > 100) {
    if (!params.iKnowWhatImDoing) {
      background("black");
      fill("red");
      textSize(32);
      text("This is too many bugs...", 32, 64);
      
      textSize(16);
      text("If you know what you're doing...", 32, 128);
      text("Click the button", 32, 128 + 16 + 8);
      return;      
    }
  }
  
  bugs = bugs.filter(bug => bug.isValid());
  
  while (bugs.length > params.count) bugs.shift();
  while (bugs.length < params.count) bugs.push(new Bug());
  
  for (let b of bugs) b.update();
  
  push();
  {
    translate(width / 2, height / 2);
    for (let b of bugs) b.draw();    
  }
  pop();
  
  if (params.fade) {
    fill(0, 0, 0, 10 * params.fadeStrength);
    rect(0, 0, width, height);
  }
  
}
{{</p5js>}}

{{< taxonomy-list "series" "Genuary 2026" >}}
