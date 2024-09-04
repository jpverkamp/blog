---
title: "CodeCrafters: Build Myself an Interpreter"
date: 2024-09-04
draft: true
programming/languages:
- Rust
programming/topics:
- Programming Languages
- Compilers
- Interpreters
- Lexers
- Tokenizers
- Parsers
- Lux
series:
- CodeCrafters
---
Didn't I [[CodeCrafters: Build Myself a Grep|just do one of these]]()? Well, yes. Yes I did. But I love building [compilers and interpreters](/programming/topics/compilers/), so when I saw this one was in beta (and thus free :wink:), I had to try it!

It's directly an implemention of the Lox languages from the [Crafting Interpreters](https://craftinginterpreters.com/) website / book ([[Crafting Interpreters|my review]]()), if incomplete. By the end of the lesson, we'll have:

* A [[wiki:tokenizer]]() that handles parentheses, braces, operators (single and multiple character), whitespace, identifiers, string literals, numeric literals, and keywords
* A [[wiki:parser]]() that can take those tokens and build an [[wiki:abstract syntax tree]]() using [[wiki:recursive descent parsing]]()
* A simple [[wiki:tree walking interpreter]]() for some subset of the language

It doesn't handle all of the syntax (yet). In particular, we don't have functions, control statements like `if` or `while` or custom `class`es. These seem... kind of important! But it's a start and something I can definitely see myself building more on it. 

Let's do it!

{{<toc>}}

## Quick note

