---
title: "CodeCrafters: Build Myself a Grep"
date: 2024-08-28
programming/languages:
- Rust
programming/topics:
- Programming Languages
- Interpreters
- Lexers
- Grep
- Regular Expressions
- Regexp
series:
- CodeCrafters
---
I recently stumbled across [CodeCrafters](https://codecrafters.io/) again[^history]. In a nutshell, they give a number of 'Build Your Own...' courses, each of which will automatically create a repo for you, guide you through solving the program step by step, and provide some feedback on the way. 

On one hand, it's a freemium (one problem a month is free) / paid service. I wish they had tiers. I really think their monthly fee is a bit steep for what they offer (we'll come back to that). But on the other hand, it's a neat tool and I've been wanting some more larger programming projects to learn more Rust on, so away we go!

First up, [[wiki:grep]]()!

<!--more-->

In a nutshell, the project on CodeCrafters (as of this writing), takes you through building a very basic regex ([[wiki:regular expression]]()) engine, including:

* Literal characters: `abc`
* Character classes: `\d` and `\w`
* Character groups: `[abc]` and negative groups: `^[abc]`
* Basic anchors: `^` and `$`
* Repeated matches: `+` and `?`
* Wildcards: `.`
* Alternatives: `|`

There's also currently one advanced module: backreferences. This includes single, multiple, and nested backreferences. 

