---
title: "Genuary 2026.11: Quine"
date: "2026-01-11"
programming/languages:
- JavaScript
programming/topics:
- Generative Art
- Procedural Content
- p5js
series:
- Genuary 2026
cover: gen26.11.png
---
## 9) Quine

Making a genart [[wiki:quine]]()? That's... certainly a thing!

So basically I made a very simple stack based virtual machine. You can check the source code below for what commands it can actually run. It will then run until it outputs enough code to match the input length (or times out). If it happens to output a quine? Woot!

If not, it will randomly mutate and try again. 

* `ticksPerFrame` - How fast the simulation will run
* `breakAfter` - If this many ops run without output, break
* `maxStack` - Limit the size of the stack
* `pauseAfter` - Pause to see what happened after output is done or a break
* `pauseTime` - How long
* `randomizePercent` - How much of the input to randomly change for the next iteration
* `runOutput` - Run the output as the next program (otherwise, randomize the input)
* `fromString` - If you want to provide your own program (this is base64 of a compressed version of the bytes that make up the code; good luck?)

If you manage to find a quine, I'd *love* to hear what it was. I haven't found one yet. The string (that you can put it `fromString`) in your developer tools / JavaScript console. 

<!--more-->

{{<p5js width="600" height="420">}}
let gui;
let params = {
  cellSize: 10, cellSizeMin: 2, cellSizeMax: 40,
  ticksPerFrame: 100, ticksPerFrameMin: 0, ticksPerFrameMax: 1000,
  breakAfter: 1000, breakAfterMin: 1, breakAfterMax: 10000,
  maxStack: 256, maxStackMin: 4, maxStackMax: 1024,
  pauseAfter: true,
  pauseTime: 0.5, pauseTimeMin: 0, pauseTimeMax: 10.0, pauseTimeStep: 0.001,
  randomizePercent: 0.1, randomizePercentMin: 0.01, randomizePercentMax: 1.0, randomizePercentStep: 0.01,
  runOutput: true,
  fromString: "",
};

const OPS = [
  {name: 'nop', f: (m) => {}},
  {name: 'push', f: (m) => m.push(m.next())},
  {name: 'pop', f: (m) => m.pop()},
  {name: 'dup', f: (m) => { 
    let v = m.pop();
    m.push(v);
    m.push(v); 
  }},
  {name: 'roll', f: (m) => {
    let d = m.pop();
    let c = m.pop();
    
    let temp = [];
    for (let i = 0; i < d; i++) {
      if (m.stack.length > 0) {
        temp.push(m.pop());
      }
    }
    
    for (let i = 0; i < c; i++) {
      temp.push(temp.shift());
    }
    
    for (let v in temp) {
      m.push(v);
    }
  }},
  
  {name: 'out', f: (m) => m.out(m.pop())},
  
  {name: 'add', f: (m) => m.push(m.pop() + m.pop())},
  {name: 'sub', f: (m) => m.push(m.pop() - m.pop())},
  {name: 'mul', f: (m) => m.push(m.pop() * m.pop())},
  {name: 'div', f: (m) => m.push(m.pop() / (m.pop() || 1))},
  
  {name: 'not', f: (m) => m.push(m.pop() == 1 ? 0 : 1)},  
  {name: 'greater', f: (m) => m.push(m.pop() > m.pop() ? 1 : 0)},
  
  {name: 'jump', f: (m) => m.pc += m.pop()},
  {name: 'back', f: (m) => m.pc -= m.pop()},
];

class VM {
  constructor(w, h) {
    this.w = w;
    this.h = h;
    this.reset();
  }
  
  reset() {
    this.message = "";
    this.code = [];
    this.output = [];
    this.stack = [];
    this.pc = 0;
    this.ticksSinceOutput = 0;
  }
  
  push(v) {
    v = floor(v);
    while (v < 0) v += 256;
    this.stack.push(v % 256);
  }
  
  pop() {
    if (this.stack.length == 0) {
      return 0;
    } else {
      return this.stack.pop();
    }
  }
  
  next() {
    let v = this.code[this.pc % this.code.length];
    this.pc += 1;
    return v;
  }
  
  out(v) {
    this.ticksSinceOutput = 0;
    this.output.push(v % OPS.length);
  }
  
  randomize() {
    let previousCode = this.code || [];
    
    this.reset();
    
    for (let i = 0; i < this.w * this.h; i++) {
      if (i < previousCode.length && random() > params.randomizePercent) {
        this.code.push(previousCode[i]);
      } else {
        this.code.push(floor(random() * 256));
      }      
    }
  }
  
  step() {
    this.ticksSinceOutput += 1;
    
    let v = this.next();
    let op = OPS[v % OPS.length];
    op.f(this);
    
    while (this.pc < 0) this.pc += this.code.length;
    this.pc = this.pc % this.code.length;
    
    while (this.stack.lenght > params.maxStack) {
      this.stack.shift();
    }
  }
  
