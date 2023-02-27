---
title: "Genuary 2023.26: My kid could have made that"
date: '2023-02-26 23:00:00'
programming/languages:
- JavaScript
programming/topics:
- Generative Art
- Procedural Content
- p5js
series:
- Genuary 2023
cover: /embeds/2023/genuary-26.png
---
[Genuary](https://genuary.art/)! 

Spend a month making one beautiful thing per day, given a bunch of prompts. A month late, but as they say, 'the second best time is now'.  

Let's do it!

## 26) My kid could have made that

<!--more-->

Generic four legged animal generator. Or something like that? 

Mostly, I made a function that can render a bunch of offsets as a polygon and then manually programmed a bunch of parameterized offsets. 

That took longer than it probably should have. :smile:

{{<p5js width="600" height="800">}}
let gui;
let params = {
  margin: 30,
  midpoint: 150,
  
  neckOffset: 10,
  neckLength: 50,
  neckWidth: 15,
  
  headWidth: 50,
  headHeight: 30,
  
  bodyThickness: 50,
  
  backLegWidth: 50,
  backLegLength: 100,
  backLegSpread: 20,
  
  frontLegWidth: 25,
  frontLegLength: 140,
  frontLegSpread: 15,
}


function setup() {
  createCanvas(400, 400);
  background("white");
  frameRate(5);
  
  gui = createGuiPanel('params');
  gui.addObject(params);
  gui.setPosition(420, 0);
}

function draw() {
  if (frameCount % 10 == 0) {
    background("white");
  }
  
  stroke("purple");
  noFill();
  
  let margin = 30;
  let midpoint = 200;
  
  let locals = {...params};
  for (let key in locals) {
    locals[key] *= 1 + random() / 10;
  }
  
  push();
  translate(locals.margin, locals.midpoint);
  relativePolygon([
    // Neck up
    [locals.neckOffset, 0],
    [-locals.neckOffset, -locals.neckLength],
    // Head
    [locals.neckWidth/2 - locals.headWidth/2, 0],
    [0, -locals.headHeight],
    [locals.headWidth, 0],
    [0, locals.headHeight],
    [-locals.headWidth/2 + locals.neckWidth/2, 0],
    // Neck down
    [locals.neckOffset, locals.neckLength],
    // Across back
    [
      - ( // Rest neck
        locals.neckOffset + locals.neckWidth
      )
      + ( // Rest of back
        width - 2 * locals.margin
      ),  
      0
    ],
    // 4th leg
    [0, locals.bodyThickness + locals.backLegLength],
    [-locals.backLegWidth, 0],
    [0, -locals.backLegLength],
    // 3/4 split
    [-locals.backLegSpread, 0],
    // 3rd leg
    [0, locals.backLegLength],
    [-locals.backLegWidth, 0],
    [0, -locals.backLegLength],
    // Across belly
    [0
      + ( // Go back to the butt
        2 * (locals.backLegWidth) 
        + locals.backLegSpread
      )
      - ( // Go to the front
        width 
        - 2 * locals.margin
      )
      + ( // Go back across front legs
        2 * locals.frontLegWidth
        + locals.frontLegSpread
      ),
      0
    ],
    // 2nd leg
    [0, locals.frontLegLength],
    [-locals.frontLegWidth, 0],
    [0, -locals.frontLegLength],
    // 1/2 split
    [-locals.frontLegSpread, 0],
    // 1st leg
    [0, locals.frontLegLength],
    [-locals.frontLegWidth, 0],
    [0, -locals.frontLegLength],
  ]);
  pop();
  
  
}

function relativePolygon(offsets) {
  beginShape();
  vertex(0, 0);
  let x = 0, y = 0;
  for (let [xd, yd] of offsets) {
    x += xd;
    y += yd;
    vertex(x, y);
  }
  endShape(CLOSE);
}
{{</p5js>}}

{{< taxonomy-list "series" "Genuary 2023" >}}
