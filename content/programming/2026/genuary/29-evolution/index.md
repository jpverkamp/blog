---
title: "Genuary 2026.29: Evolution"
date: "2026-01-29"
programming/languages:
- JavaScript
programming/topics:
- Generative Art
- Procedural Content
- p5js
series:
- Genuary 2026
cover: gen26.29.png
---
That got quite a bit more than I expected. So now it's basically an evolving programmatic image generator. :smile:

<!--more-->

The params are:

* `populationSize` is how many images to generate
* `initialGeneLength` is how long genes are when randomly generated
* `scale` is how much to downsample (if you set this to 1 it gets slow, you can use `re-render` to fix that)
* `mutationRate` is how many genes are randomly tweaked
* `mode` can be a completely `random` image, my [[Genuary 2026.13: Self Portrait|self portrait]](), or a random `image` from online (which you can also upload to)

Genes are defined as a list of floats in the range `0..1`. The range will be evenly divided between all of the operations in `ops` in the source code, a bunch of things like constants, math operations, random numbers etc and run a relatively simple stack based language. :smile:!

Once you have a set of generated images, you can single click an image to select it or double click to zoom in on a single image. 

You also have some new buttons available:

* `randomize` will regenerate all genomes
* `select all` will select all/none of the genomes
* `mutate` will apply mutation to all images (50% tweak values, 25% each insertion and deletion)
* `advance` will take any selected images, and randomly breed them together to fill any non-selected spaces; this can shorten/lengthen genomes and can include the same genome being both parents
* `debug` will print some debug information to the console
* `re-render` (in single image mode) will render a full resolution version of the currently double clicked image

Then finally, there's the 'load your own' dialog, which will replace the image used for `image` mode with whatever you upload. It works best with square images and will squash anything else to a square aspect ratio. 

The main 'evolution' would be repeatedly selecting the images you like the best and `advancing`. 

Have fun!

{{<p5js width="600" height="500">}}
let gui;
let params = {
    populationSize: 16, populationSizeMin: 1, populationSizeMax: 64,
    initialGeneLength: 100, initialGeneLengthMin: 10, initialGeneLengthMax: 500,
    scale: 8, scaleMin: 1, scaleMax: 16,
    mutationRate: 0.1, mutationRateMin: 0, mutationRateMax: 1, mutationRateStep: 0.01,
    mode: ['random', 'self-portrait', 'image'],
};

let portraitImage;
let randomImage;
let currentImage;
let displayOne;

let population; 
let selected;
let message;

let previousScale = params.scale;
let previousMode = 'random';

function sampleCurrentImage(x, y) {
  if (!currentImage) return [0, 0, 0];

  let sx = floor(x * currentImage.width);
  let sy = floor(y * currentImage.height);

  let r = currentImage.pixels[(sy * currentImage.width + sx) * 4 + 0];
  let g = currentImage.pixels[(sy * currentImage.width + sx) * 4 + 1];
  let b = currentImage.pixels[(sy * currentImage.width + sx) * 4 + 2];

  return [r / 255, g / 255, b / 255];
}

