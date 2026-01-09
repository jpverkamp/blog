---
title: "Genuary 2026.06: Lights on/off"
date: "2026-01-06"
programming/languages:
- JavaScript
programming/topics:
- Generative Art
- Procedural Content
- p5js
series:
- Genuary 2026
cover: gen26.06.png
---
## 5) Lights on/off

:smile:

(Turn on flickering.)

(If you dare.)

<!--more-->

{{<p5js width="600" height="420">}}
let gui;
let params = {
  flicker: false,
  flickerPercent: 0.05, flickerPercentMin: 0, flickerPercentMax: 1, flickerPercentStep: 0.01,
  avgFlickerDuration: 2, avgFlickerDurationMin: 0, avgFlickerDurationMax: 10, avgFlickerDurationStep: 0.1,
};

let snowflakes = [];
let armAngle = 0;
let isFlickering = false;
let flickerStart = 0;

function setup() {
  createCanvas(400, 400);
  for (let i = 0; i < 100; i++) {
    snowflakes.push(new Snowflake());
  }
    
  gui = createGuiPanel('params');
  gui.addObject(params);
  gui.setPosition(420, 0);
}

function updateFlicker() {
  if (!params.flicker) return;

  if (isFlickering) {
    flickerTimer--;
    if (flickerTimer <= 0) {
      isFlickering = false;
    }
  }
}

let randomFrame = 0;
let randomThisFrame = 0;
function noiseRandom() {
  if (frameCount != randomFrame) {
    randomFrame = frameCount;
    randomThisFrame = 0;
  }
  
  randomThisFrame += 10;
  return noise(frameCount * 0.001, randomThisFrame);
}

function draw() {
  background(20, 40, 80);

  if (!isFlickering && random() < params.flickerPercent) {
    isFlickering = true;
    flickerTimer = 1000 * randomGaussian() * params.avgFlickerDuration;
    flickerStart = millis();
  }
  
  if (isFlickering && millis() - flickerStart > flickerTimer) {
    isFlickering = false;
  }
  
  if (params.flickerPercent == 0) isFlickering = false;
  if (params.flickerPercent == 1) isFlickering = true;
  if (!params.flicker) isFlickering = false;
  
  for (let flake of snowflakes) {
    flake.update();
    flake.show();
  }

  fill(240);
  noStroke();
  rect(0, height - 80, width, 80);

  let bounce = sin(frameCount * 0.05) * 5;
  push();
  translate(width / 2, height - 120 + bounce);
  drawSnowman(isFlickering);
  pop();
  
  if (isFlickering) {
    let red = 0.1 * (millis() - flickerStart);
    if (red > 64) red = 64;
    fill(255, 0, 0, red);
  } else {
    fill(0, 180);
  }
  noStroke();
  rect(0, 0, width, height);
}

function drawSnowman(evil) {
  let evilness = 0;
  if (evil) {
    evilness = (millis() - flickerStart) / 200;
  }
  if (evilness > 10) {
    evilness = 10;
  }
  
  // Body
  fill(255);
  ellipse(0, 80, 140);   // bottom
  ellipse(0, 0, 110);    // middle
  ellipse(0, -90, 80);   // head

  // Eyes
  if (!evil) {
    fill(0);
    noStroke();
    ellipse(-10, -95, 5);
    ellipse(10, -95, 5);
    
  } else {
    let eyePairs = floor(evilness / 2);
    eyePairs = constrain(eyePairs, 1, 6);

    for (let i = 0; i < eyePairs; i++) {
      let yOffset = map(i, 0, eyePairs - 1, -100, -80);
      let xOffset = evil ? sin(frameCount * 0.05 + i) * 4 : 0;
      let eyeSize = evil ? 6 + i * 1.2 : 5;

      fill(255, 0, 0);
      noStroke();
      
      ellipse(-10 + xOffset, yOffset, eyeSize);
      ellipse( 10 + xOffset, yOffset, eyeSize);

      if (evil && evilness > 6) {
        fill(0);
        ellipse(-10 + xOffset, yOffset, eyeSize / 2);
        ellipse( 10 + xOffset, yOffset, eyeSize / 2);
      }
    }
  }

  // Nose
  if (!evil) {
    fill(255, 150, 0);
    triangle(0, -90, 30, -85, 0, -80);
  }

  // Buttons
  fill(0);
  ellipse(0, -10, 6);
  ellipse(0, 10, 6);
  ellipse(0, 30, 6);

  // Arms
  function drawArm(x1, y1, x2, y2, maxDepth = 0, depth = 0) {
    stroke(120, 70, 15);
    strokeWeight(4);
    
    line(x1, y1, x2, y2);    
    if (depth >= maxDepth) return;
    if (!evil) return;
    
    for (let i = 0; i < 1 + floor(noiseRandom() * 3); i++) {
      let angle = atan2(y2 - y1, x2 - x1) + noiseRandom() * 2 * PI / 2 - PI / 2;
      let len = 2 * noiseRandom() * sqrt((y2 - y1) ** 2 + (x2 - x1) ** 2);

      let nx = x2 + cos(angle) * len;
      let ny = y2 + sin(angle) * len;

      stroke(120, 70, 15, 50);
      strokeWeight(2);
      drawArm(x2, y2, nx, ny, maxDepth, depth + 1);
    }
  }
  
  // Left arm (static)
  drawArm(-55, -5, -110, -40, evilness);

  // Right arm (animated wave)
  push();
  translate(55, -5);
  
  armAngle = sin(frameCount * 0.08) * 0.6;
  rotate(armAngle);
  drawArm(0, 0, 60, -40, evilness);
  pop();
}

class Snowflake {
  constructor() {
    this.x = random(width);
    this.y = random(-height, height);
    this.size = random(2, 5);
    this.speed = random(1, 3);
  }

  update() {
    this.y += this.speed;
    if (this.y > height) {
      this.y = random(-50, -10);
      this.x = random(width);
    }
  }

  show() {
    noStroke();
    
    if (isFlickering) {
      fill(255, 0, 0);
    } else {
      fill(255);    
    }
    ellipse(this.x, this.y, this.size);
  }
}
{{</p5js>}}

{{< taxonomy-list "series" "Genuary 2026" >}}
