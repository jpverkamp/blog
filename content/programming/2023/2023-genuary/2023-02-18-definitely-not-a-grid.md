---
title: "Genuary 2023.18: Definitely not a grid"
date: 2023-02-18
programming/languages:
- JavaScript
programming/topics:
- Generative Art
- Procedural Content
- p5js
series:
- Genuary 2023
cover: /embeds/2023/genuary-18.png
---
[Genuary](https://genuary.art/)! 

## 18) Definitely not a grid

<!--more-->

> Good artists borrow, great artists steal.
> 
> -- Pablo Picasso (maybe)

Copy [[Genuary 2023.17: A grid inside a grid inside a grid]](); apply a bunch of translations and rotations. 

*Definitely* not a grid any more. :smile:

{{<p5js width="600" height="420">}}
let gui;
let params = {
  N: 2,
  NMin: 2,
  NMax: 8,
  
  minSize: 4,
  minSizeMin: 1,
  minSizeMax: 85,
  
  fillChance: 0.75,
  fillChanceMin: 0.01,
  fillChanceMax: 0.99,
  fillChanceStep: 0.01,
  
  breadthFirst: true,
  colorBorder: false,
  colorFill: true,
  
  updatesPerFrame: 10,
  updatesPerFrameMin: 1,
  updatesPerFrameMax: 100,
  
  maxTranslation: 10,
  maxTranslationMin: 1,
  maxTranslationMax: 100,
  
  maxRotationDeg: 10,
  maxRotationDegMin: 1,
  maxRotationDegMax: 360,
};
let lastParams;

let queue;

function setup() {
  createCanvas(400, 400);
  colorMode(HSL, 100);
  
  queue = [{x: -200, y: -200, w: 200, h: 200}];
  translate(200, 200);
  
  gui = createGuiPanel('params');
  gui.addObject(params);
  gui.setPosition(420, 0);
}

function draw() {
  if (lastParams != JSON.stringify(params)) {
    queue = [{x: 0, y: 0, w: 400, h: 400}];
    lastParams = JSON.stringify(params);
    background(255);
  }
  
  for (let i = 0; i < params.updatesPerFrame; i++) {
    if (queue.length == 0) {
      return;
    }

    translate(
      2 * params.maxTranslation * random() - params.maxTranslation,
      2 * params.maxTranslation * random() - params.maxTranslation
    );
    let rotate_deg = 2 * params.maxRotationDeg * random() - params.maxRotationDeg;
    rotate(TWO_PI * rotate_deg / 360.0);
    
    let {x, y, w, h} = params.breadthFirst ? queue.shift() : queue.pop();
    
    for (let nx = 0; nx < params.N; nx++) {
      for (let ny = 0; ny < params.N; ny++) {
        let subw = w / params.N;
        let subh = h / params.N;
        let subx = x + nx * subw;
        let suby = y + ny * subh;
        
        let black = [100, 100, 0, 100];
        let color = [random(100), 100, 75];
        
        stroke(params.colorBorder ? color : black);
        fill(params.colorFill ? color : black);
        
        if (!params.colorBorder && !params.colorFill) {
          fill("white");
        }

        rect(subx, suby, subw, subh);

        if (subw > params.minSize && subh > params.minSize && random() < params.fillChance)         {
          queue.push({x: subx, y: suby, w: subw, h: subh});
        }
      }
    }
  }
}
{{</p5js>}}

{{< taxonomy-list "series" "Genuary 2023" >}}