ops = {
    const_z: ({stack}) => stack.push(0),
    const_one: ({stack}) => stack.push(1),
    const_half: ({stack}) => stack.push(0.5),
    const_pi: ({stack}) => stack.push(PI / TWO_PI),

    const_x: ({stack, x}) => stack.push(x),
    const_y: ({stack, y}) => stack.push(y),
    const_r: ({stack, r}) => stack.push(r),
    const_g: ({stack, g}) => stack.push(g),
    const_b: ({stack, b}) => stack.push(b),
    const_theta: ({stack, theta}) => stack.push(theta),
    const_radius: ({stack, radius}) => stack.push(radius),
    
    add: ({stack}) => {
        const b = stack.pop() || 0;
        const a = stack.pop() || 0;
        stack.push(a + b);
    },
    sub: ({stack}) => {
        const b = stack.pop() || 0;
        const a = stack.pop() || 0;
        stack.push(a - b);
    },
    mul: ({stack}) => {
        const b = stack.pop() || 0;
        const a = stack.pop() || 0;
        stack.push(a * b);
    },
    div: ({stack}) => {
        const b = stack.pop() || 0;
        const a = stack.pop() || 1;
        stack.push(a / b);
    },
    sin: ({stack}) => {
        const a = stack.pop() || 0;
        stack.push(sin(a * TWO_PI));
    },
    cos: ({stack}) => {
        const a = stack.pop() || 0;
        stack.push(cos(a * TWO_PI));
    },
    mod: ({stack}) => {
        const b = stack.pop() || 1;
        const a = stack.pop() || 0;
        const r = a / b;
        stack.push((r - floor(r)) * b);
    },
    inverse: ({stack}) => {
        const a = stack.pop() || 1;
        stack.push(1 - a);
    },

    if_gt: ({stack}) => {
        const f = stack.pop() || 0;
        const t = stack.pop() || 0;
        const a = stack.pop() || 0;
        const b = stack.pop() || 0;
        stack.push(a > b ? t : f);
    },
    if_eq: ({stack}) => {
        const f = stack.pop() || 0;
        const t = stack.pop() || 0;
        const a = stack.pop() || 0;
        const b = stack.pop() || 0;
        stack.push(a === b ? t : f);
    },

    abs: ({stack}) => {
        const a = stack.pop() || 0;
        stack.push(abs(a));
    },
    sqrt: ({stack}) => {
        const a = stack.pop() || 0;
        stack.push(sqrt(a));
    },
    log: ({stack}) => {
        const a = stack.pop() || 1;
        stack.push(log(a));
    },
    exp: ({stack}) => {
        const a = stack.pop() || 0;
        stack.push(exp(a));
    },

    drop: ({stack}) => {
        stack.pop();
    },
    dup: ({stack}) => {
        const a = stack.pop() || 0;
        stack.push(a);
        stack.push(a);
    },
    swap: ({stack}) => {
        const b = stack.pop() || 0;
        const a = stack.pop() || 0;
        stack.push(b);
        stack.push(a);
    },

    noise: ({stack, x, y}) => {
        const scale = stack.pop() || 1;
        stack.push(noise(x * scale, y * scale));
    },
    random: ({stack}) => {
        stack.push(random());
    },

    average3: ({stack}) => {
        const c = stack.pop() || 0;
        const b = stack.pop() || 0;
        const a = stack.pop() || 0;
        stack.push((a + b + c) / 3);
    },

    sample: ({stack, x, y}) => {
      let [r, g, b] = sampleCurrentImage(x, y);
      stack.push(b);
      stack.push(g);
      stack.push(r);
    },

    sampleR: ({stack, x, y}) => { stack.push(sampleCurrentImage(x, y)[0]); },
    sampleG: ({stack, x, y}) => { stack.push(sampleCurrentImage(x, y)[1]); },
    sampleB: ({stack, x, y}) => { stack.push(sampleCurrentImage(x, y)[2]); },
};

class Gene {
    constructor () {
        this.gene = [];
        this.selected = false;

        this.width = width / params.scale;
        this.height = height / params.scale;
        this.buffer = createGraphics(this.width, this.height);

        for (let i = 0; i < params.initialGeneLength; i++) {
            this.gene.push(random());
        }
    }

    mutate() {
        for (let i = 0; i < this.gene.length; i++) {
            if (random() < params.mutationRate) {
              let mutationMode = random();
              if (mutationMode < 0.5) {
                this.gene[i] += (random() - random()) / 10;
                while (this.gene[i] < 0) this.gene[i] += 1;
                while (this.gene[i] > 1) this.gene[i] -= 1;

              } else if (mutationMode < 0.75) {
                this.gene.splice(i, 1);
                i--;
              } else {
                this.gene.splice(i, 0, random());
                i++;
              }
            }
        }
    }

    crossover(other) {
      let child = new Gene();

      let i = floor(random(this.gene.length));
      let j = floor(random(other.gene.length));

      child.gene = [
        ...this.gene.slice(0, i),
        ...other.gene.slice(j)
      ];

      return child;
    }

