---
title: "Genuary 2026.19: 16x16"
date: "2026-01-19"
programming/languages:
- JavaScript
programming/topics:
- Generative Art
- Procedural Content
- p5js
series:
- Genuary 2026
cover: gen26.19.png
---
I'm... not really sure where I was going with this one. :smile:

Basically, 16x16 tiny sketches that slide around like a [[wiki:sliding block puzzle]](). Although with how chaotic some of the simulations are, it's not always easy to see. 

<!--more-->

{{<p5js width="600" height="420">}}
const DEBUG_PRINT = false;
const NOISE_SIZE = 100;

let gui;
let params = {
  // How many frames each move takes
  slideFrames: 10,
  slideFramesMin: 1,
  slideFramesMax: 100,

  // Variation on speed
  slideSpeedVariation: 0.1,
  slideSpeedVariationMin: 0,
  slideSpeedVariationMax: 1,
  slideSpeedVariationStep: 0.01,
  
  // How many blocks should be removed
  missingBlocks: 3,
  missingBlocksMin: 1,
  missingBlocksMax: 16,

  // Fade mode will fade instead of clearing 
  fadeMode: true,

  // Draw borders
  drawBorders: true,
};

let lastParams;
let grid = [];
let slidingBlocks = [];
let noiseTexture;

