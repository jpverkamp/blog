---
title: "AoC 2022 Day 12: Climbiantor"
date: 2022-12-12 00:00:03
programming/languages:
- Rust
programming/sources:
- Advent of Code
series:
- Advent of Code 2022
---
### Source: [Hill Climbing Algorithm](https://adventofcode.com/2022/day/12)

#### **Part 1:** Given a height map, find the shortest path between two points such that the path can descend any distance but can only climb by a maximum of 1. 

<!--more-->

Ooh, that's fun. Just glancing at it, I already know I want to solve this backwards. Don't find the path from start to finish, instead start at the end and recursively fill the map with the distance to each known point flooding outwards until we find the start. 

But that's getting ahead of myself, first let's parse it:

```rust
#[derive(Debug)]
struct HeightMap {
    data: Matrix<u8>,
    src: Point,
    dst: Point,
}

impl From<Vec<String>> for HeightMap {
    fn from(lines: Vec<String>) -> Self {
        let width = lines.get(0).expect("must have at least one line").len();
        let height = lines.len();

        let mut data = Matrix::new(width, height);
        let mut src = Point::ORIGIN;
        let mut dst = Point::ORIGIN;

        for (y, line) in lines.iter().enumerate() {
            for (x, c) in line.chars().enumerate() {
                match c {
                    'S' => {
                        data[[x, y]] = 1;
                        src = Point {
                            x: x as isize,
                            y: y as isize,
                        };
                    }
                    'E' => {
                        data[[x, y]] = 26;
                        dst = Point {
                            x: x as isize,
                            y: y as isize,
                        };
                    }
                    _ => {
                        data[[x, y]] = (c as u8) - ('a' as u8) + 1;
                    }
                }
            }
        }

        HeightMap { data, src, dst }
    }
}
```

Sweet. 

Next, calculate `DistanceMap` from that `HeightMap`. We don't need them (yet?) but I'm going to go ahead and store the actual path as well, as a second `Matrix` of directions showing which way to go next. It's a single time computation, so I'm actually going to put the entire functionality into the `from(&HeightMap)` function. 

```rust
#[derive(Debug)]
struct DistanceMap {
    distances: Matrix<Option<usize>>,
    directions: Matrix<Point>,
}

impl From<&HeightMap> for DistanceMap {
    fn from(heights: &HeightMap) -> Self {
        let width = heights.data.width();
        let height = heights.data.height();

        let mut distances = Matrix::<Option<usize>>::new(width, height);
        let mut directions = Matrix::<Point>::new(width, height);

        distances[[heights.dst.x as usize, heights.dst.y as usize]] = Some(0);

        let mut q = VecDeque::new();
        q.push_back(heights.dst);

        while !q.is_empty() {
            let p_dst = q.pop_front().unwrap();
            let h_dst = heights.data.at(&p_dst);

            // d_dst will always be set if there are no bugs
            let d_dst_p = distances.at(&p_dst);
            let d_dst = d_dst_p.unwrap();

            for m in MOVES.into_iter() {
                let p_src = p_dst + m;

                if !distances.in_bounds(p_src.x as usize, p_src.y as usize) {
                    continue;
                }

                let h_src = heights.data.at(&p_src);
                let d_src = distances.at(&p_src);

                // If the jump is too high, can't go this way
                if *h_dst > h_src + 1 {
                    continue;
                }

                // If we already have a better path, don't go this way
                if d_src.is_some() && d_src.unwrap() < d_dst + 1 {
                    continue;
                }

                // If we make it this far, we found a new (valid) better path

                // Store the new distance and direction
                distances[[p_src.x as usize, p_src.y as usize]] = Some(d_dst + 1);
                directions[[p_src.x as usize, p_src.y as usize]] = m;

                // Add this point to the queue of points to expand further
                if !q.contains(&p_src) {
                    q.push_back(p_src);
                }
            }
        }

        DistanceMap {
            distances,
            directions,
        }
    }
}
```

