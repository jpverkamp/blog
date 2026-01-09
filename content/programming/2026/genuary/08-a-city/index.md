---
title: "Genuary 2026.08: A city"
date: "2026-01-08"
programming/languages:
- JavaScript
programming/topics:
- Generative Art
- Procedural Content
- p5js
series:
- Genuary 2026
cover: gen26.08.png
---
## 8) A city

Simple parallax graphics and (slowly) blinking windows. I enjoyed this one. 

<!--more-->

{{<p5js width="600" height="420">}}
let gui;
let params = {
  layers: 3, layersMin: 1, layersMax: 5,
  stars: 120, starsMin: 0, starsMax: 1000,
  moon: true,
  moonSpeed: 0.15, moonSpeedMin: 0, moonSpeedMax: 2, moonSpeedStep: 0.01,
};


let layers = [];
let stars = [];
let scrollSpeed = 0.2;
let moon; 

function setup() {
  createCanvas(400, 400);
  noStroke();
  
  gui = createGuiPanel('params');
  gui.addObject(params);
  gui.setPosition(420, 0);
}

function draw() {
  // Update objects based on changing params
  while (stars.length > params.stars) stars.shift();
  while (stars.length < params.stars || random() < 0.01) {
    stars.push({
      x: random(width),
      y: random(height),
      r: random(1, 3)
    });
  }
  
  if (moon == undefined) {
    moon = {
      t: 0,
      phase: random(0, 1)
    };    
  }
  
  while (layers.length > params.layers) layers.pop();
  while (layers.length < params.layers) {
    let i = layers.length;
    let total = params.layers;

    let speed = map(i, 0, total - 1, 0.05, 0.25);
    let minH = map(i, 0, total - 1, 120, 200);
    let maxH = map(i, 0, total - 1, 200, 320);

    let shade = map(i, 0, total - 1, 65, 30);
    let col = color(shade - 10, shade - 5, shade);

    layers.push(createLayer(speed, col, minH, maxH));
  }
  
  drawSky();
  for (let layer of layers) {
    drawLayer(layer);
  }
}

function drawSky() {
  for (let y = 0; y < height; y++) {
    let t = map(y, 0, height, 0, 1);
    let c = lerpColor(color(10, 15, 40), color(40, 40, 70), t);
    stroke(c);
    line(0, y, width, y);
  }
  noStroke();

  fill(255, 200);
  for (let s of stars) {
    circle(s.x, s.y, s.r);
  }
  
  if (params.moon) drawMoon();
}

function drawMoon() {
  moon.t += params.moonSpeed / 100;

  // Reset arc when finished
  if (moon.t > 1) {
    moon.t = 0;
    moon.phase = (moon.phase + random(0.1, 0.25)) % 1;
  }

  // Arc path
  let startX = -50;
  let endX = width + 50;

  let x = lerp(startX, endX, moon.t);

  // Parabolic arc across the sky
  let arcHeight = height * 0.35;
  let y = height * 0.55 - sin(moon.t * PI) * arcHeight;

  // Moon body
  push();
  translate(x, y);

  noStroke();
  fill(245, 245, 230);
  circle(0, 0, 28);

  // Phase shadow
  fill(10, 15, 40);
  let phaseOffset = map(moon.phase, 0, 1, -14, 14);
  circle(phaseOffset, 0, 28);

  pop();
}

function createLayer(speed, col, minH, maxH) {
  let buildings = [];
  let x = 0;

  while (x < width * 2) {
    let w = random(30, 70);
    let h = random(minH, maxH);
    buildings.push({
      x,
      w,
      h,
      windows: generateWindows(w, h)
    });
    x += w + random(10);
  }

  return { speed, col, buildings };
}

function drawLayer(layer) {
  let baseY = height;
  fill(layer.col);

  for (let b of layer.buildings) {
    rect(b.x, baseY - b.h, b.w, b.h);

    for (let win of b.windows) {
      fill(win.on ? win.c : color(25));
      rect(
        b.x + win.x,
        baseY - win.y,
        win.w,
        win.h
      );

      if (frameCount % win.rate === 0) {
        win.on = random() > 0.4;
      }
    }

    fill(layer.col);
  }

  for (let b of layer.buildings) {
    b.x -= scrollSpeed * layer.speed * 60;
    if (b.x + b.w < 0) {
      b.x = width + random(40, 100);
    }
  }
}

function generateWindows(w, h) {
  let wins = [];
  for (let x = 6; x < w - 6; x += 10) {
    for (let y = 10; y < h - 10; y += 14) {
      wins.push({
        x,
        y,
        w: 6,
        h: 8,
        on: random() > 0.5,
        rate: int(random(180, 420)),
        c: color(255, 220, 140, 200)
      });
    }
  }
  return wins;
}
{{</p5js>}}

{{< taxonomy-list "series" "Genuary 2026" >}}