const BLOCK_VARIANTS = [
  {
    // Animated noise texture
    name: 'noise',
    init: (self) => {
      self.offsetX = floor(random(NOISE_SIZE - width / 16));
      self.offsetY = floor(random(NOISE_SIZE - height / 16));
      self.tintHue = random(360);
    },
    update: (self) => {},
    draw: (self, {screenX, screenY}) => {
      tint(self.tintHue, 100, 100);
      image(noiseTexture, 0, 0, width / 16, height / 16, self.offsetX, self.offsetY, width / 16, height / 16);
      noTint();
    },
  },
  {
    // Conway's Game of Life
    name: 'gameoflife',
    init: (self) => {
      self.cols = width / 16;
      self.rows = height / 16;
      self.grid = [];
      for (let i = 0; i < self.cols; i++) {
        self.grid.push([]);
        for (let j = 0; j < self.rows; j++) {
          self.grid[i].push(random() < 0.5 ? 1 : 0);
        }
      }
      self.hue = random(360);
    },
    update: (self) => {
      let newGrid = [];
      let updates = 0;

      for (let i = 0; i < self.cols; i++) {
        newGrid.push([]);
        for (let j = 0; j < self.rows; j++) {
          let sum = 0;
          for (let xOff = -1; xOff <= 1; xOff++) {
            for (let yOff = -1; yOff <= 1; yOff++) {
              if (xOff === 0 && yOff === 0) continue;
              let x = (i + xOff + self.cols) % self.cols;
              let y = (j + yOff + self.rows) % self.rows;
              sum += self.grid[x][y];
            }
          }
          if (self.grid[i][j] === 1 && (sum < 2 || sum > 3)) {
            newGrid[i].push(0);
          } else if (self.grid[i][j] === 0 && sum === 3) {
            newGrid[i].push(1);
          } else {
            newGrid[i].push(self.grid[i][j]);
          }
        }
      }

      for (let i = 0; i < self.cols; i++) {
        for (let j = 0; j < self.rows; j++) {
          if (self.grid[i][j] !== newGrid[i][j]) {
            updates++;
          }
        }
      }

      if (updates < 16 || random() < 0.001) {
        for (let i = 0; i < self.cols; i++) {
          for (let j = 0; j < self.rows; j++) {
            newGrid[i][j] = random() < 0.5 ? 1 : 0;
          }
        }
      }

      self.grid = newGrid;
    },
    draw: (self) => {
      let w = width / 16 / self.cols;
      let h = height / 16 / self.rows;
      for (let i = 0; i < self.cols; i++) {
        for (let j = 0; j < self.rows; j++) {
          if (self.grid[i][j] === 1) {
            noStroke();
            fill(self.hue, 80, 100);
            rect(i * w, j * h, w, h);
          }
        }
      }
    },
  },
  {
    // Bouncing balls, no collision
    name: 'bouncing-balls',
    init: (self) => {
      self.balls = [];
      let numBalls = floor(random(3, 7));
      for (let i = 0; i < numBalls; i++) {
        self.balls.push({
          x: random(width / 16),
          y: random(height / 16),
          vx: random([-1, 1]) * random(0.5, 2),
          vy: random([-1, 1]) * random(0.5, 2),
          radius: random(1, 7),
          hue: random(360),
        });
      }
    },
    update: (self) => {
      for (let ball of self.balls) {
        ball.x += ball.vx;
        ball.y += ball.vy;

        if (ball.x < 0 || ball.x > width / 16) {
          ball.vx *= -1;
        }
        if (ball.y < 0 || ball.y > height / 16) {
          ball.vy *= -1;
        }
      }
    },
    draw: (self) => {
      for (let ball of self.balls) {
        noStroke();
        fill(ball.hue, 80, 100);
        ellipse(ball.x, ball.y, ball.radius);
      }
    },
  },
  {
    // Falling rain particles, matrix style
    name: 'rain',
    init: (self) => {
      self.particles = [];
      let numParticles = floor(random(20, 50));
      for (let i = 0; i < numParticles; i++) {
        self.particles.push({
          x: random(width / 16),
          y: random(height / 16),
          hue: random(360),
        });
      }
    },
    update: (self) => {
      for (let particle of self.particles) {
        particle.y += random(0.5, 1.5);
        if (particle.y > height / 16) {
          particle.y = 0;
          particle.x = random(width / 16);
        }
      }
    },
    draw: (self) => {
      for (let particle of self.particles) {
        noStroke();
        fill(particle.hue, 80, 100);
        ellipse(particle.x, particle.y, 1);
      }
    },  
  },
  {
    // A pulsing circle
    name: 'pulse',
    init: (self) => {
      self.hue = random(360);
      self.phase = random(TWO_PI);
    },
    update: (self) => {
      self.phase += 0.1;
    },
    draw: (self) => {
      let size = (sin(self.phase) + 1) / 2 * (width / 16);
      noStroke();
      fill(self.hue, 80, 100);
      ellipse((width / 16) / 2, (height / 16) / 2, size);
    },
  },
  {
    // A worm that moves around like the snake game
    name: 'snake',
    init: (self) => {
      self.length = floor(random(5, 15));
      self.segments = [];
      self.direction = random([[1,0],[-1,0],[0,1],[0,-1]]);
      self.hue = random(360);

      let startX = floor(random(16));
      let startY = floor(random(16));
      for (let i = 0; i < self.length; i++) {
        self.segments.push({ x: startX, y: startY });
      }
    },
    update: (self) => {
      let head = self.segments[0];
      let newX = (head.x + self.direction[0] + 16) % 16;
      let newY = (head.y + self.direction[1] + 16) % 16;

      if (self.segments.some(seg => seg.x === newX && seg.y === newY)) {
        let startX = floor(random(16));
        let startY = floor(random(16));
        self.segments = [];
        for (let i = 0; i < self.length; i++) {
          self.segments.push({ x: startX, y: startY });
        }
      } else {
        self.segments.pop();
        self.segments.unshift({ x: newX, y: newY });

        if (random() < 0.3) {
          self.direction = random([[1,0],[-1,0],[0,1],[0,-1]]);
        }
      }
    },
    draw: (self) => {
      let w = width / 16;
      let h = height / 16;
      for (let seg of self.segments) {
        noStroke();
        fill(self.hue, 80, 100);
        rect(seg.x, seg.y, 1, 1);
      }
    },
  },
  {
    // N random walking particles
    name: 'bugs',
    init: (self) => {
      let blockWidth = width / 16;
      let blockHeight = height / 16;

      self.particles = [];
      let numParticles = floor(random(5, 15));
      for (let i = 0; i < numParticles; i++) {
        self.particles.push({
          x: floor(random(blockWidth)),
          y: floor(random(blockHeight)),
          hue: random(360),
        });
      }
    },
    update: (self) => {
      let blockWidth = width / 16;
      let blockHeight = height / 16;

      for (let particle of self.particles) {
        let dir = random([[1,0],[-1,0],[0,1],[0,-1]]);
        particle.x = (particle.x + dir[0] + blockWidth) % blockWidth;
        particle.y = (particle.y + dir[1] + blockHeight) % blockHeight;
      }
    },
    draw: (self) => {
      let w = width / 16;
      let h = height / 16;
      for (let particle of self.particles) {
        noStroke();
        fill(particle.hue, 80, 100);
        rect(particle.x, particle.y, 1, 1);
      }
    },  
  },
  {
    // A random chinese character that changes periodically
    name: 'char',
    init: (self) => {
      self.char = String.fromCharCode(floor(random(0x4E00, 0x9FFF)));
      self.hue = random(360);
      self.frameCounter = 0;
      self.changeInterval = floor(random(100, 200));
    },
    update: (self) => {
      self.frameCounter++;
      if (self.frameCounter >= self.changeInterval) {
        self.char = String.fromCharCode(floor(random(0x4E00, 0x9FFF)));
        self.hue = random(360);
        self.frameCounter = 0;
        self.changeInterval = floor(random(30, 120));
      }
    },
    draw: (self) => {
      const bw = width / 16;
      const bh = height / 16;
      const pad = bw * 0.1;

      textAlign(CENTER, CENTER);
      textSize(1);
      const w = textWidth(self.char);
      const h = textAscent() + textDescent();
      const s = Math.min((bw - 2 * pad) / w, (bh - 2 * pad) / h);
      textSize(s * 4);

      fill(self.hue, 80, 100);
      noStroke();
      text(self.char, bw / 2, bh / 2);
    },  
  }
];

