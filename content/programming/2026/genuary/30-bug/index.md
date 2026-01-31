---
title: "Genuary 2026.30: Bug"
date: "2026-01-30"
programming/languages:
- JavaScript
programming/topics:
- Generative Art
- Procedural Content
- p5js
series:
- Genuary 2026
cover: gen26.30.png
---
A throwback to what's probably one of my earliest programming projects (originally in [[wiki:qbasic]]()...): bugs!

It's very simple: each frame, each bug moves randomly and the draws a dot. 

That's really it. 

I've updated it a bit with various parameters to tweak. Play with them. See what they do!

<!--more-->

{{<p5js width="600" height="500">}}
let gui;
let params = {
  populationSize: 40, populationSizeMin: 1, populationSizeMax: 1000,
  updatesPerTick: 20, updatesPerTickMin: 1, updatesPerTickMax: 100,
  moveStrength: 5, moveStrengthMin: 1, moveStrengthMax: 10,
  size: 2, sizeMin: 1, sizeMax: 10,
  varyColor: true,
  cycleColor: false,
  fade: true,
  swirl: false,
  swirlStrength: 5, swirlStrengthMin: 1, swirlStrengthMax: 10,
};

let bugs;
let lastParams;

function setup() {
  let canvas = createCanvas(400, 400);
  colorMode(HSB, 360, 100, 100, 100);

  gui = createGuiPanel("params");
  gui.addObject(params);
  gui.setPosition(420, 0);

  reset();
}

function reset() {
  background("black");
  bugs = [];
}

function draw() {
  const paramsChanged =
    lastParams == undefined ||
    Object.keys(params).some((k) => params[k] !== lastParams[k]);

  if (paramsChanged) {
    reset();
    lastParams = { ...params };
    pauseUntil = undefined;
  }

  if (params.fade && frameCount % 2 == 0) {
    noStroke();
    fill(0, 0, 0, 3);
    rect(0, 0, width, height);
  }

  while (bugs.length > params.populationSize) bugs.shift();
  while (bugs.length < params.populationSize) {
    bugs.push({
      x: random(width),
      y: random(height),
      h: random(360),
    });
  }

  for (let i = 0; i < params.updatesPerTick; i++) {
    bugs.forEach((bug) => {
      bug.x += (random() - random()) * 0.8 ** (1 - params.moveStrength);
      bug.y += (random() - random()) * 0.8 ** (1 - params.moveStrength);

      if (params.cycleColor) {
        bug.h += random();
      }

      if (params.swirl) {
        let cx = width / 2;
        let cy = height / 2;
        let dx = bug.x - cx;
        let dy = bug.y - cy;
        let d = sqrt(dx * dx + dy * dy) + 0.01;
        bug.x += (-dy / d) * params.swirlStrength / 10;
        bug.y += (dx / d) * params.swirlStrength / 10;
      }

      if (bug.x < 0) bug.x = width - 1;
      if (bug.x >= width) bug.x = 0;
      if (bug.y < 0) bug.y = height - 1;
      if (bug.y >= height) bug.y = 0;
      if (bug.h < 0) bug.h = 360;
      if (bug.h > 360) bug.h = 0;
    });

    bugs.forEach((bug) => {
      let h = bug.h;
      if (params.varyColor) {
        h += (random() - random()) * 50;
      }

      noStroke();
      fill(h, 100, 100);
      circle(bug.x, bug.y, params.size);
    });
  }
}
{{</p5js>}}