That's a fun algorithm. The basic idea is:

* Initialize a queue with the target point
* While that queue is not finished, pop the next point (`dst`):
  * This point will always have a distance
  * Try each neighboring point (`src`):
    * If `src` cannot move to `dst` (a height skip of more than +1), skip this
    * If we already have a better path to `dst`, skip this
    * Otherwise, we found a new path:
      * Update the `distances` and `directions` maps
      * Add the new point to the queue since we might have a new better route to it now

And that's it. It turns out this makes the final problem *really* short:

```rust
fn part1(filename: &Path) -> String {
    let lines = read_lines(filename);
    let height_map = HeightMap::from(lines);
    let distance_map = DistanceMap::from(&height_map);

    distance_map.distances[[height_map.src.x as usize, height_map.src.y as usize]]
        .expect("must have a solution")
        .to_string()
}
```

That's it. 

I did make some fun test print functions though while working through it:

```rust
fn part1(filename: &Path) -> String {
    let lines = read_lines(filename);
    let height_map = HeightMap::from(lines);
    let distance_map = DistanceMap::from(&height_map);

    if cfg!(debug_assertions) {
        for y in 0..height_map.data.height() {
            for x in 0..height_map.data.width() {
                match distance_map.distances[[x, y]] {
                    Some(d) => { 
                        print!("{:4}", d);
                    },
                    None => {
                        print!("{:4}", '.');
                    }

                }
            }
            println!();
        }
        println!();

        for y in 0..height_map.data.height() {
            for x in 0..height_map.data.width() {
                print!(
                    "{}",
                    match distance_map.directions[[x, y]] {
                        Point { x: 0, y: 1 } => 'v',
                        Point { x: 0, y: -1 } => '^',
                        Point { x: 1, y: 0 } => '>',
                        Point { x: -1, y: 0 } => '<',
                        _ => '.',
                    }
                );
            }
            println!();
        }
    }

    distance_map.distances[[height_map.src.x as usize, height_map.src.y as usize]]
        .expect("must have a solution")
        .to_string()
}
```

For the small test case:

```bash
$ cat data/12-test.txt

Sabqponm
abcryxxl
accszExk
acctuvwj
abdefghi

$ ./target/debug/12-climbinator 1 data/12-test.txt

  31  30  29  12  13  14  15  16
  30  29  28  11   2   3   4  17
  31  28  27  10   1   0   5  18
  30  27  26   9   8   7   6  19
  29  28  25  24  23  22  21  20

^^^^>>>>
<^^^^>>v
^^^^<.vv
^<^<<<vv
<v<<<<<v
31
took 1.398833ms
```

And even cooler for my full test data:

