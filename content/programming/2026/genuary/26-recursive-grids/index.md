---
title: "Genuary 2026.26: Recursive Grids"
date: "2026-01-26"
programming/languages:
- JavaScript
programming/topics:
- Generative Art
- Procedural Content
- p5js
series:
- Genuary 2026
cover: gen26.26.png
---
A favorite technique of mine. I've already done it on [[Genuary 2026.05: Write 'genuary'|day 5]](), [[Genuary 2026.07: Boolean algebra|day 7]](), and [[Genuary 2026.13: Self Portrait|day 13]](). But now we can go one a-maze-ing step further...

See what I did there? :smile:

Basically: generate a maze. For each cell in the maze... generate a smaller maze! Recursively. 

<!--more-->

By default, we split into an average of 5x5, but it can vary (using a [[wiki:gaussian distribution]]()). You can limit the recursion based on `maxDepth` or `maxMazes` (it will very rarely / never hit a depth of 10; you can set `maxMazes` to any non-number to disable it). If you turn off `randomizeDivisions`, it will always split into *exactly* that many child nodes. 

`splitChance` controls what percent of frames tries to spawn a new maze. 

`colorize` is a little hard to look at this time, but figured I might as well. It does work better (somehow) with the solver state visualization on. 

If `onlySplitVisited` is set, only squares that are currently on the path of the generated maze already will be split. This is mostly visual while it's running, the end result should be the same. 

~The wall modes control how the different levels of cell interact:~

* ~`centered` - Remove the center 'half' of the wall (leaving 1/4 on either side)~
* ~`recursive` - Remove a wall if this node or any parent of it didn't have a wall there~
* ~`corners` - Remove only the corner of each node~
* ~`tiny` - Remove only a single spot on each node--this one more than the others doesn't always generate solvable mazes~

