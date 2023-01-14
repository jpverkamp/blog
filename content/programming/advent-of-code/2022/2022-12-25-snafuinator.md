---
title: "AoC 2022 Day 25: Snafuinator"
date: 2022-12-25 00:00:03
programming/languages:
- Rust
programming/sources:
- Advent of Code
series:
- Advent of Code 2022
programming/topics:
- Algorithms
- Numeral Systems
- Base 5
---
## Source: [Full of Hot Air](https://adventofcode.com/2022/day/25)

## Part 1

> Let a Snafu number be a base 5 number with the curious property that in addition to the digits 0, 1, and 2, it has the numbers `-` as `-1` and `=` as `-2`. Sum up a list of Snafu numbers. 

<!--more-->

:blink: Sure!

```rust
#[derive(Clone, Debug)]
struct Snafu {
    value: String,
}

impl Display for Snafu {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{}", self.value)
    }
}

impl From<String> for Snafu {
    fn from(value: String) -> Self {
        Snafu { value }
    }
}

impl From<isize> for Snafu {
    fn from(mut v: isize) -> Self {
        // Convert to base 5
        let mut digits = Vec::new();

        while v > 0 {
            let m = v % 5;
            v = v / 5;

            if m < 3 {
                digits.push(m.to_string());
            } else if m == 3 {
                digits.push(String::from("="));
                v += 1;
            } else if m == 4 {
                digits.push(String::from("-"));
                v += 1;
            }
        }

        Snafu {
            value: digits.into_iter().rev().collect::<Vec<_>>().join(""),
        }
    }
}

impl Into<isize> for Snafu {
    fn into(self) -> isize {
        self.value.chars().fold(0, |a, c| match c {
            '2' | '1' | '0' => a * 5 + c.to_digit(10).unwrap() as isize,
            '-' => a * 5 - 1,
            '=' => a * 5 - 2,
            _ => panic!("Snafu SNAFUed, what the Snafu is a {c}"),
        })
    }
}
```

The main complication is that when you're doing the normal base conversion, if you ever see a `3` or `4`, you instead need to 'borrow' one from the next round (thus the `v += 1`) and write up `=` or `-` instead. Other than that, pretty standard stuff. 

To sum them:

```rust
fn part1(filename: &Path) -> String {
    Snafu::from(
        iter_lines(filename)
            .map(Snafu::from)
            .map::<isize, _>(Snafu::into)
            .sum::<isize>(),
    )
    .to_string()
}
```

Elegant. It's interesting that I can specify the `B` type on `Map<B, F>` to let `rustc` know that `Snafu::into` is making a `Snafu` `From` an `isize`. I just wish I knw the syntax for chaining the `Shafu::from` on the end instead. But it's all good. 

## Performance

```bash
./target/release/25-snafuinator 1 data/25.txt

2-10==12-122-=1-1-22
took 504µs
```

Yeah. :smile:

## Full timing

As always, no part 2. So here is my full timing (using the test suite) for the year:

