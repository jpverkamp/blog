---
title: "Genuary 2026.27: Lifeform"
date: "2026-01-27"
programming/languages:
- JavaScript
programming/topics:
- Generative Art
- Procedural Content
- p5js
series:
- Genuary 2026
cover: gen26.27.png
---
So this one really fits better for [[Genuary 2026.25: Organic Geometry]]() and that one is a lifeform like this one, so... we'll consider them swapped or something.

Anyways, spawn branching nodes and draw a bunch of squares. Not only an organic looking lifeform but creepy to boot! I do love it without borders and with fade. 

Be careful with high child count without either a high segment length or death rate to compensate, it will get slow. 

<!--more-->

{{<p5js width="600" height="500">}}
let gui;
let params = {
  spawnRate: 0.25, spawnRateMin: 0, spawnRateMax: 1, spawnRateStep: 0.01,
  deathRate: 0.0001, deathRateMin: 0, deathRateMax: 0.01, deathRateStep: 0.0001,
  segmentLength: 10, segmentLengthMin: 10, segmentLengthMax: 100,
  maxLength: 40, maxLengthMin: 10, maxLengthMax: 100,
  childrenCount: 2, childrenCountMin: 2, childrenCountMax: 10,
  wigglyness: 3, wigglynessMin: 1, wigglynessMax: 5, 
  straightenChance: 0.5, straightenChanceMin: 0, straightenChanceMax: 1, straightenChanceStep: 0.01,
  roots: 7, rootsMin: 1, rootsMax: 16,
  borders: false,
  colorful: true,
  fade: true,
};

let roots;

let lastParams;
let pauseUntil;

function setup() {
  createCanvas(400, 400);
  colorMode(HSB, 360, 100, 100, 100);
  
  gui = createGuiPanel("params");
  gui.addObject(params);
  gui.setPosition(420, 0);

  reset();
}

class Node {
  constructor(theta, hue) {
    this.hue = hue || random(360);
    this.theta = theta;
    this.children = [];
  }
  
  update(length = 0, segment = 0) {
    let spawn = false;
    
    // If we don't have at least 1 child, we can spawn
    spawn |= (
      length < params.maxLength
      && this.children.length < 1
      && random() < params.spawnRate
    );
    
    // If we have at least one but we're at the right segment length, we can also spawn
    spawn |= (
      length < params.maxLength
      && this.children.length <= params.childrenCount
      && segment == params.segmentLength
      && random() < params.spawnRate
    );
    
    if (spawn) {
      let nextHue = this.hue + (random() - random()) * 10;
      while (nextHue < 0) nextHue += 360;
      while (nextHue > 360) nextHue -= 360;
      this.children.push(new Node(this.theta, nextHue));
    }
    
    this.hue = this.hue + (random() - random());
    while (this.hue < 0) this.hue += 360;
    while (this.hue > 360) this.hue -= 360;
    
    this.theta += (random() - random()) / (10 ** (5 - params.wigglyness));
    while (this.theta < 0) this.theta += TWO_PI;
    while (this.theta > TWO_PI) this.theta -= TWO_PI;
    
    let nextSegment = this.children.length > 1 ? 0 : segment + 1;
    this.children.forEach((c) => c.update(length + 1, nextSegment));
    
    if (random() < params.straightenChance) {
      if (this.children.count == 1) {
        this.children.forEach((c) => c.theta = this.theta);
      }
    }
    
    for (let i = this.children.length - 1; i >= 0; i--) {
      if (random() < params.deathRate) {
        this.children.splice(i, 1);
      }
    }
  }
  
  draw() {
    if (params.borders) {
      stroke("black");
    } else {
      noStroke();
    }
    
    if (params.colorful) {
      fill(this.hue, 100, 100);
    } else {
      fill("white");
    }
    
    rect(0, 0, 10, 10);
    push();
    {
      rotate(this.theta);
      translate(4, 0);
      this.children.forEach((c) => c.draw());      
    }
    pop();
  }
}

function reset() {
  roots = [];
  for (let i = 0; i < params.roots; i++) {
    roots.push(new Node(0))
  }
}

function draw() {
  const paramsChanged = lastParams == undefined || Object.keys(params).some((k) => 
    params[k] !== lastParams[k]
  );
  
  if (paramsChanged) {
    reset();
    lastParams = {...params};
    pauseUntil = undefined;
  }

  if (pauseUntil) {
    if (millis() < pauseUntil) {
      return;
    } else {
      reset();
    }
  }
  
  if (params.fade) {
    fill(0, 0, 0, 3);
    rect(0, 0, width, height);
  } else {
    background("black");
  }
  
  roots.forEach((r) => r.update());
  
  push();
  {
    if (params.roots == 1) {
      translate(width / 2, 3 * height / 4);
    } else {
      translate(width / 2, height / 2);
    }
    rotate(-PI / 2);
    roots.forEach((r) => {
      rotate(TWO_PI / params.roots);
      r.draw();
    });
  }
  pop();
}
{{</p5js>}}
