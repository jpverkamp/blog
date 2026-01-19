---
title: "Genuary 2026.18: Unexpected paths"
date: "2026-01-18"
programming/languages:
- JavaScript
programming/topics:
- Generative Art
- Procedural Content
- p5js
series:
- Genuary 2026
cover: gen26.18.png
---
I feel like the most unexpected of paths is [[wiki:Langton's Ant]]()!.

Okay, it's fairly expected. And I've even [[Langton's ant|done it before]](). Been a while though.

Anyways, here we go!

In a nutshell, you have a grid with N possible values (the length of the rule string). For each pattern, when the 'ant' walks on that cell, the value in incremented by one and you will turn according to these rules:

* `R` turn right (90° or 60° in hex)
* `L` turn left (same)
* `S` turn right 120° in hex mode (nothing in square)
* `M` turn left 120° in hex mode
* `U` turn 180° in hex mode
* anything else (`N` above), do nothing/go straight

This ends up with some really interesting behavior for such a short ruleset. Langton's Ant (LR, the default) is definitely an interesting one. For 10,000 ticks, you get chaotic behavior... and then suddenly it stabilizes!

Here are some interesting patterns:

* [RLR - chaotic growth](?rule=RLR)
* [LLRR - symmetric growth](?rule=LLRR)
* [LRRRRRLLR - square filling](?rule=LRRRRRLLR)
* [LLRRRLRLRLLR - convoluted highway](?rule=LLRRRLRLRLLR)
* [RRLLLRLLLRRR - fills a triangle](?rule=RRLLLRLLLRRR)
* [MNNLML - hex circular growth](?rule=MNNLML&hexGrid=true)
* [LMNUMLS - hex spiral growth](?rule=LMNUMLS&hexGrid=true)

You can also do some interesting things with multiple ants (they'll spawn in a circle):

* [circular](?rule=NRL&antCount=100&spawnRadius=100)

<br> 

<!--more-->

{{<p5js width="600" height="440">}}
let gui;
let params = {
  rule: "RL",
  antCount: 1, antCountMin: 1, antCountMax: 100,
  spawnRadius: 10, spawnRadiusMin: 0, spawnRadiusMax: 100,
  dieOfOldAge: false,
  maxAge: "100",
  updatesPerTick: 1, updatesPerTickMin: 1, updatesPerTickMax: 1000,
  hexGrid: false,
  colorScheme: [
    "rainbow",
    "fire",
    "ocean",
    "forest",
    "pastel",
    "monochrome",
  ],
};

const HEX_DIRS = [
  { x:  1, y:  0 },
  { x:  0, y:  1 },
  { x: -1, y:  1 },
  { x: -1, y:  0 },
  { x:  0, y: -1 },
  { x:  1, y: -1 },
];

const SQUARE_DIRS = [
  { x:  0, y: -1 },
  { x:  1, y:  0 },
  { x:  0, y:  1 },
  { x: -1, y:  0 },
];


let lastParams;
let paused = false;

let ants;
let tiles;
let bounds;

const randomD = () => {
  const r = Math.floor(Math.random() * 4);
  return [
    { x:  1, y:  0 },
    { x: -1, y:  0 },
    { x:  0, y:  1 },
    { x:  0, y: -1 },
  ][r];
};

function setup() {
  createCanvas(400, 400);
  colorMode(HSB, 360, 100, 100, 100);
  
  gui = createGuiPanel("params");
  gui.addObject(params);
  gui.setPosition(420, 0);
}

function draw() {
  if (lastParams == undefined || Object.keys(params).some(k => params[k] !== lastParams[k])) {
    ants = [];
    for (let i = 0; i < params.antCount; i++) {
      let x = floor(cos(i * TWO_PI / params.antCount) * params.spawnRadius);
      let y = floor(sin(i * TWO_PI / params.antCount) * params.spawnRadius);
      
      ants.push({
        position: {x, y},
        direction: 0,
        age: 0,
      });
    }
    
    tiles = new Map();
    
    bounds = {
      minX: ants[0].position.x,
      maxX: ants[0].position.x,
      minY: ants[0].position.y,
      maxY: ants[0].position.y,
    };
    for (let ant of ants) {
      bounds.minX = min(bounds.minX, ant.position.x);
      bounds.maxX = max(bounds.maxX, ant.position.x);
      bounds.minY = min(bounds.minY, ant.position.y);
      bounds.maxY = max(bounds.maxY, ant.position.y);
    }
    
    paused = false;
    lastParams = {...params};
  }
  
  if (paused) {
    return;
  }
  
  for (let tick = 0; tick < params.updatesPerTick; tick++) {
    for (let ant of ants) {
      ant.age += 1;
    
      let positionString = `${ant.position.x},${ant.position.y}`
      let ruleIndex = tiles.get(positionString) || 0;
      tiles.set(positionString, (ruleIndex + 1) % params.rule.length);

      let ruleValue = params.rule[ruleIndex];

      if (params.hexGrid) {
        if (ruleValue === 'L') ant.direction = (ant.direction + 5) % 6;      // -60°
        else if (ruleValue === 'R') ant.direction = (ant.direction + 1) % 6; // +60°
        else if (ruleValue === 'M') ant.direction = (ant.direction + 4) % 6; // -120°
        else if (ruleValue === 'S') ant.direction = (ant.direction + 2) % 6; // +120°
        else if (ruleValue === 'U') ant.direction = (ant.direction + 3) % 6; // +180°
      } else {
        if (ruleValue === 'L') ant.direction = (ant.direction + 3) % 4;
        else if (ruleValue === 'R') ant.direction = (ant.direction + 1) % 4;
        else if (ruleValue === 'U') ant.direction = (ant.direction + 2) % 4;
      }

      let d = (params.hexGrid ? HEX_DIRS : SQUARE_DIRS)[ant.direction];

      ant.position.x += d.x;
      ant.position.y += d.y;

      bounds.minX = min(bounds.minX, ant.position.x);
      bounds.maxX = max(bounds.maxX, ant.position.x);
      bounds.minY = min(bounds.minY, ant.position.y);
      bounds.maxY = max(bounds.maxY, ant.position.y);
    }

    if (params.dieOfOldAge) {
      let maxAge = parseInt(params.maxAge);
      if (!isNaN(maxAge)) {        
        for (let j = ants.length - 1; j >= 0; j--) {
          if (ants[j].age > maxAge) {
            ants.splice(j, 1);
          }
        }
      }
    }
  }

  background("black");
  let tilesWide = bounds.maxX - bounds.minX + 1;
  let tilesTall = bounds.maxY - bounds.minY + 1;
  
  let cellSize = min(width / tilesWide, height / tilesTall);
  if (cellSize < 1) {
    cellSize = 1;
    paused = true;
  } 
  if (ants.length == 0) {
    paused = true;
  }

  push();
  
  translate(
    width / 2 - (bounds.minX + tilesWide / 2) * cellSize,
    height / 2 - (bounds.minY + tilesTall / 2) * cellSize
  );

  noStroke();
  
  for (let [key, value] of tiles.entries()) {
    let [x, y] = key.split(",").map(Number);

    if (params.colorScheme === "monochrome") {
      fill(0, 0, map(value, 0, params.rule.length, 100, 50));
    } else if (params.colorScheme === "pastel") {
      let hue = map(value, 0, params.rule.length, 0, 360);
      fill(hue, 30, 100);
    } else if (params.colorScheme === "fire") {
      let hue = map(value, 0, params.rule.length, 30, 60);
      fill(hue, 100, 100);
    } else if (params.colorScheme === "ocean") {
      let hue = map(value, 0, params.rule.length, 180, 240);
      fill(hue, 100, 100);
    } else if (params.colorScheme === "forest") {
      let hue = map(value, 0, params.rule.length, 90, 150);
      fill(hue, 100, 50);
    } else  if (params.colorScheme === "rainbow") {
      let hue = map(value, 0, params.rule.length, 0, 360);
      fill(hue, 100, 100);
    }

    rect(
      x * cellSize,
      y * cellSize,
      cellSize,
      cellSize
    );
  }

  fill(0);
  for (let ant of ants) {
    rect(
      ant.position.x * cellSize,
      ant.position.y * cellSize,
      cellSize,
      cellSize
    );
  }

  pop();  
}
{{</p5js>}}
