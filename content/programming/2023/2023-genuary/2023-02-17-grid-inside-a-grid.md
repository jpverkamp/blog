---
title: "Genuary 2023.17: A grid inside a grid inside a grid"
date: 2023-02-17
programming/languages:
- JavaScript
programming/topics:
- Generative Art
- Procedural Content
- p5js
series:
- Genuary 2023
cover: /embeds/2023/genuary-17.png
---
[Genuary](https://genuary.art/)! 

Spend a month making one beautiful thing per day, given a bunch of prompts. A month late, but as they say, 'the second best time is now'.  

Let's do it!

## 17) A grid inside a grid inside a grid

<!--more-->

{{<p5js width="600" height="420">}}
let gui;
let params = {
  N: 2,
  NMin: 2,
  NMax: 8,
  
  fillChance: 0.85,
  fillChanceMin: 0.01,
  fillChanceMax: 0.99,
  fillChanceStep: 0.01,
  
  breadthFirst: true,
  colorful: false,
  
  updatesPerFrame: 10,
  updatesPerFrameMin: 1,
  updatesPerFrameMax: 100,
};
let lastParams;

const MIN_SIZE = 2;

let queue;

function setup() {
  createCanvas(400, 400);
  colorMode(HSL, 100);
  
  queue = [{x: 0, y: 0, w: 400, h: 400}];
  
  gui = createGuiPanel('params');
  gui.addObject(params);
  gui.setPosition(420, 0);
}

function draw() {
  if (lastParams != JSON.stringify(params)) {
    queue = [{x: 0, y: 0, w: 400, h: 400}];
    lastParams = JSON.stringify(params);
  }
  
  for (let i = 0; i < params.updatesPerFrame; i++) {
    if (queue.length == 0) {
      return;
    }

    let {x, y, w, h} = params.breadthFirst ? queue.shift() : queue.pop();
    
    for (let nx = 0; nx < params.N; nx++) {
      for (let ny = 0; ny < params.N; ny++) {
        let subw = w / params.N;
        let subh = h / params.N;
        let subx = x + nx * subw;
        let suby = y + ny * subh;

        if (params.colorful) {
          stroke(
            random(100),
            100,
            75,
          );
        } else {
          stroke(100, 100, 0, 100);
        }
        rect(subx, suby, subw, subh);

        if (subw > MIN_SIZE && subh > MIN_SIZE && random() < params.fillChance)         {
          queue.push({x: subx, y: suby, w: subw, h: subh});
        }
      }
    }
  }
}
{{</p5js>}}

{{< taxonomy-list "series" "Genuary 2023" >}}
