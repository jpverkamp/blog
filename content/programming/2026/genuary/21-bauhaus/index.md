---
title: "Genuary 2026.21: Bauhaus poster"
date: "2026-01-21"
programming/languages:
- JavaScript
programming/topics:
- Generative Art
- Procedural Content
- p5js
series:
- Genuary 2026
cover: gen26.21.png
---
A [[wiki:Bauhaus]]() style poster. 

<!--more-->

{{<p5js width="600" height="500">}}
let gui;
let params = {
  eyeSize: 180, eyeSizeMin: 100, eyeSizeMax: 300,

  arcThickness: 40, arcThicknessMin: 0, arcThicknessMax: 100,
  arcSpeed: 0.15, arcSpeedMin: 0, arcSpeedMax: 1, arcSpeedStep: 0.01,

  pulseAmount: 1, pulseAmountMin: 0, pulseAmountMax: 50,
  pulseSpeed: 10, pulseSpeedMin: 0, pulseSpeedMax: 100,

  accentSize: 22, accentSizeMin: 0, accentSizeMax: 100,
  accentOrbit: 20, accentOrbitMin: 0, accentOrbitMax: 100,
  
  paletteSwapPercent: 0.01, paletteSwapPercentMin: 0, paletteSwapPercentMax: 1, paletteSwapPercentStep: 0.01,
};

const BAUHAUS_COLORS = {
  red: [5, 95, 90],
  yellow: [50, 95, 95],
  blue: [210, 90, 80],
  black: [0, 0, 0],
};
const BAUHAUS_CREAM = [40, 20, 95];

let colors = {};

function setup() {
  createCanvas(400, 400);
  colorMode(HSB, 360, 100, 100, 100);
  angleMode(DEGREES);

  gui = createGuiPanel("params");
  gui.addObject(params);
  gui.setPosition(420, 0);
  
  randomizeColors();
}

function randomizeColors() {
  let palette = Object.values(BAUHAUS_COLORS);

  colors.eyeOuter = random(palette);
  colors.eyeInner = random(palette.filter(c => c !== colors.eyeOuter));
  colors.highlight = BAUHAUS_CREAM;

  colors.arc1 = random(palette);
  colors.arc2 = random(palette);
  colors.arc3 = BAUHAUS_COLORS.black;

  colors.accent1 = random(palette);
  colors.accent2 = random(palette);
  colors.accent3 = BAUHAUS_CREAM;

  colors.text = BAUHAUS_COLORS.black;
}

function draw() {
  background(...BAUHAUS_CREAM);

  let t = frameCount;

  drawMainEye(t);
  drawArcs(t);
  drawAccents(t);
  drawText();
  
  if (frameCount % 30 == 0 && random() < params.paletteSwapPercent) {
    randomizeColors();
  }
}

function drawMainEye(t) {
  let pulse = sin(t * params.pulseSpeed) * params.pulseAmount;

  push();
  translate(width / 2, height / 2);
  noStroke();

  fill(...colors.eyeOuter);
  circle(0, 0, params.eyeSize + pulse);

  fill(...colors.eyeInner);
  circle(0, 0, (params.eyeSize + pulse) * 0.55);

  fill(...colors.highlight);
  circle(
    -params.eyeSize * 0.18,
    -params.eyeSize * 0.18,
    params.eyeSize * 0.18
  );

  pop();
}

function drawArcs(t) {
  let rot = t * params.arcSpeed;

  noFill();
  strokeCap(SQUARE);
  strokeWeight(params.arcThickness);

  stroke(...colors.arc1);
  arc(
    width / 2,
    height / 2,
    params.eyeSize + 80,
    params.eyeSize + 80,
    40 + rot,
    180 + rot
  );

  stroke(...colors.arc2);
  arc(
    width / 2,
    height / 2,
    params.eyeSize + 40,
    params.eyeSize + 40,
    220 - rot * 0.8,
    340 - rot * 0.8
  );

  stroke(...colors.arc3);
  arc(
    width / 2,
    height / 2,
    params.eyeSize + 120,
    params.eyeSize + 120,
    300 + rot * 0.5,
    30 + rot * 0.5
  );
}

function drawAccents(t) {
  let a = t * 0.6;
  noStroke();

  fill(...colors.accent1);
  circle(
    90 + cos(a) * params.accentOrbit,
    230 + sin(a) * params.accentOrbit,
    params.accentSize * 1.4
  );

  fill(...colors.accent2);
  circle(
    260 + cos(a + 120) * params.accentOrbit,
    300 + sin(a + 120) * params.accentOrbit,
    params.accentSize
  );

  fill(...colors.accent3);
  circle(
    290 + cos(a + 240) * params.accentOrbit,
    170 + sin(a + 240) * params.accentOrbit,
    params.accentSize
  );
}

function drawText() {
  push();
  fill(...colors.text);
  textAlign(CENTER, CENTER);

  textSize(28);
  textStyle(BOLD);
  text("BAUHAUS", width - 80, height - 65);

  textSize(12);
  textStyle(NORMAL);
  text("EXHIBITION", width - 80, height - 40);
  text("GENUARY – 2026", width - 80, height - 25);

  pop();
}
{{</p5js>}}