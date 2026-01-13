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
## 11) Quine

Making a genart [[wiki:quine]]()? That's... certainly a thing!

So basically I made a very simple stack based virtual machine. You can check the source code below for what commands it can actually run. It will then run until it outputs enough code to match the input length (or times out). If it happens to output a quine? Woot!

If not, it will randomly mutate and try again. 

* `cellSize` - Change how big the program is (default is 10, theoretically with `semi quines` size shouldn't matter)
* `ticksPerFrame` - How fast the simulation will run
* `asFastAsPossible` - Ignore the above and run an entire simulation per frame (it could *technically* go even faster :smile:)
* `pauseAfter` - Pause to see what happened after output is done or a break
* `stopAfter` - When a single program has run, stop the main loop (mostly useful for debugging)
* `randomizePercent` - How much of the input to randomly change for the next iteration
* `runOutput` - Run the output as the next program (otherwise, randomize the input)
* `highlightActive` - Highlight the parts of the program that actually ran (brighter colors)
* `allowSemiQuine` - Ignore non-active parts of the program when considering a quine (if you copied the output to the program in these parts, they'd be a quine, so I think it counts)
* `allowReadingCode` - Allow (new) commands that allow reading our own source code
* `allowWritingCode` - Allow (new) commands that can modify the code you were originally running
* `debugPrint` - Print each command run/output to console.log for debugging
* `debugSlow` - Drops the framerate to 1 fps for debugging
* `debugStepButton` - Add a 'step' button that runs one step at a time (`noLoop`) for debugging (reload the page)

In addition, you can put in code in the box and 'load' it to run. This will be helpful to verify quines! I have some interesting code [below](#interesting-examples) (including a hand written quine! That uses the self reading instructions). 

If you manage to find a quine organically (or write one), I'd *love* to hear what it was!

<!--more-->

{{<p5js width="600" height="620">}}
let gui;
let params = {
  cellSize: 10, cellSizeMin: 2, cellSizeMax: 40,
  ticksPerFrame: 10, ticksPerFrameMin: 0, ticksPerFrameMax: 1000,
  asFastAsPossible: false,
  pauseAfter: false,
  stopAfter: false,
  randomizePercent: 0.1, randomizePercentMin: 0.01, randomizePercentMax: 1.0, randomizePercentStep: 0.01,
  runOutput: true,
  highlightActive: true,
  allowSemiQuine: true,
  allowReadingCode: true,
  allowWritingCode: false,
  debugPrint: false,
  debugSlow: false,
  debugStepButton: false,
};

const OPS = [
  // Do nothing
  {name: 'nop', f: (m) => {}},
  
  // Push the next value onto the stack
  {name: 'push', f: (m) => m.push(m.next()), nargs: 1},
  
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
  
  // Write the top value on the stack to output (pops)
  {name: 'out', f: (m) => {
    let v = m.pop();
    if (params.debugPrint) {
      if (v < OPS.length) {
        let name = OPS[v].name;
        console.log(`OUTPUT: ${v} (${name})`);
      } else {
        console.log(`OUTPUT: ${v}`);
      }
    }
    m.out(v);
  }},
  
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
  {name: 'skip', f: (m) => { 
    if (m.pop()) m.pc += 1; 
  }},
  
  // Jump forward/backward based on next arg
  {name: 'jump', f: (m) => m.pc += m.pop() - 1},
  {name: 'jumpback', f: (m) => m.pc -= m.pop() + 1},
  
  // And catch fire
  {name: 'halt', f: (m) => {
    while (m.output.length < m.code.length) {
      m.out(0);
    }
  }},
  
  // Read data about the current state of the machine
  {name: 'peek', f: (m) => m.push(m.code[m.pc + m.pop() - 1]), requireAllowRead: true},
  {name: 'peekback', f: (m) => m.push(m.code[m.pc - m.pop() + 1]), requireAllowRead: true},
  {name: 'pc', f: (m) => m.push(m.pc), requireAllowRead: true},
  
  // Allow self modifying code
  {name: 'poke', f: (m) => m.code[m.pc + m.pop() - 1] = m.pop(), requireAllowWrite: true},
  {name: 'pokeback', f: (m) => m.code[m.pc - m.pop() + 1] = m.pop(), requireAllowWrite: true},
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
    this.output.push(v);
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
    
    let debug_pc = this.pc;
    
    let v = this.next();
    let op = OPS[v];
    
    let debug_name = op == undefined ? `[${v}]` : op.name;
    if (params.debugPrint && debug_name != 'nop') {
      if (op.nargs) {
        let args = [];
        for (let i = 0; i < op.nargs; i++) {
          args.push(this.code[this.pc + i]);
        }
        console.log(`${debug_pc}: ${debug_name} ${args}`);
      } else {
        console.log(`${debug_pc}: ${debug_name}`);
      }
    }
    
    let canRun = true;
    if (op == undefined) {
      // nop invalid commands (can happen if we poke funny things into memory)
    } else if (!params.allowReadingCode && op.requireAllowRead) {
      // reading your own code could be considered quine-cheating :)
    } else if (!params.allowWritingCode && op.requireAllowWrite) {
      // writing self modifying code is generally a bad idea
      // but oh, it can do some wacky things
    } else {
      // hey, those all passed! we can actually do something!
      op.f(this);
    }
    
    // Force PC back into bounds
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
          //let hue = 360 * (v % OPS.length) / OPS.length;
          let hue = 360 * v / 256;

          noStroke();

          if (!params.highlightActive || this.activeMemory.has(i)) {
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
  
  inputBox = createElement('textarea');
  inputBox.elt.style.width = '380px';
  inputBox.elt.style.height = '200px';
  
  createElement('br')
  let loadSource = createButton("Load source");
  loadSource.mousePressed(() => {
    params.stopAfter = true;
    noLoop();

    currentVM.reset();
    while (currentVM.code.length < currentVM.w * currentVM.h) {
      currentVM.code.push(0);
    }
    
    let address = 0;
    for (let line of inputBox.elt.value.split("\n")) {
      if (line.trim() == "" || line[0] == '#') {
        continue;
      }
      
      // If we have an address, update it
      let hasAddress = line.split(" ")[0].endsWith(':');
      if (hasAddress) {
        address = parseInt(line.slice(0, 4));
      }
      
      for (let arg of line.split(" ").slice(hasAddress ? 1 : 0)) {
        if (arg == "" || arg[0] == '#' || arg[0] == ';') {
          break;
        }
        
        let asNumber = parseInt(arg);
        if (isNaN(asNumber)) {
          // Opcode (I hope)
          let found = false;
          for (let i = 0; i < OPS.length; i++) {
            if (OPS[i].name == arg) {
              currentVM.code[address] = i;
              found = true;
              break;
            }
          }
          
          if (!found) {
            console.warn("Undefine op: " + arg);
          }
        } else {
          currentVM.code[address] = asNumber;
        }
        
        address += 1;
      }
    }
    
    if (params.debugPrint) {
      console.log("Loaded source:", currentVM.code);
    }
    
    currentVM.draw();
  
    if (!params.debugStepButton) {
      loop();
    }
  });
  
  if (params.debugStepButton) {
    let step = createButton("Step");
    step.mousePressed(() => {
      noLoop();
      currentVM.step();
      currentVM.draw();
    });
    noLoop();
  }

  createElement('br')
}

let inputBox;
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
        currentVM.message = "QUINE FOUND!";
        
        let source = '';
        for (let i = 0; i < previousCode.length; i++) {
          let op = OPS[previousCode[i]];
          if (op == undefined || op.name == 'nop') {
            continue;
          }
      
          let index = i.toString().padStart(4, '0');
          source += `${index}: ${op.name}`;
          
          if (op.nargs) {
            for (let j = 0; j < op.nargs; j++) {
              source += ` ${previousCode[++i]}`;
            }
          }
          source += '\n';
        }
        inputBox.elt.value = source;
        
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
      
      if (params.pauseAfter || params.stopAfter) {
        noLoop();
        if (!params.stopAfter) {
          setTimeout(loop, 1000);  
        }
      }
      
      return;
    }
    
    // Possible infinite loop
    // Or at least taking annoyingly long, so kill it
    if (currentVM.ticksSinceOutput >= currentVM.w * currentVM.h) {
      currentVM.message = "timed out";
      currentVM.draw();
      
      currentVM.randomize();
      
      if (params.pauseAfter || params.stopAfter) {
        noLoop();
        if (!params.stopAfter) {
          setTimeout(loop, 1000);  
        }
      }
      
      return;
    }    
  }
  
  currentVM.draw();
  if (params.debugSlow) {
    frameRate(1);
  }
}
{{</p5js>}}

{{< taxonomy-list "series" "Genuary 2026" >}}

## Language specification

| Name       | Stack Effect      | Description                                                            |
| ---------- | ----------------- | ---------------------------------------------------------------------- |
| `nop`      | —                 | No operation                                                           |
| `push v`   | → `v`             | Push next byte in code                                                 |
| `pop`      | `a` →             | Discard top of stack                                                   |
| `dup`      | `a` → `a a`       | Duplicate top value                                                    |
| `roll`     | `c d …` → rotated | Pop `c` (count) and `d` (depth), rotate top `d` stack values `c` times |
| `out`      | `a` →             | Emit byte to output                                                    |
| `add`      | `a b` → `a+b`     | Addition                                                               |
| `sub`      | `a b` → `a-b`     | Subtraction                                                            |
| `mul`      | `a b` → `a*b`     | Multiplication                                                         |
| `div`      | `a b` → `a/b`     | Division (divide by zero yields divisor = 1)                           |
| `not`      | `a` → `!a`        | `0 → 1`, anything else → `0`                                           |
| `greater`  | `a b` → `(a > b)` | Push `1` if true, else `0`                                             |
| `skip`     | `a` →             | Skip next instruction if `a ≠ 0`                                       |
| `jump`     | `n` →             | `PC += n` (from the addr of the `jump`)                                |
| `jumpback` | `n` →             | `PC -= n` (ditto)                                                      |
| `halt`     | —                 | Fill output with zeroes until output length == code length             |
| `peek`     | `n` → byte        | Read `code[PC + n]`                                                    |
| `peekback` | `n` → byte        | Read `code[PC - n]`                                                    |
| `pc`       | → byte            | Push current PC                                                        |
| `poke`     | `v n` →           | Write `v` to `code[PC + n]`                                            |
| `pokeback` | `v n` →           | Write `v` to `code[PC - n]`                                            |

Assembly can be written with an opcodes and (in the case of `push`) a literal number after it. 

Lines starting with `\d+:` will be treated as labels, so any code after that will be written starting at that location in memory. You definitely can use this to overwrite previous code. 

Anything after `;` or `#` is a comment. 

## Interesting examples

### Writing a rainbow

Originally, I required writing out each instruction address by hand. So here is initial code to just output an ever increasing value:

```text
0000: dup
0001: out
0002: push 1
0004: add
0005: push 7
0007: jumpback
```

But eventually, I realized that was silly. :smile: So this is the same thing:

```text
dup
out
push 1
add
push 7
jumpback
```

### The protoquine

With that, I could read and output my own code. This is before I stopped manually writing all addresses:

```text
0000: push 0   ; index into code
0002: dup
0003: peek     ; code at 3 + index
0004: out
0005: push 1
0007: add      ; increment index
0008: dup
0009: push 14  ; maximum offset
0011: greater
0012: skip     ; if maximum > index don't
0013: halt
0014: push 14
0016: jumpback ; go back to 3
```

It's *so* close! It's just missing the first three bytes. 

### An actual quine

Basically, with `peek`, we can read the code from that peek through to the end of the code. We could have two loops (with a peekback first), but instead, I opted to:

* start by jumping to the end of the code (where peek can see)
* writing out the instructions to do that jump + the `dup` I need
* jumping back to the main loop to write it all out

```text
; jump to prefix output
push 38
jump

; index into code
dup

; read the code this peek + the index
peek
out

; increment index
push 1
add

; text if index > 100 bytes
; if so, halt
dup
push 100
greater
skip
halt

; jump back to read next byte
push 14
jumpback

; manually write out any bytes through peek
0040:
push 1 out  ; push
push 38 out ; 38
push 13 out ; jump
push 3 out  ; dup

; jump back to the main loop (after the jump)
0080:
push 79  
jumpback
```

This was fun to get working!

When it runs, it will automatically output the 'un-assembled' version:

```text
0000: push 38
0002: jump
0003: dup
0004: peek
0005: out
0006: push 1
0008: add
0009: dup
0010: push 100
0012: greater
0013: skip
0014: halt
0015: push 14
0017: jumpback
0040: push 1
0042: out
0043: push 38
0045: out
0046: push 13
0048: out
0049: push 3
0051: out
0080: push 79
0082: jumpback
```

(Which is itself a quine. Duh :p)

## ASCII art?

```text
0000: 0 0 0 0 0 4 4 4 4 4 4 4 0 0 0 0 0
0020: 0 0 0 4 4 4 4 4 4 4 4 4 4 4 0 0 0
0040: 0 0 4 4 4 4 0 0 0 0 0 0 4 4 4 4 0
0060: 0 4 4 4 4 0 0 0 0 0 0 0 0 4 4 4 4
0080: 0 4 4 4 0 0 4 4 0 4 4 0 0 4 4 4 4
0100: 4 4 4 0 0 4 4 4 0 4 4 4 0 0 4 4 4
0120: 4 4 4 0 0 4 4 4 0 4 4 4 0 0 4 4 4
0140: 4 4 4 0 0 0 0 0 0 0 0 0 0 0 4 4 4
0160: 4 4 4 0 0 0 4 4 4 4 4 0 0 0 4 4 4
0180: 4 4 4 0 0 0 0 4 4 4 0 0 0 0 4 4 4
0200: 0 4 4 4 0 0 0 0 0 0 0 0 0 4 4 4 4
0220: 0 4 4 4 4 0 0 0 0 0 0 0 0 4 4 4 4
0240: 0 0 4 4 4 4 0 0 0 0 0 0 4 4 4 4 0
0260: 0 0 0 4 4 4 4 4 4 4 4 4 4 4 0 0 0
0280: 0 0 0 0 0 4 4 4 4 4 4 4 0 0 0 0 0
```

You can't *quite* quine that, since you can't `peek` more than 256 characters ahead. 

```text
; jump to prefix output
push 38
jump

; index into code
dup

; read the code this peek + the index
peek
out

; increment index
push 1
add

; jump back to read next byte
push 8
jumpback

; manually write out any bytes through peek
0040:
push 1 out  ; push
push 38 out ; 38
push 13 out ; jump
push 3 out  ; dup

; jump back to the main loop (after the jump)
0080:
push 79  
jumpback

;D
0100: 0 0 0 0 0 4 4 4 4 4 4 4 0 0 0 0 0
0120: 0 0 0 4 4 4 4 4 4 4 4 4 4 4 0 0 0
0140: 0 0 4 4 4 4 0 0 0 0 0 0 4 4 4 4 0
0160: 0 4 4 4 4 0 0 0 0 0 0 0 0 4 4 4 4
0180: 0 4 4 4 0 0 4 4 0 4 4 0 0 4 4 4 4
0200: 4 4 4 0 0 4 4 4 0 4 4 4 0 0 4 4 4
0220: 4 4 4 0 0 4 4 4 0 4 4 4 0 0 4 4 4
0240: 4 4 4 0 0 0 0 0 0 0 0 0 0 0 4 4 4
0260: 4 4 4 0 0 0 4 4 4 4 4 0 0 0 4 4 4
0280: 4 4 4 0 0 0 0 4 4 4 0 0 0 0 4 4 4
0300: 0 4 4 4 0 0 0 0 0 0 0 0 0 4 4 4 4
0320: 0 4 4 4 4 0 0 0 0 0 0 0 0 4 4 4 4
0340: 0 0 4 4 4 4 0 0 0 0 0 0 4 4 4 4 0
0360: 0 0 0 4 4 4 4 4 4 4 4 4 4 4 0 0 0
0380: 0 0 0 0 0 4 4 4 4 4 4 4 0 0 0 0 0
```

But it's fun looking :smile:

Also, it does as a 'semi quine' but not an actual quine, since it does output exactly the code that *was actually run*, what it writes to the rest of the image doesn't matter. Try it!