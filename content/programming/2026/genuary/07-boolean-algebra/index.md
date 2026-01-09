---
title: "Genuary 2026.07: Boolean algebra"
date: "2026-01-07"
programming/languages:
- JavaScript
programming/topics:
- Generative Art
- Procedural Content
- p5js
series:
- Genuary 2026
cover: gen26.07.png
---
## 5) Boolean algebra

So the basic idea here is to recursively divide the space. The black squares are the randomly chosen values. Then, for each level of the tree, combine the children using one of the selected functions (and/or/xor/etc), drawing a border if the result of that combination is true. 

Try various combinations of settings!

<!--more-->

{{<p5js width="600" height="420">}}
let gui;
let params = {
  divisions: 7, divisionsMax: 12,
  offset: 3, offsetMax: 20,
  andEnabled: true,
  orEnabled: true,
  xorEnabled: true,
  notAEnabled: false,
  notBEnabled: false,
  randomEnabled: false,
  randomSplits: false,
  colorsEnabled: true,
};

let operators;

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

function setup() {
  createCanvas(400, 400);
    
  gui = createGuiPanel('params');
  gui.addObject(params);
  gui.setPosition(420, 0);
}

function draw() {
  background("white");
  noStroke();
  fill("black");
  
  operators = [];
  
  if (params.andEnabled) {
    operators.push({
      f: (a, b) => a && b,
      c: "red"
    });
  }

  if (params.orEnabled) {
    operators.push({
      f: (a, b) => a || b,
      c: "green"
    });
  }

  if (params.xorEnabled) {
    operators.push({
      f: (a, b) => (a && !b) || (!a && b),
      c: "blue"
    });
  }

  if (params.notAEnabled) {
    operators.push({
      f: (a, b) => !a,
      c: "yellow"
    });
  }

  if (params.notBEnabled) {
    operators.push({
      f: (a, b) => !b,
      c: "cyan"
    });
  }
  
  if (params.randomEnabled) {
    operators.push({
      f: (a, b) => noiseRandom() > 0.5,
      c: "magenta"
    })
  }
  
  booleanAlgebra(0, 0, width, height, 0);
}

function booleanAlgebra(x, y, w, h, d) {
  let v = noiseRandom() < 0.5;
  
  if (d >= params.divisions) {
    if (w < 1) w = 1;
    if (h < 1) h = 1;
    
    if (v) {
      fill("black");
      stroke("white")
      rect(x, y, w, h);
    }
    return v;
  }

  // Bounds offset
  let sx = x + params.offset;
  let sy = y + params.offset;
  let sw = w - 2 * params.offset;
  let sh = h - 2 * params.offset;

  // The half width/height and halfway x/y
  let sw2 = sw / 2;
  let sx2 = sx + sw2;
  let sh2 = sh / 2;
  let sy2 = sy + sh2;

  // Split horiz/verti/horiz/etc
  let a, b;
  let split_x = d % 2 == 0;
  if (params.randomSplits) {
    split_x = noiseRandom() < 0.5;
  }
  
  if (split_x) {
    a = booleanAlgebra(sx, sy, sw2, sh, d + 1);
    b = booleanAlgebra(sx2, sy, sw2, sh, d + 1);
  } else {
    a = booleanAlgebra(sx, sy, sw, sh2, d + 1);
    b = booleanAlgebra(sx, sy2, sw, sh2, d + 1);
  }

  // Randomly choose operation to apply
  if (operators.length > 0) {
    let op = operators[floor(operators.length * noiseRandom())];
    v = op.f(a, b);

    // Borders based on that value
    if (v) {
      noFill();
      if (params.colorsEnabled) {
        stroke(op.c);
      } else {
        stroke("black");
      }
      
      rect(x, y, w, h);
    }
  }
  
  return v;
}
{{</p5js>}}

{{< taxonomy-list "series" "Genuary 2026" >}}