class Block {
  constructor() {
    this.sliding = false;
    
    let i = floor(random(BLOCK_VARIANTS.length));
    let variant = BLOCK_VARIANTS[i];

    variant.init(this);
    this.update = () => variant.update(this);
    this.draw = (args) => variant.draw(this, args);
  }
}

function setup() {
  createCanvas(400, 400);
  colorMode(HSB, 360, 100, 100, 100);

  gui = createGuiPanel("params");
  gui.addObject(params);
  gui.setPosition(420, 0);

  reset();
}

function reset() {
  grid = [];
  slidingBlocks = [];

  for (let i = 0; i < 16; i++) {
    grid.push([]);
    for (let j = 0; j < 16; j++) {
      grid[i].push(null);
    }
  }

  for (let i = 0; i < 16; i++) {
    for (let j = 0; j < 16; j++) {
      grid[i][j] = new Block();
    }
  }
  
  // Remove missing blocks
  for (let i = 0; i < params.missingBlocks; i++) {
    while(true) {
      let x = floor(random() * 16);
      let y = floor(random() * 16);
      
      if (grid[x][y] != null) {
        if (DEBUG_PRINT) console.log("Removing block at", x, y);
        grid[x][y] = null;
        break;
      }
    }
  }
}

function draw() {
  if (lastParams == undefined || Object.keys(params).some((k) => params[k] !== lastParams[k])) {
    reset();
    lastParams = { ...params };
  }

  // Initialize/update noise texture
  if (!noiseTexture) {
    noiseTexture = createGraphics(NOISE_SIZE, NOISE_SIZE);
    noiseTexture.colorMode(HSB, 360, 100, 100, 100);
  }
  noiseTexture.loadPixels();
  for (let x = 0; x < NOISE_SIZE; x++) {
    for (let y = 0; y < NOISE_SIZE; y++) {
      let n = noise(x * 0.05, y * 0.05, frameCount * 0.01);
      n = n > 0.5 ? 1 : 0;
      let brightness = n * 100;
      noiseTexture.set(x, y, color(0, 0, brightness));
    }
  }
  noiseTexture.updatePixels();

  if (params.fadeMode) {
    noStroke();
    fill(0, 0, 0, 10);
    rect(0, 0, width, height);
  } else {
    background("black");
  }

  // Update all block's internal states
  for (let x = 0; x < 16; x++) {
    for (let y = 0; y < 16; y++) {
      if (grid[x][y] !== null) {
        grid[x][y].update();
      }
    }
  }

  // If we have any empty spaces, start a slide into that position
  for (let x = 0; x < 16; x++) {
    for (let y = 0; y < 16; y++) {
      // Skip cells that are already occupied
      if (grid[x][y] !== null) continue;

      // Skip cells something is already sliding into
      if (slidingBlocks.some(sb => sb.dst.x === x && sb.dst.y === y)) continue;

      // Find neighbors that can slide into this cell
      let neighbors = [];
      for (let [xd, yd] of [[-1,0],[1,0],[0,-1],[0,1]]) {
        let nx = x + xd;
        let ny = y + yd;
        if (nx >= 0 && nx < 16 && ny >= 0 && ny < 16) {
          // Only consider non-empty, non-sliding neighbors
          if (grid[nx][ny] !== null && !grid[nx][ny].sliding) {
            neighbors.push({ x: nx, y: ny });
          }
        }
      }

      // If we have neighbors, pick one at random to slide into that position
      if (neighbors.length > 0) {
        let choice = random(neighbors);

        if (DEBUG_PRINT) {
          console.log(`Starting slide from (${choice.x}, ${choice.y}) to (${x}, ${y})`);
        }

        slidingBlocks.push({
          src: { x: choice.x, y: choice.y },
          dst: { x: x, y: y },
          progress: 0,
        });
        grid[choice.x][choice.y].sliding = true;
      }
    }
  }
  
  if (DEBUG_PRINT) console.log("Currently sliding count:", slidingBlocks.length);

  // Update sliding blocks
  for (let i = slidingBlocks.length - 1; i >= 0; i--) {
    let sb = slidingBlocks[i];
    sb.progress++;

    if (random() < params.slideSpeedVariation) {
      sb.progress++;
    }

    // If the slide is complete, finalize the move
    if (sb.progress >= params.slideFrames) {
      if (DEBUG_PRINT) {
        console.log(`Completing slide from (${sb.src.x}, ${sb.src.y}) to (${sb.dst.x}, ${sb.dst.y})`);
      }

      grid[sb.dst.x][sb.dst.y] = grid[sb.src.x][sb.src.y];
      grid[sb.dst.x][sb.dst.y].sliding = false;
      grid[sb.src.x][sb.src.y] = null;
      slidingBlocks.splice(i, 1);
    }
  }

  let blockWidth = width / 16;
  let blockHeight = height / 16;

  for (let x = 0; x < 16; x++) {
    for (let y = 0; y < 16; y++) {
      let block = grid[x][y];
      if (!block) continue;
        
      push();
      translate(blockWidth * x, blockHeight * y);

      // If this block is sliding, compute its position
      let slidingBlock = slidingBlocks.find(sb => sb.src.x === x && sb.src.y === y);
      let screenX = x * blockWidth;
      let screenY = y * blockHeight;

      if (slidingBlock) {
        let progress = slidingBlock.progress / params.slideFrames;
        screenX = lerp(slidingBlock.src.x, slidingBlock.dst.x, progress) * blockWidth;
        screenY = lerp(slidingBlock.src.y, slidingBlock.dst.y, progress) * blockHeight;
        translate(screenX - x * blockWidth, screenY - y * blockHeight);
      }

      block.draw({x, y, screenX, screenY});
      
      if (params.drawBorders) {
        stroke("darkgray");
        strokeWeight(0.1);
        noFill();
        rect(0, 0, blockWidth, blockHeight);
      }

      pop();
    }
  }
}
{{</p5js>}}
