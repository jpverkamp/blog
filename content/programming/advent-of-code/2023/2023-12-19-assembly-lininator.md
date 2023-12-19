---
title: "AoC 2023 Day 19: Assembly Lininator"
date: 2023-12-19 00:00:03
programming/languages:
- Rust
programming/sources:
- Advent of Code
series:
- Advent of Code 2023
---
## Source: [Day 19: Aplenty](https://adventofcode.com/2023/day/19)

[Full solution](https://github.com/jpverkamp/advent-of-code/tree/master/2023/solutions/day19) for today (spoilers!)

{{<toc>}}

## Part 1

> You are given a series of parts with 4 ratings as such:
>
> `{x=787,m=2655,a=1222,s=2876}`
>
> In addition, you are given a series of rules describing a graph as such:
>
> `px{a<2006:qkq,m>2090:A,rfg}`
>
> In this example, if you are at the node `px`, if `a < 2006`, move to `qkq`. Otherwise, if `m > 2090` move to `A`. If no other case matches, the last defaults to `rfg`. 
>
> `A` and `R` are special cases for accept and reject. 
>
> Calculate the sum of sum of all four ratings for all nodes that end at `Accept`. 

<!--more-->

### Types and Parsing

That's a really long problem description. Reminds me of [[AoC 2023 Day 5: Growinator|day 5]]() Let's write up an equally long set of types and parsers!

```rust

#[derive(Debug, Copy, Clone, Eq, PartialEq, Hash)]
pub enum Label<'a> {
    Input,
    Accept,
    Reject,
    Node(&'a str),
}

#[derive(Debug, Copy, Clone)]
pub enum RatingCategory {
    X,
    M,
    A,
    S,
}

#[derive(Debug, Copy, Clone)]
pub struct Part {
    pub x: u64,
    pub m: u64,
    pub a: u64,
    pub s: u64,
}

#[derive(Debug, Copy, Clone)]
pub enum Comparator {
    LessThan,
    GreaterThan,
}

#[derive(Debug, Copy, Clone)]
pub struct Comparison<'a> {
    pub category: RatingCategory,
    pub comparator: Comparator,
    pub value: u64,
    pub label: Label<'a>,
}

#[derive(Debug)]
pub struct Rule<'a> {
    pub label: Label<'a>,
    pub comparisons: Vec<Comparison<'a>>,
    pub default: Label<'a>,
}
```

`nom` it up:

```rust

// A category for part ratings, always a literal char from 'xmas'
fn rating_category(input: &str) -> IResult<&str, RatingCategory> {
    alt((
        map(char('x'), |_| RatingCategory::X),
        map(char('m'), |_| RatingCategory::M),
        map(char('a'), |_| RatingCategory::A),
        map(char('s'), |_| RatingCategory::S),
    ))(input)
}

// A label for a rule or part, an alphabetic string or the literals A and R
fn label(input: &str) -> IResult<&str, Label> {
    alt((
        map(tag("in"), |_| Label::Input),
        map(char('A'), |_| Label::Accept),
        map(char('R'), |_| Label::Reject),
        map(alpha1, Label::Node),
    ))(input)
}

// Comparison operators
fn comparator(input: &str) -> IResult<&str, Comparator> {
    alt((
        map(char('<'), |_| Comparator::LessThan),
        map(char('>'), |_| Comparator::GreaterThan),
    ))(input)
}

// A comparison takes a rating category, comparator, and a value
fn comparison(input: &str) -> IResult<&str, Comparison> {
    let (input, (category, comparator, value, label)) = tuple((
        rating_category,
        comparator,
        complete::u64,
        preceded(char(':'), label),
    ))(input)?;

    Ok((
        input,
        Comparison {
            category,
            comparator,
            value,
            label,
        },
    ))
}

// A rule has a label, a list of comparisons, and a default if no comparison matches
fn rule(input: &str) -> IResult<&str, Rule> {
    let (input, (label, comparisons, default)) = tuple((
        label,
        preceded(char('{'), separated_list1(char(','), comparison)),
        delimited(char(','), label, char('}')),
    ))(input)?;

    Ok((
        input,
        Rule {
            label,
            comparisons,
            default,
        },
    ))
}

// A part has a score for each of the four rating categories
// For now, assume they are ordered
fn part(input: &str) -> IResult<&str, Part> {
    let (input, (x, m, a, s)) = delimited(
        char('{'),
        tuple((
            preceded(tag("x="), complete::u64),
            preceded(tag(",m="), complete::u64),
            preceded(tag(",a="), complete::u64),
            preceded(tag(",s="), complete::u64),
        )),
        char('}'),
    )(input)?;

    Ok((input, Part { x, m, a, s }))
}

// A simulation contains a list of rules and a list of parts
pub fn simulation(input: &str) -> IResult<&str, (FxHashMap<Label, Rule>, Vec<Part>)> {
    let (input, (rules, parts)) = separated_pair(
        separated_list1(line_ending, rule),
        many1(line_ending),
        separated_list1(line_ending, part),
    )(input)?;

    let rules = rules
        .into_iter()
        .map(|r| (r.label, r))
        .collect::<FxHashMap<_, _>>();

    Ok((input, (rules, parts)))
}
```

There's a lot there, but hopefully by breaking it down into lots of little pieces it's fairly straight forward?

### Simulation

Okay, we have our types, how do we actually run the simulation?

```rust
fn main() -> Result<()> {
    let stdin = io::stdin();
    let input = io::read_to_string(stdin.lock())?;
    let (s, (rules, parts)) = parse::simulation(&input).unwrap();
    assert_eq!(s.trim(), "");

    let result = parts
        .iter()
        .filter_map(|part| {
            let mut label = Label::Input;
            loop {
                let rule = rules.get(&label).unwrap();
                label = rule.default;

                for comparison in rule.comparisons.iter() {
                    let value = match comparison.category {
                        RatingCategory::X => part.x,
                        RatingCategory::M => part.m,
                        RatingCategory::A => part.a,
                        RatingCategory::S => part.s,
                    };
                    match comparison.comparator {
                        Comparator::LessThan => {
                            if value < comparison.value {
                                label = comparison.label;
                                break;
                            }
                        }
                        Comparator::GreaterThan => {
                            if value > comparison.value {
                                label = comparison.label;
                                break;
                            }
                        }
                    }
                }

                if label == Label::Accept {
                    return Some(part);
                } else if label == Label::Reject {
                    return None;
                }
            }
        })
        .map(|part| part.x + part.m + part.a + part.s)
        .sum::<u64>();

    println!("{result}");
    Ok(())
}
```

I like this. Most of the work is done in a `loop` inside of the `filter_map`. The goal is to `None` for `Reject`, so it will be removed and we'll only have `Accept` left. Just hope there aren't any infinite loops :smile:. 

It's interesting how verbose unpacking the categories and comparators ended up being. That certainly does walk the line between being more specific and being more concise. I'm not entirely sure which way it falls for me. 

But in the end, it works and it's quick! Onward. 

## Part 2

> Allow each of the ratings (`xmas`) to vary from `1..=4000`. How many of these 256 trillion possibilities end in accept? 

### Brute Force

Well... you could brute force it!

```rust
let result = values
    .clone()
    .cartesian_product(values.clone())
    .inspect(|v| println!("{v:?} in {sec:?}", sec = start.elapsed()))
    .cartesian_product(values.clone())
    .cartesian_product(values.clone())
    .flat_map(|(((x, m), a), s)| {
        let part = Part { x, m, a, s };
        let mut label = Label::Input;

        // ...
    })
    .count();
```

I stuck that `inspect` in to show me just how slow this is going... 

```rust
(1, 1) in 334ns
(1, 2) in 555.949417ms
(1, 3) in 1.071667792s
(1, 4) in 1.592958542s
(1, 5) in 2.119584709s
(1, 6) in 2.644092709s
(1, 7) in 3.170371959s
(1, 8) in 3.694674s
(1, 9) in 4.219525959s
(1, 10) in 4.744019417s
```

Each of those is ~16 million, so we're running at about 33 MHz. That's... 87 days. Let's not.

### Ranges

Yup. The [[AoC 2023 Day 5: Growinator|day 5]]() is *strong* in this one. What we really want to do is apply each rule to *ranges*, possibly splitting each range in half. 

Something like this:

```text
===== =====
State { label: Input, part: RangedPart { x: 1..=4000, m: 1..=4000, a: 1..=4000, s: 1..=4000 } }
  - comparison: Comparison { category: S, comparator: LessThan, value: 1351, label: Node("px") }
   - remaining: [State { label: Input, part: RangedPart { x: 1..=4000, m: 1..=4000, a: 1..=4000, s: 1..=4000 } }]
    - value is in range, splitting
     - lo (RangedPart { x: 1..=4000, m: 1..=4000, a: 1..=4000, s: 1..=1350 }) is pushing to queue with label=Node("px")
     - hi (RangedPart { x: 1..=4000, m: 1..=4000, a: 1..=4000, s: 1351..=4000 }) is is remaining
  - defaulting: State { label: Node("qqz"), part: RangedPart { x: 1..=4000, m: 1..=4000, a: 1..=4000, s: 1351..=4000 } }
===== =====
State { label: Node("qqz"), part: RangedPart { x: 1..=4000, m: 1..=4000, a: 1..=4000, s: 1351..=4000 } }
  - comparison: Comparison { category: S, comparator: GreaterThan, value: 2770, label: Node("qs") }
   - remaining: [State { label: Node("qqz"), part: RangedPart { x: 1..=4000, m: 1..=4000, a: 1..=4000, s: 1351..=4000 } }]
    - value is in range, splitting
     - lo (RangedPart { x: 1..=4000, m: 1..=4000, a: 1..=4000, s: 1351..=2770 }) is is remaining
     - hi (RangedPart { x: 1..=4000, m: 1..=4000, a: 1..=4000, s: 2771..=4000 }) is pushing to queue with label=Node("qs")
  - comparison: Comparison { category: M, comparator: LessThan, value: 1801, label: Node("hdj") }
   - remaining: [State { label: Node("qqz"), part: RangedPart { x: 1..=4000, m: 1..=4000, a: 1..=4000, s: 1351..=2770 } }]
    - value is in range, splitting
     - lo (RangedPart { x: 1..=4000, m: 1..=1800, a: 1..=4000, s: 1351..=2770 }) is pushing to queue with label=Node("hdj")
     - hi (RangedPart { x: 1..=4000, m: 1801..=4000, a: 1..=4000, s: 1351..=2770 }) is is remaining
  - defaulting: State { label: Reject, part: RangedPart { x: 1..=4000, m: 1801..=4000, a: 1..=4000, s: 1351..=2770 } }
```

Yeah, that's a lot to read. Let's just do some code:

```rust
#[derive(Debug, Clone)]
pub struct RangedPart {
    pub x: RangeInclusive<u64>,
    pub m: RangeInclusive<u64>,
    pub a: RangeInclusive<u64>,
    pub s: RangeInclusive<u64>,
}

fn main() -> Result<()> {
    env_logger::init();

    let stdin = io::stdin();
    let input = io::read_to_string(stdin.lock())?;
    let (s, (rules, _)) = parse::simulation(&input).unwrap();
    assert_eq!(s.trim(), "");

    #[derive(Debug, Clone)]
    struct State<'a> {
        label: Label<'a>,
        part: RangedPart,
    }

    let mut queue = vec![State {
        label: Label::Input,
        part: RangedPart {
            x: 1..=4000,
            m: 1..=4000,
            a: 1..=4000,
            s: 1..=4000,
        },
    }];
    let mut accepted = Vec::new();

    while let Some(state) = queue.pop() {
        info!("===== =====");
        info!("{:?}", state);

        // If we're in accept/reject, process specifically
        if state.label == Label::Accept {
            info!("- accepting");
            accepted.push(state.part);
            continue;
        } else if state.label == Label::Reject {
            info!("- rejecting");
            continue;
        }

        let rule = rules.get(&state.label).unwrap();

        // 'Remaining' is ranges that haven't had any comparison applied to them
        // Anything that makes it all the way through will be defaulted
        let mut remaining = vec![state];

        // Apply comparisons to all remaining ranges
        for comparison in rule.comparisons.iter() {
            info!("  - comparison: {:?}", comparison);
            info!("   - remaining: {:?}", remaining);

            // Update remaining
            // Any parts that are moved to queue will filter_map to None (and be removed)
            // Anything else will Some and be kept for the next comparison
            remaining = remaining
                .into_iter()
                .filter_map(|state| {
                    // Get the relevant range
                    let value_range = match comparison.category {
                        RatingCategory::X => state.part.x.clone(),
                        RatingCategory::M => state.part.m.clone(),
                        RatingCategory::A => state.part.a.clone(),
                        RatingCategory::S => state.part.s.clone(),
                    };

                    // Apply the comparison to the range, possibly splitting
                    // There are three cases: less than, during, and greater than the range
                    if comparison.value < *value_range.start() {
                        info!("    - all values are greater than value");
                        match comparison.comparator {
                            Comparator::GreaterThan => {
                                info!("    - pushing to queue with label={:?}", comparison.label);
                                queue.push(State {
                                    label: comparison.label,
                                    part: state.part,
                                });
                                None
                            }
                            Comparator::LessThan => {
                                info!("    - remaining");
                                Some(state)
                            }
                        }
                    } else if comparison.value > *value_range.end() {
                        info!("    - all values are less than value");
                        match comparison.comparator {
                            Comparator::GreaterThan => {
                                info!("    - remaining");
                                Some(state)
                            }
                            Comparator::LessThan => {
                                info!("    - pushing to queue with label={:?}", comparison.label);
                                queue.push(State {
                                    label: comparison.label,
                                    part: state.part,
                                });
                                None
                            }
                        }
                    } else {
                        info!("    - value is in range, splitting");
                        match comparison.comparator {
                            Comparator::GreaterThan => {
                                // Comparison is less than, so the value goes with the upper half
                                // Lower half goes to queue, upper half stays in remaining
                                let lo_range = (*value_range.start()..=comparison.value).clone();
                                let hi_range =
                                    ((comparison.value + 1)..=*value_range.end()).clone();

                                let mut lo = state.clone().part;
                                match comparison.category {
                                    RatingCategory::X => lo.x = lo_range,
                                    RatingCategory::M => lo.m = lo_range,
                                    RatingCategory::A => lo.a = lo_range,
                                    RatingCategory::S => lo.s = lo_range,
                                }

                                let mut hi = state.clone().part.clone();
                                match comparison.category {
                                    RatingCategory::X => hi.x = hi_range,
                                    RatingCategory::M => hi.m = hi_range,
                                    RatingCategory::A => hi.a = hi_range,
                                    RatingCategory::S => hi.s = hi_range,
                                }

                                info!("     - lo ({:?}) is is remaining", lo);
                                info!(
                                    "     - hi ({:?}) is pushing to queue with label={:?}",
                                    hi, comparison.label
                                );

                                queue.push(State {
                                    label: comparison.label,
                                    part: hi,
                                });

                                Some(State {
                                    label: state.label,
                                    part: lo,
                                })
                            }
                            Comparator::LessThan => {
                                // Comparison is greater than, so value goes with the lower half
                                // Lower half stays in remaining, upper half goes to queue
                                let lo_range =
                                    (*value_range.start()..=(comparison.value - 1)).clone();
                                let hi_range = (comparison.value..=*value_range.end()).clone();

                                let mut lo = state.part.clone();
                                match comparison.category {
                                    RatingCategory::X => lo.x = lo_range,
                                    RatingCategory::M => lo.m = lo_range,
                                    RatingCategory::A => lo.a = lo_range,
                                    RatingCategory::S => lo.s = lo_range,
                                }

                                let mut hi = state.part.clone();
                                match comparison.category {
                                    RatingCategory::X => hi.x = hi_range,
                                    RatingCategory::M => hi.m = hi_range,
                                    RatingCategory::A => hi.a = hi_range,
                                    RatingCategory::S => hi.s = hi_range,
                                }

                                info!(
                                    "     - lo ({:?}) is pushing to queue with label={:?}",
                                    lo, comparison.label
                                );
                                info!("     - hi ({:?}) is is remaining", hi);

                                queue.push(State {
                                    label: comparison.label,
                                    part: lo,
                                });

                                Some(State {
                                    label: state.label,
                                    part: hi,
                                })
                            }
                        }
                    }
                })
                .collect();
        }

        // Anything still remaining gets the default label
        remaining.iter_mut().for_each(|state| {
            state.label = rule.default;
            info!("  - defaulting: {:?}", state);
            queue.push(state.clone());
        });
    }

    let result = accepted
        .iter()
        .map(|part| {
            (part.x.end() - part.x.start() + 1) as u128
                * (part.m.end() - part.m.start() + 1) as u128
                * (part.a.end() - part.a.start() + 1) as u128
                * (part.s.end() - part.s.start() + 1) as u128
        })
        .sum::<u128>();

    println!("{result}");
    Ok(())
}
```

It's ... a lot longer. Not going to lie. And it has a lot more `info!` logging than I often leave in. But making sure all of the cases work well for that? Well, that's when logging comes in handy (yes, I should have written more (any) test cases). 

The basic idea is:

* Keep a queue of states to process, starting with `{x: 1..=4000, m: : 1..=4000, a: 1..=4000, s: 1..=4000}`. 
* For each state in the queue:
  * Remove `Accept` and `Reject` states (and count or not)
  * Load the rule based on that state's label
  * Initialize a second list of `remaining` states; this will be any subset of the original ranges that hasn't already had a condition applied to it
  * Apply each condition to the rule in turn
    * Split the range:
      * If the condition's value is entirely above or below the current range, you will have one output range
      * If the condition's value is in the range, you will split (although which range the `condition.value` is in goes to depends on the conditional)
    * For that one or two ranges:
      * If the condition applied, move the range back to the `queue` (no more `conditions` will apply to this range)
      * If it did not, keep it in `remaining`
  * Any values left in `remaining` change to the `default` label for that state

It's arguable if that's any easier to read than the code and I'll admit, there were a number of off by one errors and flipping what 'less than' means (condition < range or range < condition).

But in the end, I think that it's actually a fairly elegant way to look at the program!

## Performance

```rust
$ just time 19 1

hyperfine --warmup 3 'just run 19 1'
Benchmark 1: just run 19 1
  Time (mean ± σ):      94.0 ms ±   3.1 ms    [User: 38.3 ms, System: 15.5 ms]
  Range (min … max):    89.4 ms … 103.4 ms    30 runs

$ just time 19 2

hyperfine --warmup 3 'just run 19 2'
Benchmark 1: just run 19 2
  Time (mean ± σ):     103.7 ms ±   2.9 ms    [User: 38.5 ms, System: 16.0 ms]
  Range (min … max):   100.6 ms … 114.4 ms    27 runs
```

Sometimes it's amazing how much more work you can do in the same amount of time. Processing 2000 inputs or trillions? Doesn't matter when you handle them as ranges!