It's a pretty interesting (if not at all complete) selection. Here's what I ended up with as a solution for the first parts: [jp-grep](https://github.com/jpverkamp/jp-grep). I'm just going to go through the most recent version of the code, but you can go through the repo [history](https://github.com/jpverkamp/jp-grep/commits/main/) to see it at previous points. 

{{<toc>}}

## Representing a regex

First, a data structure that represents a regex:

```rust
#[derive(Debug, Clone, PartialEq, Eq)]
enum Regex {
    // Single characters
    Char(CharType),
    // A sequence of regexes that each must match in order
    Sequence(Vec<Regex>),
    // A character group, may be negated
    // True if inverted, (eg [^abc])
    CharacterGroup(Vec<CharType>, bool),
    // A capturing group used for backreferences
    CapturingGroup(Box<Regex>),
    Backref(usize),
    // Repeat a pattern (e.g. +, *, ?)
    Repeated(RepeatType, Box<Regex>),
    // Anchors for teh start and end of a line
    Start,
    End,
    // Used for parsing |, will be expanded into a Choice
    Choice(Vec<Regex>),
    ChoicePlaceholder,
}


#[derive(Debug, Clone, PartialEq, Eq)]
enum CharType {
    Any,
    Single(char),
    Range(char, char),
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
enum RepeatType {
    OneOrMore,
    ZeroOrMore,
    ZeroOrOne,
}
```

This handles all of the cases above, each as mentioned in comments for that group. A few more that might be less clear:

* `CharacterGroup` includes `\d` and `\w`, since those are just multiple `CharType::Ranges`. 
* Alternatives, I called `Choice`; the `ChoicePlaceholder` is used for parsing and should no longer exist when evaluating (I could probably have done this as an `Option` instead, but this works)

It is a recursive type, since a `CapturingGroup`, `Repeated`, or `Choice` can contain more `Regex`. In the first two cases, we just `Box` that, to make sure that the structure isn't infinitely large (because of recursion), but for the last, `Vec` does the same. 

## Parsing a regex

Okay, we have the regex, how do we turn a string like `"(([abc]+)-([def]+)) is \1, not ([^xyz]+), \2, or \3"` into a regex like 

```rust
Sequence([
    CapturingGroup(
        Sequence([
            CapturingGroup(Sequence([
                Repeated(OneOrMore, CharacterGroup([
                    Single('a'),
                    Single('b'),
                    Single('c')
                ], false))
            ])),
            Char(Single('-')),
            CapturingGroup(Sequence([
                Repeated(OneOrMore, CharacterGroup([
                    Single('d'),
                    Single('e'),
                    Single('f')
                ], false))
            ]))
        ])),
        Char(Single(' ')),
        Char(Single('i')),
        Char(Single('s')),
        Char(Single(' ')),
        Backref(1),
        Char(Single(',')),
        Char(Single(' ')),
        Char(Single('n')),
        Char(Single('o')),
        Char(Single('t')),
        Char(Single(' ')),
        CapturingGroup(Sequence([
            Repeated(OneOrMore, CharacterGroup([
                Single('x'),
                Single('y'),
                Single('z')
            ], true))
        ])),
        Char(Single(',')),
        Char(Single(' ')),
        Backref(2),
        Char(Single(',')),
        Char(Single(' ')),
        Char(Single('o')),
        Char(Single('r')),
        Char(Single(' ')), 
        Backref(3)
])
```

Yeah, I know that's a lot. So... how do we do it? 

```rust
impl From<String> for Regex {
    fn from(value: String) -> Self {
        // Read until the 'until' char, or end of string if None
        fn read_until<'a>(input: &'a [char], until: Option<char>) -> (Regex, &'a [char]) {
            let mut sequence = vec![];
            let mut input = input;

            // Read until end of input
            while let Some(&c) = input.first() {
                input = &input[1..];

                // Break if we have and hit the until character
                if until == Some(c) {
                    break;
                }

                let node = match c {
                    // Predefined character groups
                    '\\' => {
                        let group = match input.first() {
                            Some('d') => Regex::Char(CharType::Range('0', '9')),
                            Some('w') => Regex::Choice(vec![
                                Regex::Char(CharType::Range('a', 'z')),
                                Regex::Char(CharType::Range('A', 'Z')),
                                Regex::Char(CharType::Range('0', '9')),
                                Regex::Char(CharType::Single('_')),
                            ]),

                            // Backreference
                            Some(&c) if c.is_digit(10) => {
                                let index = c.to_digit(10).unwrap() as usize;
                                Regex::Backref(index)
                            },

                            // Escaped control characters
                            Some(&c) if "\\()[]|".contains(c) => Regex::Char(CharType::Single(c)),

                            // A group we don't know about
                            _ => unimplemented!()
                        };
                        input = &input[1..];
                        group
                    },

                    // Custom defined character groups
                    // TODO: Implement ranges
                    // TODO: Implement escaping in character groups
                    '[' => {
                        // Handle negation
                        let negated = if let Some('^') = input.first() {
                            input = &input[1..];
                            true
                        } else {
                            false
                        };

                        let mut choices = vec![];
                        while let Some(&c) = input.first() {
                            input = &input[1..];

                            if c == ']' {
                                break;
                            }

                            choices.push(CharType::Single(c));
                        }

                        Regex::CharacterGroup(choices, negated)
                    },

                    // Capture groups
                    '(' => {
                        let (group, remaining) = read_until(input, Some(')'));
                        input = remaining;
                        Regex::CapturingGroup(Box::new(group))
                    },
                    ')' => {
                        // This should have been consumed by the parent group
                        unreachable!("Unmatched ')'");
                    },

                    // Anchors
                    '^' => Regex::Start,
                    '$' => Regex::End,

                    // Hit the any key
                    '.' => Regex::Char(CharType::Any),

                    // An alternate choice
                    // This will insert a placeholder we will deal with later
                    '|' => Regex::ChoicePlaceholder,

                    // Single characters
                    c => Regex::Char(CharType::Single(c)),
                };

                // Check for modifiers (+*)
                let node = match input.first() {
                    Some('+') => {
                        input = &input[1..];
                        Regex::Repeated(RepeatType::OneOrMore, Box::new(node))
                    },
                    Some('*') => {
                        input = &input[1..];
                        Regex::Repeated(RepeatType::ZeroOrMore, Box::new(node))
                    },
                    Some('?') => {
                        input = &input[1..];
                        Regex::Repeated(RepeatType::ZeroOrOne, Box::new(node))
                    },
                    _ => node,
                };

                sequence.push(node);
            }

            // If we have any choice placeholders, we need to split the sequence into choices
            if sequence.contains(&Regex::ChoicePlaceholder) {
                let mut choices = vec![];
                let mut current_choice = vec![];

                for node in sequence {
                    if node == Regex::ChoicePlaceholder {
                        choices.push(Regex::Sequence(current_choice));
                        current_choice = vec![];
                    } else {
                        current_choice.push(node);
                    }
                }

                choices.push(Regex::Sequence(current_choice));
                return (Regex::Choice(choices), input);
            }

            (Regex::Sequence(sequence), input)
        }

        let chars = value.chars().collect::<Vec<_>>();
        let (result, remaining_chars) = read_until(&chars, None);
        assert_eq!(remaining_chars.len(), 0, "Remaining input: {:?}", remaining_chars);
        result
    }
}
```

That should probably be `From<&str>`. But otherwise, we parse it recursively. Most of the work is `read_until` that (as it says) reads until it sees either a specific character (`Some(c)`) or the end of the strong (`None`) and returns a `Sequence`.

If we see a `\`, check for character groups. If we see `[`, parse a custom character group. If we see a `(`, parse until the matching `)` (recursion comes for free!). And if we see `|`, remember this as a `ChoicePlaceholder`. 

Then, at the end, if we ever saw a `ChoicePlaceholder` in this `sequence`, turn it into a `Choice` element. 

Tada!

## Matching a string

Okay, this is by far the more interesting part.

```rust
impl Regex {
    pub fn matches(&self, input: &str) -> bool {
        let chars = input.chars().collect::<Vec<_>>();

        // Pattern can apply at any starting point
        for i in 0..chars.len() {
            log::debug!("matches({:?}) against {:?}, start={}", chars[i..].iter().collect::<String>(), &self, i == 0);

            let mut groups = vec![];
            let results = self.match_recur(&chars[i..], i == 0, &mut groups);

            if !results.is_empty() {
                return true;
            }
        }

        false
    }
}
```

As noted, the pattern could match anywhere in the string (without anchors), so for each possible starting point, we're going to call our helper `match_recur` function. We do have a flag as well, that will signify if we're at start of string for anchors. 

This is not very efficient if you have an anchor (since it will still try every other anchor point), but not as bad as you might think. Because it will always match and immediately fail on the `^` / `Regex::Start`, each point after the first will fail fast. So it just works.

The other interesting part is that we create a `groups: Vec<char>` for each match. This is entirely to match backreferences. When we match a backreference in the string, we'll record it in the `groups` as a `Vec<char>`, that way we can directly match against it. 

This could also be used to [directly implement returning the matched groups](#future-work-returning-groups), but that wasn't part of the exercise just yet!

### `match_recur`

So what about `match_recur`? This one is quite a bit more!

```rust
fn match_recur<'a>(
    &self,
    input: &'a [char],
    at_start: bool,
    groups: &mut Vec<Option<&'a [char]>>
) -> Vec<&'a [char]> {
    log::debug!("match_recur({self:?}, {}, {at_start})", input.iter().collect::<String>());

    if input.len() == 0 {
        if self.allow_none() {
            return vec![input];
        } else {
            return vec![];
        }
    }

    match self {
        // Hit the any key
        Regex::Char(CharType::Any) => {
            return vec![&input[1..]];
        },

        // Single character matches
        Regex::Char(CharType::Single(c)) => {
            if input[0] == *c {
                return vec![&input[1..]];
            }
            return vec![];
        },
        Regex::Char(CharType::Range(start, end)) => {
            if input[0] >= *start && input[0] <= *end {
                return vec![&input[1..]];
            }
            return vec![];
        },

        // Character groups, match any of the characters (or none if negated)
        Regex::CharacterGroup(chars, negated) => {
            let matched = chars.iter().any(|c| {
                match c {
                    CharType::Single(c) => input[0] == *c,
                    CharType::Range(start, end) => input[0] >= *start && input[0] <= *end,
                    CharType::Any => true,
                }
            });

            if negated ^ matched {
                return vec![&input[1..]];
            } else {
                return vec![];
            }
        },

        // Anchors
        Regex::Start => {
            if at_start {
                return vec![input];
            } else {
                return vec![];
            }
        },
        Regex::End => {
            if input.len() == 0 {
                return vec![input];
            } else {
                return vec![];
            }
        },

        // Multi-match modifiers (?+*)
        // NOTE: These should match the longest group they can and still work
        Regex::Repeated(mode, node) => {
            match mode {
                RepeatType::ZeroOrMore => {
                    // Return all possible matches at this level
                    // Base case: match nothing and return input as is
                    let mut results = vec![input];
                    let mut remaining = input;

                    loop {
                        let recur = node.match_recur(remaining, at_start, groups);
                        if recur.is_empty() {
                            break;
                        }

                        for new_remaining in recur {
                            results.push(new_remaining);
                            remaining = new_remaining;
                        }
                    }

                    results.reverse();
                    return results;
                },

                RepeatType::OneOrMore => {
                    // Return all possible matches at this level
                    // No base case: must match at least once
                    let mut results = vec![];
                    let mut remaining = input;

                    loop {
                        let recur = node.match_recur(remaining, at_start, groups);
                        if recur.is_empty() {
                            break;
                        }

                        for new_remaining in recur {
                            results.push(new_remaining);
                            remaining = new_remaining;
                        }
                    }

                    results.reverse();
                    return results;
                },

                RepeatType::ZeroOrOne => {
                    // If zero match
                    let mut results = vec![input];

                    // If one match
                    let mut recur = node.match_recur(input, at_start, groups);
                    results.append(&mut recur);

                    results.reverse();
                    return results;
                },
            }
        },

        // A sequence of matches, all of which must match
        // If any fails, abort the entire sequence and advance to try again
        Regex::Sequence(seq) => {
            // Keep a list of the possible branching values
            // TODO: This is hugely memory intensive :)
            let mut remainings = vec![input];
            let mut seq_at_start = at_start;

            for node in seq {
                remainings = remainings.into_iter().flat_map(|input| {
                    node.match_recur(input, seq_at_start, groups)
                }).collect();
                seq_at_start = false;
            }

            return remainings;
        },

        // A choice of matches, any of which much match
        // If none match, abort the entire choice and advance to try again
        Regex::Choice(seq) => {
            let mut results = vec![];

            for node in seq {
                let mut recur = node.match_recur(input, at_start, groups);
                if !recur.is_empty() {
                    results.append(&mut recur);
                }
            }

            return results;
        },

        // Capturing groups wrap another node and then store what was captured
        Regex::CapturingGroup(node) => {
            // Add a placeholder to get order correct
            let index = groups.len();
            groups.push(None);

            let recur = node.match_recur(input, at_start, groups);
            if recur.is_empty() {
                groups.remove(index);
                return vec![];
            } else {
                groups[index] = Some(&input[..(input.len() - recur[0].len())]);
                return recur;
            }
        },

        // Backreferences
        Regex::Backref(index) => {
            let index = index - 1; // 1-indexed

            // If we haven't captured that group, this is a problem
            if groups.len() <= index || groups[index].is_none() {
                unimplemented!("Backreference to group {} that hasn't been captured", index);
            }

            let captured = groups[index].unwrap();
            if input.starts_with(captured) {
                return vec![&input[captured.len()..]];
            }
            return vec![];
        },

        // This should have been expanded by the time we get here
        Regex::ChoicePlaceholder => unreachable!("ChoicePlaceholder should have been expanded"),
    }
}
```

For the most part, it's just a matter of applying the given patternr(whatever type that is) to the given index in the `&[char]` and returning where we got to, mostly as `vec![...one thing...]` (see [here](#returning-multiple-options) for the case where we return more than one). 

That's... pretty cool IMO. 

### Returning multiple options

Okay, first up. Why does it return `Vec<&'[char]>`? 

