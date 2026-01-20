let gui;
let params = {
  splitChance: 0.1, splitChanceMin: 0, splitChanceMax: 1, splitChanceStep: 0.01,
  minChildren: 2, minChildrenMin: 0, minChildrenMax: 10,
  maxChildren: 4, maxChildrenMin: 0, maxChildrenMax: 10,
  angleRange: Math.PI / 2, angleRangeMin: 0, angleRangeMax: Math.PI, angleRangeStep: 0.01,
  randomizeAngles: true,
  spacing: 5, spacingMin: 1, spacingMax: 10,
  maxDepth: 10, maxDepthMin: 1, maxDepthMax: 10,
  ticksPerFrame: 10, ticksPerFrameMin: 1, ticksPerFrameMax: 1000,
  pauseOnResetFor: 500, pauseOnResetForMin: 0, pauseOnResetForMax: 2000,
  stopOnReset: true,
};

let tree;
let lastParams;

class TreeNode {
  constructor(x, y, angle, parent=null) {
    this.id = TreeNode.nextId ? ++TreeNode.nextId : TreeNode.nextId = 1;

    this.x = x;
    this.y = y;
    this.length = 1; 
    this.angle = angle;
    this.parent = parent;
    this.depth = parent ? parent.depth + 1 : 0;

    this.growing = true;
    this.children = [];
  }

  update() {
    this.children.map((c) => c.update());
    
    if (!this.growing) return;
    
    // If we would intersect another branch within 'spacing' steps, stop growing
    if (this.willIntersect()) {
      this.growing = false;
      return;
    }
    
    // Keep growing, maybe split
    this.length += 1;

    if (this.length >= params.spacing && random() < params.splitChance) {
      this.growing = false;

      if (this.depth >= params.maxDepth) return;

      let tip = {
        x: this.x + this.length * cos(this.angle),
        y: this.y + this.length * sin(this.angle),
      };

      let childCount = floor(random() * (params.maxChildren - params.minChildren)) + params.minChildren;
      childCount = max(2, childCount);

      for (let i = 0; i < childCount; i++) {
        let newAngle = this.angle - params.angleRange / 2 + i * params.angleRange / (childCount - 1);
        if (params.randomizeAngles) {
          newAngle = this.angle + random(-params.angleRange / 2, params.angleRange / 2);
        }
        this.children.push(new TreeNode(tip.x, tip.y, newAngle, this));
      }
    }
  }

  draw() {
    this.children.map((c) => c.draw());

    stroke("black");
    strokeWeight(1);
    line(
      this.x,
      this.y,
      this.x + this.length * cos(this.angle),
      this.y + this.length * sin(this.angle),
    )
  }

  intersects(other) {
    // Tests if this segment intersects with another segment
    let x1 = this.x;
    let y1 = this.y;
    let x2 = this.x + this.length * cos(this.angle);
    let y2 = this.y + this.length * sin(this.angle);

    let x3 = other.x;
    let y3 = other.y;
    let x4 = other.x + other.length * cos(other.angle);
    let y4 = other.y + other.length * sin(other.angle);

    // Exact endpoint matches are fine
    if ((x1 == x3 && y1 == y3) || (x1 == x4 && y1 == y4) || (x2 == x3 && y2 == y3) || (x2 == x4 && y2 == y4)) {
      return false;
    }

    let denom = (y4 - y3) * (x2 - x1) - (x4 - x3) * (y2 - y1);
    if (denom == 0) {
      return false; // parallel lines
    }

    let ua = ((x4 - x3) * (y1 - y3) - (y4 - y3) * (x1 - x3)) / denom;
    let ub = ((x2 - x1) * (y1 - y3) - (y2 - y1) * (x1 - x3)) / denom;

    return (ua >= 0 && ua <= 1 && ub >= 0 && ub <= 1);
  }

  intersectsAnyOther(other, ignore = null) {
    if (other !== ignore && this.intersects(other)) {
      return true;
    }
    return other.children.some((c) => this.intersectsAnyOther(c, ignore));
  }

  willIntersect() {
    this.length += params.spacing;
    let result = this.intersectsAnyOther(tree, this);
    this.length -= params.spacing;
    return result;
  }
  
  anyGrowing() {
    if (this.growing) return true;
    return this.children.some((c) => c.anyGrowing());
  }
}

function setup() {
  createCanvas(400, 400);
  pixelDensity(1);

  gui = createGuiPanel("params");
  gui.addObject(params);
  gui.setPosition(420, 0);

  reset();
}

function reset() {
  tree = new TreeNode(width / 2, height / 2, -PI / 2);
}

function draw() {
  if (lastParams == undefined || Object.keys(params).some((k) => params[k] !== lastParams[k])) {
    reset();
    lastParams = { ...params };
  }

  background("white");
  for (let i = 0; i < params.ticksPerFrame; i++) {
    tree.update();
  }
  tree.draw();

  if (!tree.anyGrowing()) {
    reset();

    // TODO: If params.stopOnReset, don't draw a new tree (but still allow changing params). If !stop, pause for pauseOnResetFor frames before continuing.
  }
}