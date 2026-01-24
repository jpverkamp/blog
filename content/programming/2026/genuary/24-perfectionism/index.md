---
title: "Genuary 2026.24: Perfectionist's Nightmare"
date: "2026-01-24"
programming/languages:
- JavaScript
programming/topics:
- Generative Art
- Procedural Content
- p5js
series:
- Genuary 2026
cover: gen26.24.png
---
[It started off](?gridX=10&gridY=10&brick=false&rainbow=false&fadeIn=false&fadeOut=false&perfectlyImperfect=false) with a neat grow of blocks and just sort of grew from there--as these things seem wont to do. 

This is another one that really benefits from the animation, but it's neat enough to see each simulation done. 

Try playing with the settings. [This one](?gridX=2&gridY=100&maxActivationsPerFrame=10&rainbow=false&fadeIn=false&fadeOut=false&perfectlyImperfect=false) looks like a game of Pick Up Sticks. 

<!--more-->

{{<p5js width="600" height="500">}}
let gui;
let params = {
  gridX: 17,
  gridXMin: 2,
  gridXMax: 100,
  gridY: 31,
  gridYMin: 2,
  gridYMax: 100,
  maxActivationsPerFrame: 20,
  maxActivationsPerFrameMin: 1,
  maxActivationsPerFrameMax: 100,
  brick: true,
  rainbow: true,
  fadeIn: true,
  fadeOut: true,
  perfectlyImperfect: true,
};

let lastParams;
let shapes;
let pauseUntil;

function setup() {
  createCanvas(400, 400);
  colorMode(HSB, 360, 100, 100, 100);

  gui = createGuiPanel("params");
  gui.addObject(params);
  gui.setPosition(420, 0);

  reset();
}

function reset() {
  pauseUntil = undefined;
  shapes = [];

  let cellWidth = width / params.gridX;
  let cellHeight = height / params.gridY;
  let targetHue = random(360);

  for (let j = 0; j < params.gridY; j++) {
    let extra = (params.brick && j % 2 == 0) ? 1 : 0;
    for (let i = 0; i < params.gridX + extra; i++) {
      let offsetX = 0;
      if (params.brick && j % 2 == 0) {
        offsetX = -(cellWidth / 2);
      }

      if (params.rainbow) {
        targetHue = i + j * params.gridX;
      }

      let shape = {
        originX: random(width),
        originY: random(height),
        originR: random(TWO_PI),
        originH: random(360),

        progress: 0,

        targetX: i * cellWidth + cellWidth / 2 + offsetX,
        targetY: j * cellHeight + cellHeight / 2,
        targetR: TWO_PI,
        targetH: 360 + targetHue,

        width: cellWidth,
        height: cellHeight,
        active: false,
        extra: 0,
      };
      shapes.push(shape);
    }
  }

  shuffle(shapes, true);
  
  if (params.perfectlyImperfect) {
    for (let s of shapes) {
      s.targetX += (random() - random());
      s.targetY += (random() - random());
      s.targetH += (random() - random()) * 10;
    }
  } else {
    let imperfection = floor(random(shapes.length));
    let s = shapes.splice(imperfection, 1)[0];
    s.targetX += (random() - random()) * 10;
    s.targetY += (random() - random()) * 10;
    s.targetR += (random() - random()) / 10;
    if (params.rainbow) {
      s.targetH = random(360);
    } else {
      s.targetH += (random() - random()) * 60;
    }
    s.extra = 1000;
    shapes.push(s);
  }
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

  if (params.fadeOut) {
    noStroke();
    fill(0, 0, 0, 5);
    rect(0, 0, width, height);
  } else {
    background("black");
  }
  
  for (let i = 0; i < params.maxActivationsPerFrame; i++) {
    let r = floor(random(shapes.length));
    shapes[r].active = true;
  }

  for (let shape of shapes) {
    if (shape.active) {
      shape.progress += 1;
      if (shape.progress > 100) {
        shape.progress = 100;
      }
    }

    let x = lerp(shape.originX, shape.targetX, shape.progress / 100.0);
    let y = lerp(shape.originY, shape.targetY, shape.progress / 100.0);
    let r = lerp(shape.originR, shape.targetR, shape.progress / 100.0);
    let h = lerp(shape.originH, shape.targetH, shape.progress / 100.0) % 360;
    let a = lerp(0, 100, shape.progress / 100);
    if (!params.fadeIn) {
      a = 100;
    }

    push();
    translate(x, y);
    rotate(r);

    rectMode(CENTER);
    fill(h, 100, 100, a);
    stroke(0, 0, 0, a);
    rect(0, 0, shape.width, shape.height);
    pop();

  }

  shapes.sort((a, b) => {
    let aScore = a.progress - (a.active ? 0 : 100) - a.extra;
    let bScore = b.progress - (b.active ? 0 : 100) - b.extra;
    return bScore - aScore;
  });

  if (!shapes.some((s) => !s.active || s.progress < 100)) {
    pauseUntil = millis() + 500;
  }
}

function scope(f) {
  push();
  f();
  pop();
}
{{</p5js>}}