This represents the current state of my code as of the writing of this post: [repo](https://github.com/jpverkamp/jp-lox). To see how it changed over time, you can of course look at the [git history](https://github.com/jpverkamp/jp-lox/commits/main/). 

I expect I'll be working on this one a bit more, I've already done a few things after finishing the current state of CodeCrafters. 

## Command line interface

As I have several times before, I used [clap](https://docs.rs/clap/latest/clap/) to write my CLI. 

The original command line interface of the program was supposed to be: `jp-lox (tokenize|parse|evaluate) <filename>`, which works well enough as a clap `Subcommand`, but the problem was that it required duplicating the `input` file for each subcommand. Not my favorite. So instead, I ended up with:

```rust

/// Implementation of the lox programming language for code crafters
#[derive(Debug, ClapParser)]
#[clap(name = "jp-lox", version)]
pub struct Args {
    /// Debug mode
    #[clap(short, long)]
    debug: bool,

    /// Subcommand to run
    #[clap(subcommand)]
    command: Command,

    /// The input file (or - for stdin)
    #[arg(global=true)]
    input: Option<FileOrStdin>,
}

#[derive(Debug, Subcommand)]
enum Command {
    /// Tokenize and print all tokens.
    Tokenize,
    /// Parse and print the AST.
    Parse,
    /// Evaluate the source expression.
    Evaluate,
    /// Run the source program.
    Run,
}
```

This does (for better or for worse) allows the `input` file to be either before or after the command. Since the test cases expect it to be after, that's perfectly fine. It ends up generating this help file:

```bash
# Main help
$ cargo run -- --help

    Finished `dev` profile [unoptimized + debuginfo] target(s) in 0.01s
     Running `target/debug/jp-lox --help`
Implementation of the lox programming language for code crafters

Usage: jp-lox [OPTIONS] [INPUT] <COMMAND>

Commands:
  tokenize  Tokenize and print all tokens
  parse     Parse and print the AST
  evaluate  Evaluate the source expression
  run       Run the source program
  help      Print this message or the help of the given subcommand(s)

Arguments:
  [INPUT]  The input file (or - for stdin)

Options:
  -d, --debug    Debug mode
  -h, --help     Print help
  -V, --version  Print version

# For the tokenize subcommand, basically the same for the others
$ cargo run -- tokenize --help

    Finished `dev` profile [unoptimized + debuginfo] target(s) in 0.01s
     Running `target/debug/jp-lox tokenize --help`
Tokenize and print all tokens

Usage: jp-lox tokenize [INPUT]

Arguments:
  [INPUT]  The input file (or - for stdin)

Options:
  -h, --help  Print help
```

That's not bad! 

The for the rest of `main.rs`, we basically load the input file (handling `-` as stdin as well, to better match [testit]({{<ref "2024-08-19-testit">}})) and then run through each step in turn. If that's the step we stop at, print it's output and exit. 

```rust
fn main() -> Result<()> {
    let args = Args::parse();
    if args.debug {
        env_logger::Builder::new()
            .filter_level(log::LevelFilter::Debug)
            .init();
    } else {
        env_logger::init();
    }

    // ----- Shared filename / contents loading -----

    let source = if args.input.is_none() {
        let name = "<stdin>".to_string();
        let mut contents = String::new();
        std::io::stdin().read_to_string(&mut contents)?;
        NamedSource::new(name, contents)
    } else {
        let input = args.input.unwrap();
        let name = if input.is_file() {
            input.filename().to_string()
        } else {
            "<stdin>".to_string()
        };
        let contents = input.contents()?;
        NamedSource::new(name, contents)
    };

    // ----- Tokenizing -----

    log::debug!("Tokenizing...");
    let mut tokenizer = Tokenizer::new(&source.bytes);

    if let Command::Tokenize = args.command {
        for token in &mut tokenizer {
            println!("{}", token.code_crafters_format());
        }

        if tokenizer.had_errors() {
            for error in tokenizer.iter_errors() {
                eprintln!("{}", error);
            }
            std::process::exit(65);
        }

        return Ok(());
    }

    // ----- Parsing -----

    log::debug!("Parsing...");
    let mut parser = Parser::from(tokenizer);

    let ast = match parser.parse() {
        Ok(ast) => ast,
        Err(e) => {
            eprintln!("{}", e);
            std::process::exit(65);
        }
    };

    if parser.tokenizer_had_errors() {
        for error in parser.tokenizer_iter_errors() {
            eprintln!("{}", error);
        }
        std::process::exit(65);
    }

    if let Command::Parse = args.command {
        println!("{}", ast);
        return Ok(());
    }

    // ----- Evaluating -----

    match args.command {
        Command::Evaluate | Command::Run => {
            let mut env = EnvironmentStack::new();
            let output = match ast.evaluate(&mut env) {
                Ok(value) => value,
                Err(e) => {
                    eprintln!("{}", e);
                    std::process::exit(70);
                }
            };

            // Eval prints the last command, run doesn't
            // For *reasons* numbers should't print .0 here
            if let Command::Evaluate = args.command {
                match output {
                    values::Value::Number(n) => println!("{n}"),
                    _ => println!("{}", output),
                }
            } else if let Command::Run = args.command {
                // Do nothing
            }
        }
        _ => {}
    }

    // Success (so far)
    Ok(())
}
```

That seems pretty decent to me!

## Tokenizer

Next up, `mod tokenizer`. I used a few crates here to make my life a bit cleaner:

* [`convert_case`](https://crates.io/crates/convert_case) - The test cases require output like `LEFT_PAREN` instead of `LeftParen`, this did that for free ([comments](#thoughts))
* [`derive_more`](https://crates.io/crates/derive_more) - Adds the ability to `#[derive(Display)]`, which is nice
* [`thiserror`](https://crates.io/crates/thiserror) - Simplifies error handling, I started a conversion to this from only `anyhow!`. I'm not sure what to think about this. 

After that, we have a `Token`. This ends up being fairly simple:

```rust
// span.rs
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct Span {
    pub line: usize,
    pub start: usize,
    pub end: usize,
}

// tokenizer.rs
#[derive(Debug, Display, Clone, PartialEq)]
pub enum Token {
    EOF,

    #[display("{}", _1)]
    Keyword(Span, Keyword),

    #[display("{}", _2)]
    Literal(Span, String, Value),

    #[display("{}", _1)]
    Identifier(Span, String),
}
```

A `Keyword` is any reserved `Identifier` and also includes symbolic operators. So things like `print` but also things like `+` and `==`. 

### Keywords and the `const_enum!` macro

So to write the keywords, I originally had code like this:

```rust 
pub enum Keyword {
    LeftParen,
    RightParen,
    // ...
}

impl From<&str> for Keyword {
    fn from(s: &str) -> Self {
        match s {
            "(" => Keyword::LeftParen,
            ")" => Keyword::RightParen,
            // ...
            _ => panic!("Unknown keyword: {}", s),
        }
    }
}

impl Into<&str> for Keyword {
    fn into(self) -> &'static str {
        match self {
            Keyword::LeftParen => "(",
            Keyword::RightParen => ")",
            // ...
        }
    }
}
```

This got kind of annoying. So I wrote a macro that let me do this:

```rust
// Define keywords which are based on strings
const_enum! {
    pub Keyword as &str {
        // Match these first to avoid partial matches (ex == vs =)
        EqualEqual => "==",
        BangEqual => "!=",
        LessEqual => "<=",
        GreaterEqual => ">=",

        And => "and",
        Class => "class",
        Else => "else",
        False => "false",
        For => "for",
        Fun => "fun",
        If => "if",
        Nil => "nil",
        Or => "or",
        Print => "print",
        Return => "return",
        Super => "super",
        This => "this",
        True => "true",
        Var => "var",
        While => "while",

        LeftParen => "(",
        RightParen => ")",
        LeftBrace => "{",
        RightBrace => "}",
        Comma => ",",
        Dot => ".",
        Semicolon => ";",
        Plus => "+",
        Minus => "-",
        Star => "*",
        Slash => "/",
        Equal => "=",
        Bang => "!",
        Less => "<",
        Greater => ">",
    }
}
```

This defines the enum, implements `TryFrom`, implements `to_value` (rather than `Into` for no particular reason), and implements `values()` which returns a `Vec` of all options in a map. 

Just like this:

```rust
#[macro_export]
macro_rules! const_enum {
    ($vis:vis $name:ident as $type:ty {
        $($value:ident => $char:expr),+
        $(,)?
    }) => {
        #[derive(Debug, Display, Clone, Copy, PartialEq, Eq)]
        $vis enum $name {
            $($value),+
        }

        impl $name {
            pub fn to_value(&self) -> $type {
                match *self {
                    $(
                        $name::$value => $char,
                    )+
                }
            }

            #[allow(dead_code)]
            pub fn values() -> Vec<$name> {
                vec![$($name::$value),+]
            }
        }

        impl TryFrom<$type> for $name {
            type Error = ();

            fn try_from(value: $type) -> Result<Self, Self::Error> {
                match value {
                    $(
                        $char => Ok($name::$value),
                    )+
                    _ => Err(()),
                }
            }
        }
    };
}
```

That's pretty clean! 

### The `Tokenizer` struct

Next up, the `Tokenizer` struct itself:

```rust
// The current state of the tokenizer, use it as an iterator (in general)
#[derive(Debug)]
pub struct Tokenizer<'a> {
    // Internal state stored as raw bytes
    pub(crate) source: &'a str,
    byte_pos: usize,

    // Internal state stored as utf8 characters, processed once
    chars: Vec<char>,
    char_pos: usize,

    // The current position of the iterator in the source code
    line: usize,

    // Flag that the iterator has already emitted EOF, so should not iterate any more
    emitted_eof: bool,

    // Collect tokenizer errors this tokenizer has encountered.
    errors: Vec<TokenizerError>,

    // The currently peeked token
    peeked: Option<Token>,
}
```

This takes in the source code and keeps track of where in the token steam it is. Basically, we're going to `impl Iterator<Item = Token>` (technically with `Peekable` inlined as well, see [Peeking into the tokenizer](#peeking-into-the-tokenizer)). 

### `impl Iterator<Item = Token>`

```rust
impl<'a> Iterator for Tokenizer<'a> {
    type Item = Token;

    fn next(&mut self) -> Option<Self::Item> {
        // We've already consumed the iterator
        if self.emitted_eof {
            return None;
        }

        // If we have a peeked token, clear and return it
        if let Some(token) = self.peeked.take() {
            log::debug!("Clearing peeked token: {}", token);
            self.peeked = None;
            return Some(token);
        }

        // We've reached the end of the source
        if self.char_pos >= self.chars.len() {
            log::debug!("Reached EOF");

            self.emitted_eof = true;
            return Some(Token::EOF);
        }

        // Try to match comments, from // to EOL
        if self.char_pos < self.chars.len() - 1
            && self.chars[self.char_pos] == '/'
            && self.chars[self.char_pos + 1] == '/'
        {
            log::debug!("Matching comment");

            while self.char_pos < self.chars.len() && self.chars[self.char_pos] != '\n' {
                self.char_pos += 1;
                self.byte_pos += 1;
            }

            return self.next();
        }

        // Read strings, currently there is no escaping, so read until a matching " or EOL
        // If we reach EOL, report an error and continue on the next line
        if self.chars[self.char_pos] == '"' {
            log::debug!("Matching string");

            let mut value = String::new();
            let start = self.char_pos;
            self.char_pos += 1;
            self.byte_pos += 1;

            loop {
                if self.char_pos >= self.chars.len() {
                    let error_span = Span {
                        line: self.line,
                        start,
                        end: self.char_pos,
                    };
                    self.errors
                        .push(TokenizerError::UnterminatedString(error_span));
                    return self.next();
                }

                if self.chars[self.char_pos] == '"' {
                    break;
                }

                if self.chars[self.char_pos] == '\n' {
                    self.line += 1
                }

                let c = self.chars[self.char_pos];
                value.push(c);

                self.byte_pos += c.len_utf8();
                self.char_pos += 1;
            }

            // Consume closing "
            self.char_pos += 1;
            self.byte_pos += 1;
            let end = self.char_pos;

            return Some(Token::Literal(
                Span {
                    line: self.line,
                    start,
                    end,
                },
                format!("\"{value}\""),
                Value::String(value),
            ));
        }

        // Read numbers
        // Numbers must start with a digit (cannot do .1)
        // Numbers can contain a single . (cannot do 1.2.3)
        // Numbers must have a digit after the . (cannot do 1. That's two tokens)
        if self.chars[self.char_pos].is_digit(10) {
            log::debug!("Matching number");

            let mut lexeme = String::new();
            let mut has_dot = false;
            let mut last_dot = false;
            let start = self.char_pos;

            while self.char_pos < self.chars.len() {
                let c = self.chars[self.char_pos];

                if c.is_digit(10) {
                    lexeme.push(c);
                    last_dot = false;
                } else if c == '.' && !has_dot {
                    lexeme.push(c);
                    has_dot = true;
                    last_dot = true;
                } else {
                    break;
                }

                self.char_pos += 1;
                self.byte_pos += 1;
            }

            // If the last character was a dot, we need to back up
            if last_dot {
                lexeme.pop();
                self.char_pos -= 1;
                self.byte_pos -= 1;
            }

            let value: f64 = lexeme.parse().unwrap();
            let end = self.char_pos;

            return Some(Token::Literal(
                Span {
                    line: self.line,
                    start,
                    end,
                },
                lexeme,
                Value::Number(value),
            ));
        }

        // Read constant values
        for (lexeme, value) in Value::CONSTANT_VALUES.iter() {
            let lexeme_chars = lexeme.chars().collect::<Vec<_>>();
            if self.chars[self.char_pos..].starts_with(&lexeme_chars) {
                log::debug!("Matching constant: {}", lexeme);

                let start = self.char_pos;
                self.char_pos += lexeme.len();
                self.byte_pos += lexeme.len();
                let end = self.char_pos;
                return Some(Token::Literal(
                    Span {
                        line: self.line,
                        start,
                        end,
                    },
                    lexeme.to_string(),
                    value.clone(),
                ));
            }
        }

        // Match identifiers
        // Identifiers start with a letter or _
        // Identifiers can contain letters, numbers, and _
        if self.chars[self.char_pos].is_alphabetic() || self.chars[self.char_pos] == '_' {
            log::debug!("Matching identifier");

            let mut value = String::new();
            let start = self.char_pos;

            while self.char_pos < self.chars.len() {
                let c = self.chars[self.char_pos];

                if c.is_alphanumeric() || c == '_' {
                    value.push(c);
                } else {
                    break;
                }

                self.char_pos += 1;
                self.byte_pos += 1;
            }

            let end = self.char_pos;

            // Check if it's actually a keyword
            // This is called 'maximal munch', so superduper doesn't get parsed as <super><duper>
            if let Ok(keyword) = Keyword::try_from(value.as_str()) {
                return Some(Token::Keyword(
                    Span {
                        line: self.line,
                        start,
                        end,
                    },
                    keyword,
                ));
            } else {
                return Some(Token::Identifier(
                    Span {
                        line: self.line,
                        start,
                        end,
                    },
                    value,
                ));
            }
        }

        // Match remaining keywords, this will include ones that are symbolic
        for keyword in Keyword::values() {
            let pattern = keyword.to_value();
            let pattern_chars = pattern.chars().collect::<Vec<_>>();

            if self.chars[self.char_pos..].starts_with(&pattern_chars) {
                log::debug!("Matching keyword: {}", keyword);

                let start = self.char_pos;
                self.byte_pos += pattern.len();
                self.char_pos += pattern_chars.len();
                let end = self.char_pos;

                return Some(Token::Keyword(
                    Span {
                        line: self.line,
                        start,
                        end,
                    },
                    keyword,
                ));
            }
        }

        // The only things that should be left are whitespace
        // Anything else is an error
        let c = self.chars[self.char_pos];
        self.char_pos += 1;
        self.byte_pos += c.len_utf8();

        // Newlines don't emit a token, but '\n' does increment the line number
        if c.is_whitespace() {
            if c == '\n' {
                self.line += 1;
            }
            return self.next();
        }

        // Anything else should emit an error and continue as best we can
        self.errors.push(TokenizerError::UnexpectedCharacter(
            Span {
                line: self.line,
                start: self.char_pos,
                end: self.char_pos,
            },
            c,
        ));
        self.next()
    }
}
```

I actually think this turned out fairly clean. We're using `self` to keep track of the current state, so basically we consume as much of that as we need to for whatever the next token is. 

Along that time, we also need to track a `Span` for where each token came from. Eventually, I want to put that in a [wrapper type `Spanned`](#spanned), but not for now. 

And that's it, we have a working `tokenizer`!

```bash
$ echo 'print "Hello" + " World!";' | jp-lox tokenize -

PRINT print null
STRING "Hello" Hello
PLUS + null
STRING " World!"  World!
SEMICOLON ; null
EOF  null
```

Pretty cool. 

## Parser

Okay, next up, we want to take that stream of tokens and turn it in an [[wiki:abstract syntax tree]](). There are a few different algorithms for this, but we'll go ahead and implement the [[wiki:recursive descent parser]]() from the book (and recommended by CodeCrafters). For that, we have a series of nested `parse_X` functions. 

### `AstNode` struct

But first, the struct, constructor, and a `Display` function that outputs [[wiki:s-expressions]]():

```rust
#[derive(Debug)]
pub struct Parser<'a> {
    tokenizer: Tokenizer<'a>,
}

#[derive(Debug)]
pub enum AstNode {
    Literal(Span, Value),
    Symbol(Span, String),

    Group(Span, Vec<AstNode>), // No new scope
    Block(Span, Vec<AstNode>), // New scope

    Application(Span, Box<AstNode>, Vec<AstNode>),

    Declaration(Span, String, Box<AstNode>), // Creates new variables
    Assignment(Span, String, Box<AstNode>),  // Sets values, error on undeclared

    Program(Span, Vec<AstNode>),
}

impl<'a> From<Tokenizer<'a>> for Parser<'a> {
    fn from(value: Tokenizer<'a>) -> Self {
        Parser { tokenizer: value }
    }
}

impl Display for AstNode {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            AstNode::Literal(_, value) => write!(f, "{}", value),
            AstNode::Symbol(_, name) => write!(f, "{}", name),
            AstNode::Declaration(_, name, value) => write!(f, "(var {} {})", name, value),
            AstNode::Assignment(_, name, value) => write!(f, "(= {} {})", name, value),

            AstNode::Group(_, nodes) => {
                write!(f, "(group")?;
                for node in nodes {
                    write!(f, " {}", node)?;
                }
                write!(f, ")")?;

                std::fmt::Result::Ok(())
            }

            AstNode::Block(_, nodes) => {
                write!(f, "{{")?;
                let mut first = true;
                for node in nodes {
                    if first {
                        write!(f, "{}", node)?;
                        first = false;
                    } else {
                        write!(f, " {}", node)?;
                    }
                }
                write!(f, "}}")?;

                std::fmt::Result::Ok(())
            }

            AstNode::Application(_, func, args) => {
                write!(f, "({}", func)?;
                for arg in args {
                    write!(f, " {}", arg)?;
                }
                write!(f, ")")?;

                std::fmt::Result::Ok(())
            }

            AstNode::Program(_, nodes) => {
                for node in nodes {
                    write!(f, "{}\n", node)?;
                }

                std::fmt::Result::Ok(())
            }
        }
    }
}
```

### `parse_X` functions

First, at the 'top' of the parse tree, the `parse` function itself. Takes the (internal) tokenizer and repeatedly `parse_declaration` until we have a `Program`:

```rust
impl Parser<'_> {
    pub fn parse(&mut self) -> Result<AstNode> {
        let mut nodes = vec![];
        let mut span = Span::ZERO;

        while let Some(token) = self.tokenizer.peek() {
            if token == &Token::EOF {
                break;
            }

            let node = self.parse_declaration()?;
            span = span.merge(&node.span());
            nodes.push(node);
        }

        Ok(AstNode::Program(span, nodes))
    }
}
```

Why `parse_declaration`? That's the highest level of binding, a statement that is either `var x;` or `var y = 5;` or a `parse_statement`:

```rust
fn parse_declaration(&mut self) -> Result<AstNode> {
    log::debug!("parse_declaration");

    match self.tokenizer.peek() {
        Some(Token::Keyword(_, Keyword::Var)) => self.parse_var_statement(),
        _ => self.parse_statement(),
    }
}
```

Likewise, `parse_statement` is a block (if the next token is `{`), a `print` statement, or falls through to an `expression_statement`. 

`parse_block` is an interesting one, since it parses until it sees a `}` but otherwise 'escapes' all the way back up to `parse_declaration`:

```rust
fn parse_block(&mut self) -> Result<AstNode> {
    let left_brace = self.tokenizer.next().unwrap();
    let span = left_brace.span();
    log::debug!("parse_block @ {span:?}");

    let mut nodes = vec![];
    while let Some(token) = self.tokenizer.peek() {
        if let Token::Keyword(_, Keyword::RightBrace) = token {
            break;
        }

        let node = self.parse_declaration()?;
        nodes.push(node);
    }

    let right_brace = self.tokenizer.next().unwrap();
    let span = span.merge(&right_brace.span());

    Ok(AstNode::Block(span, nodes))
}
```

Next down the tree, we have `parse_expression_statement`. This one I diverged a bit from the expected code, since I want to be able to parse either single expressions (`2 + 3`) or statements (ending with `;`). So I have to have each end with either a `;` or the end of file:

```rust
fn parse_expression_statement(&mut self) -> Result<AstNode> {
    let expression = self.parse_expression()?;

    // TODO: Should the span include this ;?
    // Currently I can't, since I can't set the expresion's span
    self.consume_semicolon_or_eof()?;

    Ok(expression)
}
```

And so on we continue down the tree, parsing each expression in descending order of precedence. This is how [[wiki:recursive descent parsers]]() handle correctly building a tree for something like `2 + 3 * 4` with `3 * 4` evaluated first. 

But in the end, that's all we need to make a parser!

```bash
echo '
var x = "Hello";
var y = " World!";
print x + y;
' | jp-lox parse -

(var x "Hello")
(var y " World!")
(print (+ x y))
```

Not bad, eh? 

### Peeking into the tokenizer

One thing that we did use a few times in various `parse_X` functions was `Tokenizer::peek`. Originally I stored the `Parser` as

```rust
#[derive(Debug)]
pub struct Parser<'a> {
    tokenizer: Peekable<Tokenizer<'a>>,
}
```

Which worked for that, but meant that I couldn't get direct access to any of the methods on `Tokenizer` (since they're not on `Peekable` and you can't get a reference). So instead, I just implemented `.peek()`  myself on `Tokenizer`. If we call `.peek()`, get the `.next()` value, cache it, and return it. If we have a cached value when we `.next()`, clear the cache, and return it. It's just that east! (I expect that's how `Peekable` is implemented.)

## Evaluator

Okay, we've got an AST, so we should be able to evaluate it, yes? Well, there are actually two different commands that we might want to do here:

```bash
$ echo '2 + 3' | jp-lox evaluate

5

$ echo '2 + 3' | jp-lox run

$ echo 'print(2 + 3);' | jp-lox evaluate

5
nil

$ echo 'print(2 + 3);' | jp-lox run

5
```

Essentially, `evaluate` will run a single expression (or a sequence of expressions) and print out the result of the last expression (thus the extra `nil` in the third example). 

`run` on the other hand is designed for entire programs and will not print out anything that isn't `print`ed. 

Weird distinction? A bit. But it works. 

### An `Evaluate` trait

So I wanted to leave myself the option of being able to `Evaluate` other things than `AstNode`, so I made `Evaluate` a `trait` instead:

```rust
pub trait Evaluate {
    fn evaluate(&self, env: &mut impl Environment<Value>) -> Result<Value>;
}
```

Originally, I didn't have that `Environment`, we'll cover that [in a bit](#adding-the-environment). 

Evaluation (at this level), is actually surprisingly straight forward. If we have a leaf node (like a `Literal`), return it's value. Otherwise, evaluate any child nodes (like for a `Program` or the `args` to a `Builtin`) recursively then evaluate me. 

Here, we use the `env` in `Symbol` (if we're getting an `Identifier` that we defined with a `var` earlier) or in `var` / assignment. We also introduce scopes with `Block`, again we'll [come back to that](#adding-the-environment).

```rust
impl Evaluate for AstNode {
    fn evaluate(&self, env: &mut impl Environment<Value>) -> Result<Value> {
        match self {
            AstNode::Literal(_, value) => Ok(value.clone()),
            AstNode::Symbol(span, name) => {
                // Keywords become builtins; fall back to env; then error
                if Keyword::try_from(name.as_str()).is_ok() {
                    return Ok(Value::Builtin(name.clone()));
                }

                match env.get(name) {
                    Some(value) => Ok(value),
                    None => {
                        let line = span.line;
                        Err(anyhow!("[line {line}] Undefined variable '{name}'"))
                    }
                }
            }

            AstNode::Program(_, nodes) | AstNode::Group(_, nodes) => {
                let mut last = Value::Nil;
                for node in nodes {
                    last = node.evaluate(env)?;
                }

                Ok(last)
            }

            AstNode::Block(_, nodes) => {
                env.enter();

                let mut last = Value::Nil;
                for node in nodes {
                    last = node.evaluate(env)?;
                }

                env.exit();

                Ok(last)
            }

            AstNode::Application(_span, func, args) => {
                let mut arg_values = Vec::new();
                for arg in args {
                    arg_values.push(arg.evaluate(env)?);
                }
                
                match func.evaluate(env)? {
                    Value::Builtin(name) => {
                        let callable = BuiltIn::try_from(name.as_str())?;
                        callable.call(arg_values)
                    }
                    _ => unimplemented!("Only built ins are implemented"),
                }
            }

            AstNode::Declaration(_, name, body) => {
                let value = body.evaluate(env)?;
                env.set(name, value.clone());
                Ok(value)
            }

            AstNode::Assignment(span, name, body) => {
                if env.get(name).is_none() {
                    let line = span.line;
                    return Err(anyhow!("[line {line}] Undefined variable '{name}'"));
                }

                let value = body.evaluate(env)?;
                env.set(name, value.clone());
                Ok(value)
            }
        }
    }
}
```

And that's enough to evaluate a program!

```bash
$ echo '
var x = "Hello";
var y = " World!";
print x + y;
' | jp-lox run -

Hello World!
```

Not bad!

### Adding the environment

The first missing piece that you might be wondering about is the `Environment`. For that, we want to implement another trait:

```rust
pub trait Environment<T> {
    fn get(&self, key: &str) -> Option<T>;
    fn set(&mut self, key: &str, value: T);
    fn enter(&mut self);
    fn exit(&mut self);
}
```

There are a few different ways that we can implement an `Environment`, but we always need to be able to `get`/`set` values and `enter`/`exit` scopes introduced by blocks. 

For this specific implementation, I made an `EnvironmentStack<T>`:

```rust
pub struct EnvironmentStack<T> {
    stack: Vec<Vec<(String, T)>>,
}

impl<T> EnvironmentStack<T> {
    pub fn new() -> Self {
        Self {
            stack: vec![vec![]],
        }
    }
}

impl<T: Clone> Environment<T> for EnvironmentStack<T> {
    fn get(&self, key: &str) -> Option<T> {
        for frame in self.stack.iter().rev() {
            for (k, v) in frame.iter().rev() {
                if k == key {
                    return Some(v.clone());
                }
            }
        }

        None
    }

    fn set(&mut self, key: &str, value: T) {
        self.stack
            .last_mut()
            .unwrap()
            .push((key.to_string(), value));
    }

    fn enter(&mut self) {
        self.stack.push(vec![]);
    }

    fn exit(&mut self) {
        self.stack.pop();
    }
}
```

This stores each value as an [[wiki:association list]]() with another list of those as scopes. When we `enter` a scope, add a new association list. `exit` pops the most recent. `get` starts at the end and down the stack until we either find the value or run out. `set` always writes to the top level... which may be an error now that I think about it. 

What should this output?

```lox
var x = 5;
{
  x = 6;
  {
    var x = 7;
    print x;
  }
  print x;
}
print x;
```

I think that the `x = 6` should actually mutate the value assigned at the outer scope (with the `var x = 5;`), resulting in `7 5 5`. But because of how I implemented `set`, it outputs `7 6 5`. Oops!

The current interface doesn't actually work with this. We'd need another `define` method. Or a `get_mut` method.

In any case, you might be wondering, why `EnvironmentStack<T>`? Especially when I'm always going to be storing `Values`? 

Well, I'm not!

I haven't done it yet ([future work](#typed)), but my goal is to be able to typecheck programs (so we can tell if you're trying to `5 + "strings"`). When doing that, I'll actually pseudo-evaulate the program, but instead of storing the actual values, I'll store `EnvironmentStack<Type>`. Or that's the plan. We'll see!

### Builtins

Another thing you might have noticed is this block:

```rust
AstNode::Application(_span, func, args) => {
    let mut arg_values = Vec::new();
    for arg in args {
        arg_values.push(arg.evaluate(env)?);
    }
    
    match func.evaluate(env)? {
        Value::Builtin(name) => {
            let callable = BuiltIn::try_from(name.as_str())?;
            callable.call(arg_values)
        }
        _ => unimplemented!("Only built ins are implemented"),
    }
}
```

What is `let callable = BuiltIn::try_from(name.as_str())?;` and how does that work? 

I went through a few different iterations of this, but again with the [future typechecking](#typed) work, I wanted a central way to define builtins. So I ended up with this lovely macro:

```rust
macro_rules! define_builtins {
    (
        $(
            $variant:ident
            $token:literal 
            {
                $(
                    $args_pat:pat => $body:tt
                ),+
                $(,)?
            }
        ),+ 
        $(,)?
    ) => {
        #[derive(Debug, Clone, Copy, PartialEq, Eq)]
        pub enum BuiltIn {
            $($variant),+
        }

        impl TryFrom<&str> for BuiltIn {
            type Error = anyhow::Error;

            fn try_from(s: &str) -> Result<Self> {
                match s {
                    $($token => Ok(BuiltIn::$variant),)+
                    _ => Err(anyhow!("Unknown builtin: {}", s)),
                }
            }
        }

        impl BuiltIn {
            #[allow(unused_braces)]
            pub fn call(&self, args: Vec<Value>) -> Result<Value> {
                match self {
                    $(BuiltIn::$variant => { // Each builtin by symbol, eg +
                        match args.as_slice() {
                            $(
                                $args_pat => { Ok($body) },
                            )+
                            _ => Err(anyhow!("Invalid arguments {args:?} for builtin: {}", stringify!($variant))),
                        }
                    },)+
                }
            }
        }
    };
}
```

That... is a crazy looking thing. But what it ends up doing is it lets me define builtins (with overloading!) like this:

```rust
define_builtins!{
    // Arithmetic
    Plus "+" {
       [Number(a), Number(b)] => { Number(a + b) },
       [String(a), String(b)] => { 
            let mut result = std::string::String::new();
            result.push_str(&a);
            result.push_str(&b);
            String(result)
       },
    },
    Minus "-" {
        [Number(a), Number(b)] => { Number(a - b) },
        [Number(v)] => { Number(-v) },
    },
    Times "*" {
        [Number(a), Number(b)] => { Number(a * b) },
    },
    Divide "/" {
        [Number(a), Number(b)] => { Number(a / b) },
    },

    // ...
    
    // I/O
    Print "print" {
        [Number(n)] => { println!("{}", n); Nil },
        [a] => { println!("{}", a); Nil },
    },
}
```

We have the `$variant` that ends up stored directly in the `enum`, a `&str` that we can look up which function we want by (I could have and probably will combine(d) this with my `Keywords`, but haven't yet), and a `match` like syntax that lets us unpack the `args` and match directly against them. 

Pretty cool. Not going to lie. 

It's even better, because it basically gives us syntax errors inline + lets us overload based on types. 

This was pretty fun to write. 

## Future work

So. We have a very (very) basic lox program that can tokenize, parse, and evaluate simple lox programs. That's enough to implement everything CodeCrafters has as of now... but what else can I do with this? 

### Finish parsing

Well, for one I can finish parsing/evaluating the rest of the language. At the very least (based on our keywords), we need to implement:

* control flow like `if` and `while`
* functions with `fun` and `return`
* [[wiki:object oriented]]() goodness with `class`, `this`, `.` (dot), and `super`

At the very least, I want to do the first two. We need control flow to make useful programs. And functions allow us to actually write pretty much everything. I'll probably do OO as well though. 

### Spanned

Another thing I want to do is rewrite how I handle spans. Currently, I have the `Span` as a field on `Token` and `AstNode`, but I don't like it. Instead, I'd rather wrap them both in `Spanned<T>`. I think I might end up with issues like `Peekable` had, but we'll see. 

### Better error output

Most of the output format was required by CodeCrafters. I'd really like to pull in something like the [miette](https://docs.rs/miette/latest/miette/) crate to be able to point to the specific location in the source code where the errors are. 

### Typed

Like `Spanned` [above](#spanned), I'd also like to be able to add another level to the program (before `evaluate`) that handles [[wiki:type checking]](). Specifically, I'm thinking of making it return `Typed<AstNode>` with a type assigned to every node recursively. We'll see if that works with the recursive nature of `AstNode`, it might not!

### WASM Compiler

I want to be able to compile the code. What better than compiling to WASM. It would give me a reason to learn about how `SharedMemory` works (for strings). 

On the other hand, I never did quite get to it (yet) for [[StackLang]]() so... we shall see!

## Thoughts

This was a fun prompt. I've been meaning to do it since I [[Crafting Interpreters|read the book]]() and this was a good excuse. I think the CodeCrafters implementation needs some work (at least `if` and `while`, if not the rest, along with output weirdness (see below)), but it's a good start and I'm glad to have done it!

Onward!

## Code crafters output format

The tokenizer test cases required a very specific format to match what was in the original Crafting Interpreters book. For example, a number that came from the token `10.40` should be output as `NUMBER 10.40 10.4` (the type, [[wiki:lexeme]](), and value). 

Not a huge fan, but I did write a function `Token::code_crafters_format` to handle this:

```rust
// Code crafters requires a very specific output format, implement it here
impl Token {
    pub fn code_crafters_format(&self) -> String {
        match self {
            Token::EOF => "EOF  null".to_string(),
            Token::Keyword(_, keyword) => {
                let name = keyword.to_string().to_case(Case::ScreamingSnake);
                let lexeme = keyword.to_value();

                format!("{name} {lexeme} null")
            }
            Token::Literal(_, lexeme, value) => {
                let name = match value {
                    Value::Nil => {
                        return "NIL nil null".to_string();
                    }
                    Value::Bool(_) => {
                        let name = value.to_string().to_case(Case::ScreamingSnake);
                        return format!("{name} {value} null");
                    }
                    Value::Number(_) => "NUMBER",
                    Value::String(_) => "STRING",
                    Value::Builtin(_) => "BUILTIN",
                };
                format!("{name} {lexeme} {value}")
            }
            Token::Identifier(_, name) => {
                format!("IDENTIFIER {name} null")
            }
        }
    }
}
```
