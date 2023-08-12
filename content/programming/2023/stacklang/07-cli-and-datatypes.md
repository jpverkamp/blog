---
title: "StackLang Part VII: New CLI and Datatypes"
date: '2023-08-05 23:59:00'
programming/languages:
- StackLang
programming/topics:
- Assemblers
- Compilers
- Memory
- Data Structures
- Stacks
- Virtual Machines
- Mathematics
- Memoization
- Caching
programming/sources:
- Project Euler
series:
- StackLang
---
Another day, another Stacklang!

{{< taxonomy-list "series" "StackLang" >}}

Today, we've got two main parts to work on:

{{<toc>}}


Full source code for StackLang: [github:jpverkamp/stacklang](https://github.com/jpverkamp/stacklang/)

## A new CLI

In a nutshell:

```bash
$ ./target/release/stacklang --help

The specific subcommands that can be run

Usage: stacklang [OPTIONS] <COMMAND>

Commands:
  vm       Run a StackLang program using the VM
  compile  Compile a StackLang program to C
  help     Print this message or the help of the given subcommand(s)

Options:
  -d, --debug
  -h, --help     Print help
  -V, --version  Print version

$ ./target/release/stacklang vm --help

Run a StackLang program using the VM

Usage: stacklang vm <PATH>

Arguments:
  <PATH>  Input filename

Options:
  -h, --help  Print help

$ ./target/release/stacklang compile --help

Compile a StackLang program to C

Usage: stacklang compile [OPTIONS] <PATH>

Arguments:
  <PATH>  Input filename

Options:
  -r, --run              Pass to compile (Clang) and automatically run
  -o, --output <OUTPUT>  Output filename, defaults to {path}.c
  -h, --help             Print help
```

I'd previously been using a [Justfile](/2023/07/12/stacklang-part-v-compiling-to-c/#justfile) to run more complicated examples, but something about that just doesn't feel right. 

Plus, there are different ways to run the different subsystems. For the interpreter/vm, really all you can do is choose the file to run (and possibly the `--debug` flag), while the compiler can also optionally specify an output filename (for the C file) and a flag to automatically invoke `clang` to compile the C and run the resulting executable. 

And also, although it's not done yet, I really want to add a `stacklang --test` harness that can take an `example/*.stack` file and run and compare the VM, compiler, and previous output as a way of testing that I didn't change anything as I refactor. 

So, how'd I do it? 

It's all down to [clap](https://docs.rs/clap/latest/clap/). I was already using it, but noway near to the level I could. 

Now, instead of a simple struct for parameters, I have:

```rust
// The top-level application
#[derive(Parser, Debug)]
#[clap(name = "stacklang", version = "0.1.0", author = "JP Verkamp")]
struct App {
    #[clap(flatten)]
    globals: GlobalArgs,

    #[clap(subcommand)]
    command: Command,
}

// Global arguments that apply to all subcommands
#[derive(Args, Debug)]
struct GlobalArgs {
    #[clap(long, short = 'd')]
    debug: bool,
}

/// The specific subcommands that can be run
#[derive(Subcommand, Debug)]
enum Command {
    #[clap(name = "vm", about = "Run a StackLang program using the VM")]
    Run {
        /// Input filename
        path: PathBuf,
    },

    #[clap(name = "compile", about = "Compile a StackLang program to C")]
    Compile {
        /// Pass to compile (Clang) and automatically run
        #[clap(long, short = 'r')]
        run: bool,

        /// Output filename, defaults to {path}.c
        #[clap(long, short = 'o')]
        output: Option<PathBuf>,

        /// Input filename
        path: PathBuf,
    },
}
```

First, `GlobalArgs` will be specified at the top level. So I can pass a `--debug` flag for either `vm`, `compile`, or anything I add. And then after that, `Command` is an `enum`. Each subcommand gets it's own data. 

And to use it is just as easy:

```rust
// Run specified subcommand
match args.command {
    Command::Run { path } => {
        let file = std::fs::File::open(path).unwrap();

        let tokens = lexer::tokenize(BufReader::new(file));
        log::info!("Tokens: {:#?}", tokens);

        let ast = parser::parse(tokens);
        log::info!("AST:\n{:#?}", ast);

        vm::evaluate(ast);
    }
    Command::Compile { run, output, path } => {
        let file = std::fs::File::open(path.clone()).unwrap();

        let tokens = lexer::tokenize(BufReader::new(file));
        log::info!("Tokens: {:#?}", tokens);

        let ast = parser::parse(tokens);
        log::info!("AST:\n{:#?}", ast);

        let c_code = compile_c::compile(ast);

        // Set output path if not specified
        let c_path = match output {
            Some(s) => s,
            None => {
                let mut c_path = path.clone();
                c_path.set_extension("c");
                c_path
            }
        };
        log::info!("Writing C code to {}", c_path.to_str().unwrap());
        std::fs::write(c_path.clone(), c_code).unwrap();

        // If run flag is set, compile and run
        if run {
            let exe_path = {
                let mut exe_path = c_path.clone();
                exe_path.set_extension("");
                exe_path
            };
            log::info!("Compiling C code to {}", exe_path.to_str().unwrap());

            let mut cmd = std::process::Command::new("clang");
            cmd.arg(c_path).arg("-o").arg(exe_path.clone());

            let status = cmd.status().unwrap();
            if !status.success() {
                panic!("clang failed");
            }

            let mut cmd = std::process::Command::new(exe_path);
            let status = cmd.status().unwrap();
            if !status.success() {
                panic!("program failed");
            }
        }
    }
}
```

Very cool. 

```bash

$ ./target/release/stacklang vm examples/factorial.stack

120

# Compiles to examples/factorial.c
$ ./target/release/stacklang compile examples/factorial.stack

$ cat examples/factorial.c

#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
...%

$ ./target/release/stacklang compile --run examples/factorial.stack

120
```

I'm going to have to see what I can do about a test harness (as mentioned). Perhaps next time!

## New datatypes (VM only; so far!)

On another note, I keep wanting to do more with StackLang. One thing that will help with that is more powerful datastructures! As a way to see how it's going, I decided to semi-randomly work out the solution to {{<crosslink "Project Euler">}} [problem 14](https://projecteuler.net/problem=14): Find the number under 1 million with the longest {{<wikipedia "Collatz Sequence">}}. 

It's not a particularly hard problem to just directly crunch numbers on, but you can save an awful lot of time by caching/{{<wikipedia "memoizing">}} the results. In a nutshell: the first time you calculate a specific Collatz length, store it in a data structure for later.

The best options for this storage? A {{<wikipedia "hashmap">}} or a vector!

### Hash

I ended up adding two Hash types: `Hash` and `IntHash`:

```rust
/// A value is a literal value that has been evaluated.
#[derive(Clone, Debug, PartialEq, Eq)]
#[repr(u8)]
pub enum Value {
    ...
    Hash(Rc<RefCell<HashMap<String, Value>>>),
    IntHash(Rc<RefCell<HashMap<i64, Value>>>),
}
```

This primarily relates to the key. I wrote the `String` version first, but I don't actually want `Strings` for this problem, I want an `int -> int` Hash. Ergo `IntHash`. 

It's a bit wacky looking with `Rc<RefCell<HashMap<...>>>`, but that's for a reason I've mentioned before: because I `clone` values fairly often, if I don't have a `Rc`, I'll end up to references to new, copied `HashMap`. Besides being slow to copy values, it's not actually correct. We'll never write anything to somewhere we can read. `RefCell` then works to actually let us `mut` the value in the `Rc`. Fairly standard (if weird looking) Rust. 

With the value written, I need to be able to print them:

```rust

impl Display for Value {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(
            f,
            "{}",
            match self {
                ...
                Value::Hash(v) => {
                    format!(
                        "Hash<{}>",
                        v.clone()
                            .borrow()
                            .iter()
                            .map(|(k, v)| format!("{}:{}", k, v))
                            .collect::<Vec<String>>()
                            .join(", ")
                    )
                }
                ...
            }
        )
    }
}
```

And finally, some library functions:

* `make-hash -> {hash}`: create a new empty (string) hash
* `make-int-hash -> {hash}`: create an empty integer keyed hash
* `hash-has? {hash} {key} -> {boolean}`: checks if a key is in a hash
* `hash-ref {hash} {key} -> {value}`: read a value from a hash
* `hash-set! {hash} {key} {value}`: update a hash at a specific key (or set the value if not previously defined)

I'm not going to share the entire code here, it's a bit repetitive. But for the most part, it was pretty straight forward to add. I really will want to be adding libraries and import statements (and a standard library?) at some point. 

But you can see the entire code for hashes [here](https://github.com/jpverkamp/stacklang/blob/ffab86f8a3a3d2b27bca4afd6b4270e2b9ffbadf/src/vm.rs#L466-L554). 

It's relying pretty heavily on the Rust `HashMap` type under the hood, which since C doesn't have one of those in the standard libraries is going to make porting this to the compiler interesting. We'll see how I end up handling this. 

Here's my very very basic `example` for `hash.stack`:

```text
make-hash @h

h "x" 5 hash-set!
h "y" 6 hash-set!

h writeln
h "x" hash-get

h "x" 7 hash-set!
h writeln%
```

And running it:

```bash
$ ./target/release/stacklang vm examples/hash.stack

Hash<x:5, y:6>
Hash<x:7, y:6>
```

### ~~List~~ Stack

Edit: Turns out... these are stacks. And the language is named StackLang. :smile:

Next up, stacks! Basically, Python style lists / Rust style `vec`! Basically, a data structure that has a fixed current size, allows for quick `push` and `pop` at the end of the list and also `get` and `set` at a specific index. 

Something like this:

* `make-stack -> {stack}`: makes an empty stack
* `stack-length {stack} -> {integer}`: gets the length
* `stack-push! {stack} {value}`: pushes to the end of the stack
* `stack-pop! {stack} -> {value}`: pops off the end of the stack
* `stack-ref {stack} {index} -> {value}`: gets the value at a specific index
* `stack-set! {stack} {index} {value}`: sets a value within the stack

Implementation details [here](https://github.com/jpverkamp/stacklang/blob/5984da1606757b2f1450396ea90f9d1bf9b1c2bb/src/vm.rs#L243-L302). 


#### List/Stack literals

While I was working on stacks, one thing that I've been meaning to add to the language is `Stack` literals:

```text
[ 1 2 3 ] @l

l writeln
```

We're already lexing and parsing them, we just need to actually evaluate them when we see them:

```rust
// List expressions are parsed into Stack values
Expression::List(children) => {
    let mut values = vec![];
    for node in children {
        eval(node, stack);
        values.push(stack.pop().unwrap());
    }
    stack.push(Value::Stack(Rc::new(RefCell::new(values))));
}
```

That really is it. And we can put all sorts of interesting things in them... like blocks! See [the implementation of cond below](#cond-statements). 

One weirdness is that the expression is still a 'list', but the datatype / value is a Stack. Weirdness, but it works fine. 

#### Examples

Here's my very basic `example` code for `list.stack`:

```text
[ 1 2 3 ] @l

l writeln

l stack-pop! writeln
l writeln

l 5 stack-push!
l writeln

l 1 stack-ref writeln
```

I know it doesn't actually use `make-stack`, but it doesn't have to! `[]` ends up equivalent to that. 

Running it:

```bash
$ ./target/release/stacklang vm examples/list.stack

[1, 2, 3]
3
[1, 2]
[1, 2, 5]
2
```

This one is much easier (for me at least) to implement by hand, although there are some neat performance tricks I'll have to be aware of. Basically, allocate some initial amount of memory. If we ever try to `push` past it, allocate a new, larger chunk, and copy the data over. Other than that, we should be pretty much good to go. 

We'll give it a try, but not just yet. 

### Cond statements

Speaking of lists/stacks, one thing that I've been finding annoying is a constant use of nested `if` statements. They're a bit more verbose than many languages, so nesting them is even more annoying that it should be. 

What if we could make a cleaner syntax for a whole list of `cond`itionals? 

```text
{
  @n

  [
    # Base case
    { @0 !1 n 1 <= } 1
    
    # If n is even, divide by 2
    { @0 !1 n 2 % 0 = } { @0 !1 n 2 / collatz-length 1 + }
    
    # Default: If n is odd, multiply by 3 and add 1
    { @0 !1 n 3 * 1 + collatz-length 1 +}
  ] cond
  @l

  l
} @collatz-length
```

In this case, we have three branches:

* `n <= 1`: return 1
* `n is even`: return `1 + collatz-length(n / 2)`
* `n is odd`: return `1 + collatz-length(3 * n + 1)`

And that's exactly what the `cond` statement does. In the specification, it takes exactly an odd number of expressions in a list: some number of pairs of test/value and then a default. Something like this: `[test1 value1 test2 value2 ... default]`.

To evaluate it, run `test1` (this should always be a block). If it's true and `value1` is a block, evaluate and return it. If `value1` is a value, just return it. If `test1` evaluates to false, continue down the line. If no `test` is true, evaluate/return `default`. 

The code for it... well, it's a bit of a thing, mostly to deal with the 'if it's a block, run it; if not, return it' thing. I do need to abstract that. 

[Here is](https://github.com/jpverkamp/stacklang/blob/0c878415a10879e98be2f0bc8259f88904646a07/src/vm.rs#L243-L321) the full (slightly ugly) code for `cond`. 

### Project Euler: Problem 14

Now that we have all that, let's solve Project Euler Problem 14! As mentioned, we want to find the value up to one million that leads to the longest Collatz sequence. 

#### With HashMap

First, storing the cached values in an `IntHash`:

```text
# https://projecteuler.net/problem=14
# Which starting number, under one million, produces the longest Collatz chain?

1000000 @bound

make-int-hash @cache
cache 1 1 hash-set!

{
  @n

  [
    # Already cached
    { @0 !1 cache n hash-has? } { @0 !1 cache n hash-get }
    
    # If n is even, divide by 2
    { @0 !1 n 2 % 0 = } { @0 !1 n 2 / collatz-length 1 + }
    
    # Default: If n is odd, multiply by 3 and add 1
    { @0 !1 n 3 * 1 + collatz-length 1 +}
  ] cond
  @l

  cache n l hash-set!
  l
} @collatz-length

# Store best value so far
make-hash @results
results "best-v" 1 hash-set!
results "best-l" 1 hash-set!

# Store best value so far
1 @best-v
1 @best-l

# Check each value under 1 million
{
  @v !0
  v 1 + !v
  v collatz-length @l

  {
    @0 !0
    v !best-v
    l !best-l

    "new best: " write
    v write
    " -> " write
    l writeln
  } 
  { @0 !0 }
  l best-l > if
} bound loop

best-v writeln
```

Hopefully it's commented fairly well. But essentially what we want to do is define `collatz-length` to recursively (and with memoization) calculate the length at any arbitrary value and then run a `loop` from 1 to 1,000,000, tracking the best value seen:

```bash
$ ./target/release/stacklang vm examples/euler-14-cond.stack

new best: 2 -> 2
new best: 3 -> 8
new best: 6 -> 9
new best: 7 -> 17
new best: 9 -> 20
...
new best: 626331 -> 509
new best: 837799 -> 525
837799
```

It's not by any stretch of the imagination *fast*. About 45 seconds on my machine. I can do better! That's what I'm hoping to do with compiling... if I can figure out the hash thing. 

But it *is* functional. And I think the code isn't actually that bad. One thing I really do need to clean up is the `@0 !1` and the like I have to currently put everywhere to do the arity checks... Perhaps when I get proper type checking? 

#### With Stacks

And finally, because it's something that I'm more confident in building into the compiler, the same code with a `Stack`:

```text
# https://projecteuler.net/problem=14
# Which starting number, under one million, produces the longest Collatz chain?

1000000 @bound

make-stack @cache
cache 1 stack-push! 
cache 1 stack-push! 

{
  @n

  # Extend the cache if needed
  n cache stack-length - 2 + @extension
  { 
    @0 !0
    { 
      @0 !0
      cache 0 stack-push! 
    } extension loop 
    "extended cache by " write extension writeln
  }
  { @0 !0 }
  extension 0 > if

  [
    # Already cached
    { @0 !1 cache n stack-ref 0 > } { @0 !1 cache n stack-ref }

    # Base case
    { @0 !1 n 1 <= } 1
    
    # If n is even, divide by 2
    { @0 !1 n 2 % 0 = } { @0 !1 n 2 / collatz-length 1 + }
    
    # Default: If n is odd, multiply by 3 and add 1
    { @0 !1 n 3 * 1 + collatz-length 1 +}
  ] cond
  @l

  cache n l stack-set!
  l
} @collatz-length

# Store best value so far
1 @best-v
1 @best-l

# Check each value under 1 million
{
  @v !0
  v 1 + !v
  v collatz-length @l

  {
    @0 !0
    v !best-v
    l !best-l

    "new best: " write
    v write
    " -> " write
    l writeln
  } 
  { @0 !0 }
  l best-l > if
} bound loop

best-v writeln
```

The main difference here is the 'Extend the cache if needed' section. Basically, if the current `stack` isn't long enough to store the value we're going to add to it, push values until it is. This isn't at all efficient, but for the moment, it at least works:

```bash
$ ./target/release/stacklang vm examples/euler-14-list.stack

extended cache by 1 to 1
extended cache by 1 to 2
new best: 2 -> 2
extended cache by 1 to 3
extended cache by 7 to 10
extended cache by 6 to 16
new best: 3 -> 8
new best: 6 -> 9
extended cache by 6 to 22
extended cache by 12 to 34
extended cache by 18 to 52
new best: 7 -> 17
new best: 9 -> 20
extended cache by 18 to 70
extended cache by 36 to 106
extended cache by 54 to 160
new best: 18 -> 21
new best: 25 -> 24
extended cache by 54 to 214
extended cache by 108 to 322
extended cache by 162 to 484
extended cache by 216 to 700
extended cache by 90 to 790
extended cache by 396 to 1186
extended cache by 594 to 1780
extended cache by 378 to 2158
extended cache by 1080 to 3238
extended cache by 1620 to 4858
extended cache by 2430 to 7288
extended cache by 1944 to 9232
new best: 27 -> 112
new best: 54 -> 113
new best: 73 -> 116
new best: 97 -> 119
97
```

For small values of `bound` :smile:

When we get to larger values, the values go way up before they come back down. It may only be 500 or so elements in the chain, but if we have to allocate space for everything? 

You can see it above, even in the first 100 values, we're already maxing out over 9000. (heh)

