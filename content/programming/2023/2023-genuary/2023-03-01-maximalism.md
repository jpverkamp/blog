---
title: "Genuary 2023.29: Maximalism"
date: 2023-03-01
programming/languages:
- JavaScript
programming/topics:
- Generative Art
- Procedural Content
- p5js
- Line Art
series:
- Genuary 2023
cover: /embeds/2023/genuary-29.png
---
[Genuary](https://genuary.art/)! 

Spend a month making one beautiful thing per day, given a bunch of prompts. A month late, but as they say, 'the second best time is now'.  

Let's do it!

## 29) Maximalism

<!--more-->

{{<p5js width="600" height="800">}}
let gui;
let params = {
  lineWeight: 0.1, lineWeightMin: 0, lineWeightMax: 2.0, lineWeightStep: 0.01,
  lineStepSize: 10, lineStepSizeMin: 1,
  colorful: ['no', 'yes', 'very'],
  balls: 5,
  doubleBalls: true,
  solidBalls: false,
}

let WORK_IT;
let COLORS = [
  "red",
  "green",
  "blue",
  "cyan",
  "magenta",
  "yellow",
  "black",
]

function setup() {
  createCanvas(400, 400);
  
  WORK_IT = {
    topLeft: {},
    topRight: {x: width, r: TWO_PI * 1/4},
    bottomLeft: {y: height, r: TWO_PI * 3/4},
    bottomRight: {x: width, y: height, r: TWO_PI * 2/4},

    centerTopLeft: {s: 0.5, x: width / 2, y: height / 2, r: TWO_PI * 2/4},
    centerTopRight: {s: 0.5, x: width / 2, y: height / 2, r: TWO_PI * 3/4},
    centerBottomLeft: {s: 0.5, x: width / 2, y: height / 2, r: TWO_PI * 1/4},
    centerBottomRight: {s: 0.5, x: width / 2, y: height / 2},
    
    smallTopLeft: {s: 0.5},
    smallTopRight: {s: 0.5, x: width, r: TWO_PI * 1/4},
    smallBottomLeft: {s: 0.5, y: height, r: TWO_PI * 3/4},
    smallBottomRight: {s: 0.5, x: width, y: height, r: TWO_PI * 2/4},
  };
  
  for (let key in WORK_IT) {
    params[key] = random() < 0.5;
  }
 
  gui = createGuiPanel('params');
  gui.addObject(params);
  gui.setPosition(420, 0);
}

function draw() {
  noLoop();
  background("white");
  
  // BALLS
  strokeWeight(1);
  noStroke();
  noFill();
  (params.solidBalls ? fill : stroke)("black");
  
  for (let i = 0; i < params.balls; i++) {
    let r = max(width, height) / 2 * i / params.balls;
    let a = TWO_PI * i / params.balls;
    let x = width / 2 + r * cos(a);
    let y = height / 2 + r * sin(a);
    
    if (params.colorful != 'no') {
      (params.solidBalls ? fill : stroke)(random(COLORS));
    }
    circle(x, y, r);
    
    if (params.doubleBalls) {
      x = width / 2 - r * cos(a);
      y = height / 2 - r * sin(a);

      if (params.colorful != 'no') {
        (params.solidBalls ? fill : stroke)(random(COLORS));
      }
      circle(x, y, r);
    }
  }

  // LINES
  strokeWeight(params.lineWeight);
  stroke("black");
  
  for (let i = 0; i <= max(width, height); i += params.lineStepSize) {
    for (let key in WORK_IT) {
      if (params[key]) {
        if (params.colorful == 'yes') {
          stroke(random(COLORS));
        }
        missyElliott(doLines, WORK_IT[key]);
      }
    }
  }
}


function doLines() {
  let size = max(width, height);
  for (let i = 0; i <= size; i += params.lineStepSize) {
    if (params.colorful == 'very') {
      stroke(random(COLORS));
    }
    
    line(i, 0, 0, size - i);
  }
}

function missyElliott(thunk, options) {
  let {x, y, r, s} = options || {};
  
  push();
  {
    translate(x || 0, y || 0);
    if (r && r != 0) rotate(r);
    if (s && s != 1) scale(s);
  
    thunk();
  }
  pop();
}
{{</p5js>}}

{{< taxonomy-list "series" "Genuary 2023" >}}
