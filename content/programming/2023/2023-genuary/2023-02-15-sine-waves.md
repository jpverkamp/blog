---
title: "Genuary 2023.15: Sine Waves"
date: 2023-02-15
programming/languages:
- JavaScript
programming/topics:
- Generative Art
- Procedural Content
- p5js
series:
- Genuary 2023
cover: /embeds/2023/genuary-15.png
---
[Genuary](https://genuary.art/)! 

Spend a month making one beautiful thing per day, given a bunch of prompts. A month late, but as they say, 'the second best time is now'.  

Let's do it!

## 15) Sine waves

> [Fun with sine waves: 1D wobbly noise](https://www.desmos.com/calculator/nhbzwkhij3)

<!--more-->

Sine waves! Noise! Suuuuper saturated colors!

{{<p5js width="600" height="420">}}
let gui;
let params = {
  timeScale: 100, timeScaleMin: 10, timeScaleMax: 1000,
  scale: 20, scaleMin: 10, scaleMax: 100,
  trigScale: 10,
  translateScale: 100, translateScaleMax: 1000,
}

function setup() {
  createCanvas(400, 400);
  colorMode(HSB, 100);
  
  gui = createGuiPanel('params');
  gui.addObject(params);
  gui.setPosition(420, 0);
}

function draw() {
  let tf = 1.0 * sin(frameCount / params.timeScale);
  
  let swidth = width / params.scale;
  let sheight = height / params.scale;
  
  for (let x = -swidth; x < swidth * 2; x++) {
    for (let y = -sheight; y < sheight * 2; y++) {
      let xf = 1.0 * x / swidth;
      let yf = 1.0 * y / sheight;
      
      let h = parseInt(
        50 + 50 * sin(1.0 * params.trigScale * noise(xf, yf, tf))
      );
      let s = 100;
      let l = 100;
      
      push();
      {
        translate(
          1.0 * params.translateScale * sin(xf + tf),
          1.0 * params.translateScale * sin(yf + tf)
        );
        noStroke();
        fill(h, s, l, 100);     
        rect(
          x * params.scale,
          y * params.scale,
          params.scale,
          params.scale
        );
      }
      pop();
    }
  }
}
{{</p5js>}}

{{< taxonomy-list "series" "Genuary 2023" >}}
