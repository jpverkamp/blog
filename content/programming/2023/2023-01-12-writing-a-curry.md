---
title: Writing a curry! macro for MacroKata
date: 2023-01-12
programming/languages:
- Rust
programming/sources:
- macrokata
programming/topics:
- Rust
- Macros
- Compilers
---
Recently I've been wanting to learn more about macros in Rust. It was always one of my favorite parts of Racket, so let's see what we can do. 

In order to do that, I've been following the excellent [MacroKata](https://tfpk.github.io/macrokata/) series. It goes all the way through, starting with the very basics, adding in literals and expressions, handling repetition, nesting, and finally recursion. 

What I really want to talk about those is the one that I found most interesting: `curry!`.

<!--more-->

## Initial solution

The goal of this macro is to take something like: 

```rust
let add3 = curry!((a: i32) => (b: i32) => (c: i32) => _, {a + b + c})
```

And expand it to this:

```rust
let add3 = move |a: i32| {
    print_curried_argument(a);
    move |b: i32| {
        print_curried_argument(b);
        move |c: i32| {
            print_curried_argument(c);
            { a + b + c }
        }
    }
};
```

The `print_curried_argument` calls aren't at all necessary, but they do make the problem a bit more interesting.

In order to work through that, the first thing that I thought would be (of course) to define it recursively. We have the minimum required two cases:

* A base case that any problem can be reduced down to: the `_, { ... }` part
* A recursive case that can be reduced to a smaller problem: taking off the first `(var: type)` block

So let's write exactly that:

```rust
macro_rules! curry {
    // Base case: run the inner block
    (_, $block:block) => { $block };

    // Recursive case, unwrap one param:type and run it
    ( ($k:ident : $t:ty) => $($rest:tt)+ ) => {
        move |$k: $t| {
            print_curried_argument($k);
            curry!($($rest)*)
        }
    };
}
```

And that really is all you need... but what does it mean?

Well first, you're defining a macro named `curry`, so that's what `macro_rules! curry { ... }` does. After that, we have a series of patterns. The first pattern looks like this:

```rust
(_, $block:block)
```

In Rust macros, you can have either literal tokens (in this case, the literal tokens are `_` and `,`; you can have variables like `$block:block` where `$block` is the variable name and `block` is the type (`$b:block` is perhaps less confusing), or you can have repetition. We'll come back to that. 

After that, you have `=> { ... }` where you take the variables/structure in the first part and construct new code from it. In this case, that just means removing the `_, ` and keeping the `$block`.

The second case is slightly more interesting. We have all of these tokens:

* `(` - a literal opening paren
* `$k:ident` - a variable `$k` that must be a valid identifier
* `:` - a literal colon
* `$t:ty` - a variable `$t` that must be a valid type
* `)` - the closing paren
* `=>` - the literal fat arrow
* `$(...)+` - a repeated block, in this case the `+` means that there is one or more (it could also be regex style `?` or `*` for optional or zero plus)
  * `$rest:tt` - a 'token tree' called `$rest`, this can basically be anything; it's repeated because of the above

With that, all we need to do is use those variable to construct the following block:

```rust
move |$k: $t| {
    print_curried_argument($k);
    curry!($($rest)*)
}
```

This creates the closure (as expected) and then can actually call itself (`curry!`) with the same repetition syntax as before: `$($rest)*`. There are other things we can do with repetition, but for this case, we just repeat it directly. That will in turn call `curry` with slightly less in the parenthesis, so the recursion rules are satisfied and off we go. 

And exactly as expected:

```rust
$ cargo expand

let add3 = move |a: i32| {
    print_curried_argument(a);
    move |b: i32| {
        print_curried_argument(b);
        move |c: i32| {
            print_curried_argument(c);
            { a + b + c }
        }
    }
};
```

Nice.

## Shortening the syntax

But ... what if we want a slightly different syntax? Well I'm not thrilled with the current syntax we have with the `_` (unused, except as a sentinel) and extra `()` everywhere. So instead, what if we made it:

```rust
macro_rules! curry2 {
    ($block:block) => { $block };

    ( $k:ident : $t:ty => $($rest:tt)* ) => {
        move |$k: $t| {
            print_curried_argument($k);
            curry2!($($rest)*)
        }
    };
}
```

This way, as soon as we see a `block` only, we're done. Otherwise, we're expecting an `ident`, the literal `:`, a `ty`pe, and the fat arrow. 

```rust
let add3 = curry2!(a: i32 => b: i32 => c: i32 => {a + b + c});

// $ cargo expand 

let add3 = move |a: i32| {
    print_curried_argument(a);
    move |b: i32| {
        print_curried_argument(b);
        move |c: i32| {
            print_curried_argument(c);
            { a + b + c }
        }
    }
};
```

Nice!

## One more tweak

And finally, what if we wanted to get rid of the `=>` entirely. We could use `,` as we would in a function definition:

```rust
macro_rules! curry3 {
    ( $k:ident:$t:ty $block:block ) => {
        move |$k: $t| {
            print_curried_argument($k);
            $block 
        }
    };

    ( $k:ident:$t:ty, $($rest:tt)* ) => {
        move |$k: $t| {
            print_curried_argument($k);
            curry3!($($rest)*)
        }
    };
}
```

This one, I admit, is uglier. Because we don't have a `,` before the `block`, we have to specifically parse that case differently. We probably could instead have a second 'helper' macro, but this works out well enough. 

This allows us to write it this way:

```rust
let add3 = curry3!(a: i32, b: i32, c: i32 {a + b + c});

// $ cargo expand 

let add3 = move |a: i32| {
    print_curried_argument(a);
    move |b: i32| {
        print_curried_argument(b);
        move |c: i32| {
            print_curried_argument(c);
            { a + b + c }
        }
    }
};
```

Et voila. 

## Once more, with feeling

Okay fine, let's do the version that doesn't need the extra syntax (that way) and instead put it another way:

```rust
macro_rules! curry4 {
    ($block:block) => { $block };

    ( $k:ident : $t:ty, $($ks:ident : $ts:ty),+ $block:block ) => {
        move |$k: $t| {
            print_curried_argument(c);
            curry3!($($ks : $ts),+ $block)
        }
    };
}
```

So I guess it's confusing in a different way? At least the base case is the same as it was earlier. But this time, we're pushing the extra complexity into the `$rest` case. Now, it's `$($ks:ident : $ts:ty),+`, which means:

* `$(...),+` - a repeated block, one or more times (`+`) with `,` as the delimiter (that can be any literal value, but we are using `,` here), within the block:
  * `$ks:ident` - the variable for each pair, `$ks` because this is actually a list because of the repetition
  * `:` - the literal `:`
  * `$ts:ty` - the type for each, likewise

And then later, we expand it the same way with `$(ks : $ts),+`, saying put these back together with `,` delimiting them. 

I'm not sure it's better? But it's at least another way to write

Four ways to write a simple curried macro. I've done the full MacroKata series and I recommend you do the same. It's fascinating. Up next: procedural macros!