Originally, I just returned `Option<&'[char]>`, which was either `None` if we didn't have a match or `&'[char]` which was a pointer to where in the `[char]` we have advanced to (and where any future matches would start). 

But as soon as we got to `+` and `?`, that got a lot more complicated. For each match in those cases (above), we need to match as greedily as possible. So if we have `a+ab` against `"aaaab"`, we want to match `"aaa"` for `a+`, not just a single `a` (or two). But conversely, the greedy match might not work. In this case, the greediest match would be `"aaaa"`, but that doesn't leave another `a` for the `ab`. 

So `Vec<&'[char]>`? All of the possible next matches (where they will next match from) at a given position, from most to least greedy! (`results.reverse();`) 

So when we match a `Sequence`:

```rust
for node in seq {
    remainings = remainings.into_iter().flat_map(|input| {
        node.match_recur(input, seq_at_start, groups)
    }).collect();
    seq_at_start = false;
}
```

This will take each current match (`remainings`) and apply it to the input recursively, getting one or more results in turn. If that branch isn't possible, return `vec![]`, so the `flat_map` will remove those as possible matches. 

It ends up calculating *every* match at a specific point. We could probably return an `impl Iterator<&'[char]>` that lazily returns the next possibility, but that's [future work](#optimization-memoization)!

