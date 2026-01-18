---
title: "Genuary 2026.17: Wallpaper Groups"
date: "2026-01-17"
programming/languages:
- JavaScript
programming/topics:
- Generative Art
- Procedural Content
- p5js
series:
- Genuary 2026
cover: gen26.17.png
---
> Wallpaper group. There are only 17 ways to cover a plane with a repeating pattern, choose your favourite on this page: [Wallpaper group](https://en.wikipedia.org/wiki/Wallpaper_group)
> 
> This is a great article about [Classifying Symmetries](https://tiled.art/en/symmetryClassification/) that says there are actually 35 tiling patterns!
> 
> [List of planar symmetry groups](https://en.wikipedia.org/wiki/List_of_planar_symmetry_groups) is another Wikipedia page with a good summary of the wallpaper group.

I spent waaaaay too long on this one. 

- `group` is the 17 groups mentioned
- `subGroup` is horizontal or vertical for some of the above
- `cellType` is the shape of each cell
- `cellStyle` is what to fill them with 
- `debugDrawOne` shows what one tile looks like
- `debugDisplay` prints what random values were selected
- `pauseBuffer` is useful for pausing the generation (although if any of the others are random they will keep changing)

Not all of the groups and cell types are perfectly compatible. In fact, probably half or more aren't. But they still produce something, and I think that's pretty cool!

<!--more-->

{{<p5js width="600" height="440">}}
let gui;
let params = {
  cellSize: 100,
  frameRate: 1,
  showBorders: false,
  group: [
    "random",
    "p1: translation",
    "p2: 180° rotation",
    "pm: reflection",
    "pg: glide reflection",
    "cm: diagonal reflection",
    "pmm: four corners",
    "pmg: alt corners",
    "pgg: glide + 180°",
    "cmm: checkerboard 180°",
    "p3: 3-fold rotation",
    "p3m1: 3-fold + 3 reflections",
    "p31m: 3-fold + mirror pairs",
    "p4: 4-fold rotation",
    "p4m: 4-fold + reflection",
    "p4g: 4-fold + glide",
    "p6: 6-fold rotation",
    "p6m: 6-fold + 6 reflections",
    // "p6g:"
  ],
  subGroup: ["random", "horizontal", "vertical"],
  cellType: [
    "random",
    "square",
    "rect",
    "diamond",
    "triangle",
    "flathex",
    "pointyhex"
  ],
  cellStyle: [
    "random",
    "solid",
    "70s",
    "stripes",
    "wavey",
    "planets",
    "noise",
    "grid",
    "lineCurve",
    "dots",
    "flower",
  ],
  debugDrawOne: false,
  debugDisplayInfo: false,
  pauseBuffer: false,
};

let paramsCopyBecauseGUI = JSON.parse(JSON.stringify(params));
let lastStep = false;

const ROOT3 = Math.sqrt(3);
let buffer;

function setup() {
  createCanvas(400, 400);
  colorMode(HSB, 360, 100, 100, 100);

  gui = createGuiPanel("params");
  gui.addObject(params);
  gui.setPosition(420, 0);
}

function draw() {
  frameRate(params.frameRate);
  blendMode(BLEND);
  background("white");
  blendMode(MULTIPLY);

  let currentGroup = params.group;
  let currentSubGroup = params.subGroup;
  let currentCellType = params.cellType;
  let currentCellStyle = params.cellStyle;

  while (currentGroup == "random") {
    currentGroup = random(paramsCopyBecauseGUI.group);
  }
  while (currentSubGroup == "random") {
    currentSubGroup = random(paramsCopyBecauseGUI.subGroup);
  }
  while (currentCellType == "random") {
    currentCellType = random(paramsCopyBecauseGUI.cellType);
  }
  while (currentCellStyle == "random") {
    currentCellStyle = random(paramsCopyBecauseGUI.cellStyle);
  }
  
  
  if (!buffer || buffer.width !== params.cellSize || buffer.height !== params.cellSize) {
    buffer = createGraphics(params.cellSize, params.cellSize);
    buffer.colorMode(HSB, 360, 100, 100, 100);
  }

  if (!params.pauseBuffer) {
    buffer.background("white");

    // Draw pattern into buffer

    // Draw a random pattern into the buffer 
    // Then clip it based on the selected cell type

    buffer.push();
    buffer.translate(params.cellSize / 2, params.cellSize / 2);

    // Build vertices array based on cell type
    let vertexes = [];

    if (currentCellType === "square") {
      let s = params.cellSize / 2;
      vertexes = [
        [-s, -s],
        [s, -s],
        [s, s],
        [-s, s]
      ];
    } else if (currentCellType === "rect") {
      let w = params.cellSize / 2;
      let h = params.cellSize / 4;
      vertexes = [
        [-w, -h],
        [w, -h],
        [w, h],
        [-w, h]
      ];
    } else if (currentCellType === "diamond") {
      vertexes = [
        [0, -params.cellSize / 2],
        [params.cellSize / 2, 0],
        [0, params.cellSize / 2],
        [-params.cellSize / 2, 0]
      ];
    } else if (currentCellType === "triangle") {
      vertexes = [
        [0, params.cellSize / 2],
        [params.cellSize / 2, -params.cellSize / 2],
        [-params.cellSize / 2, -params.cellSize / 2]
      ];
    } else if (currentCellType === "flathex") {
      // Flat-topped hexagon (flat sides on top/bottom)
      let r = params.cellSize / 2;
      vertexes = [
        [r, 0],
        [r / 2, r * ROOT3 / 2],
        [-r / 2, r * ROOT3 / 2],
        [-r, 0],
        [-r / 2, -r * ROOT3 / 2],
        [r / 2, -r * ROOT3 / 2]
      ];

    } else if (currentCellType === "pointyhex") {
      // Pointy-topped hexagon (pointy top/bottom)
      let r = params.cellSize / 2;
      vertexes = [
        [r * ROOT3 / 2, r / 2],
        [0, r],
        [-r * ROOT3 / 2, r / 2],
        [-r * ROOT3 / 2, -r / 2],
        [0, -r],
        [r * ROOT3 / 2, -r / 2]
      ];
    }

    // Set up clipping region using vertexes
    buffer.beginClip();
    buffer.beginShape();
    for (let v of vertexes) {
      buffer.vertex(v[0], v[1]);
    }
    buffer.endShape(CLOSE);
    buffer.endClip();

    // Draw the actual pattern inside the clipping region
    if (currentCellStyle === "solid") {
      // Solid colors (mostly for testing)
      let hue = random(360);
      let saturation = random(50, 100);
      let brightness = random(50, 100);
      buffer.fill(hue, saturation, brightness, 100);
      buffer.noStroke();
      buffer.rectMode(CENTER);
      buffer.rect(0, 0, params.cellSize, params.cellSize);
    } else if (currentCellStyle === "70s") {
      // A bunch of random overlapping shapes
      let numShapes = floor(random(5, 15));
      for (let i = 0; i < numShapes; i++) {
        let hue = random(360);
        let saturation = random(50, 100);
        let brightness = random(50, 100);
        let alpha = random(50, 100);
        buffer.fill(hue, saturation, brightness, alpha);
        buffer.noStroke();

        let shapeType = floor(random(3));
        let size = random(10, params.cellSize / 2);
        let angle = random(TWO_PI);
        let x = random(-params.cellSize / 2, params.cellSize / 2);
        let y = random(-params.cellSize / 2, params.cellSize / 2);

        buffer.push();
        buffer.translate(x, y);
        buffer.rotate(angle);

        if (shapeType === 0) {
          buffer.ellipse(0, 0, size, size);
        } else if (shapeType === 1) {
          buffer.rectMode(CENTER);
          buffer.rect(0, 0, size, size);
        } else {
          buffer.triangle(-size / 2, size / 2, size / 2, size / 2, 0, -size / 2);
        }

        buffer.pop();
      }
    } else if (currentCellStyle === "stripes") {
      // Alternating colored stripes at various angles
      let numStripes = floor(random(3, 8));
      let angle = random([0, PI / 6, PI / 4, PI / 3, PI / 2]);
      let stripeWidth = params.cellSize / numStripes;

      buffer.push();
      buffer.translate(0, 0);
      buffer.rotate(angle);

      for (let i = -4; i < numStripes + 4; i++) {
        let hue = random(360);
        let saturation = random(40, 100);
        let brightness = random(40, 100);
        buffer.fill(hue, saturation, brightness, 100);
        buffer.noStroke();
        buffer.rectMode(CORNER);


        buffer.rect(i * stripeWidth - params.cellSize * 2, -params.cellSize * 2, stripeWidth, params.cellSize * 6);
      }

      buffer.pop();
    } else if (currentCellStyle === "wavey") {
      // Wavy undulating lines
      let numWaves = floor(random(2, 6));
      let amplitude = params.cellSize / floor(random(2, 6));
      let frequency = random(0.5, 2);

      buffer.noFill();
      buffer.stroke(random(360), random(50, 100), random(50, 100), 80);
      buffer.strokeWeight(random(2, 4));

      for (let wave = 0; wave < numWaves; wave++) {
        buffer.beginShape();
        let offset = (wave / numWaves) * params.cellSize * 2 - params.cellSize;

        for (let x = -params.cellSize; x <= params.cellSize; x += 2) {
          let y = offset + amplitude * sin(x * frequency * PI / params.cellSize);
          buffer.curveVertex(x, y);
        }
        buffer.endShape();
      }
    } else if (currentCellStyle === "planets") {
      // Perlin noise terrain with two colors and optional moon/ring
      let scale = random(15, 40);
      let offsetX = random(1000);
      let offsetY = random(1000);
      let planetRadius = params.cellSize * 0.25;

      // Choose three colors for terrain
      let hue1 = random(360);
      let hue2 = (hue1 + random(60, 180)) % 360;
      let hue3 = (hue1 + random(120, 240)) % 360;

      // Clip to a circle
      buffer.beginClip();
      buffer.ellipse(0, 0, planetRadius * 2, planetRadius * 2);
      buffer.endClip();

      // Draw the planet with noise-based terrain
      for (let x = -params.cellSize; x <= params.cellSize; x += 2) {
        for (let y = -params.cellSize; y <= params.cellSize; y += 2) {
          let noiseVal1 = noise(x / scale + offsetX, y / scale + offsetY);
          let noiseVal2 = noise(x / (scale * 0.5) + offsetX + 500, y / (scale * 0.5) + offsetY + 500);

          // Combine the two noise values
          let combined = noiseVal1 * 0.7 + noiseVal2 * 0.3;

          let hue, sat, bright;

          if (combined < 0.33) {
            // First color
            hue = hue1;
            sat = 70 + combined * 60;
            bright = 40 + combined * 60;
          } else if (combined < 0.67) {
            // Second color
            hue = hue2;
            sat = 70 + (combined - 0.33) * 60;
            bright = 50 + (combined - 0.33) * 50;
          } else {
            // Third color
            hue = hue3;
            sat = 70 + (combined - 0.67) * 40;
            bright = 50 + (combined - 0.67) * 50;
          }

          buffer.fill(hue, sat, bright, 100);
          buffer.noStroke();
          buffer.rect(x, y, 3, 3);
        }
      }
    } else if (currentCellStyle === "noise") {
      // Multi-layered Perlin noise filling entire cell
      let scale = random(15, 40);
      let offsetX = random(1000);
      let offsetY = random(1000);

      // Choose three colors for terrain
      let hue1 = random(360);
      let hue2 = (hue1 + random(60, 180)) % 360;
      let hue3 = (hue1 + random(120, 240)) % 360;

      // Draw noise pattern across the entire cell
      for (let x = -params.cellSize; x <= params.cellSize; x += 2) {
        for (let y = -params.cellSize; y <= params.cellSize; y += 2) {
          let noiseVal1 = noise(x / scale + offsetX, y / scale + offsetY);
          let noiseVal2 = noise(x / (scale * 0.5) + offsetX + 500, y / (scale * 0.5) + offsetY + 500);

          // Combine the two noise values
          let combined = noiseVal1 * 0.7 + noiseVal2 * 0.3;

          let hue, sat, bright;

          if (combined < 0.33) {
            // First color
            hue = hue1;
            sat = 70 + combined * 60;
            bright = 40 + combined * 60;
          } else if (combined < 0.67) {
            // Second color
            hue = hue2;
            sat = 70 + (combined - 0.33) * 60;
            bright = 50 + (combined - 0.33) * 50;
          } else {
            // Third color
            hue = hue3;
            sat = 70 + (combined - 0.67) * 40;
            bright = 50 + (combined - 0.67) * 50;
          }

          buffer.fill(hue, sat, bright, 100);
          buffer.noStroke();
          buffer.rect(x, y, 3, 3);
        }
      }
    } else if (currentCellStyle === "grid") {
      // Grid pattern
      let spacing = params.cellSize / floor(random(4, 10));

      let bghue = random(360);
      buffer.fill(bghue, 20, 100, 100);
      buffer.noStroke();
      buffer.rectMode(CENTER);
      buffer.rect(0, 0, params.cellSize, params.cellSize);

      let linehue = (bghue + 180) % 360;
      buffer.stroke(linehue, 100, 100, 50);
      buffer.strokeWeight(2);

      for (let x = -params.cellSize / 2; x <= params.cellSize / 2; x += spacing) {
        buffer.line(x, -params.cellSize / 2, x, params.cellSize / 2);
      }
      for (let y = -params.cellSize / 2; y <= params.cellSize / 2; y += spacing) {
        buffer.line(-params.cellSize / 2, y, params.cellSize / 2, y);
      }
    } else if (currentCellStyle === "lineCurve") {
      let divisions = floor(random(5, 15));
      let spacing = params.cellSize / divisions;

      buffer.stroke(0, 0, 0, 30);
      buffer.strokeWeight(1);

      for (let i = 0; i <= divisions; i++) {
        let t = i / (divisions - 1);
        let x = lerp(- params.cellSize / 2, params.cellSize / 2, t);
        let y = lerp(- params.cellSize / 2, params.cellSize / 2, t);
        buffer.line(
          -params.cellSize / 2,
          -params.cellSize / 2 + i * spacing,
          -params.cellSize / 2 + i * spacing,
          params.cellSize / 2
        );
      }
    } else if (currentCellStyle === "dots") {
      let spacing = params.cellSize / floor(random(5, 15));
      let dotSize = spacing / 4;
      buffer.noStroke();
      for (let x = -params.cellSize / 2; x <= params.cellSize / 2; x += spacing) {
        for (let y = -params.cellSize / 2; y <= params.cellSize / 2; y += spacing) {

          let hue = random(360);
          buffer.fill(hue, 100, 100, 100);

          buffer.ellipse(x, y, dotSize, dotSize);
        }
      }
    } else if (currentCellStyle === "flower") {
      let numPetals = floor(random(5, 12));
      let petalLength = params.cellSize / 2;
      let petalWidth = petalLength / 3;

      for (let i = 0; i < numPetals; i++) {
        let angle = (TWO_PI / numPetals) * i;
        let hue = random(360);
        buffer.fill(hue, 100, 100, 100);
        buffer.noStroke();

        buffer.push();
        buffer.rotate(angle);
        buffer.ellipse(petalLength / 2, 0, petalLength, petalWidth);
        buffer.pop();
      }

      // Draw center
      buffer.fill(60, 100, 100, 100);
      buffer.ellipse(0, 0, petalWidth, petalWidth);
    }

    // Optionally draw borders using the same vertexes
    if (params.showBorders) {
      buffer.stroke(0);
      buffer.noFill();
      buffer.strokeWeight(2);
      buffer.beginShape();
      for (let v of vertexes) {
        buffer.vertex(v[0], v[1]);
      }
      buffer.endShape(CLOSE);
    }

    buffer.pop();

    // /end draw pattern into buffer
  }
  
  if (params.debugDrawOne) {
    imageMode(CENTER);
    image(buffer, width / 2, height / 2);
    
    stroke("red");
    strokeWeight(1);
    noFill();
    
    rectMode(CENTER)
    rect(width / 2, height / 2, params.cellSize, params.cellSize);
    
  } else {
    imageMode(CENTER);
    for (let cellY = 0; ; cellY++) {
      let oddRow = cellY % 2;
      let y = cellY * params.cellSize - params.cellSize;

      if (currentCellType === "rect") {
        y = y / 2;
      } else if (currentCellType === "diamond") {
        y = y / 2;
        if (oddRow) {
          y = y - params.cellSize / 2;
        }
      } else if (currentCellType === "triangle") {
        y = y / 2;
      } else if (currentCellType === "flathex") {
        y = cellY * (params.cellSize * ROOT3 / 4);
      } else if (currentCellType === "pointyhex") {
        y = cellY * (params.cellSize * 3 / 4);
      }

      if (y >= height + 2 * params.cellSize) {
        break;
      }

      for (let cellX = 0; ; cellX++) {
        let x = cellX * params.cellSize - params.cellSize;

        if (currentCellType === "diamond") {
          if (oddRow) {
            y = y - (params.cellSize / 2);
            x = x + (params.cellSize / 2);
          }
        } else if (currentCellType === "flathex") {
          x = cellX * params.cellSize * 1.5;
          if (oddRow) {
            x += params.cellSize * 0.75;
          }
        } else if (currentCellType === "pointyhex") {
          x = cellX * (params.cellSize * sqrt(3) / 2);
          if (oddRow) {
            x = x + (params.cellSize * sqrt(3) / 4);
          }
        }
        
        push();
        translate(x, y);
        if (currentCellType === "triangle") {
          if (oddRow) {
            rotate(PI);
            translate(params.cellSize / 2, params.cellSize / 2);
          }
        } 
        
        // Group details
        
        if (currentGroup.startsWith("p2:")) {
          if (cellY % 2 == 1) {
            rotate(PI);
          }
        }
        
        // ----- -----
        
        if (currentGroup.startsWith("pm:")) {
          if (currentSubGroup == "horizontal") {
            if (cellY % 2 == 1) {
              translate(params.cellSize, 0)
              scale(1, -1);
            }  
          } else if (currentSubGroup == "vertical") {
            if (cellX % 2 == 1) {
              translate(0, params.cellSize)
              scale(-1, 1);
            }
          }
        }
        
        // ----- -----

        if (currentGroup.startsWith("pg:")) {
          if (currentSubGroup == "vertical") {
            if (cellY % 2 == 1) {
              translate(params.cellSize, 0)
              scale(1, -1);
            }  
          } else if (currentSubGroup == "horizontal") {
            if (cellX % 2 == 1) {
              translate(0, params.cellSize)
              scale(-1, 1);
            }
          }
        }
        
        // ----- -----
        
        if (currentGroup.startsWith("cm:")) {
          if (cellY % 2 == 1) {
            scale(1, -1);
          }  
          
          if (cellX % 2 == 1) {
            scale(-1, 1);
          }
        }
        
        // ----- -----
        
        if (currentGroup.startsWith("pmm:")) {
          if (cellY % 2 == 1) {
            if (cellX % 2 == 1) {
              rotate(PI);
            } else {
              rotate(PI / 2);
            }
          } else if (cellX % 2 == 1) {
            rotate(-PI / 2);
          } 
        }
        
        // ----- -----

        if (currentGroup.startsWith("pmg:")) {
          if (currentSubGroup == "horizontal") {
            if (cellX % 2 == 1) {
              if (cellY % 2 == 1) {
                rotate(PI / 2);
              } else {
                rotate(PI);
              }
            } else if (cellY % 2 == 1) {
              rotate(-PI / 2);
            }
          } else {
            if (cellY % 2 == 1) {
              if (cellX % 2 == 1) {
                rotate(PI / 2);
              } else {
                rotate(PI);
              }
            } else if (cellX % 2 == 1) {
              rotate(-PI / 2);
            } 
          }

        }
        
        // ----- -----
        
        if (currentGroup.startsWith("pgg:")) {
          if (cellX % 2 == 1 && cellY % 2 == 0) {
            rotate(PI);
          } else if (cellX % 2 == 0 && cellY % 2 == 1) {
            rotate(PI);
          }
        }
        
        // ----- -----
        
        if (currentGroup.startsWith("cmm:")) {
          if ((cellX + cellY) % 2 == 1) {
            rotate(PI);
          }
        }
        
        // ----- -----
        
        if (currentGroup.startsWith("p4:") && !currentGroup.startsWith("p4m:") && !currentGroup.startsWith("p4g:")) {
          let quadrant = (cellX % 2) + (cellY % 2) * 2;
          if (quadrant === 1) {
            rotate(PI / 2);
          } else if (quadrant === 2) {
            rotate(-PI / 2);
          } else if (quadrant === 3) {
            rotate(PI);
          }
        }
        
        // ----- -----
        
        if (currentGroup.startsWith("p4m:")) {
          if (cellX % 2 == 1) {
            translate(0, params.cellSize);
            scale(-1, 1);
          }
          if (cellY % 2 == 1) {
            translate(params.cellSize, 0);
            scale(1, -1);
          }
        }
        
        // ----- -----
        
        if (currentGroup.startsWith("p4g:")) {
          // p4g: 4-fold rotation + glide reflections at 45°
          let pattern = (cellX % 2) + (cellY % 2) * 2;
          if (pattern === 1 || pattern === 2) {
            rotate(PI / 2);
          }
          if (cellX % 2 == 1) {
            translate(0, params.cellSize);
            scale(-1, 1);
          }
        }
        
        // ----- -----
        
        if (currentGroup.startsWith("p3:") && !currentGroup.startsWith("p3m1:") && !currentGroup.startsWith("p31m:")) {
          let pattern = (cellX + cellY * 2) % 3;
          if (pattern === 1) {
            rotate(TWO_PI / 3);
          } else if (pattern === 2) {
            rotate(-TWO_PI / 3);
          }
        }
        
        // ----- -----
        
        if (currentGroup.startsWith("p3m1:")) {
          let pattern = (cellX + cellY) % 3;
          if (pattern === 1) {
            rotate(TWO_PI / 3);
          } else if (pattern === 2) {
            rotate(-TWO_PI / 3);
          }
          if ((cellX + cellY) % 2 == 1) {
            scale(-1, 1);
          }
        }
        
        // ----- -----
        
        if (currentGroup.startsWith("p31m:")) {
          let pattern = (cellX * 2 + cellY) % 3;
          if (pattern === 1) {
            rotate(TWO_PI / 3);
          } else if (pattern === 2) {
            rotate(-TWO_PI / 3);
          }
          if (cellY % 2 == 1) {
            scale(1, -1);
          }
        }
        
        // ----- -----
        
        if (currentGroup.startsWith("p6:") && !currentGroup.startsWith("p6m:") && !currentGroup.startsWith("p6g:")) {
          let pattern = (cellX + cellY * 2) % 6;
          if (pattern === 1) {
            rotate(TWO_PI / 6);
          } else if (pattern === 2) {
            rotate(TWO_PI * 2 / 6);
          } else if (pattern === 3) {
            rotate(TWO_PI * 3 / 6);
          } else if (pattern === 4) {
            rotate(TWO_PI * 4 / 6);
          } else if (pattern === 5) {
            rotate(TWO_PI * 5 / 6);
          }
        }
        
        // ----- -----
        
        if (currentGroup.startsWith("p6m:")) {
          let pattern = (cellX + cellY) % 6;
          if (pattern === 1) {
            rotate(TWO_PI / 6);
          } else if (pattern === 2) {
            rotate(TWO_PI * 2 / 6);
          } else if (pattern === 3) {
            rotate(TWO_PI * 3 / 6);
          } else if (pattern === 4) {
            rotate(TWO_PI * 4 / 6);
          } else if (pattern === 5) {
            rotate(TWO_PI * 5 / 6);
          }
          if ((cellX + cellY) % 2 == 1) {
            scale(-1, 1);
          }
        }
        
        // ----- -----
        
        image(buffer, 0, 0);
        pop();

        if (currentCellType === "diamond") {
          if (oddRow) {
            y = y + (params.cellSize / 2);
          }
        } 
        
        if (x >= width + 2 * params.cellSize) {
          break;
        }
      }
    }
  }

  if (params.debugDisplayInfo) {
    fill(0);
    textAlign(LEFT, TOP);
    textSize(12);
    let infoText = `Group: ${currentGroup}\nSub-group: ${currentSubGroup}\nCell type: ${currentCellType}\nCell style: ${currentCellStyle}`;
    text(infoText, 10, 10);
  }
}
{{</p5js>}}
