---
title: Lunar Arithmetic in Rust
date: 2022-09-21
programming/languages:
- Rust
programming/topics:
- Mathematics
- OEIS
---
I've been playing with various languages / language design a lot recently (inspired by my [Runelang series](/series/runelang-in-the-browser/)). As I tweak and change what I'd like to implement in a language... I kept finding myself coming back to more or less exactly how Rust looks (albeit without the borrowing). So... that seems like a pretty good reason to start picking up some Rust. 

In another thread of thought, I stumbled upon two OEIS (on-line encyclopedia of integer sequences) sequences: [A087061: Array T(n,k) = lunar sum n+k (n >= 0, k >= 0) read by antidiagonals](https://oeis.org/A087061) and [A087062: Array T(n,k) = lunar product n*k (n >= 1, k >= 1) read by antidiagonals](https://oeis.org/A087062). Seemed like a fun bit of esoteric math to play with. 

So... let's combine them!

(Warning: I have very little idea what I'm doing. That's sort of the point. :D Happy to chat if you have better ways I could have done this!)

## Defining Lunar Integers

So both of these sequences resolve around Lunar numbers (apparently previously called dismal numbers, but it was too depressing?). In essence, Lunar numbers are Integers, but addition and multiplication are defined differently. Specifically:

### Addition: when adding `A + B`, for each digit `a` and `b`, the resulting digit is `max(a, b)`

```text
  169
+ 248
-----
  269 
```

### Multiplication: when multiplying `A * B`, for each digit `b` in `B`, take `min(a, b) for a in A`; add those resulting values as above

```text
    169
  x 248
  -----
    168
   144
+ 122
-------
  12468 
```

Weird. Probably useless. But interesting! Let's implement them. 

## LunarInteger type

First, a new type. If we're going to implement the addition and multiplication operators in Rust, this is probably the best way to do it. Our `LunarInteger` struct is simple: just a single `u32` value (would signed `LunarInteger`s make sense? maybe a question for another day). We'll go ahead and give it `Debug`, since that makes early printing easier. 

```rust
#[derive(Debug)]
pub struct LunarInteger(u32);
```

Easy enough:

```rust
> println!("{:?}", LunarInteger(169));
LunarInteger(169)
```

But what if we want a slightly fancier way to print it? Well, I'll admit I went down something of a rabbit hole here... I knew that I needed to implement `Display`, but when I tried the basic idea I had, it didn't respect width:

```rust
impl fmt::Display for LunarInteger {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        write!(f, "{} 🌘", self.0)
    }
}
```

Apparently, what I need to do (or at least one way to do it) is to take the original formatter to write the number `and_then` apply the moon:

```rust
impl fmt::Display for LunarInteger {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        self.0.fmt(f).and_then(|_| write!(f, "🌘"))
    }
}
```

Weird, but sure. 


```rust
println!("{}", LunarInteger(169));
> 169🌘
```

Fun. And *totally* worth doing. 

## Splitting to digits

The next thing that we'll need to do is some way of converting a `LunarInteger` to digits, so that we can work with those one by one. There are a couple ways to deal with this, but here's what I ended up with:

```rust
fn integer_to_digits(n: u32) -> Vec<u32> {
    n.to_string()
        .chars()
        .map(|d| d.to_digit(10).unwrap())
        .collect()
}

fn digits_to_integer(ls: Vec<u32>) -> u32 {
    ls.iter()
        .map(|d| d.to_string())
        .collect::<String>()
        .parse()
        .unwrap()
}
```

It's not actually specific to `LunarInteger`, but that's fine. It works:

```rust
println!("{:?}", integer_to_digits(8675309));
> [8, 6, 7, 5, 3, 0, 9]

println!("{:?}", digits_to_integer([8, 6, 7, 5, 3, 0, 9].to_vec()));
> 8675309
```

## Defining addition

Okay, we have all the pieces we need, let's actually define one of our operations. We need addition for multiplication, so that's the place to start!

To make `+` work, 'all' we have to do is implement `ops::Add` on `LunarInteger`. Give it an `Output` type and define the `add` function. Piece of cake? 

```rust
impl ops::Add<LunarInteger> for LunarInteger {
    type Output = Self;

    fn add(self, rhs: LunarInteger) -> LunarInteger {
        let lhs_digits = integer_to_digits(self.0).into_iter().rev();
        let rhs_digits = integer_to_digits(rhs.0).into_iter().rev();

        // Iterate over digits of both from least to most significant
        // If we have a digit from each, return the larger
        let result_digits = lhs_digits.zip_longest(rhs_digits).map(|pair| match pair {
            Both(l, r) => max(l, r),
            Left(l) => l,
            Right(r) => r,
        });

        let result = digits_to_integer(result_digits.rev().collect());
        LunarInteger(result)
    }
}
```

This actually ended up fairly functional. Because we want to deal with the digits in reverse order (from least to most significant), we'll `into_iter` (still getting the difference there into my head) and then `rev` it before `zip`ing the two together. I do specifically need `zip_longest` rather than `zip` since the former will properly deal with numbers of different widths while the latter will truncate. Not at all what we want. It does need the `itertools` dependency, but that's fair. 

So with that, we either have `Both` digits--take the `max`--or either a digit from the `Left` or `Right`--take the one we have. Apply that across the numbers and put it back together and *bam*. Addition. 

```rust
let a = LunarInteger(169);
let b = LunarInteger(248);
let ra = a + b;
println!("{} + {} = {}", a, b, ra);

> error[E0382]: borrow of moved value: `a`
>   --> src/main.rs:86:30
>    |
> 83 |     let a = LunarInteger(169);
>    |         - move occurs because `a` has type `LunarInteger`, which does not implement the `Copy` trait
> 84 |     let b = LunarInteger(248);
> 85 |     let ra = a + b;
>    |              ----- `a` moved due to usage in operator
> 86 |     println!("{} + {} = {}", a, b, ra);
>    |                              ^ value borrowed here after move
>    |
> note: calling this operator moves the left-hand side
```

Hmm. That's not great. Luckily, the Rust compiler is really quite good at telling you how to fix things (once you get used to it). Update our struct to include `#[derive(Copy, Clone, Debug)]` and:

```rust
> let a = LunarInteger(169);
> let b = LunarInteger(248);
> let ra = a + b;
> println!("{} + {} = {}", a, b, ra);

169🌘 + 248🌘 = 269🌘
```

Nice!

## Defining multiplication

On to multiplication! This one I tried *so long* to get working in a functional way. But unfortunately, there seems to be a number of gotchas around the borrow checker and closures (the closure take ownership of the values it closes over, so you can't use them in the outer function safely any more), so I ended up implementing this one rather more traditionally:


```rust
impl ops::Mul<LunarInteger> for LunarInteger {
    type Output = Self;

    fn mul(self, rhs: LunarInteger) -> LunarInteger {
        let lhs_digits: Vec<u32> = integer_to_digits(self.0).into_iter().rev().collect();
        let rhs_digits: Vec<u32> = integer_to_digits(rhs.0).into_iter().rev().collect();

		// Collect the `values` of each digit * the lhs 
        let mut values = Vec::new();
        for (i, rd) in rhs_digits.iter().enumerate() {
            // Multiply one digit by the entire lhs
            let mut digits: Vec<u32> = Vec::new();
            for ld in lhs_digits.iter() {
                digits.push(*min(rd, &ld));
            }

			// Convert back to a LunarInteger, offset 1, 10, 100, etc
            let value = LunarInteger(
                digits_to_integer(digits.into_iter().rev().collect())
                * 10_u32.pow(i as u32)
            );

            values.push(value);
        }

		// Add the values together using the previous `Add` functionality
        let mut result = LunarInteger(0);
        for value in values {
            result = result + value;
        }

        result
    }
}
```

First, we convert to digits. Then, we create a vector of `values`. Each of these will be one of the rows of multiplied values that we have to add together later. The `let mut digits` bit does the actual multiplication (with `min`) and `... * 10_u32.pow(i as u32)` takes the result and multiplies by `1, 10, 100, 1000...` as each place value increases. Originally, I was appending a vector of an increasing number of zeroes before the `digits_to_integer` conversion. But again: borrow checker issues. I'm ... going to have to wrap my head around that. Which is sort of the point of Rust I suppose. 

But having this in place... it just works(tm):

```rust
let a = LunarInteger(169);
let b = LunarInteger(248);
let rm = a * b;
println!("{} * {} = {}", a, b, rm);

> 169🌘 * 248🌘 = 12468🌘
```

Not bad.

## Results

Okay, the moment we've all been waiting for! Actually printing the [A087061](https://oeis.org/A087061) and [A087062](https://oeis.org/A087062) sequence! Mostly, it's a matter of printing and formatting. And... after all that work to get `Display` fancy, the moons are just too noisy, so I'm only printing the underlying integers after all. C'est la vie. 

```rust
println!("Addition table");
for i in 0..20 {
	for j in 0..20 {
		let li = LunarInteger(i);
		let lj = LunarInteger(j);
		let lr = li + lj;

		print!("{:4}", lr.0);
	}
	println!();
}
println!();

> Addition table
>    0   1   2   3   4   5   6   7   8   9  10  11  12  13  14  15  16  17  18  19
>    1   1   2   3   4   5   6   7   8   9  11  11  12  13  14  15  16  17  18  19
>    2   2   2   3   4   5   6   7   8   9  12  12  12  13  14  15  16  17  18  19
>    3   3   3   3   4   5   6   7   8   9  13  13  13  13  14  15  16  17  18  19
>    4   4   4   4   4   5   6   7   8   9  14  14  14  14  14  15  16  17  18  19
>    5   5   5   5   5   5   6   7   8   9  15  15  15  15  15  15  16  17  18  19
>    6   6   6   6   6   6   6   7   8   9  16  16  16  16  16  16  16  17  18  19
>    7   7   7   7   7   7   7   7   8   9  17  17  17  17  17  17  17  17  18  19
>    8   8   8   8   8   8   8   8   8   9  18  18  18  18  18  18  18  18  18  19
>    9   9   9   9   9   9   9   9   9   9  19  19  19  19  19  19  19  19  19  19
>   10  11  12  13  14  15  16  17  18  19  10  11  12  13  14  15  16  17  18  19
>   11  11  12  13  14  15  16  17  18  19  11  11  12  13  14  15  16  17  18  19
>   12  12  12  13  14  15  16  17  18  19  12  12  12  13  14  15  16  17  18  19
>   13  13  13  13  14  15  16  17  18  19  13  13  13  13  14  15  16  17  18  19
>   14  14  14  14  14  15  16  17  18  19  14  14  14  14  14  15  16  17  18  19
>   15  15  15  15  15  15  16  17  18  19  15  15  15  15  15  15  16  17  18  19
>   16  16  16  16  16  16  16  17  18  19  16  16  16  16  16  16  16  17  18  19
>   17  17  17  17  17  17  17  17  18  19  17  17  17  17  17  17  17  17  18  19
>   18  18  18  18  18  18  18  18  18  19  18  18  18  18  18  18  18  18  18  19
>   19  19  19  19  19  19  19  19  19  19  19  19  19  19  19  19  19  19  19  19

println!("Addition sequence (A087061)");
let mut i = 0;
let mut j = 0;
for _ in 0..100 {
	let li = LunarInteger(i);
	let lj = LunarInteger(j);
	let lr = li + lj;

	print!("{} ", lr.0);

	if j == 0 {
		j = i + 1;
		i = 0;
	} else {
		j -= 1;
		i += 1;
	}
}
println!("\n");

> Addition sequence (A087061)
> 0 1 1 2 1 2 3 2 2 3 4 3 2 3 4 5 4 3 3 4 5 6 5 4 3 4 5 6 7 6 5 4 4 5 6 7 8 7 6 5 4 5 6 7 8 9 8 7 6 5 5 6 7 8 9 10 9 8 7 6 5 6 7 8 9 10 11 11 9 8 7 6 6 7 8 9 11 11 12 11 12 9 8 7 6 7 8 9 12 11 12 13 12 12 13 9 8 7 7 8

println!("Multiplication table");
for i in 0..20 {
	for j in 0..20 {
		let li = LunarInteger(i + 1);
		let lj = LunarInteger(j + 1);
		let lr = li * lj;

		print!("{:4}", lr.0);
	}
	println!();
}
println!();

> Multiplication table
>    1   1   1   1   1   1   1   1   1  10  11  11  11  11  11  11  11  11  11  10
>    1   2   2   2   2   2   2   2   2  10  11  12  12  12  12  12  12  12  12  20
>    1   2   3   3   3   3   3   3   3  10  11  12  13  13  13  13  13  13  13  20
>    1   2   3   4   4   4   4   4   4  10  11  12  13  14  14  14  14  14  14  20
>    1   2   3   4   5   5   5   5   5  10  11  12  13  14  15  15  15  15  15  20
>    1   2   3   4   5   6   6   6   6  10  11  12  13  14  15  16  16  16  16  20
>    1   2   3   4   5   6   7   7   7  10  11  12  13  14  15  16  17  17  17  20
>    1   2   3   4   5   6   7   8   8  10  11  12  13  14  15  16  17  18  18  20
>    1   2   3   4   5   6   7   8   9  10  11  12  13  14  15  16  17  18  19  20
>   10  10  10  10  10  10  10  10  10 100 110 110 110 110 110 110 110 110 110 100
>   11  11  11  11  11  11  11  11  11 110 111 111 111 111 111 111 111 111 111 110
>   11  12  12  12  12  12  12  12  12 110 111 112 112 112 112 112 112 112 112 120
>   11  12  13  13  13  13  13  13  13 110 111 112 113 113 113 113 113 113 113 120
>   11  12  13  14  14  14  14  14  14 110 111 112 113 114 114 114 114 114 114 120
>   11  12  13  14  15  15  15  15  15 110 111 112 113 114 115 115 115 115 115 120
>   11  12  13  14  15  16  16  16  16 110 111 112 113 114 115 116 116 116 116 120
>   11  12  13  14  15  16  17  17  17 110 111 112 113 114 115 116 117 117 117 120
>   11  12  13  14  15  16  17  18  18 110 111 112 113 114 115 116 117 118 118 120
>   11  12  13  14  15  16  17  18  19 110 111 112 113 114 115 116 117 118 119 120
>   10  20  20  20  20  20  20  20  20 100 110 120 120 120 120 120 120 120 120 200

println!("Multiplication sequence (A087062)");
let mut i = 0;
let mut j = 0;
for _ in 0..100 {
	let li = LunarInteger(i + 1);
	let lj = LunarInteger(j + 1);
	let lr = li * lj;

	print!("{} ", lr.0);

	if j == 0 {
		j = i + 1;
		i = 0;
	} else {
		j -= 1;
		i += 1;
	}
}
println!("\n");

> Multiplication sequence (A087062)
> 1 1 1 1 2 1 1 2 2 1 1 2 3 2 1 1 2 3 3 2 1 1 2 3 4 3 2 1 1 2 3 4 4 3 2 1 1 2 3 4 5 4 3 2 1 10 2 3 4 5 5 4 3 2 10 11 10 3 4 5 6 5 4 3 10 11 11 11 10 4 5 6 6 5 4 10 11 11 11 12 11 10 5 6 7 6 5 10 11 12 11 11 12 12 11 10 6 7 7 6
```

Checking against the sequences... good to go! Awesome. 

Okay, now I need to find my next Rust problem to solve :D. 