```text
 403 402 403 404 405 406 407 398  .   .   .   .  399 400 401 402 403 404 405 406 407  .   .   .   .   .   .  326 325 324 323 322 321 320 319 318 317 316 315 314 313 312 311 310 309 308 307 306 305 304 303 302 301 300 299 300 301 302 301 300 299  .   .   .   .   .   . 
 402 401 402 403 404 405 406 397  .   .   .   .  398 399 400 401  .   .   .   .   .   .   .   .   .   .  326 325 324 323 322 321 320 319 318 317 316 315 314 313 312 311 310 309 308 307 306 305 304 303 302 301 300 299 298 299 300 301 300 299 298  .   .   .   .   .   . 
 401 400 401 402 403 396 395 396  .   .   .   .  397 398 399 400  .   .   .   .   .   .   .   .   .   .   .  326 325 324  .   .  321 320 319 318 317 316 315 314 313 312 311  .   .  306 305 304 303 302 301 300 299 298 297 298 299 300 299 298 297 296  .   .   .   .   . 
 400 399 400 401 402 403 394 395 396  .   .  395 396 397 398 399  .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .  321 320 319 318 317 316 315 314 313 312 313  .  305 304 303 302 301 300 299 298 297 296 297 298 299 298 297 296 295 294 293  .   .   . 
 399 398 399 396 403 404 393 394 395 396 395 394 395 396 397 398 399  .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .  322 321 320 319 318 317 316 315 314 313  .   .  304 303 302 301 300 299 298 297 296 295 296 297 298 297 296 295 294 293 292  .   .   . 
 398 397 396 395 394 405 392 393 394 395 394 393 394 395 396 397 398  .   .   .   .   .   .   .  334 333  .   .   .   .   .   .   .  323 322 321 320 319 318 317 316 315 314 315 196 195 194 301 300 299 298 297  .  295 294 295 296 297 296 295 294 293 292 291  .   .  294
 397 396 395 394 393 392 391 392 393 394 393 392 393 394 395 396 397 398  .   .   .   .   .  334 333 332 331 330 329 328 327 326 325 324 323 322 321 320 319 318 317 316 197 196 195 194 193 192 191 298 297 296 295 294 293 294 295 296 295 294 293 292 291 290 291 292 293
 396 395 396 397 398 391 390 391 392 393 392 391 392 393 394 395 396 397  .   .   .   .   .  335 334 333 332 331 330 329 328 327 326 325 324 323 322 321 320  .   .  197 196 195 194 193 192 191 190 189 296 295 294 293 292 293 294 295 296  .   .  291 290 289 290 291 292
 395 394 395 396 397 390 389 390 391 392 391 390 391 392 393 394  .  398 399 400  .   .   .  336 335 334 333 332 331 330 329 328 327 326 325 324 323 322 321  .  199 198 197 196 107 106 105 190 189 188 187 294 293 292 291  .   .   .  297  .   .  290 289 288 289 290 291
 394 393 394 395 396 389 388 389  .   .   .  389 390 391 392 393  .   .  400  .   .   .  338 337 336 335 334 333 332 331 330 329 328 327 326 325 324 323 322 201 200 199 198 107 106 105 104 103 188 187 186 185 292 291 290 289 288  .   .   .   .  289 288 287 288 289 290
 393 392 393 394 389 388 387  .   .   .   .  388 389 390 391 392  .   .   .   .   .  340 339 338 337 336 335 334 333 332 331 330 329 328 327 326 325 324 203 202 201 200 107 106 105 104 103 102 101 186 185 184 183 290 289 288 287 286 285  .   .   .   .  286 287 288 289
 392 391 392 393 394 387 386  .   .   .   .  387 388 389 390 391 392  .   .   .   .   .   .  339  .   .   .  335 334 333 332 331 330 329 328 327 326 205 204 203 202 109 108 107  40  39  38 101 100  99 184 183 182 181 180 287 286 285 284 283  .   .   .  285 286 287 288
 391 390 391 392 393 386 385 384  .   .   .  386 387 388 389  .   .   .   .   .   .   .   .  340  .   .   .   .  335 334 333 332 331 330 329 208 207 206 205 204 111 110 109  40  39  38  37  36  99  98  97 182 181 180 179 178 177 284 283 282 281 282  .  284 285 286 287
 390 389 388 387 386 385 384 383 382 383 384 385 386 387 388  .   .   .   .   .   .   .   .  341  .   .   .   .  336 335 334 333 332 211 210 209 208 207 206 113 112 111 110  39  38  37  36  35  34  97  96  95 180 179 178 177 176 175 176 281 280 281 282 283 284 285 286
 389 388 387 386 385 384 383 382 381 382 383 384 385 386 387 388 389 390  .   .  345 344 343 342  .   .   .  338 337 336 335 214 213 212 211 210 117 116 115 114 113 112  41  40  39  10  35  34  33  96  95  94  93  92  91 176 175 174 175 176 279 280 281 284 285 286 287
 388 387 388 387 390 391 382 381 380 381 382 383 384 385 386 387 388 389  .   .  346 345 344 343 342 341 340 339 338 337 336 215 214 213 212 119 118 117 116 115 114  43  42  41  10   9   8  33  32  31  94  93  92  91  90  89  90 173 174 175 278 279 280 285 286 287 288
 387 386 387 388 389 390 381 380 379 380 381 382 383  .  387 388 389  .  349 348 347 346 345 344 343 342 341 340 339 338 217 216 215 214 121 120 119  48  47  46  45  44  43  42   9   8   7   8  31  30  29  28  27  90  89  88  89 172 173 174 277 278 279 286 287 288 289
 386 385 386 387 388 389 390 379 378 379 380 381  .   .   .  389  .   .   .  349 348 347 346 345 344 343 342 341 340 339 218 217 216 123 122 121 120  49  48  47  46  45  44  43   8   7   6   7  30  29  28  27  26  27  28  87  88 171 172 173 276 277 278 287 288 289 290
 385 384 385 386 387 388 389 378 377  .   .   .   .   .   .   .   .   .   .  350 349 348 347 346 345 344 343  .  341 340 219 218 217 124 123 122  51  50  49  48   9   8   7   8   7   6   5   6   7   8   9  10  25  26  27  86  87 170 171 172 275 276 277 288 289 290 291
 384 383 384 385 386 379 378 377 376  .   .   .   .   .   .   .   .   .   .  351 350 349 348 347 346 345  .   .  342 341 220 219 218 125 124 123  52  51  50   9   8   7   6   7   6   5   4   5   6   7   8   9  24  25  84  85  86 169 170 171 274 275 276 289 290 291 292
 383 382 381 386 387 378 377 376 375  .   .   .   .   .   .   .   .   .   .  352 351 350 349  .   .   .   .   .  343  .  221 220 219 126 125 124  53  52  51   8   7   6   5   0   1   2   3   4   5   6   7  22  23  24  83  84  85 168 169 170 273 274 291 290 291 292 293
 382 381 380 379 378 377 376 375 374  .   .   .   .   .   .   .   .   .   .   .  352 351 350  .   .   .   .   .   .   .   .  221 220 221 126 125 126  53  52  53   6   5   4   3   2   3   4   5   6  21  20  21  22  81  82  83 166 167 168 271 272 273 292 291 292 293 294
 381 380 379 378 377 376 375 374 373  .   .   .   .   .   .   .   .   .   .   .  353 352 351 352 353  .   .   .   .  362 361 222 221 222 127 126 127 128  53  54  55  56   5   4   3   4   5   6   7  20  19  20  79  80  81 164 165 166 269 270 271 294 293 292 293 294 295
 380 379 378 377 376 375 374 373 372 371 370  .   .   .   .   .   .  359 358  .  354 353 352 353  .   .   .   .   .  361 360 359 222 223 224 127 128 129 130  55  56   7   6   5   4   5   6   7   8   9  18  19  78  79 164 163 164 165 268 269 270 295 294 293 294 295 296
 379 378 377 376 375 374 373 372 371 370 369 368 367 366  .   .   .  358 357 356 355 354 353 354  .   .  361  .   .   .  359 358 357 224 225 226 129 130 131  56  57   8   7   6   5  12  13   8   9  10  17  18  77  78 163 162 163 266 267 268 297 296 295 294 295 296 297
 378 377 376 375 374 373 372 371 370 369 368 367 366 365  .   .   .  359 358 357 356 355 354 355  .  359 360  .   .   .  358 357 356 225 226 227 130 131 132  57  58   9   8   9  10  11  12  13  14  15  16  17  76  77  78 161 162 265 266 267 298 297 296 295 296 297 298
 377 376 375 374 373 372 371 370 369 368 367 366 365 364 363 362 361 360 359 358 357 356 355 356 357 358 359 360 359 358 357 356 355 226 227 228 131 132 133  58  59  10   9  10  11  68  69  14  15  16  17  18  75  76  77 160 161 264 265 266 299 298 297 296 297 298 299
 378 377 378 379 380 373 372 391 392 369 368 367 366 365 364 363 362 361 360 359 358 357 356 357 358 359 360 359 358 357 356 355 354 353 228 229 132 133 134  59  60  61  10  11  12  67  68  69  16  17  18  19  74  75  76 159 160 263 264 265  .  299 298 297 298 299 300
 379 378 379 380 375 374 391 390 391 392 393 394 367 366 365 364 363 362 361 360 359 358 357 358 359 360 359 358 357  .   .   .  353 352 229 230 133 134 135  60  61  62  63  64  65  66  67  68  69  70  71  72  73  74 157 158 159 262 263 264  .  300 299 298 299 300 301
 380 379 380 377 376 375 376 389 390 391 392 393 368 367 366 365 364 363 362  .   .   .  358 359 360 359 358 357 356  .   .   .   .  351 230 231 134 135 136  61  62  63  64  65  66 147 148  69  70  71  72  73  74  75 156 157 158 261 262 263  .  301 300 299 300 301 302
 381 380 381 382 377 386 387 388 389 390 391 392 369 368 367 366 365 364 363  .   .   .   .  360 359 358 357 356 355  .   .   .   .  350 231 232 233 136 137 138 139  64  65 144 145 146 147 148 149 150  73  74 153 154 155 156 157 260 261  .   .   .   .  300 301 302 303
 382 381 382 383 384 385 386 387 388 389 390 391 392 369 368 367 366 365 364  .   .   .   .  359 358 357 356 355 354  .   .   .  350 349 232 233 234 137 138 139 140 141 142 143 144 145 146 147 148 149 150 151 152 153 154 155 258 259 260  .   .   .   .  301 302 303 304
 383 382 383 384 385 386 387 388 389 390 391 392 393 370 369 368 367 366 365  .   .   .   .  358 357 356 355 354 353 352 351 350 349 348 347 234 235 236 139 140 141 142 143 144 145 246 247 248 149 150 151 152 153 154 155 256 257 258 259  .   .   .  303 302 303 304 305
 384 383 384 385 386 387 388 389 390 391 376 393 372 371 370 369 368 367 366 367  .   .  358 357 356 355 354 353 352 351 350 349 348 347 346 235 236 237 238 239 240 241 242 243 244 245 246 247 248 249 250 251 252 253 254 255 256 257  .   .   .  305 304 303 304 305 306
 385 384 385 386 387 388 389 390 391 376 375 374 373 372 371 370 369 368 367 368  .   .   .  356 355 354 353 352 351 350 349 348 347 346 345 344 237 238 239 240 241 242 243 244 245 246 247 248 249 250 251 252 253 254 255 256 257 312  .   .   .  306 305 304 305 306 307
 386 385 386 387 388 389 390 391 392  .  376 375 374 373 372 371 370 369 368 369  .   .   .   .  356 355 354  .   .  349 348 347 346 345 344 343 342 239 240 241 242 243 244 245  .   .   .   .   .  251 252 253 254 255 256 313 312 311 310 309 308 307 306 305 306 307 308
 387 386 387 388 389 390 391 392 393  .   .   .  375  .   .   .  371 370 369 370  .   .   .   .  357  .   .   .   .  348 347 346 345 344 343 342 341 340 339 338 337 336 335 334  .   .   .   .  321 320 319 318 317 316 315 314 313 312 311 310 309 308 307  .   .   .  309
 388 387 388 389 390 391 392 393 394  .   .   .   .   .   .   .  372 371 370 371  .   .   .   .   .   .   .   .   .  347 346 345 344 343 342 341 340 339 338 337 336 335 334 333  .   .   .  323 322 321 320 319 318 317 316 315 314 313 312 311 310 309 308 309  .   .   . 
 389 388 389 390 391 392 393 394 395  .   .   .   .   .   .  374 373 372 371  .   .   .   .   .   .   .   .  348 347 346 345 344 343 342 341 340 339 338 337 336 335 334 333 332 333  .   .  324 323 322 321 320 319 318 317 316 315 314 313 312 311 310 309 310  .   .   . 
 390 389 390 391 392 393 394 395  .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .  347 346 345 344 343 342 341 340 339 338 337 336 335 334 333 332 331  .   .  326 325 324 323 322 321 320 319 318 317 316 315 314 313 312 311  .   .   .   .   . 
 391 390 391 392 393 394 395  .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .  345 344 343 342 341 340 339 338 337 336 335 334 333 332 331 330 329 328 327 326 325 324 323 322 321 320 319 318 317 316 315 314 313  .   .   .   .   .   . 

^^^^^^^^....^^^^>>>>>......^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^<^^^......
^^^^^>>^....^^^^..........<<<<<<<<<<<<<<<<<<<^^^^^^^^^^^^<^^^......
^^^^^<^^....^^^^...........vvv..vvvvvvvvvvv..^^^^^^^^^^^^<^^^^.....
^^^>>>^^^..^^^^^.................vvvvvvvvvv>.^^^^^^^^^^^^<^^^^^^...
^^>^vv^^^<^^^^^^^................vvvvvvvvvv..<<^^^^^<^^^^<^^^^^^...
^^^^^v^^^<^^^^^^^.......^^.......vvvvvvvvvv>^^^<<^^^.^^^^<^^^^^^..^
^^<<<^^^^<^^^^^^^^.....<<<<<<<<<<vvvvvvvvv^^^^^^^<^^^^^^^<<<<^^^^^^
^^^^^^^^^<^^^^^^>>.....vvvvvvvvvvvvvvvv..<<<<<<^^^<^^^^>>>v..^^^^^^
^^^^^^^^><<^^^^^.v>>...vvvvvvvvvvvvvvvv.<vvv^^^<^^^<^^^...v..^^^^^^
^^^^>^^>...^^^^^..v...<vvvvvvvvvvvvvvvv<vvv^^^^^<^^^<^^^^....<<^^^^
^^^^<^^....^^^^^.....<vvvvvvvvvvvvvvvv<vvv<<<<<^^<^^^<<^^^^....^^^^
^^^^^^^....^^^^>>......v...vvvvvvvvvv<vvv<vv^^^<^^<^^^^<<^^^...^^^^
^^>>>^^^...^^^^........v....vvvvvvv<<vvv<vv^^^^^<^^<^^^^^<<^^^.^^^^
^^^^^^^^^^^^^^^........v....vvvvv<<vvvv<vvv<<<^^^^^^<<<^^^^<^^^>>>>
^^<<<<^^^^^^^^^^^^..<<<v...<vvv<<vvv<<<vvv<vv^<^^<^^^^^<<^^^^^^vvvv
^^^v^^^^^^^^^>>>>>..vvvv<<<vvvvvvvv<vvvvv<vv^^^<^^<<<^^^^^^^^^^vvvv
^^^^^^<^^^^^>.vvv.<<vvvvvvvvvv<vvv<vv<<<<vvv^^^^^^^^^<<^^^^^^^^vvvv
^^^^^^^^^>>>...v...vvvvvvvvvvvvvv<vvvvvvvvvv^^^^<<<<^^^^^^^^^^^vvvv
^^^^^>>^^..........vvvvvvvv.vvvvvvvv<vvv^^^<^^^^^^^^^^>^^^^^^^^vvvv
^^>>>^^^^..........vvvvvvv..vvvvvvvvvvv^^^^<<<^^^^^>^^^^^^^^^^>vvvv
^^^vv^^^^..........vvvv.....v.vvvvvvvvv<^^^.>>>>>>>^^>^^>^^>^^<vvvv
^^^^^^^^^...........vvv........vv>vv>vv><<<<vvvvv^^^>^^>^^>^^>vvvvv
^^^^^^^^^...........vvv>>....^^vvvvvv>vv>>vvvvvvv<^^^^>^^^^^^<vvvvv
^^^^^^^^^^^......^^.vvvv.....<^^vv>vvv>vv<vvvvvvv>^^^^^^^>^^>vvvvvv
^^^^^^^^^^^^^^...<<<vvvv..^...^^^vv>vvvvvvvvv^^vvv^^^^<^^^^^<vvvvvv
^^^^^^^^^^^^^^...vvvvvvv.^^...^^^vvvvvvvvvv>>>>>>>>>^^^^^^^^vvvvvvv
<<<<<<<<<<<<<<<<<vvvvvvv>>>^^^^^^vvvvvvvvvvvv^^vvvvv^^^^^^^^vvvvvvv
vv>>>vv^^vvvvvvvvvvvvvvvvv^^^<<<^^vvvvvvv>vvv^^^vvvv^^>^^^^^.vvvvvv
vvvv<v<^^^^^vvvvvvvvvvvvv^^^^...<^vvvvvvvv>>>>>>>>>>>>^^^^^^.vvvvvv
vvv<vv>^^^^^vvvvvvv...vv^^^^^....^vvvvvvvvvvv^^vvvvvvv^^^^^>.vvvvvv
vvv>v^^^^^^^vvvvvvv....^^^^^^....^vv>vv>>vv^^^^^^^vv^^^^>^^....vvvv
vvvv>>>>>>>>>vvvvvv....^^^^^^...^^vvvvvvv>>>>>>>>>>>>>>>^^^....vvvv
vvvvvvvvvvvvvvvvvvv....^^^^^^^^^^^^vv>vvvvvvv^^^vvvvvvv^^^>...<vvvv
vvvvvvvvvv^v<vvvvvv>..<^^^^^^^^^^^^vvv>>>>>>>>>>>>>>>>>>>>...<vvvvv
vv>vvvvvv<<<vvvvvvvv...<<<<<<^^^^^^^vvvvvvvvvvvvvvvvvvvvv^...vvvvvv
vvv>>vvvv.vvvvvvvvvv....vvv..^^^^^^^^vvvvvvv.....vvvvvv<<<<<<vvvvvv
vvvvvvvvv...v...vvvv....v....^^^^^^^^^^^^^^^....<<<<<<<vvvvvvvv...v
vvvvvvvvv.......vvvv.........^^^^^^^^^^^^^^^...<vvvvvvvvvvvvvvv>...
vvvv>vvvv......<vvv........^^^^^^^^^^^^^^^^^>..vvvvvvvvvvvvvvvvv...
vvvvvvvv...................<^^^^^^^^^^^^^^^^..<vvvvvvvvvvvvvvv.....
vvvvvvv.....................<<<<<<<<<<<<<<<<<<vvvvvvvvvvvvvvv......
383
took 22.88925ms
```