### Backreferences

The other interesting implementation is how I did capturing groups and backreferences. That's why we're passing the `groups: &mut Vec<Option<&'a [char]>>` around. At each index, it will contain the substring (subchars?) that the capturing group actually matched. 

Why `Option`? That's to deal with ordering. If you have something like `((a)(b))`, the `ab` should be `\1`, but `a` will be the first group matched. So instead, I `push(None)` when the group is created and update that to `Some(...)` when the match is completed. 

Then, when you get a `Backreference`, we match the literal string stored in `groups` and we're good to go!

## Optimization: Memoization

So, what can we do better? 

One problem that we're seeing is that it's possible that we'll match the same subset of the string a couple different ways. For example, if we have `(a+)(a+)b` against `"aaaab"`, we could theoretically match `"a" / "aaa"`, `"aa" / "aa"`, or `"aaa" / "a"` and all will be matching `b` against `"b"`. 

This is perhaps a silly example, but as matches and/or input get far far larger, this is exactly the sort of issue that will cause a regex denial of service sort of attack. 

But there's hope! It's also exactly the sort of thing [[wiki:memoization]]() solves! If you get exactly the same arguments, return the same answer. The `groups` is a problem here, but perhaps not an insurmountable one. Worth trying! Perhaps as an optional flag? 

