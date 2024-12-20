---
title: "Finish Myself a Grep"
date: 2024-10-05
programming/languages:
- Rust
programming/topics:
- Programming Languages
- Interpreters
- Lexers
- Grep
- Regular Expressions
- Regex
series:
- CodeCrafters
---
Hey, I said that I would follow up on my post about [[CodeCrafters: Build Myself a Grep|Building Myself a Grep]]()... well here it is!

And I'm actually surprised with myself in how far I actually made it! 

You can see the current state of my code [on Github](https://github.com/jpverkamp/jp-grep). You can install it from that repo (checked out) with `cargo install --path .`

I mostly worked off the [MDN documentation](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Regular_expressions):

## Details

{{<toc>}}

## Supported Regex Features

* Assertions: 
  * `^` and `$` for entire patterns
  * Parsing look head/behind (not matched)

* Character classes
  * Single characters: `[abc]`
  * Ranges: `[a-z]`
  * Negated classes: `[^abc]`
  * Wildcards: `.`
  * Classes: `\d`/`\D` for digits, `\w`/`\W` for 'words', and `\s`/`\S` for whitespace
  * Escape characters: `\t\r\n\v\f`
  * Control characters: `\cX` (I've never used these)
  * Hex and unicode literals: `\hXX` and `\uXXXX`
  * Disjunction: `|` (both in capture groups and not)

* Groups and back references
  * Capture groups: `(abc)`
  * Named capture groups: `(?<name>abc)`
  * Non-capturing groups: `(?:abc)`
  * Flags: `(?ims-ims:abc)`
    * Both enabling and disabling
    * `i` and `s` but not `m`
  * Backreferences: `\n`
  * Named backreferences: `\k<name>`

* Quantifiers
  * `*` for zero or more
  * `+` for one or more
  * `?` for zero or one
  * `*?`, `+?`, and `??` for lazy / non-greedy matches
  * `abc{n}` exactly n matches
  * `abc{n,}` at least n matches
  * `abc{,m}` up to m matches
  * `abc{n,m}` at least n and up to m matches (inclusive)
  * Lazy matches for all of those

Most of those were fairly straight forward extensions of previous code. In think the most interesting ones were handling the parsing of all the different things that can go in groups (including flags).

For each of them, you can check my [git commit history](https://github.com/jpverkamp/jp-grep/commits/main/) to see how I implemented specific things. It's mostly one commit per feature, but not always. 

## Unsupported Regex Features (so far!)

* Assertions:
  * Word boundaries (`\b` and `\B`)
  * Look ahead/behind (parsed but not matched)

* Character classes
  * `[\b]` for backspace characters
  * Long unicode format: `\u{XXXXX}`
  * Unicode properties: `\p{...}`/`\P{...}`

* Groups and back references:
  * `m` flag / mode: multiline matches

The look ahead/behind is the one I'm most interested in supporting. I don't even think it will be that hard, I just honestly missed it. 

The more interesting one will be the `m` flag. Currently, I only match lines, so that will be a decently large restructuring. We'll see. 

## Supported CLI flags 

I've made an awful lot of progress on this one too!

```bash
$ jp-grep --help

A custom grep implementation; always behaves as egrep

Usage: jp-grep [OPTIONS] [PATTERN] [PATHS]...

Arguments:
  [PATTERN]   The regular expression to evaluate; may also be specified with -e
  [PATHS]...  Paths to search for matches; if none are provided read from stdin

Options:
  -A, --after-context <AFTER_CONTEXT>
          Lines of context to print after each match
  -B, --before-context <BEFORE_CONTEXT>
          Lines of context to print before each match
  -C, --context <CONTEXT>
          Lines to print both before and after
  -c, --count
          Only print the matching count
  -E, --extended-regexp
          Extended regex mode (egrep); this option is ignored (always true)
  -e, --regexp <ADDITIONAL_PATTERNS>
          Additional patterns, will return a line if any match
  -h, --no-filename
          Never print filenames
      --help
          Display this help message
  -i, --ignore-case
          Default to case insensitive match
  -n, --line-number
          Print line numbers before matches and context
  -r, --recursive
          Recursively add any directories (-R also works)
  -v, --invert-match
          Invert the match; only print lines that don't match any pattern
  -V, --version
          Print version
```

Of those, the context flags (`-A`, `-B`, and `-C`) were probably the most tricky, since I basically had to implement a [[wiki:circular buffer]]() for them. I could have just read the entire file into memory, but from the beginning, I didn't want to do that. 

`-E` is a little silly, since that's the only `grep` pattern I support (and the only one I actually use in `grep`, so that's fair). 

So far as supporting multiple files, recursive search, and stdin, read the section on [collecting files](#collecting-files) later.

So far as printing (handling line numbers and file names), read the section on [printing lines](#printing-lines).

Overall, pretty fun code. 

## Unsupported CLI flags

So far, there are a bunch of flags that I don't support for grep. Of those, there are a bunch that I don't intend to support (like built in compression support and properly dealing with symlinks). 

The things that I would still like to support though are:

* Input options:

  * `-f file`/`--file=file` - Read patterns from file

* Output options:

  * `-a`/`--text` - Currently I always have this set; I don't treat binary files differently
  * `-L`/`--files-without-match` - only print files that don't match
  * `-o`/`--only-matching` - only print the matching groups; I have the groups for backreferences, use them!

* File filtering - files to include/exclude (useful with recursive matches): 

  * `--exclude pattern`
  * `--exclude-dir pattern`
  * `--include pattern`
  * `--include-dir pattern`
     
That's not too bad, all things consider.

## Error handling

One thing that I actually played a bit with this time around was custom error handling in the parser. Rather than just returning `&str` all over the place for `Err` types, I made my own:

```rust
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub(crate) enum ParserError {
    RemainingInput,
    UnexpectedEnd,
    InvalidCharacter(char, &'static str),
    InvalidUnicodeCodePoint(u32),
    InvalidRange(char, char),
    InvalidRepeatRange(u32, u32),
}

impl std::fmt::Display for ParserError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            ParserError::RemainingInput => write!(f, "Unexpected input after parsing"),
            ParserError::UnexpectedEnd => write!(f, "Unexpected end of input"),
            ParserError::InvalidCharacter(c, expected) => {
                write!(f, "Invalid character '{}', expected {}", c, expected)
            }
            ParserError::InvalidUnicodeCodePoint(code_point) => {
                write!(f, "Invalid unicode code point: {}", code_point)
            }
            ParserError::InvalidRange(start, end) => {
                write!(f, "Invalid range: {}-{}", start, end)
            }
            ParserError::InvalidRepeatRange(start, end) => {
                write!(f, "Invalid range: {}-{}", start, end)
            }
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub(crate) struct ParserErrorWithPosition {
    pub position: usize,
    pub error: ParserError,
}
```

The `WithPosition` type also lets me pinpoint exactly where in a pattern I failed:

```rust
jp-grep 'this is some long complicated pattern, \hXX see?'

Error parsing regex: Invalid character 'X', expected hex digit
| this is some long complicated pattern, \hXX see?
|                                          ^
```

That's pretty neat and I hope helpful! :smile:

## Expanding past CodeCrafters

Overall, I'm pretty happy with this project. It's got a pretty decent chunk of code, including...

```bash
$ jp-grep -c -v -e '//' -e '^\s*$' **/*.rs

1241
```

...over 1000 lines of Rust code, including tests but not blank lines or comments. :smile:

I'll probably pick this up at least once more.

Now... will I actually use this? Probably not. But it was certainly interesting to write. 

Other than that, was CodeCrafters actually helpful for this? Middling. It was the kick I needed to actually do it (I've been meaning to write this for *years* at this point) and once I was started, I could finish it. On the other hand, the output format they require was a bit annoying at times, I've mostly moved away from that. 

Still, worth I think. I'll probably continue to do their free programs. Kafka is up next. Whee servers!


<!--more-->

## Collecting files

Here's the code I wrote to collect and loop through files. It has it's own enum, since I can support either `stdin` or a list of files and then it also needs to be able (if requested) to handle directories recursively. I do this with a `queue` rather than recursively--same thing really. 

Two things that I made sure this code does:

* It doesn't open the files ahead of time (at one point the `Readable` stored open files). This prevents issues with the filesystem running out of file handles to give me if I try to grep a huge directory. 

* Each individual file is read lazily. The `Boxed` `map` handles that. By returning the `Map`, the iterator is stored and only gives lines as we need them.

Why the `Box`? Because I need a `dyn` type of `Iterator` if I don't want to read ahead of time so far as I can tell. Otherwise, I will always need to refer to `Stdin` or `File` differently. A bit annoying that, but this works. 

```rust
// Collect the Lines iterators we're going to be working on
enum Readable {
    Stdin,
    File(PathBuf),
}

impl Readable {
    fn lines(&mut self) -> Box<dyn Iterator<Item = std::io::Result<String>> + '_> {
        match self {
            Readable::Stdin => Box::new(
                stdin()
                    .lock()
                    .lines()
                    .map(|line| line.map(|s| s.to_string())),
            ),
            Readable::File(r) => Box::new({
                BufReader::new(File::open(r.clone()).expect(
                    format!("Failed to open file: {path}", path = r.to_string_lossy()).as_str(),
                ))
                .lines()
                .map(|line| line.map(|s| s.to_string()))
            }),
        }
    }
}

// Collect all inputs as 'Readable' iterators
// This will handle multiple provided paths the cases for directories (recursive or not)
fn collect_input(args: &Args) -> Vec<(String, Readable)> {
    let mut files = vec![];

    if args.paths.is_empty() {
        files.push(("stdin".to_string(), Readable::Stdin));
    } else {
        let mut path_queue = args
            .paths
            .iter()
            .map(|p| PathBuf::from(p))
            .collect::<VecDeque<_>>();

        while let Some(path) = path_queue.pop_front() {
            if path.is_dir() {
                if !args.recursive {
                    eprintln!(
                        "Error: {path} is a directory, but -r/--recursive was not set",
                        path = path.to_string_lossy()
                    );
                    std::process::exit(1);
                }

                // Handle recursively adding directories
                match fs::read_dir(path.clone()) {
                    Ok(entries) => {
                        for entry in entries {
                            match entry {
                                Ok(e) => path_queue.push_back(e.path()),
                                Err(e) => {
                                    eprintln!("Error reading directory entry: {error}", error = e);
                                    std::process::exit(1);
                                }
                            }
                        }
                    }
                    Err(e) => {
                        eprintln!(
                            "Error reading directory {path}: {error}",
                            path = path.to_string_lossy(),
                            error = e
                        );
                        std::process::exit(1);
                    }
                }
            } else if path.is_file() {
                files.push((path.to_string_lossy().to_string(), Readable::File(path)))
            } else {
                eprintln!(
                    "Error: {path} is not a file or directory",
                    path = path.to_string_lossy()
                );
                std::process::exit(1);
            }
        }
    }

    files
}
```

## Printing lines

Printing is something I do in a few different places now, mostly to handle the context before and after the lines. 

In addition, there are a bunch of rules:

* Don't print line numbers unless the `-n`/`--line-number` flag is passed
* Don't print filenames if we're only working on one source
* Print filenames for more than one unless `-h`/`--nofilename` is passed
  * Which I also had to manually fix for [clap](https://docs.rs/clap/latest/clap/)'s `--help` flag

So I wrapped it all up in a function:

```rust
fn print_line(
    content: &str,
    line_number: usize,
    path: &str,
    print_line_numbers: bool,
    print_filename: bool,
) {
    if print_line_numbers {
        if print_filename {
            println!(
                "{path}:{no}:{content}",
                path = path,
                no = line_number,
                content = content
            );
        } else {
            println!("{no}:{content}", no = line_number, content = content);
        }
    } else {
        if print_filename {
            println!("{path}:{content}", path = path, content = content);
        } else {
            println!("{content}", content = content);
        }
    }
}
```
