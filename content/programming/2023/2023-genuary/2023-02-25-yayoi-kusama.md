---
title: "Genuary 2023.25: Yayoi Kusama"
date: '2023-02-25 23:00:00'
programming/languages:
- JavaScript
programming/topics:
- Generative Art
- Procedural Content
- p5js
series:
- Genuary 2023
cover: /embeds/2023/genuary-25.png
---
[Genuary](https://genuary.art/)! 

Spend a month making one beautiful thing per day, given a bunch of prompts. A month late, but as they say, 'the second best time is now'.  

Let's do it!

## 25) Yayoi Kusama

Wikipedia: {{<wikipedia "Yayoi Kusama">}}

<!--more-->

It's got a bunch of orange dots like hers? I think the inspiration for this one is loose at best. But it's mesmerizing to watch. :smile:

{{<p5js width="600" height="420">}}
let gui;
let params = {
  dotScale: 1.4, dotScaleMin: 1.01, dotScaleMax: 2.0, dotScaleStep: 0.01,
  waveCount: 3, waveCountMin: 1, waveCountMax: 20,
  colorize: false,
  colorizePerWave: false,
}


function setup() {
  createCanvas(400, 400);
  
  gui = createGuiPanel('params');
  gui.addObject(params);
  gui.setPosition(420, 0);
}

function draw() {
  background(0);
  let p = generatePillar();
  randomSeed(1);
  
  for (let wave = 0; wave < params.waveCount; wave++) {
    if (params.colorizePerWave) {
      p = generatePillar();
    }
    
    let r = 10 * random();
    for (let y = 0; y < height; y++) {
      let x = 100 + 100 * cos(1.0 * y / height + frameCount / 10.0 + 3 * wave / 10 + r);
      image(p, x, y, 200, 1, 0, y, 200, 1);
    }
  }
}

function generatePillar() {
  let g = createGraphics(200, 400);
  g.background("black");
  
  g.noStroke();
  g.fill("orange");
  
  let offset = 1;
  for (let size = 1; offset < 100; size *= params.dotScale) {
    for (let y = 0; y < height; y += size * 2) {
      if (params.colorize) {  
        g.fill(randomRGB());
      }
      g.circle(offset, y, size);
      g.circle(200 - offset, y, size);
    }
    
    offset += size * 2;
  }
  
  return g;
}

function randomRGB() {
  return [
    random(255),
    random(255),
    random(255)
  ];
}
{{</p5js>}}

{{< taxonomy-list "series" "Genuary 2023" >}}
