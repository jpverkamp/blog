---
title: "Genuary 2023.10: Generative Music"
date: 2023-02-10
programming/languages:
- JavaScript
programming/topics:
- Generative Art
- Procedural Content
- p5js
- Audio
- Music
series:
- Genuary 2023
cover: /embeds/2023/genuary-10.png
---
[Genuary](https://genuary.art/)! 

Spend a month making one beautiful thing per day, given a bunch of prompts. A month late, but as they say, 'the second best time is now'.  

Let's do it!

## 10) Generative music

Wikipedia: [[wiki:Aleatoric music|Generative music]]()

**NOTE: Because of limitations in JavaScript autoplaying sound, you must click to start.**

**NOTE: This currently doesn't work in Safari. Something funny with the p5.sound addon. I'm working on it.**

<!--more-->

{{<p5js width="600" height="420" libraries="https://cdnjs.cloudflare.com/ajax/libs/p5.js/1.5.0/addons/p5.sound.js">}}
let gui;
let params = {
  width: 32, widthMin: 4, widthMax: 64,
  height: 4, heightMin: 1, heightMax: 8,
  bpm: 140, bpmMin: 30, bpmMax: 280,
  randomFill: 0.2, randomFillMin: 0.0, randomFillMax: 1.0, randomFillStep: 0.01,
};

const MAX_VALUE = 8;
const COLORS = [
  "black",
  "red",
  "green",
  "blue",
  "cyan",
  "magenta",
  "yellow",
  "white",
];
const NOTES = [
  'A4',
  'B4',
  'C4',
  'D4',
  'E4',
  'F4',
  'G4',
];

class CellValues {
  constructor() {
    this.data = {};
  }
  
  get(x, y) {
    if ([x, y] in this.data) {
      return this.data[[x, y]];
    } else {
      return 0;
    }
  }
  
  set(x, y, v) {
    if ([x, y] in this.data && v == 0) {
      delete this.data[[x, y]];
    } else {
      this.data[[x, y]] = v;
    }
  }
}

let cell_values;
let start_millis = 0;
let last_beat = -1;
let synth;

function setup() {
  let canvas = createCanvas(400, 400);
  
  cell_values = new CellValues();
  cell_values.set(3, 5, 1);
  
  // Toggle squares
  canvas.mousePressed(() => {
    if (!synth) {
        start_millis = millis();
        userStartAudio();
        synth = new p5.PolySynth();
    }

    let cx = parseInt(params.width * mouseX / width);
    let cy = parseInt(params.height * mouseY / height);
    
    let key = JSON.stringify([cx, cy]);
    
    cell_values.set(
      cx,
      cy,
      (
        cell_values.get(cx, cy)
        + (mouseButton == LEFT ? 1 : -1)
        + MAX_VALUE
      ) % MAX_VALUE
    );
  });

  gui = createGuiPanel('params');
  gui.addObject(params);
  gui.setPosition(420, 0);
  
  let randomize = () => {
    for (let cx = 0; cx < params.width; cx++) {
      for (let cy = 0; cy < params.height; cy++) {
        if (random() < params.randomFill) {
          cell_values.set(cx, cy, parseInt(random() * MAX_VALUE));
        } else {
          cell_values.set(cx, cy, 0);
        }
      }
    }
  };
  
  createButton('randomize').mousePressed(randomize);
  randomize();
}

function draw() {
  background(0);
  
  let elapsed_millis = 0;
  let beat = -1;
  if (synth) {
    elapsed_millis = millis() - start_millis;
    beat = parseInt(elapsed_millis / 1000.0 * params.bpm / 60.0);
  }
  
  let cell_width = width / params.width;
  let cell_height = height / params.height;

  // Update display
  for (let cx = 0; cx < params.width; cx++) {
    for (let cy = 0; cy < params.height; cy++) {
      if (beat % params.width == cx) {
        stroke("yellow");
      } else {
        noStroke();
      }
      
      fill(COLORS[cell_values.get(cx, cy)]);
      
      rect(
        2 + cx * cell_width,
        2 + cy * cell_height,
        cell_width - 4,
        cell_height - 4,
        8
      );
    }
  }
  
  // Play music
  if (synth) {
    if (beat != last_beat) {
        let cx = beat % params.width;
        for (let cy = 0; cy < params.height; cy++) {
        let cell_value = cell_values.get(cx, cy);
        if (cell_value == 0) continue; 
        
        synth.play(
            NOTES[cell_value - 1],
            1.0,                      // velocity [0, 1]
            0,                        // time start
            60.0 / params.bpm - 0.05, // duration (seconds)
        );
        }
        
        last_beat = beat;
    }
  }
}
{{</p5js>}}

{{< taxonomy-list "series" "Genuary 2023" >}}
