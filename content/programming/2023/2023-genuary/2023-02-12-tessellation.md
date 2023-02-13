---
title: "Genuary 2023.12: Tessellation"
date: 2023-02-12
programming/languages:
- JavaScript
programming/topics:
- Generative Art
- Procedural Content
- p5js
series:
- Genuary 2023
cover: /embeds/2023/genuary-12.png
---
[Genuary](https://genuary.art/)! 

Spend a month making one beautiful thing per day, given a bunch of prompts. A month late, but as they say, 'the second best time is now'.  

Let's do it!

## 12) Tessellation

Wikipedia: {{<wikipedia "Tessellation">}}
 ({{<wikipedia title="List of Tesselations" text="List">}})

This was not at all the direction I ended to go, but it got really interesting, so I decided to keep it. 

What I remember doing years and years ago, I think roughly around the time of Windows 95 (I feel old) or perhaps even pre-Windows was using a tesselation program that would give you a basic shape and then allow you to pull the edges in a way it would propagate to automatically keep the tesselation valid. It was pretty awesome... but I have no idea what it was called any more. 

It might have been [Shodor on Tessellations.org](http://www.tessellations.org/software-shodor.shtml), or perhaps [TesselMania!](http://www.tessellations.org/software-tesselmania0.shtml). Been a while. 

In any case, enjoy!

{{<p5js width="600" height="420">}}
const SIZE = 40;

let gui;
let params = {
  scale: 1.0, scaleMin: 0.25, scaleMax: 3.0, scaleStep: 0.01,
  drawBorders: true,
  applyRotation: true,
  fastFlux: true,
  varyRotations: true,
}

let g;
let buffer;
let bufferMask;
let lastRedrawBuffer;

function setup() {
  createCanvas(400, 400);
  g = createGraphics(width, height);
  
  buffer = createGraphics(2 * SIZE, 2 * SIZE);
  for (let i = 0; i < 100; i++) {
    buffer.fill(
      255 * random(),
      255 * random(),
      255 * random(),
      255 * random()
    );
    buffer.rect(
      random(4 * SIZE) - 2 * SIZE,
      random(4 * SIZE) - 2 * SIZE, 
      random(2 * SIZE),
      random(2 * SIZE)
    )
  }
  redrawBuffer();
  
  bufferMask = createGraphics(2 * SIZE, 2 * SIZE);
  bufferMask.push();
  {
    bufferMask.translate(SIZE, SIZE);
    bufferMask.scale(params.scale);
    bufferMask.stroke("black");
    bufferMask.fill("black");
    ngon(bufferMask, 6, SIZE);
  }
  bufferMask.pop();
 
  gui = createGuiPanel('params');
  gui.addObject(params);
  gui.setPosition(420, 0);
}

function draw() {
  g.background(255);
  
  if (params.fastFlux) {
    drawOneToBuffer();
  } else {
    if (millis() - lastRedrawBuffer > 1000) {
      redrawBuffer();
    }
  }
  
  let masked = buffer.get();
  masked.mask(bufferMask);
  
  g.push(); 
  {
    g.stroke("black");
    g.fill("green");
  
    g.translate(200, 200);
    g.scale(params.scale);
    
    g.stroke("black");
    g.noFill();
    
    if (params.drawBorders) {
      g.stroke("black");
      g.strokeWeight(2);
      ngon(g, 6, SIZE);      
    }
    
    g.push();
    {
      g.translate(-SIZE, -SIZE);
      g.image(masked, 0, 0);
    }
    g.pop();
        
    for (let xd = -10; xd < 10; xd++) {
      for (let yd = -50; yd < 50; yd++) {
        if (xd == 0 && yd == 0) continue;
        
        g.push();
        {
          let rowOffset = abs(yd) % 2 == 1 ? 1.5 * SIZE : 0;
          
          // Major thanks to:
          // https://www.redblobgames.com/grids/hexagons/
          g.translate(
            rowOffset + 3.0 * xd * SIZE, 
            sqrt(3) / 2 * yd * SIZE
          );
          
          if (params.applyRotation) {
            let n = noise(
                xd,
                yd,
                params.varyRotations ? frameCount / 500.0 : 0
            );
            g.rotate(TWO_PI / 6.0 * parseInt(n * 6));
          }
          
          g.push();
          {
            g.translate(-SIZE, -SIZE);
            g.image(masked, 0, 0);
          }
          g.pop();
          
          if (params.drawBorders) {
            g.stroke("black");
            g.strokeWeight(2);
            ngon(g, 6, SIZE);            
          }
        }
        g.pop();
      }
    }
  }
  g.pop();
  
  image(g, 0, 0);
}

function ngon(g, n, size) {
  g.beginShape();
  for (let i = 0; i < n; i++) {
    let x = size * cos(TWO_PI * i / n);
    let y = size * sin(TWO_PI * i / n);
    g.vertex(x, y);
  }
  g.endShape(CLOSE);
}

function redrawBuffer() {
  buffer.background(255);
  for (let i = 0; i < 100; i++) {
    drawOneToBuffer();
  }
  lastRedrawBuffer = millis();
}

function drawOneToBuffer() {
  buffer.fill(
    255 * random(),
    255 * random(),
    255 * random(),
    255 * random()
  );
  buffer.rect(
    random(4 * SIZE) - 2 * SIZE,
    random(4 * SIZE) - 2 * SIZE, 
    random(2 * SIZE),
    random(2 * SIZE)
  );
}
{{</p5js>}}

<!--more-->

{{< taxonomy-list "series" "Genuary 2023" >}}
