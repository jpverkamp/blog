---
title: "Genuary 2026.03: Fibonacci forever"
date: 2026-01-03
programming/languages:
- JavaScript
programming/topics:
- Generative Art
- Procedural Content
- p5js
series:
- Genuary 2026
cover: cover.png
---
## 3) Fibonacci forever

[[wiki:Fibonacci]]()

This is entirely based around this Fibonacci generator function:

```javascript
function makeFibber(maxValue = 1000) {
  let a = 1;
  let b = 1;
  return () => {
    let n = a + b;
    a = b;
    b = n;
    if (b > maxValue) {
      a = 1;
      b = 1;
    }
    return a;
  };
}
```

Make a `fibber` and then just keep calling it for next values. 

All sorts of exciting options here!

<!--more-->

{{<p5js width="600" height="420">}}
let gui;
let params = {
  gridWidth: 10, gridWidthMin: 1, gridWidthMax: 50,
  gridHeight: 10, gridHeightMin: 1, gridHeightMax: 50,
  fibColor: true,
  fibHueStep: true,
  fibSize: true,
  fibSizeStep: true,
  circlize: true,
  enableRotation: true,
  animateScale: true,
  fibRotation: true,
  fibRadiusScale: true,
  fibPhaseOffset: true,
  persistFrames: true,
};

let hueFib, sizeFib, rotationFib, radiusFib, phaseFib;

function makeFibber(maxValue = 1000) {
  let a = 1;
  let b = 1;
  return () => {
    let n = a + b;
    a = b;
    b = n;
    if (b > maxValue) {
      a = 1;
      b = 1;
    }
    return a;
  };
}

function setup() {
  createCanvas(400, 400);
  colorMode(HSB, 360, 100, 100);
  background(0);

  gui = createGuiPanel('params');
  gui.addObject(params);
  gui.setPosition(420, 0);

  hueFib = makeFibber(360);
  sizeFib = makeFibber(100);
  rotationFib = makeFibber(360);
  radiusFib = makeFibber(50);
  phaseFib = makeFibber(10);
}

function draw() {
  if (!params.persistFrames) {
    background(0, 0, 0);
  }

  let centerX = width / 2;
  let centerY = height / 2;

  let w = width / params.gridWidth;
  let h = height / params.gridHeight;

  for (let gridY = 0; gridY < params.gridHeight; gridY++) {
    for (let gridX = 0; gridX < params.gridWidth; gridX++) {
      let x = gridX * w + w / 2;
      let y = gridY * h + h / 2;

      if (params.circlize) {
        let index = gridY * params.gridWidth + gridX;
        let angle = index * 137.5;
        let radius = sqrt(index) * (params.fibRadiusScale ? radiusFib() : width / 20);
        x = centerX + radius * cos(radians(angle));
        y = centerY + radius * sin(radians(angle));
      }

      if (params.enableRotation) {
        let dx = x - centerX;
        let dy = y - centerY;
        let r = sqrt(dx*dx + dy*dy);
        let theta = atan2(dy, dx);
        let rot = params.fibRotation ? radians(rotationFib() % 360) * 0.01 : 0.01;
        theta += rot + frameCount * 0.01;
        x = centerX + r * cos(theta);
        y = centerY + r * sin(theta);
      }

      let diameter = params.fibSize ? sizeFib() % w : w * 0.8;
      if (params.fibSizeStep && params.animateScale) {
        let phase = params.fibPhaseOffset ? phaseFib() % 10 : 0;
        diameter *= 0.5 + 0.5 * sin(frameCount / 20 + (gridX + gridY + phase) / 2);
      }

      let hue;
      if (params.fibColor) {
        hue = hueFib();
        if (params.fibHueStep) hue += frameCount;
      } else {
        hue = (x + y) % 360;
      }

      fill(hue % 360, 100, 100);
      noStroke();
      ellipse(x, y, diameter, diameter);
    }
  }
}
{{</p5js>}}

{{< taxonomy-list "series" "Genuary 2026" >}}