## Future work: Returning groups

Another group, as mentioned is returning the actual matches from `matches`. This is actually really easy! We just have to insert a `\0` element that matches the entire thing and then change `matches(...) -> bool` to `Vec<String>`! We'll get there. 

## Other future work

### regex features

There are a number of things in regexes that I don't support yet:

* ranges in groups - this is mostly a parsing problem
* negated groups - such as `\D` for 'not a digit', again mostly a parsing problem
* more classes - whitespace
* escape characters - tabs, carriage returns, etc
* unicode character class escapes - we already support unicode, but escapes would be handy
* more anchors - `\b` for boundaries
* lookahead/lookbehind - match but don't consume the text, shouldn't be hard?
* named capture groups / named backreferences - mostly a syntax thing + a `HashMap` instead of `Vec`
* non-capturing groups - just a flag
* flags - `(?ims:...)` - will probably need a new parameter for the `match_recur` function to track which flags are on
* exactly `n` repeats - `*`, `+`, and `?` are really just subcases of this
* non-greedy matches - `x+?`, this will just (not) reverse the order of the match

But... I don't think any of those are insurmountable. It's not part of the CodeCrafters tests (yet), but still I think worth doing. 

### grep features

In addition, we currently only support the `-E` flag to `grep`. There are ... a whole bunch more that are probably worth supporting! In particular:

* `-A` / `-B` - print the context before/after matches
* multiple patterns + `--exclude` - match several patterns both positive and negative
* handling directories, `-R` etc

Not actually that much, but it would be fun to have an alternative. 

### Performance

Finally, it would be interesting to test against some really complicated expressions / large files. The current solution (as mentioned [here](#returning-multiple-options)) returns every possible solution as it's working, eating up a potentially crazy amount of RAM and calculating a bunch of cases we don't need. It would be nice not to do that. 

Furthermore, we could do the theoretical computer science and turn this into a [[wiki:non-deterministic finite automata]](). Performant? Not sure. But interesting. 

## Summary and thoughts on CodeCrafters

Overall, it was an interesting problem and I think that the CodeCrafters interface is well done. You push to a git repo and it runs a bunch of test cases against it, showing you what failed. 

Conversely, it's ... incomplete? I feel like a number of the additional [regex cases](#regex-features) could have been included. Perhaps future modules? But still, incomplete. 

Still, for the month, it's free and it was an interesting problem to solve. So, worth doing. For the moment, I probably won't pay for CodeCrafters, but I will continue to solve the free problems! :smile:

[^history]: One bit of unfortunate history was [here](https://github.com/rust-lang/rustlings/pull/1768) where CodeCrafters added themselves (as a paid service) to 'what to do next' without disclosing it. I still think that wasn't a great move, but time passes. And it's an interesting enough service. 