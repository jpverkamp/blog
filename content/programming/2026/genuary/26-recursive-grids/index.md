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
A favorite technique of mine. I've already done it on [[Genuary 2026.05: Write 'genuary'|day 5]]() and [[Genuary 2026.07: Boolean algebra|day 7]](). But now we can go one a-maze-ing step further...

See what I did there? :smile:

Basically: generate a maze. For each cell in the maze... generate a smaller maze! Recursively. 

By default, we split into an average of 5x5, but it can vary (using a [[wiki:gaussian distribution]]()). You can limit the recursion based on `maxDepth` or `maxMazes` (it will very rarely / never hit a depth of 10; you can set `maxMazes` to any non-number to disable it). If you turn off `randomizeDivisions`, it will always split into *exactly* that many child nodes. 

`splitChance` controls what percent of frames tries to spawn a new maze. 

`colorize` is a little hard to look at this time, but figured I might as well. 

If `onlySplitVisited` is set, only squares that are currently on the path of the generated maze already will be split. This is mostly visual while it's running, the end result should be the same. 

The wall modes control how the different levels of cell interact:

* `centered` - Remove the center 'half' of the wall (leaving 1/4 on either side)
* `recursive` - Remove a wall if this node or any parent of it didn't have a wall there
* `corners` - Remove only the corner of each node
* `tiny` - Remove only a single spot on each node--this one more than the others doesn't always generate solvable mazes

One thing I would love to do would be to add an A* solver after it's done that works just on the pixels of the generated image. That'd be cool. Maybe later. 

<!--more-->

{{<p5js width="600" height="500">}}
let gui;
let params = {
  divisions: 5, divisionsMin: 2, divisionsMax: 20,
  randomizeDivisions: true,
  maxDepth: 5, maxDepthMin: 2, maxDepthMax: 10,
  maxMazes: "1000",
  pauseMode: ["pause", "stop", "continue"],
  splitChance: 0.5, splitChanceMin: 0, splitChanceMax: 1, splitChanceStep: 0.01,
  colorize: false,  
  onlySplitVisited: true,
  wallMode: ["centered", "recursive", "corners", "tiny"],
};

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
    
    let cellW = w / this.size;
    let cellH = h / this.size;

    if (cell.subMaze) {
      return cell.subMaze.recur(cellW, cellH, depth + 1);
    }
    
    if (depth >= params.maxDepth) return false;

    let newSize = this.size;
    if (params.randomizeDivisions) {
      newSize = floor(randomGaussian(params.divisions, params.divisions / 2));
    }
    newSize = max(newSize, 2);
        
    if (newSize * 2 > cellW) return false;
    if (newSize * 2 > cellH) return false;
    
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
    strokeWeight(0.5);
    noFill();
    for (let row of this.grid) {
      for (let cell of row) {
        const cx = x + cell.x * cellW;
        const cy = y + cell.y * cellH;
        
        // Edges 
        if (cell.y == 0) {
          
        }
        
        let enabled = {...cell.walls};
        
        let removeX = true;
        let removeY = true;
        
        // If any ancestor didn't have a wall on this boder, we don't either
        if (params.wallMode == 'recursive') {
          if (cell.x == 0 && !walls.W) enabled.W = false;
          if (cell.x == this.size - 1 && !walls.E) enabled.E = false;
          if (cell.y == 0 && !walls.N) enabled.N = false;
          if (cell.y == 0 && !walls.S) enabled.S = false;
        }
        
        // Corners skip their walls
        if (params.wallMode == 'corners') {
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
        }
        
        // A single spot on each wall is removed
        if (params.wallMode == 'tiny') {
          let halfP = floor(this.size / 2);
          if (cell.x == 0 && cell.y == halfP) {
            enabled.W = false;
          }
          if (cell.x == this.size - 1 && cell.y == halfP) {
            enabled.E = false;
          }
          if (cell.y == 0 && cell.x == halfP) {
            enabled.N = false;
          }
          if (cell.y == this.size - 1 && cell.x == halfP) {
            enabled.S = false;
          }
        }
        
        // The center half (1/4 each side) is removed
        if (params.wallMode == 'centered') {
          let qs = this.size / 4;
          if (cell.x == 0 && cell.y >= qs && cell.y <= this.size - qs) {
            enabled.W = false;
          }
          if (cell.x == this.size - 1 && cell.y >= qs && cell.y <= this.size - qs) {
            enabled.E = false;
          }
          if (cell.y == 0 && cell.x >= qs && cell.x <= this.size - qs) {
            enabled.N = false;
          }
          if (cell.y == this.size - 1 && cell.x >= qs && cell.x <= this.size - qs) {
            enabled.S = false;
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
}

function draw() {
  if (lastParams == undefined || Object.keys(params).some((k) => params[k] !== lastParams[k])) {
    reset();
    lastParams = {
      ...params
    };
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
  
  if (!didUpdate && hitMaximum) {
    if (params.pauseMode == "pause") {
      pauseUntil = millis() + 1000;    
    } else if (params.pauseMode == "stop") {
      pauseUntil = millis() + 1e9;
    } else {
      reset();
    }
  }
  
  background("white");
  
  maze.draw();
}
{{</p5js>}}

## Examples

### [Even fifths](?randomizeDivisions=false)

![](even-fifths.png)

### [Lucky 13](?divisions=13&randomizeDivisions=false)

![](lucky-13.png)

### [Four corners](?divisions=4&wallMode=corners)

![](four-corners.png)

### [It's certainly colorful](?divisions=4&maxDepth=10&colorize=true&wallMode=corners)

![](colorful.png)