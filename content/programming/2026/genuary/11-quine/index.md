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

* `cellSize` - Change how big the program is (default is 10, theoretically with `semi quines` size shouldn't matter)
* `ticksPerFrame` - How fast the simulation will run
* `asFastAsPossible` - Ignore the above and run an entire simulation per frame (it could *technically* go even faster :smile:)
* `pauseAfter` - Pause to see what happened after output is done or a break
* `randomizePercent` - How much of the input to randomly change for the next iteration
* `runOutput` - Run the output as the next program (otherwise, randomize the input)
* `highlightActive` - Highlight the parts of the program that actually ran (brighter colors)
* `allowSemiQuine` - Ignore non-active parts of the program when considering a quine (if you copied the output to the program in these parts, they'd be a quine, so I think it counts)
* `fromString` - If you want to provide your own program (this is base64 of a compressed version of the bytes that make up the code; good luck?)

If you manage to find a quine, I'd *love* to hear what it was. I haven't found one yet. The string (that you can put it `fromString`) in your developer tools / JavaScript console. 

<!--more-->

{{<p5js width="600" height="460">}}
let gui;
let params = {
  cellSize: 10, cellSizeMin: 2, cellSizeMax: 40,
  ticksPerFrame: 10, ticksPerFrameMin: 0, ticksPerFrameMax: 1000,
  asFastAsPossible: false,
  pauseAfter: true,
  randomizePercent: 0.1, randomizePercentMin: 0.01, randomizePercentMax: 1.0, randomizePercentStep: 0.01,
  runOutput: true,
  highlightActive: true,
  allowSemiQuine: true,
  fromString: "",
};

const OPS = [
  // Do nothing
  {name: 'nop', f: (m) => {}},
  
  // Push the next value onto the stack
  {name: 'push', f: (m) => m.push(m.next())},
  
  // Pop a value off the stack without doing anything with it
  {name: 'pop', f: (m) => m.pop()},
  
  // Duplicate the top of the stack
  {name: 'dup', f: (m) => { 
    let v = m.pop();
    m.push(v);
    m.push(v); 
  }},
  
  // Read d off the stack, rotate them c times and push them back
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
  
  // 'push n': read n, then read that many values, pushing them all
  // Can basically be used to put strings/arrays on the stack
  {name: 'pusheen', f: (m) => {
    let n = m.next();
    for (let i = 0; i < n; i++) {
      m.push(m.next());
    }
  }},
  
  // Write the top value on the stack to output (pops)
  {name: 'out', f: (m) => m.out(m.pop())},
  
  // Basic math
  // Everything is unsigned byte arithmetic 
  {name: 'add', f: (m) => m.push(m.pop() + m.pop())},
  {name: 'sub', f: (m) => m.push(m.pop() - m.pop())},
  {name: 'mul', f: (m) => m.push(m.pop() * m.pop())},
  {name: 'div', f: (m) => m.push(m.pop() / (m.pop() || 1))},
  
  // Anything != 0 -> 0, 0 -> 1
  {name: 'not', f: (m) => m.push(m.pop() == 1 ? 0 : 1)},  
  
  // Pop two values, push 1 if the first is greater
  {name: 'greater', f: (m) => m.push(m.pop() > m.pop() ? 1 : 0)},
  
  // Skip the next command if the top of the stack is non-zero
  {name: 'cond', f: (m) => { 
    if (m.pop()) m.pc += 1; 
  }},
  
  // Jump forward by the argument or the top of the stack
  {name: 'jumparg', f: (m) => m.pc += m.next()},
  {name: 'jumpstack', f: (m) => m.pc += m.pop()},
  
  // Jump backwards by the top of the stack
  {name: 'backjumparg', f: (m) => m.pc -= m.next()},
  {name: 'backjumpstack', f: (m) => m.pc -= m.pop()},
  
  // And catch fire
  {name: 'halt', f: (m) => {
    while (m.output.length < m.code.length) {
      m.out(0);
    }
  }}
];

// Represents our virtual machine
class VM {
  // Initialize a machine with no code but a given memory layout/size
  constructor(w, h) {
    this.w = w;
    this.h = h;
    this.reset();
  }
  
  // Reset everything in this VM that could change
  reset() {
    this.message = "";  // Debugging message
    this.code = [];    // The code to run 
    this.output = [];  // Output generated so far
    this.stack = [];   // Current stack
    this.pc = 0;       // Program counter
    
    // How long it's been since last output (used to detect infinitish loops)
    this.ticksSinceOutput = 0;
    
    // Highlight which parts of memory are actually used when running the program
    // You can get a 'free' quine by setting anything in the non active set to the output
    // Since it's not run anyways
    this.activeMemory = new Set();
    
    // Track how many times we've done this...
    evaluations += 1;
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
    this.activeMemory.add(this.pc);
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
          if (params.highlightActive && this.activeMemory.has(i)) {
            fill(hue, 100, 100);
          } else {
            fill(hue, 50, 100);
          }
          
          rect(
            xOffset + cellX * params.cellSize,
            cellY * params.cellSize,
            params.cellSize,
            params.cellSize,
          );
        }
      }
    }
    
    draw(this.code, 0, true);
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
      text(`[${evaluations}] ${this.message}`, 8, this.h * params.cellSize + 16);
    } else {
      text(`[${evaluations}] ${this.stack}`, 8, this.h * params.cellSize + 16);
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
let evaluations = 0;

function draw() {
  // If we don't have a machine, initialize it
  // If we do, but the size changed, re-initialize it
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
  
  // If we have a brand new string and have never loaded it, load it once only
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

  // Iterate the VM
  for (let i = 0; i < params.ticksPerFrame; i++) {
    if (params.asFastAsPossible) {
      i = 0; // lol
    }
    currentVM.step();
    
    // If we have (at least) enough output, halt 
    // Check for a quine (code == output)
    if (currentVM.output.length >= currentVM.code.length) {
      let previousCode = currentVM.code;
      let newCode = currentVM.output.slice(0, currentVM.code.length);
      
      let isQuine = true;
      for (let i = 0; i < previousCode.length; i++) {
        if (params.allowSemiQuine && !currentVM.activeMemory.has(i)) {
          // currentVM.code[i] = newCode[i];
          continue;
        }
        
        if (previousCode[i] != newCode[i]) {
          isQuine = false;
          break;
        }
      }
      
      if (isQuine) {
        currentVM.message = "QUINE FOUND! (see JS console)";
        compressAndBase64(newCode).then(console.log);
        
        currentVM.draw();
        
        noLoop();
        return;
      }
     
      // If we made it this far, we don't have a quine so update to next output
      // And let's do it again
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
        setTimeout(loop, 1000);  
      }
      
      return;
    }
    
    // Possible infinite loop
    // Or at least taking annoyingly long, so kill it
    if (currentVM.ticksSinceOutput >= currentVM.w * currentVM.h) {
      currentVM.message = "timed out";
      currentVM.draw();
      
      currentVM.randomize();
      
      if (params.pauseAfter) {
        noLoop();
        setTimeout(loop, 1000);  
      }
      
      return;
    }    
  }
  
  currentVM.draw();
}

// Used only when outputting the found quine
// base64(gzip(code))

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
  try {
    const binary = atob(b64);
    const bytes = Uint8Array.from(binary, c => c.charCodeAt(0));

    const ds = new DecompressionStream("gzip");
    const writer = ds.writable.getWriter();
    writer.write(bytes);
    writer.close();

    return new Uint8Array(
      await new Response(ds.readable).arrayBuffer()
    );
  } catch(err) {
    return [];
  }
}
{{</p5js>}}

{{< taxonomy-list "series" "Genuary 2026" >}}
