---
title: "Genuary 2023.16: Reflections of a Reflection"
date: 2023-02-16
programming/languages:
- JavaScript
programming/topics:
- Generative Art
- Procedural Content
- p5js
series:
- Genuary 2023
cover: /embeds/2023/genuary-16.png
---
[Genuary](https://genuary.art/)! 

## 16) Reflection of a reflection

<!--more-->

Just some happy bouncing particles. Woot. 

{{<p5js width="600" height="420">}}
let gui;
let params = {
  particleCount: 1,
  particleCountMin: 0,
  particleCountMax: 500,
  
  wallCount: 2,
  wallCountMin: 0,
  wallCountMax: 50,
  
  updatesPerFrame: 10,
  updatesPerFrameMin: 1,
  updatesPerFrameMax: 50,
  
  drawMode: [
    'solid',
    'fade',
    'clear',
  ],
  
  thickness: 5,
  thicknessMin: 1,
  thicknessMax: 10,
  
  rainbow: true,
  drawWalls: true,
}

let particles;
let walls;

function setup() {
  createCanvas(400, 400);
  colorMode(HSL, 100);
  
  gui = createGuiPanel('params');
  gui.addObject(params);
  gui.setPosition(420, 0);
  
  particles = [];
  walls = [];
  
  walls.push({
    point1: createVector(0, 0),
    point2: createVector(0, height),
  });
  walls.push({
    point1: createVector(0, height),
    point2: createVector(width, height),
  });
  walls.push({
    point1: createVector(width, height),
    point2: createVector(width, 0),
  });
  walls.push({
    point1: createVector(width, 0),
    point2: createVector(0, 0),
  });
}

function draw() {
  if (params.drawMode == 'clear') {
    background(255);
  } else if (params.drawMode == 'fade') {
    background(255, 255, 255, 16);
  }
  
  updateToParams();
  doRainbow();
  
  for (let i = 0; i < params.updatesPerFrame; i++) {
    moveParticles();
    drawParticles();
  }
  
  if (params.drawWalls) {
    drawWalls();  
  }
}

function updateToParams() {
  while (particles.length < params.particleCount) {
    console.log('adding point');
    particles.push({
      color: [
        parseInt(random(100)),
        50 + parseInt(random(50)),
        50 + parseInt(random(50)),
        100
      ],
      position: createVector(
        random(width),
        random(height)
      ),
      velocity: createVector(
        2.0 * random() - 1.0,
        2.0 * random() - 1.0
      )
    });
  }
  
  while (particles.length > params.particleCount) {
    console.log('removing point');
    particles.pop();
  }

  while (walls.length - 4  < params.wallCount) {
    console.log('adding wall');
    walls.push({
      point1: createVector(
        random(width),
        random(height)
      ), 
      point2: createVector(
        random(width),
        random(height)
      )
    });
  }
  
  while (walls.length - 4 > params.wallCount) {
    console.log('removing wall');
    walls.pop();
  }
}

function moveParticles() {
  for (let particle of particles) {
    let newPosition = p5.Vector.add(
      particle.position,
      particle.velocity
    );
    
    // Bounce off walls
    for (let wall of walls) {
      // Hit a wall
      let d1 = pointPointDistance(newPosition, wall.point1);
      let d2 = pointPointDistance(newPosition, wall.point2);
      let dw = pointPointDistance(wall.point1, wall.point2);
      let buffer = 0.1;

      if (d1 + d2 >= dw - buffer && d1 + d2 <= dw + buffer) {
        newPosition.sub(particle.velocity);
        
        let wallV = p5.Vector.sub(wall.point2, wall.point1);
        wallV.rotate(HALF_PI);
        particle.velocity.reflect(wallV);

        newPosition.add(particle.velocity);
      }      
    }
   
    particle.position.set(newPosition);
  }
}

function pointLineDistance(p1, p2, p0) {
  return (
    ((p2.x - p1.x) * (p1.y - p0.y) - (p1.x - p0.x) * (p2.y - p1.y))
    /
    sqrt((p2.x - p1.x) ** 2 + (p2.y - p1.y) ** 2)
  );
}

function pointPointDistance(p1, p2) {
  return dist(p1.x, p1.y, p2.x, p2.y);
}

function doRainbow() {
  if (params.rainbow) {
    for (let particle of particles) {
      particle.color[0] = (particle.color[0] + random()) % 100;
    }
  }
}

function drawParticles() {
  for (let particle of particles) {
    noStroke();
    fill(particle.color);
    circle(particle.position.x, particle.position.y, params.thickness);
  }
}

function drawWalls() {
  for (let wall of walls) {
    stroke("black");
    strokeWeight(params.thickness);
    noFill();
    line(wall.point1.x, wall.point1.y, wall.point2.x, wall.point2.y);
  }
}
{{</p5js>}}

{{< taxonomy-list "series" "Genuary 2023" >}}