Edit: I removed wall modes since only `corners` actually always makes solvable mazes (so that's the only remaining one). 

~One thing I would love to do would be to add an A* solver after it's done that works just on the pixels of the generated image. That'd be cool. Maybe later.~

Edit: I added the solver! It runs A*, turn it on with `runSolver`. It won't reset the maze. 

{{<p5js width="600" height="500">}}
let gui;
let params = {
  divisions: 5, divisionsMin: 2, divisionsMax: 20,
  randomizeDivisions: true,
  maxDepth: 4, maxDepthMin: 2, maxDepthMax: 10,
  maxMazes: "250",
  solverStepsPerFrame: 25, solverStepsPerFrameMin: 1, solverStepsPerFrameMax: 1000,
  pauseMode: ["pause", "stop", "continue"],
  splitChance: 0.5, splitChanceMin: 0, splitChanceMax: 1, splitChanceStep: 0.01,
  colorize: false,  
  onlySplitVisited: true,
  runSolver: false,
  displaySolverState: true,
};

class AStarSolver {
  constructor() {
    this.stateBuffer = createGraphics(width, height);
    this.stateBuffer.colorMode(HSB, 360, 100, 100, 100);
    this.stateBufferDirty = true;
    this.resetFromPixels();
  }

  // Reload the current maze from the current pixel data of the canvas
  // This has to be done when we hit a wall that didn't previously exist
  resetFromPixels(pixelData) {
    this.pixelData = pixelData || this.capturePixels();
    this.w = width;
    this.h = height;
    this.size = this.w * this.h;

    this.walkable = new Uint8Array(this.size);
    for (let y = 0; y < this.h; y++) {
      for (let x = 0; x < this.w; x++) {
        this.walkable[this.idx(x, y)] = this.isWalkableFromData(x, y, this.pixelData) ? 1 : 0;
      }
    }

    this.startIdx = this.findFirstOpen();
    this.goalIdx = this.findLastOpen();

    this.cameFrom = new Int32Array(this.size).fill(-1);
    this.gScore = new Float32Array(this.size).fill(Infinity);
    this.fScore = new Float32Array(this.size).fill(Infinity);
    this.openSet = [];
    this.openFlags = new Uint8Array(this.size);
    this.closed = new Uint8Array(this.size);
    this.path = [];
    this.finished = false;
    this.stateBufferDirty = true;

    if (this.startIdx >= 0 && this.goalIdx >= 0) {
      this.gScore[this.startIdx] = 0;
      this.fScore[this.startIdx] = this.heuristic(this.startIdx, this.goalIdx);
      this.openSet.push(this.startIdx);
      this.openFlags[this.startIdx] = 1;
      this.bestIdx = this.startIdx;
    } else {
      this.finished = true;
    }
  }

  capturePixels() {
    loadPixels();
    return Uint8ClampedArray.from(pixels);
  }

  idx(x, y) {
    return y * this.w + x;
  }

  pos(i) {
    return [i % this.w, Math.floor(i / this.w)];
  }

  isWalkableFromData(x, y, data) {
    const base = 4 * (y * this.w + x);
    const r = data[base];
    const g = data[base + 1];
    const b = data[base + 2];
    return (r + g + b) > 512;
  }

  // Find the 'start' of the maze
  // This is mostly just 1,1
  findFirstOpen() {
    for (let i = width + 1; i < this.size; i++) {
      if (this.walkable[i]) return i;
    }
    return -1;
  }

  // Find the 'end' of the maze
  findLastOpen() {
    for (let i = this.size - width - 1; i >= 0; i--) {
      if (this.walkable[i]) return i;
    }
    return -1;
  }

  refreshWalkable() {
    const snapshot = this.capturePixels();
    for (let y = 0; y < this.h; y++) {
      for (let x = 0; x < this.w; x++) {
        const i = this.idx(x, y);
        const w = this.isWalkableFromData(x, y, snapshot) ? 1 : 0;
        this.walkable[i] = w;
      }
    }
    this.pixelData = snapshot;
  }

  // Manhattan distance heuristic
  heuristic(a, b) {
    const [ax, ay] = this.pos(a);
    const [bx, by] = this.pos(b);
    return abs(ax - bx) + abs(ay - by);
  }

  // Reconstruct the best path so far so we can display it
  reconstructPath(i) {
    const rev = [];
    let current = i;
    while (current >= 0) {
      rev.push(this.pos(current));
      current = this.cameFrom[current];
    }
    return rev.reverse();
  }

  popLowestF() {
    let bestIdx = 0;
    for (let i = 1; i < this.openSet.length; i++) {
      if (this.fScore[this.openSet[i]] < this.fScore[this.openSet[bestIdx]]) {
        bestIdx = i;
      }
    }
    const node = this.openSet.splice(bestIdx, 1)[0];
    this.openFlags[node] = 0;
    return node;
  }

  neighbors(i) {
    const [x, y] = this.pos(i);
    const out = [];
    if (x > 0) out.push(this.idx(x - 1, y));
    if (x < this.w - 1) out.push(this.idx(x + 1, y));
    if (y > 0) out.push(this.idx(x, y - 1));
    if (y < this.h - 1) out.push(this.idx(x, y + 1));
    return out;
  }

  // Verify that the current path is still valid
  // The maze changes over time, so reset if we hit a new wall
  verify() {
    const stillOpen = (idx) => idx >= 0 && this.isWalkableFromData(...this.pos(idx), this.pixelData);

    if (!stillOpen(this.startIdx) || !stillOpen(this.goalIdx)) {
      this.resetFromPixels(this.pixelData);
      return;
    }

    // If solver is finished but has no path, the maze was impossible - reset to try again
    if (this.finished && this.path.length === 0) {
      this.resetFromPixels(this.pixelData);
      return;
    }

    if (this.path.length === 0) return;
    for (const [x, y] of this.path) {
      if (!this.isWalkableFromData(x, y, this.pixelData)) {
        this.resetFromPixels(this.pixelData);
        return;
      }
    }
  }

  // Perform one step of the A* algorithm
  step() {
    if (this.finished || this.startIdx < 0 || this.goalIdx < 0) return;
    if (this.openSet.length === 0) {
      this.finished = true;
      return;
    }

    const current = this.popLowestF();
    this.closed[current] = 1;
    this.bestIdx = current;
    this.stateBufferDirty = true;

    if (current === this.goalIdx) {
      this.finished = true;
      this.path = this.reconstructPath(current);
      return;
    }

    for (const n of this.neighbors(current)) {
      if (!this.walkable[n] || this.closed[n]) continue;
      const tentativeG = this.gScore[current] + 1;
      if (tentativeG < this.gScore[n]) {
        this.cameFrom[n] = current;
        this.gScore[n] = tentativeG;
        this.fScore[n] = tentativeG + this.heuristic(n, this.goalIdx);
        if (!this.openFlags[n]) {
          this.openSet.push(n);
          this.openFlags[n] = 1;
        }
      }
    }
  }

  updateStateBuffer() {
    this.stateBuffer.clear();
    this.stateBuffer.noStroke();
    
    if (params.colorize) {
      // Vary hue of closed set when colorize is enabled
      for (let i = 0; i < this.size; i++) {
        if (this.closed[i]) {
          const [x, y] = this.pos(i);
          const hue = (i / this.size) * 360;
          this.stateBuffer.fill(hue, 60, 80, 40);
          this.stateBuffer.rect(x, y, 1, 1);
        }
      }
    } else {
      // Closed set in light gray
      this.stateBuffer.fill(0, 0, 60, 40);
      for (let i = 0; i < this.size; i++) {
        if (this.closed[i]) {
          const [x, y] = this.pos(i);
          this.stateBuffer.rect(x, y, 1, 1);
        }
      }
    }
    
    // Open set in orange
    this.stateBuffer.fill(30, 90, 90, 70);
    for (let i = 0; i < this.size; i++) {
      if (this.openFlags[i]) {
        const [x, y] = this.pos(i);
        this.stateBuffer.rect(x, y, 1, 1);
      }
    }
    
    this.stateBufferDirty = false;
  }

  draw() {
    if (this.startIdx < 0 || this.goalIdx < 0) return;

    if (params.displaySolverState) {
      if (this.stateBufferDirty) {
        this.updateStateBuffer();
      }
      image(this.stateBuffer, 0, 0);
    }

    strokeWeight(2);
    noFill();

    let toDraw = this.path;
    if (toDraw.length === 0 && this.bestIdx >= 0) {
      toDraw = this.reconstructPath(this.bestIdx);
    }

    if (toDraw.length > 1) {
        stroke("red");
        beginShape();
        for (const [x, y] of toDraw) {
            vertex(x + 0.5, y + 0.5);
        }
        endShape();
    }

    stroke("blue");
    strokeWeight(6);
    point(...this.pos(this.startIdx));
    stroke("green");
    point(...this.pos(this.goalIdx));
  }
}

class Maze {
  constructor(size, startSide = "north", endSide = "south") {
    this.hue = random(360);
    this.size = size;
    this.startSide = startSide;
    this.endSide = endSide;

    this.grid = [];
    for (let y = 0; y < size; y++) {
      const row = [];
      for (let x = 0; x < size; x++) {
        row.push({
          x,
          y,
          visited: false,
          walls: { N: true, E: true, S: true, W: true },
          subMaze: null,
        });
      }
      this.grid.push(row);
    }

    let i = Math.floor(Math.random() * this.size);
    if (startSide == 'north') {
      this.current = this.grid[0][i];
    } else if (startSide == 'south') {
      this.current = this.grid[this.size - 1][i];
    } else if (startSide == 'west') {
      this.current = this.grid[i][0];
    } else if (startSide == 'east') {
      this.current = this.grid[i][this.size - 1];
    }
    
    this.current.visited = true;
    this.stack = [this.current];
  }

  step() {
    let didAnything = false;
    
    for (let y = 0; y < this.size; y++) {
      for (let x = 0; x < this.size; x++) {
        didAnything |= this.grid[x][y].subMaze?.step();
      }
    }
    
    if (this.stack.length === 0) return didAnything;

    let cell = this.stack[this.stack.length - 1];
    let neighbors = [];

    if (cell.y > 0) neighbors.push([this.grid[cell.y - 1][cell.x], "N"]);
    if (cell.x < this.size - 1) neighbors.push([this.grid[cell.y][cell.x + 1], "E"]);
    if (cell.y < this.size - 1) neighbors.push([this.grid[cell.y + 1][cell.x], "S"]);
    if (cell.x > 0) neighbors.push([this.grid[cell.y][cell.x - 1], "W"]);

    neighbors = neighbors
      .filter(([n]) => !n.visited)
      .map(([n, dir]) => ({ cell: n, dir }));

    if (neighbors.length > 0) {
      let next = neighbors[Math.floor(Math.random() * neighbors.length)];
      let nextCell = next.cell;

      let dx = nextCell.x - cell.x;
      let dy = nextCell.y - cell.y;

      if (dx === 1) {
        cell.walls.E = false;
        nextCell.walls.W = false;
      } else if (dx === -1) {
        cell.walls.W = false;
        nextCell.walls.E = false;
      } else if (dy === 1) {
        cell.walls.S = false;
        nextCell.walls.N = false;
      } else if (dy === -1) {
        cell.walls.N = false;
        nextCell.walls.S = false;
      }

      nextCell.visited = true;
      this.stack.push(nextCell);
    } else {
      this.stack.pop();
    }

    return true;
  }
  
  recur(w = width, h = height, depth = 1) {
    let x = floor(random(this.size));
    let y = floor(random(this.size));
    let cell = this.grid[y][x];
    
    let cellW = floor(w / this.size);
    let cellH = floor(h / this.size);

    if (cell.subMaze) {
      return cell.subMaze.recur(cellW, cellH, depth + 1);
    }
    
    if (depth >= params.maxDepth) return false;

    let newSize = this.size;
    if (params.randomizeDivisions) {
      newSize = floor(randomGaussian(params.divisions, params.divisions / 2));
    }
    newSize = max(newSize, 2);
        
    // Ensure each cell is at least 3 pixels wide to avoid subpixel rendering issues
    let minCellSize = 3;
    if (cellW / newSize < minCellSize) return false;
    if (cellH / newSize < minCellSize) return false;
    
    if (params.onlySplitVisited && !cell.visited) return false;
    
    cell.subMaze = new Maze(newSize);
    return true;
  }

  draw(x = 0, y = 0, w = width, h = height, walls = {}) {
    if (params.colorize) {
      noStroke();
      fill(this.hue, 20, 100);
      rect(x, y, w, h);
    }
    
    const cellW = w / this.size;
    const cellH = h / this.size;
    
    let halfW = floor(this.size / 2);
    let halfH = floor(this.size / 2);
    let width14 = this.size / 4;
    let width34 = width14 * 3;
    let height14 = this.size / 4;
    let height34 = height14 * 3;

    stroke("black");
    strokeWeight(1);
    noFill();
    for (let row of this.grid) {
      for (let cell of row) {
        const cx = x + cell.x * cellW;
        const cy = y + cell.y * cellH;
        
        let enabled = {...cell.walls};
        
        let removeX = true;
        let removeY = true;
        
        if (cell.x == 0) {
            if (cell.y == 0) {
                enabled.N = false;
                enabled.W = false;
            } else if (cell.y == this.size - 1) {
                enabled.S = false;
                enabled.W = false;
            }
            } else if (cell.x == this.size - 1) {
            if (cell.y == 0) {
                enabled.N = false;
                enabled.E = false;
            } else if (cell.y == this.size - 1) {
                enabled.S = false;
                enabled.E = false;
            }
        }
          
        if (enabled.N) line(cx, cy, cx + cellW, cy);
        if (enabled.E) line(cx + cellW, cy, cx + cellW, cy + cellH);
        if (enabled.S) line(cx + cellW, cy + cellH, cx, cy + cellH);
        if (enabled.W) line(cx, cy + cellH, cx, cy);

        if (cell.subMaze) {
          let subWalls = {
            N: cell.walls.N & walls.N,
            E: cell.walls.E & walls.E,
            S: cell.walls.S & walls.S,
            W: cell.walls.W & walls.W,
          };
          cell.subMaze.draw(cx, cy, cellW, cellH, subWalls);
        }
      }
    }
  }
  
  count() {
    let sum = 1;
    for (let row of this.grid) {
      for (let cell of row) {
        if (cell.subMaze) {
          sum += cell.subMaze.count();
        }
      }
    }
    return sum;
  }
}

let maze;
let lastParams;
let pauseUntil;
let solver;

function setup() {
  createCanvas(400, 400);
  colorMode(HSB, 360, 100, 100, 100);
  
  gui = createGuiPanel("params");
  gui.addObject(params);
  gui.setPosition(420, 0);

  reset();
}

function reset() {
  pauseUntil = undefined;
  maze = new Maze(params.divisions);
  solver = undefined;
}

function draw() {
  // Rendering related params don't reset the maze (so we can solve a maze we generated!)
  const dontResetMazeParams = ['runSolver', 'displaySolverState', 'solverStepsPerFrame', 'colorize'];
  const mazeParamsChanged = lastParams == undefined || Object.keys(params).some((k) => 
    !dontResetMazeParams.includes(k) && params[k] !== lastParams[k]
  );
  
  if (mazeParamsChanged) {
    reset();
    lastParams = {
      ...params
    };
  } else if (lastParams) {
    lastParams = {
      ...params
    };
    pauseUntil = undefined;
  }

  if (pauseUntil) {
    if (millis() < pauseUntil) {
      return;
    } else {
      reset();
    }
  }
  
  let didUpdate = maze.step();
  let hitMaximum = parseInt(params.maxMazes) && maze.count() >= params.maxMazes;
  
  if (random() < params.splitChance && !hitMaximum) {
    didUpdate |= maze.recur();    
  }
  
  background("white");
  
  maze.draw();

  if (params.runSolver) {
    if (!solver) solver = new AStarSolver();
    solver.refreshWalkable();
    solver.verify();
    for (let i = 0; i < params.solverStepsPerFrame; i++) {
      solver.step();
    }
    solver.draw();
  } else {
    solver = undefined;
  }
  
  // Only pause/stop when maze is done AND solver is either disabled or finished
  let solverDone = !params.runSolver || (solver && solver.finished);
  if (!didUpdate && hitMaximum && solverDone) {
    if (params.pauseMode == "pause") {
      pauseUntil = millis() + 1000;    
    } else if (params.pauseMode == "stop") {
      pauseUntil = millis() + 1e9;
    } else {
      reset();
    }
  }
}
{{</p5js>}}

## Examples

### [Even fifths](?randomizeDivisions=false&runSolver=true)

![](even-fifths.png)

### [Lucky 13](?divisions=13&randomizeDivisions=false&runSolver=true)

![](lucky-13.png)

Edit: This was previously possible on 13x13, but now it has to be 11x11 to avoid subpixel issues with the solver. I'm keeping the name anyways. :p

### [Four corners](?divisions=4&wallMode=corners&runSolver=true)

![](four-corners.png)

### [It's certainly colorful](?divisions=7&maxDepth=10&maxMazes=1000&splitChance=1&colorize=true&runSolver=true)

![](colorful.png)