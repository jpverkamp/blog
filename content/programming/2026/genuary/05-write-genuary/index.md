---
title: "Genuary 2026.05: Write 'genuary'"
date: "2026-01-05"
programming/languages:
- JavaScript
programming/topics:
- Generative Art
- Procedural Content
- p5js
series:
- Genuary 2026
cover: gen26.05.png
---
## 5) Write 'genuary'

Yeah, this one got weird and recursive. But it's only sort of font data, so I think it works. 

<!--more-->

{{<p5js width="600" height="420">}}
let gui;
let params = {
  maxDepth: 6, maxDepthMin: 1, maxDepthMax: 16,
  randomColor: true,
  timeScale: "0.00001",
  debugRender: false,
  multiplier: 1.2, multiplierMin: 0, multiplierMax: 1.6, multiplierStep: 0.1,
};

let not_font_data = `\
*** *** *   * *  *  **  * * \
* * * * **  * * * * * * * * \
*** *** * * * * *** **   *  \
  * *   * * * * * * * *  *  \
*** *** * *  ** * * * *  *  \
`;
let not_font_width = 7 * 4;
let not_font_height = 5;

function randomAt(x, y, z) {
  let t = frameCount * params.timeScale;
  let v = params.multiplier * noise(1 + x * t, 1 + y * t, 1 + z * t);
  if (v < 0) { v = 0 };
  if (v > 1) { v = 1 };
  return v;
}

function setup() {
  createCanvas(400, 400);
  colorMode(HSB, 360, 100, 100);

  gui = createGuiPanel('params');
  gui.addObject(params);
  gui.setPosition(420, 0);
}

function render_to(x, y, w, h) {
  if (params.debugRender) {
    strokeWeight(1);
    stroke("white");
    fill("black");
    rect(x, y, w, h);
    return;
  }
    
  let cell_width = floor(w / not_font_width);
  let cell_height = floor(h / not_font_height);
  
  for (let cell_x = 0; cell_x < not_font_width; cell_x++) {
    for (let cell_y = 0; cell_y < not_font_height; cell_y++) {
      let cell_i = cell_x + cell_y * not_font_width;
      
      if (not_font_data[cell_i] == '*') {
        if (params.randomColor) {
          fill(randomAt(x, y, 0) * 360, 100, 100); 
        } else {
          fill("white");
        }
        rect(
          x + cell_x * cell_width,
          y + cell_y * cell_height,
          cell_width,
          cell_height
        );
      }
    }
  }
}

function render_split(x, y, w, h, depth=1) {
  // if (w < not_font_width || h < not_font_height) {
  //   return;
  // }
  
  if (depth >= params.maxDepth) {
    render_to(x, y, w, h);
    return;
  }
  
  if (w > h) {
    let split_w = randomAt(x, y, 1) * w;
    render_split(x, y, split_w, h, depth + 1);
    render_split(x + split_w, y, w - split_w, h, depth + 1);
  } else {
    let split_h = randomAt(x, y, 2) * h;
    render_split(x, y, w, split_h, depth + 1);
    render_split(x, y + split_h, w, h - split_h, depth + 1);
  }
  
}

function draw() {
  background("black");
  strokeWeight(0);

  render_split(0, 0, width, height);
}
{{</p5js>}}

{{< taxonomy-list "series" "Genuary 2026" >}}
