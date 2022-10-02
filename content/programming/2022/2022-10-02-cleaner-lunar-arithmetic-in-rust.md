---
title: Cleaner Lunar Arithmetic in Rust
date: 2022-10-02
programming/languages:
- Rust
programming/topics:
- Mathematics
- OEIS
---
Another day, a slightly better way to implement {{<crosslink "Lunar Arithmetic in Rust">}}. Give the previous post a read if you need a quick refresher on what Lunar integers are. Otherwise, here are two better (I hope) ways to solve the same problem. 

<!--more--> 

Otherwise:

```rust
use core::cmp::{max, min};
use std::fmt;
use std::ops;
use itertools::{Itertools, EitherOrBoth::*};

#[derive(Debug)]
pub struct LunarInteger(Vec<u8>);

impl LunarInteger {
    pub fn new(n: u32) -> Self {
        let digits = n.to_string().chars().map(|d| d.to_digit(10).unwrap() as u8).rev().collect();
        Self(digits)
    }
    
    pub fn value(&self) -> u32 {
        self.0.iter().rev().map(|d| d.to_string()).collect::<String>().parse().unwrap()
    }
}

impl fmt::Display for LunarInteger {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        self.value().fmt(f)
    }
}

impl<'a, 'b> ops::Add<&'b LunarInteger> for &'a LunarInteger {
    type Output = LunarInteger;

    fn add(self, other: &'b LunarInteger) -> LunarInteger {
        // Iterate over digits of both from least to most significant 
        // If we have a digit from each, return the larger
        LunarInteger(self.0.iter().zip_longest(other.0.iter()).map(|pair| {
            match pair {
                Both(l, r)  => max(l, r),
                Left(l)     => l,
                Right(r)    => r,
            }
        }).copied().collect())
    }
}

impl<'a, 'b> ops::Mul<&'b LunarInteger> for &'a LunarInteger {
    type Output = LunarInteger;
    
    fn mul(self, other: &'b LunarInteger) -> LunarInteger {
        let mut sum = LunarInteger(vec![0; 1]);
    
        for (i, b) in other.0.iter().enumerate() {
            // Prefix with zeroes (digits are backwards)
            let mut digits: Vec<u8> = vec![0; i];
            
            // Add the multiplied values for this digit of other
            for a in self.0.iter() {
                digits.push(min(*a, *b));
            }
            
            // Add the the running sum
            sum = &sum + &LunarInteger(digits)
            
        }
        
        sum
    }
}
```

I think this is *significantly* cleaner. Still not sure if it's idiomatic, but it's not bad. 

This time around, rather than messing with keeping various structures of numbers and digits around, a `LunarInteger` is *always* a struct over a `vec` of digits (`u8`), specifically in *reverse order*. Since that's the order that addition and multiplication are actually implemented, it doesn't make sense to reverse them all of them time. Actually... this finally managed to make why you would want to deal with {{<wikipedia "little-endian">}} numbers... For all these years I just accepted it and moved on. 

We can construct them from a `u32` with `LunarInteger::new` and get the value with `LunarInteger::value`. Display then uses `value`, but otherwise remains mostly the same. 

This time around though, we're also going to tweak the function signatures of `Add` and `Mul` we're implementing. It has to be a train on a type... but that type can be a reference type. That works around a lot of the borrowing issues I've been dealing with previously. So instead of `Add<LunarInteger> for LunarInteger` we're on `Add<&LunarInteger> for &LunarInteger`. Thanks to [this StackOverflow answer](https://stackoverflow.com/a/28005283) for pointing me in the right direction. 

But... there's one more step. It's not strictly necessary, but it is nice. One thing you can (and I think often should) do in Rust is parameterize over the lifetime of variables. In this case, we can add any two Lunar integers so long as both exist while we're adding. It doesn't matter if they have the same or different lifetime outside of our function though. Thus: `impl<'a, 'b> ops::Mul<&'b LunarInteger> for &'a LunarInteger`

What that's saying is that for given lifetimes `'a` and `'b`, where `'a` is the lifetime of the left hand side / self and `'b` is the lifetime of the right hand side / other, implement add. 

Rust is weird. 

Powerful though. 

In any case, the rest is mostly the same, although I did also clean up multiplication. `vec![0; i]` creates a vector of `i` zeroes (possibly including no zeroes) and then adds the digits to them. Since we're storing the digits in reverse order, we have to add the zeroes first. Then sum them up directly (using the aforementioned `Add`) with all sorts of referencing and dereferencing and off we go!

It of course works:

```rust
fn main() {
  println!("{}", LunarInteger::new(8675309));
  
  let a = &LunarInteger::new(169);
  let b = &LunarInteger::new(248);
  let ra = a + b;
  println!("{} + {} = {}", a, b, ra);
  
  let rm = a * b;
  println!("{} * {} = {}", a, b, rm);
}

> 8675309
> 169 + 248 = 269
> 169 * 248 = 12468
```

Although I'm still not a fan of all of the `&` and `*` floating around, plus the fact that you can't just add `LunarInteger`s directly. 

But... can we do better? 

## Another option

Of course we can. :D The [second answer to the same StackOverflow post](https://stackoverflow.com/a/57021762) mentions a handy crate that actually does a lot of the 'magic' for implementing operators for you:

{{<doc rust impl_ops>}}

For this, you get a family of macros that let you implement one of the possible `OP` functions and you get all four for 'free':

* `&T op &U` - implement this one
* `&T op U` - free
* `T op &U` - free
* `T op U` - free

```rust
#[macro_use] extern crate impl_ops;
use std::ops;

#[derive(Debug)]
pub struct LunarInteger(Vec<u8>);

impl LunarInteger {
    pub fn new(n: u32) -> Self {
        let digits = n.to_string().chars().map(|d| d.to_digit(10).unwrap() as u8).rev().collect();
        Self(digits)
    }
    
    pub fn value(&self) -> u32 {
        self.0.iter().rev().map(|d| d.to_string()).collect::<String>().parse().unwrap()
    }
}

impl fmt::Display for LunarInteger {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        self.value().fmt(f)
    }
}

impl_op_ex!(+ |la: &LunarInteger, lb: &LunarInteger| -> LunarInteger {
    // Iterate over digits of both from least to most significant 
    // If we have a digit from each, return the larger
    LunarInteger(la.0.iter().zip_longest(lb.0.iter()).map(|pair| {
        match pair {
            Both(l, r)  => max(l, r),
            Left(l)     => l,
            Right(r)    => r,
        }
    }).copied().collect())
});

impl_op_ex!(* |la: &LunarInteger, lb: &LunarInteger| -> LunarInteger {
    let mut sum = LunarInteger(vec![0; 1]);

    for (i, b) in lb.0.iter().enumerate() {
        // Prefix with zeroes (digits are backwards)
        let mut digits: Vec<u8> = vec![0; i];
        
        // Add the multiplied values for this digit of other
        for a in la.0.iter() {
            digits.push(min(*a, *b));
        }
        
        // Add the the running sum
        sum = sum + LunarInteger(digits)
    }
    
    sum
});
```

I like it. :D 

```rust

fn main() {
  println!("{}", LunarInteger::new(8675309));
  
  let a = &LunarInteger::new(169);
  let b = &LunarInteger::new(248);
  let ra = a + b;
  println!("{} + {} = {}", a, b, ra);
  
  let rm = a * b;
  println!("{} * {} = {}", a, b, rm);
}

> 8675309
> 169 + 248 = 269
> 169 * 248 = 12468
```

Nice. 

Now... on to something else. Maybe in Rust, maybe not. We shall see!