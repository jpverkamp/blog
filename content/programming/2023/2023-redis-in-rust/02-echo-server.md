---
title: "Redis in Rust: An Echo Server [Part 2]"
date: 2023-02-04 23:00:00
programming/languages:
- Rust
programming/topics:
- Redis
- Networking
- Server
- TCP
series:
- Cloning Redis in Rust
---
Following up from [[Cloning Redis in Rust: RESP [Part 1]]](), we can parse the protocol. So now... let's do something with it. 

The obvious(ish) next step, in my mind? Make a server. It's all going to be over the network eventually, so it's either here or storing data. Here it is!

Specifically, my goal is *not* to build the networking and data structures for this project from scratch. Where there are primitives or libraries that will do something like networking for me, I'm going to use them. 

Ergo:

- [`tokio`](https://docs.rs/tokio/latest/tokio/) for networking (+ async)
- [`tracing`](https://docs.rs/tracing/latest/tracing/) for logging

So, how do I write a simple server in Tokio? 

{{<toc>}}

<!--more-->

## I'm listening!

Okay, very first version. Let's start up Tokio, listen on a port, get a client, and say hello. 

```rust
use tokio::net::{TcpListener, TcpStream};
use tokio::io::{AsyncWriteExt};

#[tokio::main]
async fn main() -> std::io::Result<()> {
    let addr = "0.0.0.0:6379";

    let listener = TcpListener::bind(addr).await?;
    
    loop {
        let (stream, _) = listener.accept().await?;
        let _result = handle(stream).await;
    }
}

async fn handle(mut stream: TcpStream) -> std::io::Result<()> {
    stream.write_all("Hello world!\n".as_bytes()).await?;
    Ok(())
}
```

One thing to note is that this does have `cargo add tokio --features full`:

```bash
cargo add tokio --features full

    Updating crates.io index
      Adding tokio v1.25.0 to dependencies.
             Features:
             + bytes
             + fs
             + full
             + io-std
             + io-util
             + libc
             + macros
             + memchr
             + net
             + num_cpus
             + parking_lot
             + process
             + rt
             + rt-multi-thread
             + signal
             + signal-hook-registry
             + socket2
             + sync
             + time
             + tokio-macros
             - mio
             - stats
             - test-util
             - tracing
             - windows-sys
```

That gives us the macro for `#[tokio::main]` (which allows us to make `main` `async` and handles setting up a task runner for us), the `TcpListener` and `TcpStream` modules that are specific to Tokio, and also `AsyncWriteExt` which lets us call `stream.write_all`. I'm not 100% sure why it's all broken up like that. Binary size? Compilation time? 

In any case, it's not much code. It just starts up a server with `TcpListener::bind`, waiting for connections. For each connection, just say hi. 

```bash
# Server
$ cargo run --bin server

   Compiling redis-rs v0.1.0 (/Users/jp/Projects/redis-rs)
    Finished dev [unoptimized + debuginfo] target(s) in 1.02s
     Running `target/debug/server`

# Client
$ nc localhost 6379

Hello world!
```

Sweet. 

## What did you say again?

Okay, so the server can talk to the client. What about the reverse? Can we read from the client?

To be able to `stream.read`, we need a buffer for it to read into. Handle that and go ahead and do the `.await?` thing to allow it to run `async` (although we're not actually doing that well yet, I'll come back to that...) and return errors immediately (the `?`). 

```rust
use tokio::net::{TcpListener, TcpStream};
use tokio::io::{AsyncReadExt, AsyncWriteExt};

#[tokio::main]
async fn main() -> std::io::Result<()> {
    let addr = "0.0.0.0:6379";

    let listener = TcpListener::bind(addr).await?;
    
    loop {
        let (stream, _) = listener.accept().await?;
        let _result = handle(stream).await;
    }
}

async fn handle(mut stream: TcpStream) -> std::io::Result<()> {
    stream.write_all("Hello world!\n".as_bytes()).await?;

    let mut buf = [0; 1024];
    loop {
        let bytes_read = stream.read(&mut buf).await?;
        if bytes_read == 0 {
            break;
        }

        println!("From client: {:?}", &buf[0..bytes_read]);
        stream.write_all(&buf[0..bytes_read]).await?;
    }
    
    Ok(())
}
```

Trying it out? 

```bash
# Server
$ cargo run --bin server

   Compiling redis-rs v0.1.0 (/Users/jp/Projects/redis-rs)
    Finished dev [unoptimized + debuginfo] target(s) in 0.52s
     Running `target/debug/server`
From client: [72, 111, 119, 32, 97, 114, 101, 32, 121, 111, 117, 63, 10]
From client: [71, 111, 111, 100, 32, 98, 121, 101, 10]

# Client
$ nc localhost 6379

Hello world!
How are you?
How are you?
Good bye
Good bye
^C
```

Sweet. 

But we have a bit of a problem:

```bash
# Server
cargo run --bin server

    Finished dev [unoptimized + debuginfo] target(s) in 0.44s
     Running `target/debug/server`

# Client 1
$ nc localhost 6379

# Client 2
$ nc localhost 6379

# Client 1 RECV: Hello world!
# Client 1 SEND: Hello from 1
# Server: From client: [72, 101, 108, 108, 111, 32, 102, 114, 111, 109, 32, 49, 10]
# Client 1 RECV: Hello from 1
# Client 2 SEND: Hello from 2
# ...
# Client 2 SEND: Hello? Are you listening? 
# ...
# Client 1 SEND: Hello again from 1
# Server: From client: [72, 101, 108, 108, 111, 32, 50, 32, 102, 114, 111, 109, 32, 49, 10]
# Client 1 RECV: Hello again from 1
# Client 1 CLOSE
# Client 2 RECV: Hello world!
# Server: From client: [72, 101, 108, 108, 111, 32, 102, 114, 111, 109, 32, 50, 10, 72, 101, 108, 108, 111, 32, 50, 32, 102, 114, 111, 109, 32, 50, 10]
# Client 2 RECV: Hello from 2
# Client 2 RECV: Hello? Are you listening? 
```

In a nutshell, we're not actually handling these clients asynchronously at all. Luckily, netcat buffered for us, so when the first client let go, the second client got `accepted` and the server responded. But what we really want is to be able to talk to 2 (or even more?!) clients at the same time. 

## Actually asynchronously 

It's actually amazing how easy this part is with Tokio:

```rust

use tokio::net::{TcpListener, TcpStream};
use tokio::io::{AsyncReadExt, AsyncWriteExt};

#[tokio::main]
async fn main() -> std::io::Result<()> {
    let addr = "0.0.0.0:6379";

    let listener = TcpListener::bind(addr).await?;
    
    loop {
        let (stream, _) = listener.accept().await?;

        tokio::spawn(async move {
            let _result = handle(stream).await;
        });
    }
}

async fn handle(mut stream: TcpStream) -> std::io::Result<()> {
    // ...
}
```

That's it. That's the difference. We just need to wrap the call to `handle` in `tokio::spawn` and essentially for free, the two can run async along side one another:

```bash
# Server
cargo run --bin server

   Compiling redis-rs v0.1.0 (/Users/jp/Projects/redis-rs)
    Finished dev [unoptimized + debuginfo] target(s) in 1.71s
     Running `target/debug/server`

$ nc localhost 6379
# Client 1 RECV: Hello world!
# Client 1 SEND: Hello from 1
# Server: From client: [72, 101, 108, 108, 111, 32, 102, 114, 111, 109, 32, 49, 10]
# Client 1 RECV: Hello from 1
$ nc localhost 6379
# Client 2 RECV: Hello world!
# Client 1 SEND: Hello again from 1
# Server: From client: [72, 101, 108, 108, 111, 32, 97, 103, 97, 105, 110, 32, 102, 114, 111, 109, 32, 49, 10]
# Client 1 RECV: Hello again from 1
# Client 2 SEND: Hello from 2
# Server: From client: [72, 101, 108, 108, 111, 32, 102, 114, 111, 109, 32, 50, 10]
# Client 2 RECV: Hello from 2
# Client 2 SEND: Hello again from 2
# Server: From client: [72, 101, 108, 108, 111, 32, 97, 103, 97, 105, 110, 32, 102, 114, 111, 109, 32, 50, 10]
# Client 2 RECV: Hello again from 2
# Client 2 SEND: Good bye
# Server: From client: [71, 111, 111, 100, 32, 98, 121, 101, 10]
# Client 2 RECV: Good bye
# Client 2 CLOSE
# Client 1 SEND: Good bye
# Server: From client: [71, 111, 111, 100, 32, 98, 121, 101, 10]
# Client 1 RECV: Good bye
# Client 1 CLOSE
```

Nice!

## Doing the lumberjack thing. 

One thing that I always want to build in relatively early is good logging. For Python, I almost always use the built in `logging` module + [`coloredlogs`](https://pypi.org/project/coloredlogs/). For Rust, the equivalent would seem to be [`tracing`](https://docs.rs/tracing/latest/tracing/).

So let's add that!

```bash
cargo add tracing tracing_subscriber

    Updating crates.io index
warning: translating `tracing_subscriber` to `tracing-subscriber`
      Adding tracing v0.1.37 to dependencies.
             Features:
             + attributes
             + std
             + tracing-attributes
             - async-await
             - log
             - log-always
             - max_level_debug
             - max_level_error
             - max_level_info
             - max_level_off
             - max_level_trace
             - max_level_warn
             - release_max_level_debug
             - release_max_level_error
             - release_max_level_info
             - release_max_level_off
             - release_max_level_trace
             - release_max_level_warn
             - valuable
      Adding tracing-subscriber v0.3.16 to dependencies.
             Features:
             + alloc
             + ansi
             + fmt
             + nu-ansi-term
             + registry
             + sharded-slab
             + smallvec
             + std
             + thread_local
             + tracing-log
             - env-filter
             - json
             - local-time
             - matchers
             - once_cell
             - parking_lot
             - regex
             - serde
             - serde_json
             - time
             - tracing
             - tracing-serde
             - valuable
             - valuable-serde
             - valuable_crate
```

It's actually pretty cool that you can actually use `--features max_level_info` to just automatically log up to info for free. That's neat. But for now, I'll use `tracing_subscribe` manually.

```rust
use std::net::SocketAddr;

use tokio::net::{TcpListener, TcpStream};
use tokio::io::{AsyncReadExt, AsyncWriteExt};

use tracing_subscriber;

#[tokio::main]
async fn main() -> std::io::Result<()> {
    tracing_subscriber::fmt::init();

    let addr = "0.0.0.0:6379";

    let listener = TcpListener::bind(addr).await?;
    tracing::info!("[server] Listening on {addr}");
    
    loop {
        let (stream, addr) = listener.accept().await?;
        tracing::debug!("[server] Accepted connection from {addr:?}");
        tokio::spawn(async move {
            if let Err(e) = handle(stream, addr).await {
                tracing::warn!("[server] An error occurred: {e:?}");
            }
        });
    }
}

async fn handle(mut stream: TcpStream, addr: SocketAddr) -> std::io::Result<()> {
    tracing::info!("[{addr}] Accepted connection");

    let mut buf = [0; 1024];
    loop {
        let bytes_read = stream.read(&mut buf).await?;
        if bytes_read == 0 {
            break;
        }
        tracing::debug!("[{addr}] Received {bytes_read} bytes");

        let string = String::from_utf8_lossy(&buf[0..bytes_read]);
        tracing::debug!("[{addr} Received {string:?}");

        stream.write_all(string.as_bytes()).await?;
    }

    tracing::info!("[{addr}] Ending connection");

    Ok(())
}
```

Mostly, we just have a bunch of `tracing::info!` and `tracing::debug!` calls around. I did try to get spans working, but they seemed to act funny with multiple threads, so this is enough for now. 

Checking it out:

```bash
# Server
$ RUST_LOG=debug cargo run --bin server

   Compiling redis-rs v0.1.0 (/Users/jp/Projects/redis-rs)
    Finished dev [unoptimized + debuginfo] target(s) in 0.56s
     Running `target/debug/server`

# Client
$ nc localhost 6379

# Client I/O
# > Hello
# < Hello
# > Goodbye
# < Goodbye

# Server logs
2023-02-05T02:23:44.647267Z  INFO server: [server] Listening on 0.0.0.0:6379
2023-02-05T02:23:47.556100Z DEBUG server: [server] Accepted connection from 127.0.0.1:53986
2023-02-05T02:23:47.556184Z  INFO server: [127.0.0.1:53986] Accepted connection
2023-02-05T02:23:49.148031Z DEBUG server: [127.0.0.1:53986] Received 6 bytes
2023-02-05T02:23:49.148187Z DEBUG server: [127.0.0.1:53986 Received "Hello\n"
2023-02-05T02:23:52.525595Z DEBUG server: [127.0.0.1:53986] Received 8 bytes
2023-02-05T02:23:52.525690Z DEBUG server: [127.0.0.1:53986 Received "Goodbye\n"
2023-02-05T02:23:53.329806Z  INFO server: [127.0.0.1:53986] Ending connection
```

That's pretty cool. And it does work fine with multiple clients as well:

```bash
$ RUST_LOG=debug cargo run --bin server

    Finished dev [unoptimized + debuginfo] target(s) in 0.10s
     Running `target/debug/server`
2023-02-05T02:26:03.249739Z  INFO server: [server] Listening on 0.0.0.0:6379
2023-02-05T02:26:07.012916Z DEBUG server: [server] Accepted connection from 127.0.0.1:54523
2023-02-05T02:26:07.013035Z  INFO server: [127.0.0.1:54523] Accepted connection
2023-02-05T02:26:08.963769Z DEBUG server: [127.0.0.1:54523] Received 13 bytes
2023-02-05T02:26:08.964088Z DEBUG server: [127.0.0.1:54523 Received "Hello from 1\n"
2023-02-05T02:26:10.421350Z DEBUG server: [server] accepted connection from 127.0.0.1:54527
2023-02-05T02:26:10.421475Z  INFO server: [127.0.0.1:54527] Accepted connection
2023-02-05T02:26:12.230319Z DEBUG server: [127.0.0.1:54527] Received 13 bytes
2023-02-05T02:26:12.230440Z DEBUG server: [127.0.0.1:54527 Received "Hello from 2\n"
2023-02-05T02:26:15.365158Z DEBUG server: [127.0.0.1:54523] Received 11 bytes
2023-02-05T02:26:15.365239Z DEBUG server: [127.0.0.1:54523 Received "Still here\n"
2023-02-05T02:26:17.203135Z DEBUG server: [127.0.0.1:54527] Received 9 bytes
2023-02-05T02:26:17.203212Z DEBUG server: [127.0.0.1:54527 Received "Good bye\n"
2023-02-05T02:26:19.171721Z DEBUG server: [127.0.0.1:54523] Received 9 bytes
2023-02-05T02:26:19.171809Z DEBUG server: [127.0.0.1:54523 Received "Good bye\n"
2023-02-05T02:26:19.507445Z  INFO server: [127.0.0.1:54523] Ending connection
2023-02-05T02:26:20.473141Z  INFO server: [127.0.0.1:54527] Ending connection
```

## So... weren't we doing something with Redis? 

Right. Redis. This is already getting a bit long, so for now, let's just assume we have a client that knows how to speak RESP (see [[Cloning Redis in Rust: RESP [Part 1]]]()).

Take that, parse it, log the parsed version, turn it back into a string, and send it back. 

```rust

use std::net::SocketAddr;
use std::str::FromStr;

use redis_rs::RedisType;

use tokio::net::{TcpListener, TcpStream};
use tokio::io::{AsyncReadExt, AsyncWriteExt};

use tracing_subscriber;

#[tokio::main]
async fn main() -> std::io::Result<()> {
    tracing_subscriber::fmt::init();

    let addr = "0.0.0.0:6379";

    let listener = TcpListener::bind(addr).await?;
    tracing::info!("[server] Listening on {addr}");
    
    loop {
        let (stream, addr) = listener.accept().await?;
        tracing::debug!("[server] Accepted connection from {addr:?}");
        tokio::spawn(async move {
            if let Err(e) = handle(stream, addr).await {
                tracing::warn!("[server] An error occurred: {e:?}");
            }
        });
    }
}

async fn handle(mut stream: TcpStream, addr: SocketAddr) -> std::io::Result<()> {
    tracing::info!("[{addr}] Accepted connection");

    let mut buf = [0; 1024];
    loop {
        let bytes_read = stream.read(&mut buf).await?;
        if bytes_read == 0 {
            break;
        }
        tracing::debug!("[{addr}] Received {bytes_read} bytes");

        let string = String::from_utf8_lossy(&buf[0..bytes_read]);
        let data = match RedisType::from_str(&string) {
            Ok(data) => data,
            Err(err) => {
                tracing::warn!("[{addr}] Error parsing input: {err:?}");
                continue;
            },
        };
        tracing::debug!("[{addr} Received {data:?}");

        stream.write_all(data.to_string().as_bytes()).await?;
    }

    tracing::info!("[{addr}] Ending connection");

    Ok(())
}
```

The main difference is that we're taking the `buf`, converting it into a `string` (for reasons?), turning that into a `RedisType`, logging it, and then turning it back `to_string().as_bytes()` to send back to the client. 

Whew. 

```bash
# Server
$ RUST_LOG=debug cargo run --bin server

   Compiling redis-rs v0.1.0 (/Users/jp/Projects/redis-rs)
    Finished dev [unoptimized + debuginfo] target(s) in 1.02s
     Running `target/debug/server`

# Client
$ nc localhost 6379

> :42

# Server logs
2023-02-05T02:29:40.849183Z  INFO server: [server] Listening on 0.0.0.0:6379
2023-02-05T02:29:43.191540Z DEBUG server: [server] Accepted connection from 127.0.0.1:55112
2023-02-05T02:29:43.191725Z  INFO server: [127.0.0.1:55112] Accepted connection
2023-02-05T02:29:44.694273Z DEBUG server: [127.0.0.1:55112] Received 4 bytes
2023-02-05T02:29:44.694439Z  WARN server: [127.0.0.1:55112] Error parsing input: InvalidSuffix
```

Hmm. It turns out that the version of `nc` I have doesn't have a `--crlf` flag to send `\r\n` as we're expecting. So... we have to cheat a bit with echo:

```bash
# Server
RUST_LOG=debug cargo run --bin server

    Finished dev [unoptimized + debuginfo] target(s) in 0.10s
     Running `target/debug/server`

# Client 
$ echo -ne ':42\r\n' | nc localhost 6379

:42

# Server logs
2023-02-05T02:30:45.463949Z  INFO server: [server] Listening on 0.0.0.0:6379
2023-02-05T02:30:50.970001Z DEBUG server: [server] Accepted connection from 127.0.0.1:55312
2023-02-05T02:30:50.970090Z  INFO server: [127.0.0.1:55312] Accepted connection
2023-02-05T02:30:50.970109Z DEBUG server: [127.0.0.1:55312] Received 5 bytes
2023-02-05T02:30:50.970130Z DEBUG server: [127.0.0.1:55312 Received Integer { value: 42 }
2023-02-05T02:30:50.970145Z  INFO server: [127.0.0.1:55312] Ending connection
```

Much better! 

So now, we can receive proper RESP data and parse it! Sweet. 

## Is that it? 

For now, that's it. 

Next up though, I think I'll probably want to actually add a few commands to the server. It looks like the expected input is always an RESP Array of Bulk Strings. And probably write a simple client that can turn commands into this, so that I don't have to keep using echo. 

My goal:

```bash
$ RUST_LOG=debug cargo run --bin server
...

$ RUST_LOG=debug cargo run --bin client

> SET greeting "Hello world!"
"OK"
> GET greeting
"Hello world!"
```

But that is for another day. 
