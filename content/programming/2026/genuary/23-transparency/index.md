---
title: "Genuary 2026.23: Transparency"
date: "2026-01-23"
programming/languages:
- JavaScript
programming/topics:
- Generative Art
- Procedural Content
- p5js
series:
- Genuary 2026
cover: gen26.23.png
---
[[Genuary 2026.10: Polar coordinates]]() did the transparency thing, but ... let's do it again!

This is one that really stands out when it's animated. 

<!--more-->

{{<p5js width="600" height="500">}}
let gui;
let params = {
  transparency: 50, transparencyMin: 0, transparencyMax: 100, transparencyStep: 5,
  gridX: 10, gridXMin: 2, gridXMax: 20, gridXStep: 1,
  gridY: 10, gridYMin: 2, gridYMax: 20, gridYStep: 1,
  overlap: 50, overlapMin: 0, overlapMax: 200, overlapStep: 5,
  sway: 20, swayMin: 0, swayMax: 100, swayStep: 1,
  pulse: 0.5, pulseMin: 0, pulseMax: 2, pulseStep: 0.1,
  varyHue: true,
  hueVariation: 1, hueVariationMin: 0, hueVariationMax: 10, hueVariationStep: 1,
  border: true,
};

let lastParams;
let shapes;

function setup() {
  createCanvas(400, 400);
  colorMode(HSB, 360, 100, 100, 100);

  gui = createGuiPanel("params");
  gui.addObject(params);
  gui.setPosition(420, 0);

  reset();
}

function reset() {
    shapes = [];

    let cellWidth = width / params.gridX;
    let cellHeight = height / params.gridY;

    for (let i = 0; i < params.gridX; i++) {
        for (let j = 0; j < params.gridY; j++) {
            let x = i * cellWidth + cellWidth / 2;
            let y = j * cellHeight + cellHeight / 2;
            let shape = {
              x: x,
              y: y,
              size: max(cellWidth, cellHeight) + params.overlap,
              hue: random(360),
              swayX: random(-params.sway, params.sway),
              swayY: random(-params.sway, params.sway),
              pulse: random(1 - params.pulse, 1 + params.pulse)
            };
            shapes.push(shape);
        }
  } 
  
  shuffle(shapes, true);
}

function draw() {
  if (lastParams == undefined || Object.keys(params).some((k) => params[k] !== lastParams[k])) {
    reset();
    lastParams = { ...params };
  }
    
  background(255);

  for (let shape of shapes) {
    let x = shape.x + shape.swayX * sin(frameCount * 0.02 + shape.x);
    let y = shape.y + shape.swayY * cos(frameCount * 0.02 + shape.y);
    let size = shape.size * (1 + params.pulse * 0.5 * sin(frameCount * 0.05 + shape.x + shape.y));
    
    
    if (params.varyHue) {
      shape.hue += params.hueVariation * 0.1;
      shape.hue = shape.hue % 360;
    }

    fill(shape.hue, 70, 100, 100 - params.transparency);
    
    if (params.border) {
      stroke(0, 0, 0, 100 - params.transparency);
    } else {
      noStroke();
    }

    ellipse(x, y, size);
  }
}
{{</p5js>}}