    evaluate() {
      if (currentImage) currentImage.loadPixels();

      this.buffer.background(0);
      this.buffer.loadPixels();
      
      let opKeys = Object.keys(ops);

      for (let y = 0; y < this.height; y++) {
          for (let x = 0; x < this.width; x++) {
              let stack = [];
              let scaledX = x / this.width;
              let scaledY = y / this.height;

              let theta = atan2(y - this.height / 2, x - this.width / 2);
              let radius = dist(x, y, this.width / 2, this.height / 2) / (this.width / 2);

              let r = 0;
              let g = 128;
              let b = 255;

              if (currentImage) {
                let [r, g, b] = sampleCurrentImage(scaledX, scaledY);
              }
              
              for (let i = 0; i < this.gene.length; i++) {
                  const opIndex = floor(this.gene[i] * opKeys.length);
                  const opKey = opKeys[opIndex];
                  ops[opKey]({
                      stack,
                      r: r / 255,
                      g: g / 255,
                      b: b / 255,
                      theta: (theta + PI) / TWO_PI,
                      radius: radius / dist(0, 0, this.width / 2, this.height / 2),
                      x: scaledX,
                      y: scaledY,
                  });
              }

              const hue = map(stack.pop() || 0, 0, 1, 0, 360);
              const sat = map(stack.pop() || 1, 0, 1, 0, 100);
              const bri = map(stack.pop() || 1, 0, 1, 0, 100);

              let output_c = color(hue, sat, bri);
              this.buffer.pixels[(y * this.width + x) * 4 + 0] = red(output_c);
              this.buffer.pixels[(y * this.width + x) * 4 + 1] = green(output_c);
              this.buffer.pixels[(y * this.width + x) * 4 + 2] = blue(output_c);
              this.buffer.pixels[(y * this.width + x) * 4 + 3] = 255;
          }
      }

      this.buffer.updatePixels();
    }
}

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
  let canvas = createCanvas(400, 400);
  colorMode(HSB, 360, 100, 100, 100);
  
  gui = createGuiPanel("params");
  gui.addObject(params);
  gui.setPosition(420, 0);

  // Select on click
  canvas.mousePressed(() => {
    message = null;

    let gridSize = ceil(sqrt(population.length));
    let x = floor(mouseX / (width / gridSize));
    let y = floor(mouseY / (height / gridSize));
    let index = y * gridSize + x;
    if (population[index]) {
      population[index].selected = !population[index].selected;
    }
  });

  // Display a single image on double click
  // Or go back to the full display
  canvas.doubleClicked(() => {
    message = null;

    if (displayOne === false) {
      let gridSize = ceil(sqrt(population.length));
      let x = floor(mouseX / (width / gridSize));
      let y = floor(mouseY / (height / gridSize));
      let index = y * gridSize + x;
      if (population[index]) {
        displayOne = index;
      }
    } else {
      displayOne = false;
    }
  });

  createElement('br');

  // Generate a new population
  createButton('randomize').mousePressed(() => { 
    message = null;
    displayOne = false;
    reset();
  });

  // Toggle select all
  createButton('select all').mousePressed(() => {
    message = null;
    displayOne = false;

    let allSelected = population.every(g => g.selected);
    if (allSelected) {
      for (let g of population) {
        g.selected = false;
      }
    } else {
      for (let g of population) {
        g.selected = true;
      }
    }
  });

  // Mutate selected
  createButton('mutate').mousePressed(() => {
    message = null;

    if (displayOne !== false) {
      if (typeof displayOne !== 'number') {
        message = "Cannot mutate from re-rendered";
        return;
      }
      let g = population[displayOne];
      g.mutate();
      g.evaluate();
      return;
    }
    
    let selectedGenes = population.filter(g => g.selected);
    if (selectedGenes.length < 1) {
      message = "Select at least one gene.";
      return;
    }

    for (let g of population) {
      if (g.selected) {
        g.mutate();
        g.evaluate();
      }
    }
  });

  // Keep selected and advance new
  createButton('advance').mousePressed(() => {
    message = null;
    
    let selectedGenes = population.filter(g => g.selected);
    if (displayOne !== false) {
      if (typeof displayOne !== 'number') {
        message = "Cannot advance from re-rendered";
        return;
      }
      selectedGenes = [population[displayOne]];
      displayOne = false;
    }
     
    if (selectedGenes.length < 1) {
      message = "Select at least one gene.";
      return;
    }

    for (let i = 0; i < population.length; i++) {
      if (!population[i].selected) {
        let parentA = random(selectedGenes);
        let parentB = random(selectedGenes);
        let newGene = parentA.crossover(parentB);
        newGene.mutate();
        newGene.evaluate();
        population[i] = newGene;
      }
    }
  });

  // Debug information
  createButton('debug').mousePressed(() => {
    if (displayOne !== false) {
      let one = null;
      if (typeof displayOne === 'number') {
        one = population[displayOne];
      } else {
        one = displayOne;
      }
      console.log(one.gene);

      let opNames = one.gene.map(v => {
        let opKeys = Object.keys(ops);
        const opIndex = floor(v * opKeys.length);
        return opKeys[opIndex];
      });
      console.log(opNames);      
    } else {
      let minLength = Infinity;
      let maxLength = -Infinity;
      let totalLength = 0;
      let avgLength = 0;

      population.forEach((g, i) => {
        console.log(`Gene ${i}: length=${g.gene.length}`);
        if (g.gene.length < minLength) minLength = g.gene.length;
        if (g.gene.length > maxLength) maxLength = g.gene.length;
        totalLength += g.gene.length;
      });

      message = `Min: ${minLength}, Max: ${maxLength}, Avg: ${totalLength / population.length}`;
      console.log(message);
    }
  });

  // A button to render full scale
  let fullScaleButton = createButton('re-render').mousePressed(() => {
    message = null;
    if (displayOne === false) {
      message = "Switch to single view to re-render at full scale.";
      return;
    }

    let upscaled = new Gene();
    upscaled.gene = [...population[displayOne].gene];
    upscaled.width = width;
    upscaled.height = height;
    upscaled.buffer = createGraphics(upscaled.width, upscaled.height);
    upscaled.evaluate();

    displayOne = upscaled;
  });
    
  createElement('br');

  createSpan('Load your own image: ');
  let fileInput = createFileInput((file) => {
    if (file.type === 'image') {
      randomImage = loadImage(file.data, () => {
        message = "Image loaded successfully!";
        if (params.mode === 'image') {
          currentImage = randomImage;
          for (let g of population) {
            g.evaluate();
          }
        } else {
          message = 'Switch mode to image';
        }
      });
    } else {
      message = "Please upload an image file.";
    }
  });
  fileInput.elt.accept = 'image/*';
  createElement('br');  
  createElement('br');

  reset();
}

