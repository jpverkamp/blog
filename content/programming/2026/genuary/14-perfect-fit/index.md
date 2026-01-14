---
title: "Genuary 2026.14: Fits Perfectly"
date: "2026-01-14"
programming/languages:
- JavaScript
programming/topics:
- Generative Art
- Procedural Content
- p5js
series:
- Genuary 2026
cover: gen26.14.png
---
## 14) Fits Perfectly

Basically, we'll pack as many circles in as we can!

* `retriesPerFrame` is how many circles it will try to place before giving up and drawing the frame
* `minDiameter` is the smallest a circle can be (this should be 1 for a 'perfect fit')
* `maxDiameter` is the largest one can be
* `spacing` is how much space to leave between circles (this should be 0 a 'perfect fit')
* `borders` will draw a black border on each circle
* `fillInside` will place circles *inside* of each other as well as outside, so long as there is still enough `spacing`
* `blackPercent` is how many of the circles will be black rather than bright colors

Here is an example with diameter 1-200; spacing 0, and fillInside/black off. I did max out retriesPerFrame, but this still took a while, since even with 100/frame, the last few empty spots have a ~1/100,000 chance of being chosen. 

![An image matching the prompt with an actually full space](prompt.png)

<!--more-->

{{<p5js width="600" height="460">}}
let gui;
let params = {
  retriesPerFrame: 10,
  minDiameter: 3, minDiameterMin: 1, minDiameterMax: 100,
  maxDiameter: 100, maxDiameterMin: 10, maxDiameterMax: 400,
  spacing: 3, spacingMin: -10, spacingMax: 10,
  borders: true,
  fillInside: true,
  blackPercent: 0.25, blackPercentMin: 0, blackPercentMax: 1, blackPercentStep: 0.01,
};

let lastParams;
let circles = [];

function setup() {
  createCanvas(400, 400);
  colorMode(HSB, 360, 100, 100);
  
  gui = createGuiPanel("params");
  gui.addObject(params);
  gui.setPosition(420, 0);
}

function intersectsAny(c1) {
  return circles.some((c2) => {
    let dx = c1.x - c2.x;
    let dy = c1.y - c2.y;
    let dist2 = dx * dx + dy * dy;

    let outsideDist = (c1.d + c2.d) / 2 + params.spacing;
    let insideDist  = Math.abs(c2.d - c1.d) / 2 - params.spacing;

    let outside = dist2 >= outsideDist * outsideDist;
    let inside  = insideDist >= 0 && dist2 <= insideDist * insideDist;

    if (params.fillInside) {
      // reject only partial overlaps
      return !(outside || inside);
    } else {
      // reject any overlap
      return !outside;
    }
  });
}

function draw() {
  // Reset if any params change
  if (lastParams == undefined || Object.keys(params).some(k => params[k] !== lastParams[k])) {
    circles = [];
    lastParams = {...params};
  }
  
  // Find a random point not in any previous circle
  let foundOne = false;
  
  for (let i = 0; i < params.retriesPerFrame; i++) {
    let x = floor(random() * width);
    let y = floor(random() * height);
    
    // A 1 pixel circle would fit, so place the largest one we could
    if (!intersectsAny({x, y, d: params.minDiameter})) {    
      for (let d = params.maxDiameter; d >= params.minDiameter; d--) {
        if (!intersectsAny({x, y, d})) {
          foundOne = true;
          circles.push({
            x,
            y,
            d,
            h: floor(random() * 360),
            b: random() < params.blackPercent,
          });
          break;
        }
      }
      
      if (foundOne) {
        break;
      }
    }
  }
  
  background("white");
  for (let {x, y, d, h, b} of circles) {
    if (params.borders) {
      stroke("black");
    } else {
      noStroke();
    }
    
    if (b) {
      fill("black");
    } else {
      fill(h, 100, 100);
    }
    circle(x, y, d);
  }
}
{{</p5js>}}

{{< taxonomy-list "series" "Genuary 2026" >}}