  draw() {
    background("white");
    
    // My program
    let draw = (data, xOffset) => {
      for (let cellX = 0; cellX < this.w; cellX++) {
        for (let cellY = 0; cellY < this.h; cellY++) {
          let i = cellX + cellY * this.w
          if (i >= data.length) {
            break;
          }
          
          let v = data[i];
          let hue = 360 * (v % OPS.length) / OPS.length;

          noStroke();
          fill(hue, 50, 100);
          
          rect(
            xOffset + cellX * params.cellSize,
            cellY * params.cellSize,
            params.cellSize,
            params.cellSize,
          );
        }
      }
    }
    
    draw(this.code, 0);
    draw(this.output, this.w * params.cellSize);
    
    // PC
    stroke("black");
    noFill();
    rect(
      this.pc % this.w * params.cellSize,
      floor(this.pc / this.w) * params.cellSize,
      params.cellSize,
      params.cellSize,
    );

    // Debug
    fill("black");
    if (this.message) {
      text(this.message, 8, this.h * params.cellSize + 16);
    } else {
      text(this.stack, 8, this.h * params.cellSize + 16);
    }
    
    // Borders
    stroke("black");
    strokeWeight(1);
    noFill();
    rect(
      0,
      0,
      this.w * params.cellSize,
      this.h * params.cellSize
    );
    
    rect(
      this.w * params.cellSize,
      0,
      this.w * params.cellSize,
      this.h * params.cellSize
    );
  }
}

function setup() {
  createCanvas(400, 400);
  noStroke();
  colorMode(HSB, 360, 100, 100, 100);

  gui = createGuiPanel("params");
  gui.addObject(params);
  gui.setPosition(420, 0);
}

let loadedFromString = false;
let lastCellSize;
let currentVM; 

function draw() {
  if (currentVM == undefined || lastCellSize != params.cellSize) {
    lastCellSize = params.cellSize;
    currentVM = new VM(
      width / params.cellSize / 2,
      height / params.cellSize - 2,
    );
    
    currentVM.code = [];
    for (let i = 0; i < currentVM.w * currentVM.h; i++) {
      currentVM.code.push(0);
    }
  }
  
  if (params.fromString && !loadedFromString) {
    loadedFromString = true;
    noLoop();

    base64AndDecompress(params.fromString).then(bytes => {
      currentVM.reset();
      currentVM.code = Array.from(bytes).slice(0, currentVM.w * currentVM.h);

      while (currentVM.code.length < currentVM.w * currentVM.h) {
        currentVM.code.push(0);
      }

      loop();
    });
    return;
  }
  
  for (let i = 0; i < params.ticksPerFrame; i++) {
    currentVM.step();
    
    if (currentVM.output.length >= currentVM.code.length) {
      let previousCode = currentVM.code;
      let newCode = currentVM.output.slice(0, currentVM.code.length);
      if (newCode == previousCode) {
        currentVM.message = "QUINE FOUND! (see JS console)";
        compressAndBase64(newCode).then(console.log);
        
        currentVM.draw();
        
        noLoop();
        return;
      }
      
      currentVM.message = "output complete";
      currentVM.draw();
      
      currentVM.reset();
      if (params.runOutput) {
        currentVM.code = newCode;
      } else {
        currentVM.code = previousCode;
        currentVM.randomize();
      }
      
      if (params.pauseAfter) {
        noLoop();
        setTimeout(loop, params.pauseTime * 1000);  
      }
      
      return;
    }
    
    if (currentVM.ticksSinceOutput >= params.breakAfter) {
      currentVM.message = "timed out";
      currentVM.draw();
      
      currentVM.randomize();
      
      if (params.pauseAfter) {
        noLoop();
        setTimeout(loop, params.pauseTime * 1000);  
      }
      
      return;
    }    
  }
  
  currentVM.draw();
}

async function compressAndBase64(newCode) {
  const bytes = new Uint8Array(newCode);

  const cs = new CompressionStream("gzip");
  const writer = cs.writable.getWriter();
  writer.write(bytes);
  writer.close();

  const compressed = new Uint8Array(
    await new Response(cs.readable).arrayBuffer()
  );

  return btoa(String.fromCharCode(...compressed));
}

async function base64AndDecompress(b64) {
  const binary = atob(b64);
  const bytes = Uint8Array.from(binary, c => c.charCodeAt(0));

  const ds = new DecompressionStream("gzip");
  const writer = ds.writable.getWriter();
  writer.write(bytes);
  writer.close();

  return new Uint8Array(
    await new Response(ds.readable).arrayBuffer()
  );
}
{{</p5js>}}

{{< taxonomy-list "series" "Genuary 2026" >}}