function reset() {
  if (params.mode == 'self-portrait') {
    currentImage = portraitImage;
  } else if (params.mode == 'image') {
    currentImage = randomImage;
  } else {
    currentImage = null;
  }

  population = [];
  
  for (let i = 0; i < params.populationSize; i++) {
      let gene = new Gene();
      gene.evaluate();
      population.push(gene);
  }

  message = null;
  displayOne = false;
}

function draw() {
  while (population.length > params.populationSize) {
    population.shift();
  } 
  while (population.length < params.populationSize) {
    let gene = new Gene();
    gene.evaluate();
    population.push(gene);
  }

  if (previousScale !== params.scale) {
    for (let g of population) {
      g.width = width / params.scale;
      g.height = height / params.scale;
      g.buffer = createGraphics(g.width, g.height);
      g.evaluate();
    }
    previousScale = params.scale;
  }

  if (previousMode !== params.mode) {
    message = '';

    if (params.mode == 'self-portrait') {
      currentImage = portraitImage;
    } else if (params.mode == 'image') {
      currentImage = randomImage;
    } else {
      currentImage = null;
    }

    for (let g of population) {
      g.evaluate();
    }

    previousMode = params.mode;
  }

  background(0);
  if (displayOne !== false) {
    if (typeof displayOne === 'number') {
      let g = population[displayOne];
      image(g.buffer, 0, 0, width, height);
    } else {
      image(displayOne.buffer, 0, 0, width, height);
    }
  } else {
    let gridSize = ceil(sqrt(population.length));
    for (let i = 0; i < population.length; i++) {
      let g = population[i];
      let x = (i % gridSize) * (width / gridSize);
      let y = floor(i / gridSize) * (height / gridSize);
      image(g.buffer, x, y, width / gridSize, height / gridSize);

      if (g.selected) {
        noFill();
        stroke("black")
        strokeWeight(4);
        rect(x, y, width / gridSize, height / gridSize);

        stroke("white");
        strokeWeight(2);
        rect(x, y, width / gridSize, height / gridSize);

        // Check mark in the top right
        noFill();
        stroke("black")
        strokeWeight(4);
        let cx = x + width / gridSize - 20;
        let cy = y + 20;
        line(cx - 8, cy, cx - 2, cy + 6);
        line(cx - 2, cy + 6, cx + 8, cy - 6);

        stroke("white")
        strokeWeight(2);
        cx = x + width / gridSize - 20;
        cy = y + 20;
        line(cx - 8, cy, cx - 2, cy + 6);
        line(cx - 2, cy + 6, cx + 8, cy - 6);
      }
    }
  }

  if (message) {
    fill(0, 0, 100, 80);
    rect(0, height - 30, width, 30);
    fill(0);
    noStroke();
    textAlign(LEFT, CENTER);
    textSize(16);
    text(message, 10, height - 15);
  }
}
{{</p5js>}}