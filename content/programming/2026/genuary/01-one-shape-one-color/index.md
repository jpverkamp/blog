---
title: "Genuary 2026.01: One color, one shape"
date: 2026-01-01
programming/languages:
- JavaScript
programming/topics:
- Generative Art
- Procedural Content
- p5js
series:
- Genuary 2026
cover: gen26.01.png
---
It's been a [[Genuary 2023|couple years]]() since I last did [Genuary](https://genuary.art/). Let's do it again. I don't expect to make any masterpieces, but I enjoy making tiny pretty pictures. It's something I've been doing honestly as long as I've been programming (I remember making [[wiki:brownian motion]]() 'bugs' in QBasic in the 90s...). 

## 1) One color, one shape

<!--more-->

{{<p5js width="600" height="420">}}
let gui;
let params = {
  hue: 120, hueMin: 0, hueMax: 360,
  count: 300, countMin: 10, countMax: 1000,
  minSize: 0.01, minSizeMin: 0, minSizeMax: 0.5, minSizeStep: 0.01,
  maxSize: 0.02, maxSizeMin: 0, maxSizeMax: 0.5, maxSizeStep: 0.01,
};

let shapes = [];

function setup() {
  createCanvas(400, 400);
  
  colorMode(HSB);
  
  gui = createGuiPanel('params');
  gui.addObject(params);
  gui.setPosition(420, 0);
}

function draw() {
  background(0);
  stroke(0);
  
  // Always overfill by one (so the shapes change)
  while (shapes.length < params.count + 1) {
    shapes.push([
        random(width),
        random(height),
        random(width * params.minSize, width * params.maxSize),
        random(50, 100),
    ]);
  }
  
  while (shapes.length > params.count) {
    shapes.shift();
  }
  
  for (let [x, y, d, v] of shapes) {
    fill(params.hue, 100, v);  
    circle(x, y, d);
  }
}
{{</p5js>}}

{{< taxonomy-list "series" "Genuary 2026" >}}