```bash
cargo test --release

   Compiling aoc2022 v0.1.0 (/Users/jp/Projects/advent-of-code/2022)
    Finished release [optimized] target(s) in 1.02s
     Running unittests src/lib.rs (target/release/deps/aoc-765a7ec64a9447a7)

running 0 tests

test result: ok. 0 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s

     Running unittests src/bin/01-calorinator.rs (target/release/deps/01_calorinator-1f1c805958dd23b8)

running 2 tests
test tests::test1 ... ok
test tests::test2 ... ok

test result: ok. 2 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s

     Running unittests src/bin/02-roshamboinator.rs (target/release/deps/02_roshamboinator-980fde3a10149cf7)

running 2 tests
test tests::test2 ... ok
test tests::test1 ... ok

test result: ok. 2 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s

     Running unittests src/bin/03-rucksackinator.rs (target/release/deps/03_rucksackinator-06ca807af3141647)

running 2 tests
test tests::test1 ... ok
test tests::test2 ... ok

test result: ok. 2 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s

     Running unittests src/bin/04-overlapinator.rs (target/release/deps/04_overlapinator-605c0b425fd7871c)

running 2 tests
test tests::test1 ... ok
test tests::test2 ... ok

test result: ok. 2 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s

     Running unittests src/bin/05-stackinator.rs (target/release/deps/05_stackinator-66d6530baf949543)

running 2 tests
test tests::test1 ... ok
test tests::test2 ... ok

test result: ok. 2 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s

     Running unittests src/bin/06-ring-bufferinator.rs (target/release/deps/06_ring_bufferinator-9d8aaf21068f434f)

running 2 tests
test tests::test1 ... ok
test tests::test2 ... ok

test result: ok. 2 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s

     Running unittests src/bin/07-recursive-fileinator.rs (target/release/deps/07_recursive_fileinator-3c23b188905ff2f3)

running 2 tests
test tests::test1 ... ok
test tests::test2 ... ok

test result: ok. 2 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s

     Running unittests src/bin/08-treetopinator.rs (target/release/deps/08_treetopinator-b34eba0cef22ee66)

running 2 tests
test tests::test1 ... ok
test tests::test2 ... ok

test result: ok. 2 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s

     Running unittests src/bin/09-ropeinator.rs (target/release/deps/09_ropeinator-f6aaadbab186c375)

running 2 tests
test tests::test1 ... ok
test tests::test2 ... ok

test result: ok. 2 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s

     Running unittests src/bin/10-interpretator.rs (target/release/deps/10_interpretator-9755dd8dca096910)

running 2 tests
test tests::test1 ... ok
test tests::test2 ... ok

test result: ok. 2 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s

     Running unittests src/bin/11-monkeyator.rs (target/release/deps/11_monkeyator-06c0acc568da6f84)

running 2 tests
test tests::test1 ... ok
test tests::test2 ... ok

test result: ok. 2 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.01s

     Running unittests src/bin/12-climbinator.rs (target/release/deps/12_climbinator-811044ca1816810b)

running 2 tests
test tests::test1 ... ok
test tests::test2 ... ok

test result: ok. 2 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s

     Running unittests src/bin/13-list-parsinator.rs (target/release/deps/13_list_parsinator-6d04b8aac551bc53)

running 2 tests
test tests::test1 ... ok
test tests::test2 ... ok

test result: ok. 2 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s

     Running unittests src/bin/14-sandinator.rs (target/release/deps/14_sandinator-f5710a23d9c407e4)

running 2 tests
test tests::test1 ... ok
test tests::test2 ... ok

test result: ok. 2 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.66s

     Running unittests src/bin/15-beaconator.rs (target/release/deps/15_beaconator-2f9f931b8c2ba954)

running 2 tests
test tests::test1 ... ok
test tests::test2 ... ok

test result: ok. 2 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.68s

     Running unittests src/bin/16-pressurinator.rs (target/release/deps/16_pressurinator-5d4814b12d55a973)

running 2 tests
test tests::test1 ... ok
test tests::test2 ... ok

test result: ok. 2 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 12.56s

     Running unittests src/bin/17-tetrisinator.rs (target/release/deps/17_tetrisinator-041bdd7b4e2867a3)

running 2 tests
test tests::test1 ... ok
test tests::test2 ... ok

test result: ok. 2 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 1.39s

     Running unittests src/bin/18-lavinator.rs (target/release/deps/18_lavinator-cd56e7905a199c99)

running 2 tests
test tests::test1 ... ok
test tests::test2 ... ok

test result: ok. 2 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s

     Running unittests src/bin/19-blueprintinator.rs (target/release/deps/19_blueprintinator-299e17a5876d198c)

running 2 tests
test tests::test1 ... ok
test tests::test2 has been running for over 60 seconds
test tests::test2 ... ok

test result: ok. 2 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 160.19s

     Running unittests src/bin/20-deencryptinator.rs (target/release/deps/20_deencryptinator-008079e4e2c7fe78)

running 13 tests
test tests::test_exact_loop_backward ... ok
test tests::test_double_looped_backward ... ok
test tests::test_double_looped_forward ... ok
test tests::test_decrypt ... ok
test tests::test_looped_forward ... ok
test tests::test_mix ... ok
test tests::test_singleton ... ok
test tests::test_small_backward ... ok
test tests::test_looped_backward ... ok
test tests::test_small_forward ... ok
test tests::test_zeros ... ok
test tests::test1 ... ok
test tests::test2 ... ok

test result: ok. 13 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.22s

     Running unittests src/bin/21-yellinator.rs (target/release/deps/21_yellinator-9dec1cea2202e4ac)

running 2 tests
test tests::test1 ... ok
test tests::test2 ... ok

test result: ok. 2 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.02s

     Running unittests src/bin/22-wonderator.rs (target/release/deps/22_wonderator-571bc387493bd3ee)

running 2 tests
test tests::test2 ... ok
test tests::test1 ... ok

test result: ok. 2 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s

     Running unittests src/bin/23-elf-scattinator.rs (target/release/deps/23_elf_scattinator-422cb1543c456d31)

running 2 tests
test tests::test1 ... ok
test tests::test2 ... ok

test result: ok. 2 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 8.28s

     Running unittests src/bin/24-blizzinator.rs (target/release/deps/24_blizzinator-d1e73327ec7b9260)

running 2 tests
test tests::test1 ... ok
test tests::test2 ... ok

test result: ok. 2 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 2.75s

     Running unittests src/bin/25-snafuinator.rs (target/release/deps/25_snafuinator-26713c1ea51a40cc)

running 2 tests
test tests::test2 ... ok
test tests::test1 ... ok

test result: ok. 2 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s

     Running unittests src/main.rs (target/release/deps/aoc2022-1ba13ca3d64483e5)

running 0 tests

test result: ok. 0 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s

   Doc-tests aoc

running 0 tests

test result: ok. 0 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s
```

That's a pretty awesome amount of 0.00s (16 of the 25 days). :smile:

The only ones over 1 second:

* Day 16 Pressurinator: 12.56s
* Day 17 Tetrisinator: 1.39s
* Day 19 Blueprintinator: <strike>2m20.19s</strike> [1.92s]({{<ref "#edit-dec-25-evening-">}})
* Day 23 Elf Scattinator: 8.23s
* Day 24 Blizzinator: 2.75s

With the exception of Day 19, keeping them around or under 10 seconds isn't bad at all. I may have to take another crack at optimizing that one. 

Some day. :smile:

Until then, Merry Christmas!

## Edit Dec 25 (evening :smile:)

Perhaps some day can even be today! See [my edit to Day 19]({{<ref "2022-12-19-blueprintinator#edit-dec-25-optimizing-max-builds" >}}). Sooo much faster. 

```bash
$ cargo test --release --bin 19-blueprintinator

   Compiling aoc2022 v0.1.0 (/Users/jp/Projects/advent-of-code/2022)
    Finished release [optimized] target(s) in 1.20s
     Running unittests src/bin/19-blueprintinator.rs (target/release/deps/19_blueprintinator-299e17a5876d198c)

running 2 tests
test tests::test1 ... ok
test tests::test2 ... ok

test result: ok. 2 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 1.92s
```

Nice.