It's huge, but that's so cool to look at. I particularly like being able to see the ridges (regions of `.`) where there's no way to actually climb up onto them from any direction and how that makes choke points. 

Very cool. 

On to part 2!

#### **Part 2:** Expand the search to any point with height 1 (not just the `S`). Find the minimum distance.

This one delightfully didn't changes to the underlying code, just scanning over the `distance_map`:

```rust
fn part2(filename: &Path) -> String {
    let lines = read_lines(filename);
    let height_map = HeightMap::from(lines);
    let distance_map = DistanceMap::from(&height_map);

    let mut best_distance = usize::MAX;

    for y in 0..height_map.data.height() {
        for x in 0..height_map.data.width() {
            if height_map.data[[x, y]] > 1 {
                continue;
            }

            match distance_map.distances[[x, y]] {
                Some(d) if d < best_distance => {
                    best_distance = d;
                }
                _ => {}
            }
        }
    }

    best_distance.to_string()
}
```

#### Performance

Whee!

```bash
$ ./target/release/12-climbinator 1 data/12.txt

383
took 402.208µs

$ ./target/release/12-climbinator 2 data/12.txt

377
took 153.75µs
```

I don't have a backtracking solution, but I expect this is even a bit faster than that would have been. It certainly does have the advantage of near `O(1)` memory (the queue takes a bit). 

Onward once again!