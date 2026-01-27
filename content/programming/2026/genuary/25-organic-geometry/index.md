---
title: "Genuary 2026.25: Organic Geometry"
date: "2026-01-25"
programming/languages:
- JavaScript
programming/topics:
- Generative Art
- Procedural Content
- p5js
series:
- Genuary 2026
cover: gen26.25.png
---
So basically we have a simulation where each of n different species has a weight of attraction/repulsion for each other species. This is, by itself, enough to generate some pretty organic behavior!

Edit: This one probably fits better for [[Genuary 2026.27: Lifeform]]() and that one here. 

<!--more-->

{{<p5js width="600" height="500">}}
let gui;
let params = {
  critterCount: 500, critterCountMin: 10, critterCountMax: 2500,
  critterSize: 5, critterSizeMin: 1, critterSizeMax: 20,
  speciesCount: 20, speciesCountMin: 1, speciesCountMax: 100,
  force: 3, forceMin: 1, forceMax: 5,
  edgeMode: ['wrap', 'clip', 'respawn', 'avoid'],
  varyWeights: true,
  varyHues: true,
  fadeMode: ['fade', 'persist', 'erase'],
  symmetricWeights: true,
};

let hues;
let weights;
let critters;

let lastParams;
let pauseUntil;

function setup() {
  createCanvas(400, 400);
  colorMode(HSB, 360, 100, 100, 100);
  
  rectMode(CENTER);

  gui = createGuiPanel("params");
  gui.addObject(params);
  gui.setPosition(420, 0);

  reset();
}

function reset() {
  pauseUntil = undefined;
  
  weights = [];
  hues = [];
  
  for (let i = 0; i < params.speciesCount; i++) {
    hues.push(random(360));
    let row = [];
    for (let j = 0; j < params.speciesCount; j++) {
      row.push(random() - random());
    }
    weights.push(row);
  }
  
  critters = [];
  
}

function draw() {
  if (lastParams == undefined || Object.keys(params).some((k) => params[k] !== lastParams[k])) {
    reset();
    lastParams = {
      ...params
    };
  }

  if (pauseUntil) {
    if (millis() < pauseUntil) {
      return;
    } else {
      reset();
    }
  }
  
  if (params.fadeMode == 'fade') {
    noStroke();
    fill(0, 0, 0, 10);
    rect(width / 2, height / 2, width, height);    
  } else if (params.fadeMode == 'persist') {
    // do nothing
  } else if (params.fadeMode == 'erase') {
    background("black");
  }
  
  while (critters.length > params.critterCount) critters.shift();
  while (critters.length < params.critterCount) {

    critters.push({
      type: floor(random(params.speciesCount)),
      x: random(width),
      y: random(height),
    });
  }
  
  let force = (10 ** (6 - params.force));
  
  for (let c of critters) {
    let fx = 0;
    let fy = 0;
    
    for (let o of critters) {
      if (c == o) continue;
      
      let [a, b] = [c.type, o.type];
      
      if (params.symmetricWeights) {
        [a, b] = [min(a, b), max(a, b)];
      }      
      
      fx += (o.x - c.x) * weights[a][b];
      fy += (o.y - c.y) * weights[a][b];
    }
    
    c.x += 1.0 * fx / force;
    c.y += 1.0 * fy / force;
    
    if (params.edgeMode == 'wrap') {
      if (c.x < -params.critterSize) c.x = width;
      if (c.x > width + params.critterSize) c.x = 0;
      if (c.y < -params.critterSize) c.y = height;
      if (c.y > height + params.critterSize) c.y = 0;      
    } else if (params.edgeMode == 'clip') {
      if (c.x < params.critterSize) c.x = params.critterSize;
      if (c.x > width - params.critterSize) c.x = width - params.critterSize;
      if (c.y < params.critterSize) c.y = params.critterSize;
      if (c.y > height - params.critterSize) c.y = height - params.critterSize; 
    } else if (params.edgeMode == 'avoid') {
      let margin = 40;
      let strength = 0.5;

      if (c.x < margin) {
        c.x += (margin - c.x) * strength;
      }

      if (c.x > width - margin) {
        c.x -= (c.x - (width - margin)) * strength;
      }

      if (c.y < margin) {
        c.y += (margin - c.y) * strength;
      }

      if (c.y > height - margin) {
        c.y -= (c.y - (height - margin)) * strength;
      }
    }
  }
  
  if (params.edgeMode == 'respawn') {
    critters = critters.filter((c) => (
      c.x >= -params.critterSize
      && c.x < width + params.critterSize
      && c.y >= -params.critterSize
      && c.y < height + params.critterSize
    ));
  }
  
  if (params.varyWeights) {
    for (let i = 0; i < params.speciesCount; i++) {
      for (let j = 0; j < params.speciesCount; j++) {
        weights[i][j] += (random() - random()) / 10;
      }
    }    
  }
  
  if (params.varyHues) {
    for (let i = 0; i < params.speciesCount; i++) {
      hues[i] += (random() - random()) * 30;
      while (hues[i] < 0) hues[i] += 360;
      while (hues[i] > 360) hues[i] -= 360;
    }
  }
  
  for (let c of critters) {
    push();
    translate(c.x, c.y);
    stroke("black");
    strokeWeight(0.1);
    fill(hues[c.type], 100, 100);
    rect(0, 0, params.critterSize);
    pop();
  }
  
}
{{</p5js>}}