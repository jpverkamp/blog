---
title: "Genuary 2026.09: Cellular automata"
date: "2026-01-09"
programming/languages:
- JavaScript
programming/topics:
- Generative Art
- Procedural Content
- p5js
series:
- Genuary 2026
cover: gen26.09.png
---
## 9) Cellular automata

Just a bunch of random rules, with the ability (if you put this in p5js at least) to add them pretty easily.

This one can do some wacky things if you randomize it. But also, it *might* crash your browser tab on some of these settings. Sorry. :smile:

Try:

* Perlin, Max, fuzz, diffuse

<!--more-->

{{<p5js width="600" height="420">}}
let gui;
let params = {
  cellSize: 4, cellSizeMin: 2, cellSizeMax: 20,
  ageMultiplier: 1, ageMultiplierMin: 1, ageMultiplierMax: 360,
  randomize: true,
  randomizePercent: 0.01, randomizePercentMin: 0, randomizePercentMax: 1, randomizePercentStep: 0.01,
  perlinSource: false,
  perlinMask: true,
  gameOfLife: false,
  maze: true,
  majority: false,
  fuzz: false,
  dieOff: true,
  dieOffAge: 10, dieOffAgeMin: 1, dieOffAgeMax: 100,
  flicker: false,
  diffuse: false,
};

let rules = [];
let cells = {};

function setup() {
  createCanvas(400, 400);
  noStroke();
  colorMode(HSB);

  rules.push({
    name: "randomize",
    f: (x, y) => (random() < params.randomizePercent ? 1 : cells[[x, y]]),
  });

  rules.push({
    name: "perlinSource",
    f: (x, y) => {
      let n = noise(x * 0.05, y * 0.05, frameCount * 0.01);
      return n > 0.55 ? 1 : 0;
    },
  });

  rules.push({
    name: "perlinMask",
    f: (x, y) => {
      let n = noise(1e3 + x * 0.05, 1e3 + y * 0.05, frameCount * 0.01);
      return n > 0.55 ? cells[[x, y]] : 0;
    },
  });

  rules.push({
    name: "gameOfLife",
    f: (x, y) => {
      let count = count_neighbors(x, y, 1, (v) => v > 0);

      if (count < 2 || count > 3) {
        return 0;
      } else if (count == 3) {
        return 1;
      } else {
        return 0;
      }
    },
  });

  rules.push({
    name: "maze",
    f: (x, y) => {
      let c = count_neighbors(x, y, 1, (v) => v > 0);
      if (cells[[x, y]]) return c >= 1 && c <= 5 ? 1 : 0;
      return c == 3 ? 1 : 0;
    },
  });

  rules.push({
    name: "fuzz",
    f: (x, y) => {
      let c = count_neighbors(x, y, 1, (v) => v > 0);
      if (c == 2) return 1;
      if (cells[[x, y]]) return 1;
      return 0;
    },
  });

  rules.push({
    name: "dieOff",
    f: (x, y) => (cells[[x, y]] < params.dieOffAge ? cells[[x, y]] : 0),
  });

  rules.push({
    name: "flicker",
    f: (x, y) => {
      let v = cells[[x, y]] || 0;

      let c2 = count_neighbors(x, y, 2, (n) => n > 0);
      if (v <= 0 && c2 >= 6 && c2 <= 9) return 1;
      if (v > 0 && c2 > 12) return 0;

      return v;
    },
  });

  rules.push({
    name: "diffuse",
    f: (x, y) => {
      let sum = 0;
      let count = 0;

      for (let xn = x - 2; xn <= x + 2; xn++) {
        for (let yn = y - 2; yn <= y + 2; yn++) {
          if (xn == x && yn == y) continue;
          let v = cells[[xn, yn]];
          if (v > 0) {
            sum += v;
            count++;
          }
        }
      }

      return count > 0 ? floor(sum / count) : 0;
    },
  });

  gui = createGuiPanel("params");
  gui.addObject(params);
  gui.setPosition(420, 0);
}

function count_neighbors(x, y, offset, f) {
  let count = 0;

  for (let xn = x - offset; xn <= x + offset; xn++) {
    for (let yn = y - offset; yn <= y + offset; yn++) {
      if (x == xn && y == yn) continue;

      if (f(cells[[xn, yn]])) {
        count += 1;
      }
    }
  }

  return count;
}

function draw() {
  let cells_x = width / params.cellSize;
  let cells_y = height / params.cellSize;

  let prev = { ...cells };

  for (let { name, f } of rules) {
    if (!params[name]) continue;

    let next = {};

    for (let x = 0; x < cells_x; x++) {
      for (let y = 0; y < cells_y; y++) {
        next[[x, y]] = f(x, y);
      }
    }

    cells = next;
  }

  for (let x = 0; x < cells_x; x++) {
    for (let y = 0; y < cells_y; y++) {
      if (cells[[x, y]] && prev[[x, y]]) {
        cells[[x, y]] = cells[[x, y]] + prev[[x, y]];
      }
    }
  }

  background("white");
  noStroke();
  fill("black");

  for (let x = 0; x < cells_x; x++) {
    for (let y = 0; y < cells_y; y++) {
      let v = cells[[x, y]];
      if (v > 0) {
        fill((v * params.ageMultiplier) % 360, 100, 100);
        rect(
          x * params.cellSize,
          y * params.cellSize,
          params.cellSize,
          params.cellSize
        );
      }
    }
  }
}
{{</p5js>}}

{{< taxonomy-list "series" "Genuary 2026" >}}
