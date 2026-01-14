---
title: "Genuary 2026.13: Self Portrait"
date: "2026-01-13"
programming/languages:
- JavaScript
programming/topics:
- Generative Art
- Procedural Content
- p5js
series:
- Genuary 2026
cover: gen26.13.png
---
## 13) Self Portrait

That was surprisingly fun. 

Basically, it will take recursively divide the picture over time. Each time, it will find the node with the largest error (real image color compared to the current random color) and split it in 4, assigning each to the nearest random color from our palette. 

* `colors` controls how many maximum (random) colors will be chosen
* `edges` will draw the boxes of the tree
* `minimumBlock` is the size at which it won't split any more
* `resetAfter` will generate new colors even this many frames

If you don't want to look at me any more, turning off `selfPortraitMode` will load an image from [picsum.dev](https://picsum.dev/). 

<!--more-->

{{<p5js width="600" height="460">}}
let gui;
let params = {
  colors: 10, colorsMin: 2, colorsMax: 256,
  edges: false,
  minimumBlock: 3, minimumBlockMin: 1, minimumBlockMax: 10,
  selfPortraitMode: true,
  resetAfter: 1000, resetAfterMin: 10, resetAfterMax: 10000,
};

let portraitImage;
let randomImage;
let currentImage;

let colors = [];

let tree;

let lastParams;
let lastReset = 0;

function preload() {
  console.log('Loading...');

  portraitImage = loadImage("jp.png");
  randomImage = loadImage("https://picsum.photos/400");

  if (params.selfPortraitMode) {
    currentImage = portraitImage;
  } else {
    currentImage = randomImage;
  }
  
  console.log("done");
}

function setup() {
  createCanvas(400, 400);
  
  gui = createGuiPanel("params");
  gui.addObject(params);
  gui.setPosition(420, 0);
}

// Calculate the average r, g, b over a region of the currentImage
function averageColor(x, y, w, h) {
  let sumr = 0, sumg = 0, sumb = 0, count = 0;

  for (let xi = 0; xi < w; xi++) {
    for (let yi = 0; yi < h; yi++) {
      const px = x + xi;
      const py = y + yi;

      const idx = (px + py * currentImage.width) * 4;

      sumr += currentImage.pixels[idx + 0];
      sumg += currentImage.pixels[idx + 1];
      sumb += currentImage.pixels[idx + 2];
      count++;
    }
  }

  return [
    floor(sumr / count),
    floor(sumg / count),
    floor(sumb / count),
  ];
}

// How far is a region of currentImage from the given r, g, b
// Normalize based on region size
function totalError(x, y, w, h, r, g, b) {
  let error = 0;

  for (let xi = 0; xi < w; xi++) {
    for (let yi = 0; yi < h; yi++) {
      const px = x + xi;
      const py = y + yi;

      const idx = (px + py * currentImage.width) * 4;

      error += Math.abs(r - currentImage.pixels[idx + 0]);
      error += Math.abs(g - currentImage.pixels[idx + 1]);
      error += Math.abs(b - currentImage.pixels[idx + 2]);
    }
  }

  return error / (w * h / 2);
}

// Find the closest color in colors to r, g, b
function closestColor(r, g, b) {
  let best = null;
  let bestDist = Infinity;

  for (const c of colors) {
    const dr = c[0] - r;
    const dg = c[1] - g;
    const db = c[2] - b;

    const dist = dr * dr + dg * dg + db * db; // squared distance

    if (dist < bestDist) {
      bestDist = dist;
      best = c;
    }
  }

  return best;
}

// Given a tree, recursively find the largest error value in the tree
function findMaximumError(tree) {
  if (tree.type === 'leaf') {
    return tree.error;
  }

  let maxError = -Infinity;

  for (const child of tree.children) {
    const e = findMaximumError(child);
    if (e > maxError) {
      maxError = e;
    }
  }

  return maxError;
}

// Given an error value (that exists in the tree (see above))
// Find the node that error is at and split it
function splitAtError(tree, error) {
  if (tree.type === 'leaf' && tree.error === error) {
    const { x, y, w, h } = tree;

    const hw = Math.floor(w / 2);
    const hh = Math.floor(h / 2);

    tree.type = 'branch';
    tree.children = [
      makeLeaf(x,        y,        hw,     hh),     // TL
      makeLeaf(x + hw,   y,        w - hw, hh),     // TR
      makeLeaf(x,        y + hh,   hw,     h - hh), // BL
      makeLeaf(x + hw,   y + hh,   w - hw, h - hh)  // BR
    ];

    return true;
  }

  if (tree.type === 'branch') {
    for (const child of tree.children) {
      if (splitAtError(child, error)) {
        return true;
      }
    }
  }

  return false;
}

// Helper function to make a leaf node of a region
// Find the closest color to the region's average, that's the color
// And error is how far that color is from 'perfect'
function makeLeaf(x, y, w, h) {
  let [ar, ag, ab] = averageColor(x, y, w, h);
  let [r, g, b] = closestColor(ar, ag, ab);
  let err = totalError(x, y, w, h, r, g, b);

  if (w <= params.minimumBlock || h <= params.minimumBlock) {
    err = 0;
  }
  
  return {
    type: 'leaf',
    x, y, w, h,
    r, g, b,
    error: err
  };
}

// Draw the current tree structure recursively
function drawTree(tree) {
  if (tree.type == 'leaf') {
    fill(tree.r, tree.g, tree.b);
    rect(tree.x, tree.y, tree.w, tree.h);
  } else {
    for (let child of tree.children) {
      drawTree(child);
    }
  }
}

function draw() {
  if (frameCount - lastReset > params.resetAfter) {
    colors = [];
    tree = undefined;
    lastReset = frameCount;
  }
  
  if (params.edges) {
    stroke("black");
  } else {
    noStroke();
  }
  
  while (colors.length > params.colors) { colors.shift(); }
  while (colors.length < params.colors) { 
    colors.push([
      floor(random(256)),
      floor(random(256)),
      floor(random(256))
    ]);
  }
  
  if (lastParams == undefined || Object.keys(params).some(k => params[k] !== lastParams[k])) {
    
    if (lastParams != undefined && params.selfPortraitMode != lastParams.selfPortraitMode) {
      if (params.selfPortraitMode) {
        currentImage = portraitImage;
      } else {
        currentImage = randomImage;
      }
    }
    
    lastReset = frameCount;
    tree = undefined;
    lastParams = {...params};
  }

  currentImage.loadPixels();

  if (tree == undefined) {
    tree = makeLeaf(0, 0, width, height);
  } else {
    let error = findMaximumError(tree);
    splitAtError(tree, error);
  }
  
  drawTree(tree);
}
{{</p5js>}}

{{< taxonomy-list "series" "Genuary 2026" >}}
