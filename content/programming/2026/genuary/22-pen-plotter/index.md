---
title: "Genuary 2026.22: Pen plotter ready"
date: "2026-01-22"
programming/languages:
- JavaScript
programming/topics:
- Generative Art
- Procedural Content
- p5js
series:
- Genuary 2026
cover: gen26.22.png
---
Split a polygon into triangles and then recursively split those triangles over and over again!

<!--more-->

{{<p5js width="600" height="500">}}
let gui;
let params = {
  initialSides: 6, initialSidesMin: 3, initialSidesMax: 12, initialSidesStep: 1,
  splitsPerFrame: 10, splitsPerFrameMin: 1, splitsPerFrameMax: 10, splitsPerFrameStep: 1,
  minArea: 50, minAreaMin: 1, minAreaMax: 2000, minAreaStep: 1,
  minSegment: 5, minSegmentMin: 1, minSegmentMax: 100, minSegmentStep: 1,
  colorize: false,
  hueVariation: 30, hueVariationMin: 0, hueVariationMax: 100, hueVariationStep: 1,
  pauseOnResetFor: 500, pauseOnResetForMin: 0, pauseOnResetForMax: 2000,
  stopOnReset: false,
};

let lastParams;
let triangles;
let pauseStart;
let stopped = false;

function setup() {
  createCanvas(400, 400);
  colorMode(HSB, 360, 100, 100, 100);

  gui = createGuiPanel("params");
  gui.addObject(params);
  gui.setPosition(420, 0);

  reset();
}

function reset() {
  triangles = [];

  let r = width * 0.4;
  let cx = width / 2;
  let cy = height / 2;

  for (let i = 0; i < params.initialSides; i++) {
    let a1 = (TWO_PI * i) / params.initialSides;
    let a2 = (TWO_PI * (i + 1)) / params.initialSides;

    let p1 = createVector(cx, cy);
    let p2 = createVector(
      cx + cos(a1) * r,
      cy + sin(a1) * r
    );
    let p3 = createVector(
      cx + cos(a2) * r,
      cy + sin(a2) * r
    );

    triangles.push({
      a: p1,
      b: p2,
      c: p3,
      hue: random(360)
    });
  }
}

function draw() {
  if (lastParams == undefined || Object.keys(params).some((k) => params[k] !== lastParams[k])) {
    reset();
    stopped = false;
    pauseStart = undefined;
    lastParams = { ...params };
  }

  if (stopped) return;

  background(0, 0, 95);

  let splits = params.splitsPerFrame;
  let updatesMade = false;

  for (let i = 0; i < splits; i++) {
    for (let retry = 0; retry < 100; retry++) {
      let index = floor(random(triangles.length));

      let t = triangles.splice(index, 1)[0];
      let g = p5.Vector.add(t.a, t.b).add(t.c).div(3);

      let corners = [
        { v: t.a, e1: t.b, e2: t.c },
        { v: t.b, e1: t.c, e2: t.a },
        { v: t.c, e1: t.a, e2: t.b },
      ];
      let choice = random(corners);

      let p = intersect(choice.v, g, choice.e1, choice.e2);
      if (!p) {
        triangles.push(t);
        continue;
      }

      if (p5.Vector.dist(choice.e1, choice.e2) < params.minSegment) {
        triangles.push(t);
        continue;
      }

      if (triangleArea(choice.v, choice.e1, choice.e2) / 2 < params.minArea ||
        triangleArea(choice.v, p, choice.e1) < params.minArea ||
        triangleArea(choice.v, p, choice.e2) < params.minArea) {
        triangles.push(t);
        continue;
      }
    
      triangles.push(
        {
          a: choice.v.copy(),
          b: choice.e1.copy(),
          c: p.copy(),
          hue: t.hue + random(-params.hueVariation, params.hueVariation)
        },
        {
          a: choice.v.copy(),
          b: p.copy(),
          c: choice.e2.copy(),
          hue: t.hue + random(-params.hueVariation, params.hueVariation)
        }
      );

      updatesMade = true;
      break;
    }
  }

  stroke(0);
  noFill();

  for (let t of triangles) {
    if (params.colorize) {
      fill(t.hue, 80, 80, 20);
    }
    t.hue += random(-params.hueVariation / 10, params.hueVariation / 10);
    while (t.hue < 0) t.hue += 360;
    while (t.hue >= 360) t.hue -= 360;

    beginShape();
    vertex(t.a.x, t.a.y);
    vertex(t.b.x, t.b.y);
    vertex(t.c.x, t.c.y);
    endShape(CLOSE);
  }

  if (!updatesMade) {
    if (params.stopOnReset) {
      stopped = true;
    } else if (pauseStart == undefined) {
      pauseStart = millis();
    } else if (millis() - pauseStart >= params.pauseOnResetFor) {
      pauseStart = undefined;
      reset();
    }
  }
}

function intersect(a, b, c, d) {
  let r = p5.Vector.sub(b, a);
  let s = p5.Vector.sub(d, c);

  let denom = r.x * s.y - r.y * s.x;
  if (abs(denom) < 1e-6) return null;

  let t = ((c.x - a.x) * s.y - (c.y - a.y) * s.x) / denom;
  let u = ((c.x - a.x) * r.y - (c.y - a.y) * r.x) / denom;

  if (t >= 0 && u >= 0 && u <= 1) {
    return createVector(
      a.x + t * r.x,
      a.y + t * r.y
    );
  }

  return null;
}

function triangleArea(a, b, c) {
  return abs(
    (a.x * (b.y - c.y) +
     b.x * (c.y - a.y) +
     c.x * (a.y - b.y)) / 2
  );
}
{{</p5js>}}

If you'd rather something a bit more stained glass, [you can colorize it](?splitsPerFrame=1&minArea=512&colorize=true):

![](colorized.png)