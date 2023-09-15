---
title: "StackLang Part II: The Lexer"
date: '2023-04-16 23:00:00'
programming/languages:
- Rust
- StackLang
programming/topics:
- Assemblers
- Compilers
- Memory
- Data Structures
- Stacks
- Virtual Machines
series:
- StackLang
---
StackLang, part 2: lexing. 

It's quite often the simplest part of implementing a programming language (although parsers for s-expression based languages come close), but it's still something that needs done. So here we go!

<!--more-->

---

Posts in this series:

{{< taxonomy-list "series" "StackLang" >}}

This post:

{{<toc>}}

Full source code for StackLang: [github:jpverkamp/stacklang](https://github.com/jpverkamp/stacklang/)


## General structure

My goal is to split everything out into modules this time around, so we have:

## `main.rs`: The entry point

```rust
use log;
use std::io::BufReader;

mod types;
mod lexer;

#[derive(Parser, Debug)]
#[command(author, version, about, long_about = None)]
struct Args {
    /// Name of the person to greet
    #[arg(short, long)]
    file: String,
}

fn main() {
    pretty_env_logger::init();
    let args = Args::parse();

    let file = std::fs::File::open(args.file).unwrap();
    let tokens = lexer::tokenize(BufReader::new(file));

    log::info!(
        "Tokens: {}",
        tokens
            .iter()
            .map(|token| token.token.clone())
            .collect::<Vec<String>>()
            .join(" ")
    );
}
```

## `types.rs`: The type of Tokens

Easy enough. Next up, we need the type of a token:

```rust
/// A token is a single unit of a program.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Token {
    /// The row of the token in the source code.
    pub row: usize,
    /// The column of the token in the source code.
    pub column: usize,
    /// The token itself.
    pub token: String,
}
```

I want row and column to print where code actually was in error messages. 

## `lexer.rs`: Actually lexing

It's so relatively short that I can actually put it all inline:

```rust
use std::io::BufRead;

use regex::Regex;
use substring::Substring;

use crate::types::Token;

/// Tokenizes a stream of characters into a vector of tokens.
pub fn tokenize(reader: impl BufRead) -> Vec<Token> {
    log::debug!("tokenize()");

    let mut tokens = vec![];
    let token_patterns = vec![
        // single characters
        r"[\{}()\[\]]",
        // <numbers>
        // complex numbers
        r"-?\d+(\.\d*)?[+-]-?\d+(\.\d*)?i",
        // floats (including scientific notation)
        r"-?\d+(\.\d*)?[eE]-?\d+(\.\d*)?",
        // rationals
        r"-?\d+/\d+",
        // hex literals
        r"0x[0-9a-fA-F]+",
        // binary literals
        r"0b[01]+",
        // integers
        r"-?\d+(\.\d*)?",
        // </numbers>
        // strings
        "\"(\\.|[^\"])*\"",
        // basic identifiers, must start with a letter or _
        r"[a-zA-Z][^\{}()\[\]\s\.]*",
        // purely symbolic identifiers, cannot contain letters or numbers
        r"[^a-zA-Z0-9\{}()\[\]\s\.]+",
    ];
    let token_regex = Regex::new(format!("^({})", token_patterns.join("|")).as_str()).unwrap();
    let whitespace_regex = Regex::new(r"^\s+").unwrap();

    // Scan the input line by line tracking rows
    for (row, line) in reader.lines().enumerate() {
        let line = line.unwrap();
        let mut line = line.as_str();
        let mut column = 0;

        log::debug!("tokenize: line {}: {:?}", row, line);

        // Within a row, scan for tokens character by character
        loop {
            // Skip whitespace
            if let Some(c) = whitespace_regex.captures(line) {
                line = line.substring(c[0].len(), line.len());
                column += c[0].len();
            }

            // Read the next token (patterns above)
            if let Some(c) = token_regex.captures(line) {
                // Ignore comments
                if c[0].starts_with('#') {
                    break;
                }

                tokens.push(Token {
                    row,
                    column,
                    token: c[0].to_string(),
                });
                line = line.substring(c[0].len(), line.len());
                column = c[0].len();
            } else if line.len() != 0 {
                panic!("no token found at {row}:{column} = {line:?}");
            }

            if line.len() == 0 {
                break;
            }
        }
    }

    tokens
}
```

The entire point of the thing is to do a few parts:

* Iterate line by line through the input 
  * TODO: Handle multi-line strings, somehow
* Within a string, consume any leading whitespace
* As soon as we have none, try each regex in order
  * If it starts with `#`, it's a comment, don't include in the token stream
  * Return the first matching one
  * Update the column index based on the length of the token
* As soon as the line is empty, we're done, move on

And... that's really it. 

It's probably not the best thing in the world to pass the complexity of parsing directly off to regexes... but they really do exactly what I need.

The only gotcha is that you have to be a little careful about order, since as mentioned I will take the *first* match on the list of regexes. So originally, I had integers parsed first, but it turns out that you'd parse `1/2` as `["1", "/", "2"]` instead of `["1/2"] as I want. That's why you write tests!

Another special case: splitting identifiers. As mentioned in [[StackLang Part I: The Idea]](), I have a rather broad allowance for what can be in an identifier. Anything that isn't already used elsewhere (brackets, whitespaces, and dots) can be part of an identifier, but it has to start with a letter. 

If it doesn't, it falls into the purely symbolic identifiers, which are mostly built in functions (like `+` and `<=`) or special prefixes (like `@` and `!`). We'll see if this continues to make sense. 

## `lexer.rs`: Test cases

Speaking of which:

```rust
#[cfg(test)]
mod test {
    #[test]
    fn test_brackets() {
        let input = "[](){}";
        let tokens = super::tokenize(input.as_bytes());
        assert_eq!(tokens.len(), 6);
        assert_eq!(tokens[0].token, "[");
        assert_eq!(tokens[1].token, "]");
        assert_eq!(tokens[2].token, "(");
        assert_eq!(tokens[3].token, ")");
        assert_eq!(tokens[4].token, "{");
        assert_eq!(tokens[5].token, "}");
    }

    #[test]
    fn test_integers() {
        let input = "1 2 3 100 8675309 0";
        let tokens = super::tokenize(input.as_bytes());
        assert_eq!(tokens.len(), 6);
        assert_eq!(tokens[0].token, "1");
        assert_eq!(tokens[1].token, "2");
        assert_eq!(tokens[2].token, "3");
        assert_eq!(tokens[3].token, "100");
        assert_eq!(tokens[4].token, "8675309");
        assert_eq!(tokens[5].token, "0");
    }

    #[test]
    fn test_negative_integers() {
        let input = "-1 -2 -3 -100 -8675309 -0";
        let tokens = super::tokenize(input.as_bytes());
        assert_eq!(tokens.len(), 6);
        assert_eq!(tokens[0].token, "-1");
        assert_eq!(tokens[1].token, "-2");
        assert_eq!(tokens[2].token, "-3");
        assert_eq!(tokens[3].token, "-100");
        assert_eq!(tokens[4].token, "-8675309");
        assert_eq!(tokens[5].token, "-0");
    }

    #[test]
    fn test_rationals() {
        let input = "1/2 3/4 5/6 7/8 9/10";
        let tokens = super::tokenize(input.as_bytes());
        assert_eq!(tokens.len(), 5);
        assert_eq!(tokens[0].token, "1/2");
        assert_eq!(tokens[1].token, "3/4");
        assert_eq!(tokens[2].token, "5/6");
        assert_eq!(tokens[3].token, "7/8");
        assert_eq!(tokens[4].token, "9/10");
    }

    #[test]
    fn test_floats() {
        let input = "1.0 2.0 3.0 100.0 8675309.0 0.0";
        let tokens = super::tokenize(input.as_bytes());
        assert_eq!(tokens.len(), 6);
        assert_eq!(tokens[0].token, "1.0");
        assert_eq!(tokens[1].token, "2.0");
        assert_eq!(tokens[2].token, "3.0");
        assert_eq!(tokens[3].token, "100.0");
        assert_eq!(tokens[4].token, "8675309.0");
        assert_eq!(tokens[5].token, "0.0");
    }

    #[test]
    fn test_float_scientific() {
        let input = "1e1 1.1e2 1.0e3 1.0e2 8.6e6 0e0";
        let tokens = super::tokenize(input.as_bytes());
        assert_eq!(tokens.len(), 6);
        assert_eq!(tokens[0].token, "1e1");
        assert_eq!(tokens[1].token, "1.1e2");
        assert_eq!(tokens[2].token, "1.0e3");
        assert_eq!(tokens[3].token, "1.0e2");
        assert_eq!(tokens[4].token, "8.6e6");
        assert_eq!(tokens[5].token, "0e0");
    }

    #[test]
    fn test_hex() {
        let input = "0x1 0xFF 0xdeadbeef 0x0";
        let tokens = super::tokenize(input.as_bytes());
        assert_eq!(tokens.len(), 4);
        assert_eq!(tokens[0].token, "0x1");
        assert_eq!(tokens[1].token, "0xFF");
        assert_eq!(tokens[2].token, "0xdeadbeef");
        assert_eq!(tokens[3].token, "0x0");
    }

    #[test]
    fn test_binary() {
        let input = "0b1 0b1111 0b1101 0b0";
        let tokens = super::tokenize(input.as_bytes());
        assert_eq!(tokens.len(), 4);
        assert_eq!(tokens[0].token, "0b1");
        assert_eq!(tokens[1].token, "0b1111");
        assert_eq!(tokens[2].token, "0b1101");
        assert_eq!(tokens[3].token, "0b0");
    }

    #[test]
    fn test_strings() {
        let input = "\"\" \"hello\" \"hello world\" \"hello\\nworld\"";
        let tokens = super::tokenize(input.as_bytes());
        assert_eq!(tokens.len(), 4);
        assert_eq!(tokens[0].token, "\"\"");
        assert_eq!(tokens[1].token, "\"hello\"");
        assert_eq!(tokens[2].token, "\"hello world\"");
        assert_eq!(tokens[3].token, "\"hello\\nworld\"");
    }

    #[test]
    fn test_identifiers() {
        let input = "test fact camelCase snake_case with-symbols?";
        let tokens = super::tokenize(input.as_bytes());
        assert_eq!(tokens.len(), 5);
        assert_eq!(tokens[0].token, "test");
        assert_eq!(tokens[1].token, "fact");
        assert_eq!(tokens[2].token, "camelCase");
        assert_eq!(tokens[3].token, "snake_case");
        assert_eq!(tokens[4].token, "with-symbols?");
    }


    #[test]
    fn test_symbolic() {
        let input = "+ - * &! | ^ ~!! <==";
        let tokens = super::tokenize(input.as_bytes());
        assert_eq!(tokens.len(), 8);
        assert_eq!(tokens[0].token, "+");
        assert_eq!(tokens[1].token, "-");
        assert_eq!(tokens[2].token, "*");
        assert_eq!(tokens[3].token, "&!");
        assert_eq!(tokens[4].token, "|");
        assert_eq!(tokens[5].token, "^");
        assert_eq!(tokens[6].token, "~!!");
        assert_eq!(tokens[7].token, "<==");
    }

    #[test]
    fn test_prefixed() {
        let input = "@fact !fact";
        let tokens = super::tokenize(input.as_bytes());
        assert_eq!(tokens.len(), 4);
        assert_eq!(tokens[0].token, "@");
        assert_eq!(tokens[1].token, "fact");
        assert_eq!(tokens[2].token, "!");
        assert_eq!(tokens[3].token, "fact");
    }
}
```

Is it exhaustive? Probably not. Did it take surprisingly little time to write, since I let Copilot help me? Awesomelutely. 