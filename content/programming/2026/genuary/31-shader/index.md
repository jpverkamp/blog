---
title: "Genuary 2026.31: Shader"
date: "2026-01-31 00:00:00"
programming/languages:
- JavaScript
programming/topics:
- Generative Art
- Procedural Content
- p5js
series:
- Genuary 2026
cover: gen26.31.png
---
I have very little experience with [[wiki:graphics shaders]](), but I'd like to learn. Perhaps I'll take a month to redo all these prompts with shaders. That'd be neat. 

But for now, one shader, messing around a bit. 

<!--more-->

{{<p5js width="600" height="500">}}
let gui;
let params = {
  scale: 2.5, scaleMin: 1, scaleMax: 30, scaleStep: 0.5,
  smoothness: 0.2, smoothnessMin: 0, smoothnessMax: 2, smoothnessStep: 0.1,
  distanceBetween: 0.5, distanceBetweenMin: 0, distanceBetweenMax: 1, distanceBetweenStep: 0.1,
  phaseOffset: 0.1, phaseOffsetMin: 0, phaseOffsetMax: 1, phaseOffsetStep: 0.1,
  wiggle: true,
};

let s;

const vert = `
attribute vec3 aPosition;
void main() {
  gl_Position = vec4(aPosition, 1.0);
}
`;

const frag = `
precision mediump float;

uniform vec2 u_resolution;
uniform float u_time;
uniform float u_scale;
uniform float u_smooth;
uniform float u_repeat;
uniform float u_distance_between; 
uniform float u_phase_offset;
uniform float u_wiggle;

float sdCircle(vec2 p, float r) {
  return length(p) - r;
}

float sdBox(vec2 p, vec2 b) {
  vec2 d = abs(p) - b;
  return length(max(d, 0.0)) + min(max(d.x, d.y), 0.0);
}

float smin(float a, float b, float k) {
  float h = clamp(0.5 + 0.5 * (b - a) / k, 0.0, 1.0);
  return mix(b, a, h) - k * h * (1.0 - h);
}

vec2 repeat(vec2 p, float s) {
  return mod(p + s * 0.5, s) - s * 0.5;
}

float noise(vec2 p) {
    return sin(p.x*12.9898 + p.y*78.233 + u_time*3.0) * 43758.5453 - floor(sin(p.x*12.9898 + p.y*78.233 + u_time*3.0) * 43758.5453);
}


float map(vec2 p) {
  p = repeat(p, u_repeat);

  float dist = u_distance_between * 0.4;

  float t = u_time;
  float phase = u_phase_offset * 6.28318;

  vec2 offsetA = dist * vec2(
    cos(t),
    sin(t)
  );

  vec2 offsetB = dist * vec2(
    cos(t + phase),
    sin(t + phase)
  );

  vec2 pc = p + offsetA;
  vec2 pb = p - offsetB;
  
  float wiggleA = 0.0;
  float wiggleB = 0.0;
  if (u_wiggle > 0.5) {
    wiggleA = 0.05 * sin(10.0*pc.x + 5.0*pc.y + t*5.0);
    wiggleB = 0.05 * cos(8.0*pb.x - 6.0*pb.y + t*4.0);
  }

  float a = sdCircle(pc, 0.35 + wiggleA);
  float b = sdBox(pb, vec2(0.25 + wiggleB));

  return smin(a, b, u_smooth);
}


vec2 normal(vec2 p) {
  float e = 0.001;
  return normalize(vec2(
    map(p + vec2(e, 0.0)) - map(p - vec2(e, 0.0)),
    map(p + vec2(0.0, e)) - map(p - vec2(0.0, e))
  ));
}

void main() {
  vec2 uv = (gl_FragCoord.xy - 0.5 * u_resolution) / u_resolution.y;
  uv *= u_scale;

  float t = u_time * 0.4;
  uv *= mat2(cos(t), -sin(t), sin(t), cos(t));

  float d = map(uv);
  float mask = smoothstep(0.01, 0.0, d);

  vec2 n = normal(uv);
  vec2 light = normalize(vec2(0.7, 0.9));
  float diff = clamp(dot(n, light), 0.0, 1.0);

  vec3 base = mix(
    vec3(0.08, 0.1, 0.15),
    vec3(0.6, 0.8, 1.0),
    diff
  );

  float glow = exp(-8.0 * abs(d));

  vec3 color = base * mask + glow * vec3(0.3, 0.6, 1.0);

  gl_FragColor = vec4(color, 1.0);
}
`;

function setup() {
  let canvas = createCanvas(400, 400, WEBGL);

  gui = createGuiPanel("params");
  gui.addObject(params);
  gui.setPosition(420, 0);

  s = createShader(vert, frag);
  noStroke();
}

function draw() {
  shader(s);
  s.setUniform("u_resolution", [width, height]);
  s.setUniform("u_time", millis() / 1000);
  s.setUniform("u_scale", params.scale);
  s.setUniform("u_smooth", params.smoothness);
  s.setUniform("u_repeat", 1.2);
  s.setUniform("u_distance_between", params.distanceBetween);
  s.setUniform("u_phase_offset", params.phaseOffset);
  s.setUniform("u_wiggle", params.wiggle ? 1.0 : 0.0);

  quad(-1, -1,  1, -1,  1,  1,  -1,  1);
}
{{</p5js>}}