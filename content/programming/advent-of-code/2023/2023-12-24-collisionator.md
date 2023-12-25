---
title: "AoC 2023 Day 24: Collisionator"
date: 2023-12-24 00:00:03
programming/languages:
- Rust
programming/sources:
- Advent of Code
series:
- Advent of Code 2023
---
## Source: [Day 24: Never Tell Me The Odds](https://adventofcode.com/2023/day/24)

[Full solution](https://github.com/jpverkamp/advent-of-code/tree/master/2023/solutions/day24) for today (spoilers!)

{{<toc>}}

## Part 1

> Given a set of 3D vectors (origin + velocity), count how many times the vectors would intersect. Ignore the Z-coordinate for this part; the collisions do not have to be at the same time. 

<!--more-->

### Parsing and Types

We don't have a `Point3`, so we'll make one:

```rust
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct Point {
    pub x: f64,
    pub y: f64,
    pub z: f64,
}

impl Add<Point> for Point {
    type Output = Point;

    fn add(self, rhs: Point) -> Self::Output {
        Point {
            x: self.x + rhs.x,
            y: self.y + rhs.y,
            z: self.z + rhs.z,
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq)]
pub struct Line {
    pub origin: Point,
    pub direction: Point,
}
```

I'm using floating point since the collisions for this part don't have to be integer values. I may [regret that](#part-2). 

And `nom` it:

```rust
fn point(input: &str) -> IResult<&str, Point> {
    map(
        tuple((
            complete::i128,
            preceded(terminated(complete::char(','), space0), complete::i128),
            preceded(terminated(complete::char(','), space0), complete::i128),
        )),
        |(x, y, z)| Point {
            x: x as f64,
            y: y as f64,
            z: z as f64,
        },
    )(input)
}

fn line(input: &str) -> IResult<&str, Line> {
    map(
        tuple((point, delimited(space0, complete::char('@'), space0), point)),
        |(origin, _, direction)| Line { origin, direction },
    )(input)
}

pub fn lines(input: &str) -> IResult<&str, Vec<Line>> {
    separated_list1(line_ending, line)(input)
}
```

### XY Intersections

This problem is *loaded* with algebra... I probably should have remembered how to do matrix/vector math, but so it goes. 

Here's the derivation. Times are $t$ and $t'$, positions are $x, y$ and velocities are $u, v$. 

First solve for $t$ using $x$:

$$
\text{} \newline
x_1 + t u_1 = x_2 + t' u_2 \newline
t u_1 = x_2 + t' u_2 - x_1 \newline
t = \(x_2 + t' u_2 - x_1) / u_1 \newline
$$

Then $y$:

$$
y_1 + t v_1 = y_2 + t' v_2 \newline
t v_1 = y_2 + t' v_2 - y_1
t = (y_2 + t' * v_2 - y_1) / v_1
$$

Set equal and solve for $t'$:

$$
(x_2 + t' u_2 - x_1) / u_1 = (y_2 + t' v_2 - y_1) / v_1 \newline
(x_2 + t' u_2 - x_1) v_1 = (y_2 + t' v_2 - y_1) u_1 \newline
x_2 v_1 + t' u_2 v_1 - x_1 v_1 = y_2 u_1 + t' v_2 u_1 - y_1 u_1 \newline
t' u_2 v_1 - t' v_2 u_1 = y_2 u_1 - x_2 v_1 - y_1 u_1 + x_1 v_1 \newline
t' (u_2 v_1 - v_2 u_1) = y_2 u_1 - x_2 v_1 - y_1 u_1 + x_1 v_1 \newline
t' = (y_2 u_1 - x_2 v_1 - y_1 u_1 + x_1 v_1) / (u_2 v_1 - v_2 u_1)
$$

And here's that in code (using `dx, dy` as $u, v$):

```rust
fn intersect_xy(l1: Line, l2: Line) -> Option<Point> {
    let Point {
        x: x1,
        y: y1,
        z: _z1,
    } = l1.origin;

    let Point {
        x: x2,
        y: y2,
        z: _z2,
    } = l2.origin;
    
    let Point {
        x: dx1,
        y: dy1,
        z: _dz1,
    } = l1.direction;
    
    let Point {
        x: dx2,
        y: dy2,
        z: _dz2,
    } = l2.direction;

    // If the denominator is (close enough to) zero, they never intersect
    if (dx2 * dy1 - dy2 * dx1).abs() < 0.0000001_f64 {
        return None;
    }

    let u = (y2 * dx1 - x2 * dy1 - y1 * dx1 + x1 * dy1) / (dx2 * dy1 - dy2 * dx1);
    let t = (x2 + u * dx2 - x1) / dx1;

    // Edge case: they intersect at time zero (we're told this shouldn't happen)
    if u < 0_f64 || t < 0_f64 {
        return None;
    }

    let x = x1 + t * dx1;
    let y = y1 + t * dy1;

    Some(Point { x, y, z: 0_f64 })
}
```

### Solution 

And with that we can just count them!

```rust
fn main() -> Result<()> {
    let stdin = io::stdin();
    let input = io::read_to_string(stdin.lock())?;
    let (s, lines) = parse::lines(input.as_str()).unwrap();
    assert!(s.trim().is_empty());

    let result = lines
        .iter()
        .cartesian_product(lines.iter())
        .filter_map(|(l1, l2)| intersect_xy(*l1, *l2))
        .filter(|p| p.x >= MIN_X && p.x <= MAX_X && p.y >= MIN_Y && p.y <= MAX_Y)
        .count()
        / 2; // counts l1,l2 and l2,l1

    println!("{result:?}");
    Ok(())
}
```

We are a bit inefficient, since we count both times for each pair of lines, but it's fast enough not to worry about that. 

## Part 2

> Find a new vector with integer position and velocity such that it hits every given vector at some future point. 

This time... it's not enough to just intersect the lines, we also have to deal with time!

### Solution 1: Brute Force

Man this one took some math. I'm just going to leave my derivations in source code comments rather than reformatting for LaTeX this time. But the general idea is this:

* Iterate all possible velocities out from `(0, 0, 0)` in a sort of spiraling motion 
* For each velocity `v`:
  * Take each pair of lines `l1` and `l2`
    * Calculate if it's possible that if our solution point started at `l1` at `t1`, would it make it to `l2` at `t2` with the velocity `v` (note: `l1` moves until `t1` and `l2` moves until `t2`)
    * Much like before, we can use piles of algebra to determine what `t1` (using only `x` and `y` coordinates) would be and then substitute that into `t2`, call this `t2xy`
    * Repeat this for `t2xz` and `t2yz`
    * If all of these time values are equal (and non-zero), we have a potential velocity!
* For each potential velocity `v`:
  * Try to calculate an origin point `p` much the same way
    * Use just two of the lines `l1` and `l2`
    * Use these to calculate `t1xy`, `t1xz`, and `t1yz` again, this time referring to the 'real' `t1` associated with the intersection with `l1`
      * If any of the values don't match, if they are negative, or if they are *non integers* this isn't a valid solution
    * Use this to work backwards to what point `p` would be, again, these values have to be *integers*

Once we've found a value, bam! We're done. 

Turn that into a lot of code (and as many comments):

```rust
fn main() -> Result<()> {
    env_logger::init();

    let stdin = io::stdin();
    let input = io::read_to_string(stdin.lock())?;
    let (s, lines) = parse::lines(input.as_str()).unwrap();
    assert!(s.trim().is_empty());

    #[allow(unused_assignments)]
    let mut velocity = None;
    let mut position = None;

    'found_solution: for bound in 0_i64.. {
        log::info!("bound: {}", bound);
        for vx in 0..=bound {
            for vy in 0..=(bound - vx) {
                let vz = bound - vx - vy;
                for (xd, yd, zd) in INVERSIONS {
                    if vx == 0 && xd < 0 {
                        continue;
                    }
                    if vy == 0 && yd < 0 {
                        continue;
                    }
                    if vz == 0 && zd < 0 {
                        continue;
                    }

                    let xd = vx * xd;
                    let yd = vy * yd;
                    let zd = vz * zd;

                    // for any two lines l1 and l2
                    // we want to be at l1 at t2 and at l2 at t2
                    // the time between is t2 - t1 = td

                    // we do not know x0

                    // x0 + xd * t1 = l1.o.x + l1.d.x * t1
                    // x0 + xd * t2 = l2.o.x + l2.d.x * t2

                    // l1.o.x + l1.d.x * t1 - xd * t1 = l2.o.x + l2.d.x * t2 - xd * t2
                    // currently t1 and t2 are unknown
                    // l1.d.x * t1 - xd * t1 = l2.o.x + l2.d.x * t2 - xd * t2 - l1.o.x
                    // t1 * (l1.d.x - xd) = l2.o.x + l2.d.x * t2 - xd * t2 - l1.o.x

                    // t1 = (l2.o.x + l2.d.x * t2 - xd * t2 - l1.o.x) / (l1.d.x - xd)
                    // t1 = (l2.o.y + l2.d.y * t2 - yd * t2 - l1.o.y) / (l1.d.y - yd)

                    // (l2.o.x + l2.d.x * t2 - xd * t2 - l1.o.x) / (l1.d.x - xd)
                    //      = (l2.o.y + l2.d.y * t2 - yd * t2 - l1.o.y) / (l1.d.y - yd)

                    // (l2.o.x + l2.d.x * t2 - xd * t2 - l1.o.x) * (l1.d.y - yd)
                    //      = (l2.o.y + l2.d.y * t2 - yd * t2 - l1.o.y) * (l1.d.x - xd)

                    // let A = l2.o.x - l1.o.x
                    // let B = l1.d.y - yd
                    // let C = l2.o.y - l1.o.y
                    // let D = l1.d.x - xd

                    // (A + l2.d.x * t2 - xd * t2) * B = (C + l2.d.y * t2 - yd * t2) * D
                    // AB + B l2.d.x t2 - B xd t2 = CD + D l2.d.y t2 - D yd t2
                    // B l2.d.x t2 - B xd t2 - D l2.d.y t2 + D yd t2 = CD - AB
                    // t2 = (CD - AB) / (B l2.d.x - B xd - D l2.d.y + D yd)

                    // To have a potential velocity some one line must be able to get to all of the other lines
                    let valid = lines.iter().any(|l1| {
                        lines.iter().filter(move |l2| l1 != *l2).all(|l2| {
                            let axy = l2.origin.x - l1.origin.x;
                            let bxy = l1.direction.y - yd as f64;
                            let cxy = l2.origin.y - l1.origin.y;
                            let dxy = l1.direction.x - xd as f64;

                            let t2xy = (cxy * dxy - axy * bxy)
                                / (bxy * l2.direction.x - bxy * xd as f64 - dxy * l2.direction.y
                                    + dxy * yd as f64);
                            if (t2xy - t2xy.round()).abs() > EPSILON {
                                return false;
                            }
                            let t2xy = t2xy.round() as i32;

                            let axz = l2.origin.x - l1.origin.x;
                            let bxz = l1.direction.z - zd as f64;
                            let cxz = l2.origin.z - l1.origin.z;
                            let dxz = l1.direction.x - xd as f64;

                            let t2xz = (cxz * dxz - axz * bxz)
                                / (bxz * l2.direction.x - bxz * xd as f64 - dxz * l2.direction.z
                                    + dxz * zd as f64);
                            if (t2xz - t2xz.round()).abs() > EPSILON {
                                return false;
                            }
                            let t2xz = t2xz.round() as i32;
                            if t2xy != t2xz {
                                return false;
                            }

                            let ayz = l2.origin.y - l1.origin.y;
                            let byz = l1.direction.z - zd as f64;
                            let cyz = l2.origin.z - l1.origin.z;
                            let dyz = l1.direction.y - yd as f64;

                            let t2yz = (cyz * dyz - ayz * byz)
                                / (byz * l2.direction.y - byz * yd as f64 - dyz * l2.direction.z
                                    + dyz * zd as f64);
                            if (t2yz - t2yz.round()).abs() > EPSILON {
                                return false;
                            }
                            let t2yz = t2yz.round() as i32;
                            if t2xy != t2yz {
                                return false;
                            }

                            true
                        })
                    });

                    if valid {
                        velocity = Some((xd, yd, zd));
                        log::info!("found potential velocity: {:?}", velocity);

                        // at t = 0 we're at x0, t0 is l[0], t1 is l[1]

                        // x0 + xd * t0 = l[0].o.x + l[0].d.x * t0
                        // x0 + xd * t1 = l[1].o.x + l[1].d.x * t1

                        // l0ox + l0dx * t0 - xd * t0 = l1ox + l1dx * t1 - xd * t1
                        // t0 = (l1ox + l1dx * t1 - xd * t1 - l0ox) / (l0dx - xd)
                        // t0 = (l1oy + l1dy * t1 - yd * t1 - l0oy) / (l0dy - yd)

                        // (l1ox + l1dx * t1 - xd * t1 - l0ox) / (l0dx - xd) = (l1oy + l1dy * t1 - yd * t1 - l0oy) / (l0dy - yd)
                        // (l1ox + l1dx * t1 - xd * t1 - l0ox) * (l0dy - yd) = (l1oy + l1dy * t1 - yd * t1 - l0oy) * (l0dx - xd)

                        // let A = l0dy - yd
                        // let B = 10dx - xd

                        // (l1ox + l1dx * t1 - xd * t1 - l0ox) * A = (l1oy + l1dy * t1 - yd * t1 - l0oy) * B
                        // l1ox * A + l1dx * t1 * A - xd * t1 * A - l0ox * A = l1oy * B + l1dy * t1 * B - yd * t1 * B - l0oy * B
                        // l1dx * t1 * A - xd * t1 * A - l1dy * t1 * B + yd * t1 * B = l1oy * B - l1ox * A - l0oy * B + l0ox * A
                        // t1 * (l1dx * A - xd * A - l1dy * B + yd * B) = l1oy * B - l1ox * A - l0oy * B + l0ox * A
                        // t1 = (l1oy * B - l1ox * A - l0oy * B + l0ox * A) / (l1dx * A - xd * A - l1dy * B + yd * B)

                        let axy = lines[0].direction.y - yd as f64;
                        let bxy = lines[0].direction.x - xd as f64;

                        let t1xy = -(lines[1].origin.y * bxy
                            - lines[1].origin.x * axy
                            - lines[0].origin.y * bxy
                            + lines[0].origin.x * axy)
                            / (lines[1].direction.y * bxy
                                - yd as f64 * bxy
                                - lines[1].direction.x * axy
                                + xd as f64 * axy);

                        let axz = lines[0].direction.z - zd as f64;
                        let bxz = lines[0].direction.x - xd as f64;

                        let t1xz = -(lines[1].origin.z * bxz
                            - lines[1].origin.x * axz
                            - lines[0].origin.z * bxz
                            + lines[0].origin.x * axz)
                            / (lines[1].direction.z * bxz
                                - zd as f64 * bxz
                                - lines[1].direction.x * axz
                                + xd as f64 * axz);

                        let ayz = lines[0].direction.z - zd as f64;
                        let byz = lines[0].direction.y - yd as f64;

                        let t1yz = -(lines[1].origin.z * byz
                            - lines[1].origin.y * ayz
                            - lines[0].origin.z * byz
                            + lines[0].origin.y * ayz)
                            / (lines[1].direction.z * byz
                                - zd as f64 * byz
                                - lines[1].direction.y * ayz
                                + yd as f64 * ayz);

                        if (t1xy - t1xz).abs() > EPSILON || (t1xy - t1yz).abs() > EPSILON {
                            log::info!("found non-matching t1: {:?} {:?} {:?}", t1xy, t1xz, t1yz);
                            continue;
                        }
                        if t1xy < 0_f64 {
                            log::info!("found negative t1: {:?}", t1xy);
                            continue;
                        }

                        // x0 + xd * t1 = l[1].o.x + l[1].d.x * t1
                        // x0 = l[1].o.x + l[1].d.x * t1 - xd * t1

                        let x0 =
                            lines[1].origin.x + lines[1].direction.x * t1xy - (xd as f64) * t1xy;
                        let y0 =
                            lines[1].origin.y + lines[1].direction.y * t1xy - (yd as f64) * t1xy;
                        let z0 =
                            lines[1].origin.z + lines[1].direction.z * t1xy - (zd as f64) * t1xy;

                        if x0.fract() != 0.0 || y0.fract() != 0.0 || z0.fract() != 0.0 {
                            log::info!("found non-integer position: {:?}", (x0, y0, z0));
                            continue;
                        }

                        let x0 = x0.round() as i128;
                        let y0 = y0.round() as i128;
                        let z0 = z0.round() as i128;

                        position = Some((x0, y0, z0));
                        log::info!("found valid position: {position:?}");

                        break 'found_solution;
                    }
                }
            }
        }
    }

    let position = position.unwrap();
    let result = position.0 + position.1 + position.2;

    println!("{result:?}");
    Ok(())
}
```

Wow that's a lot. It works though! Takes a minute and change, which all things considered isn't that bad!

### Solution 2: Using Z3

Okay, admission time. That wasn't actually my first solution. The first thing I did was realize this is a [[wiki:constrained optimization]]() problem and throw [Microsoft Research's z3](https://github.com/Z3Prover/z3) at it. 

```rust
fn main() -> Result<()> {
    env_logger::init();

    let stdin = io::stdin();
    let input = io::read_to_string(stdin.lock())?;
    let (s, lines) = parse::lines(input.as_str()).unwrap();
    assert!(s.trim().is_empty());

    // Make a giant system of equations
    // X + XD * [t] = [x] + [xd] * [t]

    // X and XD are scalars
    // [t] is a vector we're solving for
    // [x] and [xd] are the input vectors

    let config = Config::new();
    let context = Context::new(&config);
    let solver = Solver::new(&context);

    let origin_x = Int::new_const(&context, "ox");
    let origin_y = Int::new_const(&context, "oy");
    let origin_z = Int::new_const(&context, "oz");

    let direction_x = Int::new_const(&context, "dx");
    let direction_y = Int::new_const(&context, "dy");
    let direction_z = Int::new_const(&context, "dz");

    for line in lines {
        let line_origin_x = Int::from_i64(&context, line.origin.x as i64);
        let line_origin_y = Int::from_i64(&context, line.origin.y as i64);
        let line_origin_z = Int::from_i64(&context, line.origin.z as i64);

        let line_direction_x = Int::from_i64(&context, line.direction.x as i64);
        let line_direction_y = Int::from_i64(&context, line.direction.y as i64);
        let line_direction_z = Int::from_i64(&context, line.direction.z as i64);

        let t = Int::fresh_const(&context, "t");

        solver.assert(
            &(&line_origin_x + &line_direction_x * &t)._eq(&(&origin_x + &direction_x * &t)),
        );
        solver.assert(
            &(&line_origin_y + &line_direction_y * &t)._eq(&(&origin_y + &direction_y * &t)),
        );
        solver.assert(
            &(&line_origin_z + &line_direction_z * &t)._eq(&(&origin_z + &direction_z * &t)),
        );
    }

    solver.check();
    let model = solver.get_model().unwrap();

    let result_x = model.get_const_interp(&origin_x).unwrap().as_i64().unwrap();
    let result_y = model.get_const_interp(&origin_y).unwrap().as_i64().unwrap();
    let result_z = model.get_const_interp(&origin_z).unwrap().as_i64().unwrap();

    let result_dx = model
        .get_const_interp(&direction_x)
        .unwrap()
        .as_i64()
        .unwrap();
    let result_dy = model
        .get_const_interp(&direction_y)
        .unwrap()
        .as_i64()
        .unwrap();
    let result_dz = model
        .get_const_interp(&direction_z)
        .unwrap()
        .as_i64()
        .unwrap();

    log::info!(
        "result: {:?} + {:?}",
        (result_x, result_y, result_z),
        (result_dx, result_dy, result_dz),
    );

    let result = result_x + result_y + result_z;

    println!("{result:?}");
    Ok(())
}
```

Somehow... that's just not as satisfying though, you know? 

So then I spent *entirely too long* playing with algebra to work it out by hand. Yay me? 

## Performance

Like I said, [part 1](#part-1) is fast. [Part 2 brute forced](#solution-1-brute-force) is not as bad as I would have thought. And [part 2 with Z3](#solution-2-using-z3) runs in 2.5 seconds. So... I guess there is that!

```bash
# Part 1
$ just time 24 1

hyperfine --warmup 3 'just run 24 1'
Benchmark 1: just run 24 1
  Time (mean ± σ):     119.2 ms ±  17.3 ms    [User: 42.6 ms, System: 17.8 ms]
  Range (min … max):   107.1 ms … 173.2 ms    26 runs

# Part 2: Z3
$ just time 24 2-z3

hyperfine --warmup 3 'just run 24 2-z3'
Benchmark 1: just run 24 2-z3
  Time (mean ± σ):      2.561 s ±  0.047 s    [User: 2.261 s, System: 0.046 s]
  Range (min … max):    2.499 s …  2.634 s    10 runs

# Part 2: Brute force
$ just time 24 2-brute

hyperfine --warmup 3 'just run 24 2-brute'
Benchmark 1: just run 24 2
  Time (mean ± σ):     78.324 s ±  0.562 s    [User: 77.359 s, System: 0.037 s]
  Range (min … max):   77.860 s … 79.578 s    10 runs
```