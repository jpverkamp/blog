---
title: "Genuary 2026.04: lowres"
date: "2026-01-04 00:00:10"
programming/languages:
- JavaScript
programming/topics:
- Generative Art
- Procedural Content
- p5js
series:
- Genuary 2026
cover: gen26.04.png
---
## 4) lowres

Perlin noise, but ... really lowres? You can play with how low res or how many colors you want. 

<!--more-->

{{<p5js width="600" height="420">}}
let gui;
let params = {
  lowRes: 16, lowResMin: 1, lowResMax: 100,
  colors: 16, colorsMin: 1, colorsMax: 64,
  threshold: 0.5, thresholdMin: 0, thresholdMax: 1, thresholdStep: 0.01,
  varyValue: false,
};

function setup() {
  createCanvas(400, 400);
  colorMode(HSB, 360, 100, 100);
  noSmooth();

  gui = createGuiPanel('params');
  gui.addObject(params);
  gui.setPosition(420, 0);
}

function draw() {
  for (let y = 0; y < params.lowRes; y++) {
    for (let x = 0; x < params.lowRes; x++) {
      let real_w = width / params.lowRes;
      let real_h = height / params.lowRes;
      let real_x = real_w * x;
      let real_y = real_h * y;
      
      let n = noise(
        x * 0.08,
        y * 0.08,
        frameCount * 0.02
      );
      
      let n2 = noise(
        (10 * params.lowRes + x) * 0.08,
        (10 * params.lowRes + y) * 0.08,
        1 + frameCount * 0.04
      );
      
      fill(0);

      if (n > params.threshold) {
        let hp = (n - params.threshold) / (1 - params.threshold);
        hp = constrain(hp, 0, 1);
        hp = pow(hp, 1.5);
        
        let h = floor(hp * params.colors) * (360 / params.colors);
        
        if (params.varyValue) {
          fill(h, 100, n2 * 50 + 50);
        } else {
          fill(h, 100, 100);
        }
        
      }
      
      rect(real_x, real_y, real_w, real_h);
    }
  }
}
{{</p5js>}}

{{< taxonomy-list "series" "Genuary 2026" >}}
