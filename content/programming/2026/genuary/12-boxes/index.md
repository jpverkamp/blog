---
title: "Genuary 2026.12: Boxes"
date: "2026-01-12"
programming/languages:
- JavaScript
programming/topics:
- Generative Art
- Procedural Content
- p5js
series:
- Genuary 2026
cover: gen26.12.png
---
## 12) Boxes

It's like [draw a box](https://drawabox.com/). But somehow even more. And automatic. 

If you let it run for a while, you get some crazy abstract art!

![Boxes after running for a long time](run-for-a-while.png)

<!--more-->

{{<p5js width="600" height="460">}}
let gui;
let params = {
  cubes: 3, cubesMin: 1, cubesMax: 9,
  drawSpeed: 5, drawSpeedMin: 1, drawSpeedMax: 100,
  spin: true,
  colorful: true,
  persist: true,
  blackPercent: 0, blackPercentMin: 0, blackPercentMax: 1, blackPercentStep: 0.01,
};

let buffer;
let cubes = [];

function setup() {
  createCanvas(400, 400);
  colorMode(HSB, 360, 100, 100, 100);
  background(0);
  
  buffer = createGraphics(400, 400, WEBGL);
  buffer.pixelDensity(1);
  buffer.colorMode(HSB, 360, 100, 100, 100);

  gui = createGuiPanel("params");
  gui.addObject(params);
  gui.setPosition(420, 0);
}

function draw() {
  while (cubes.length > params.cubes) cubes.shift();
  while (cubes.length < params.cubes) {
    cubes.push(new CubeDrawer(
      createVector(
        (6 * random() - 3) * 50,
        (6 * random() - 3) * 50,
        (6 * random() - 3) * 50,
      ),
      50,
    ))
  }
 
  if (!params.persist) {
    background(0);
    
    buffer.clear();
    buffer.background(0);
    buffer.push();
    buffer.resetMatrix();
    buffer.pop();
  }
  
  cubes.forEach(cube => cube.drawStep());
  cubes = cubes.filter(cube => !cube.isDone());
  
  image(buffer, 0, 0, width, height);
}

class CubeDrawer {
  constructor(offset, size) {
    this.size = size;
    this.offset = offset;
    this.progress = 0;
    
    this.speedVariance = random(0.9, 1.1);
    
    this.hue = random(360);
    this.isBlack = random() < params.blackPercent;

    this.rx = random(TWO_PI);
    this.ry = random(TWO_PI);
    this.rz = random(TWO_PI);
    
    this.spinX = random(-0.002, 0.002);
    this.spinY = random(-0.002, 0.002);
    this.spinZ = random(-0.002, 0.002);

    let s = size / 2;
    this.vertices = [
      createVector(-s, -s, -s),
      createVector( s, -s, -s),
      createVector( s,  s, -s),
      createVector(-s,  s, -s),
      createVector(-s, -s,  s),
      createVector( s, -s,  s),
      createVector( s,  s,  s),
      createVector(-s,  s,  s),
    ];

    this.edges = [
      [0,1], [1,2], [2,3], [3,0],
      [4,5], [5,6], [6,7], [7,4],
      [0,4], [1,5], [2,6], [3,7]
    ];

    this.segments = [];
    let stepsPerEdge = size * 2;

    for (let e of this.edges) {
      let a = this.vertices[e[0]];
      let b = this.vertices[e[1]];

      for (let i = 0; i < stepsPerEdge; i++) {
        let t = i / stepsPerEdge;
        this.segments.push({
          from: a,
          to: b,
          t: t
        });
      }
    }
  }

  drawStep() {
    buffer.push();
    buffer.translate(this.offset.x, this.offset.y, this.offset.z);
    
    if (params.spin) {
      this.rx += this.spinX * params.drawSpeed / 3;
      this.ry += this.spinY * params.drawSpeed / 3;
      this.rz += this.spinZ * params.drawSpeed / 3;
    }
    
    buffer.rotateX(this.rx);
    buffer.rotateY(this.ry);
    buffer.rotateZ(this.rz);

    let steps = min(this.progress, this.segments.length);
    
    if (params.colorful) {
      buffer.stroke(this.hue, 100, 100, 100);
    } else {
      buffer.stroke(255);  
    }

    if (this.isBlack) {
      buffer.stroke("black");
    }

    buffer.strokeWeight(1);

    for (let i = 0; i < steps; i++) {
      let s = this.segments[i];
      let p = p5.Vector.lerp(s.from, s.to, s.t);
      buffer.point(p.x, p.y, p.z);
    }

    this.progress += params.drawSpeed * this.speedVariance;
    buffer.pop();
  }
  
  isDone() {
    return this.progress >= this.segments.length;
  }
}
{{</p5js>}}

{{< taxonomy-list "series" "Genuary 2026" >}}
