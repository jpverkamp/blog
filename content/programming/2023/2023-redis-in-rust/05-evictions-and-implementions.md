---
title: "Redis in Rust: Evictions and Implementations"
date: '2023-03-26 00:00:15'
programming/languages:
- Rust
programming/topics:
- Redis
- REPL
- Client
- Parsing
- Networking
- TCP
series:
- Cloning Redis in Rust
---
Another Redis in Rust series. It's really starting to come together now! 

In this post, updating the state to store expiration times + a thread to handle said eviction + the implementation of a small pile more of the general Redis functions. 

{{<toc>}}

<!--more-->

## Better Redis function definitions

Where we left off last time, I was doing a lot to manually parse the parameters of more complicated functions (such as `SET`, which really ends up being one of the most complicated, amusingly). But doing all that by hand is a bit annoying, not to mention long and error prone. 

We're writing in Rust, let's write some macros to handle that for us!

To start with, all of these macros are currently part of the same `lazy_static!` block that I've been using to define the `COMMANDS`:

```rust
lazy_static! {
    static ref COMMANDS: HashMap<&'static str, Command> = {
        let mut m = HashMap::new();

        macro_rules! assert_n_args {
            ($args:ident, $n:literal) => {
                if $args.len() != $n {
                    return Err(String::from(format!("Expected {} args, got {}", $n, $args.len())));
                }
            }
        }

        // ...

        m
    }
}
```

And therein, we have the first. Essentially, when we are processing the `args` sent to a command, we can call `assert_n_args(args, 2)`. If the `args` doesn't have exactly 2 values, return an error. Turns the 3 lines into one much simpler one. 

Likewise, if we have to have at least 2:

```rust
macro_rules! assert_n_or_more_args {
    ($args:ident, $n:literal) => {
        if $args.len() < $n {
            return Err(String::from(format!("Expected at least {} args, got {}", $n, $args.len())));
        }
    }
}
```

What starts getting more interesting is when we want to pull a specific kind of value out of the args. In this case, what if we want a string. Because we want to automatically convert types, we are going to handle two different cases here: `RedisType::String` (direct comparison) and `RedisType::Integer` (cast to a string first):

```rust
macro_rules! get_string_arg {
    ($args:ident, $index:expr) => {
        {
            if $index >= $args.len() {
                return Err(String::from("Not enough args"));
            }

            match $args[$index].clone() {
                RedisType::String{value} => value,
                RedisType::Integer{value} => value.to_string(),
                _ => return Err(String::from(format!("Attempted to use {} as a string", $args[$index]))),

            }
        }
    }
}
```

Now we're really getting into the savings. This not only checks that there *is* actually the requisite arg (handling index out of bounds for me) but also that we can `match` on the type. All in one line:

```
let key = get_string_arg(args, 0);
let value = get_string_arg(args, 1);
```

Two lines instead of ~20. Not bad. 

Next, we often want to do string comparisons (for keywords, such as `SET key value NX`). So a macro for that:

```rust
macro_rules! is_string_eq {
    ($args:ident, $index:expr, $value:literal) => {
        get_string_arg!($args, $index).to_ascii_uppercase() == $value.to_ascii_uppercase()
    }
}
```

And it even uses `get_string_arg!` behind the scenes!

Okay, what about other types? Well, we're dealing with casting again, so how about integers and floats:

```rust
macro_rules! get_integer_arg {
    ($args:ident, $index:expr) => {
        {
            if $index >= $args.len() {
                return Err(String::from("Not enough args"));
            }

            match $args[$index].clone() {
                RedisType::String{value} => {
                    match value.parse() {
                        Ok(value) => value,
                        Err(_) => return Err(String::from(format!("Attempted to use {} as an integer", $args[$index]))),
                    }
                },
                RedisType::Integer{value} => value,
                _ => return Err(String::from(format!("Attempted to use {} as an integer", $args[$index]))),
            }
        }
    }
}

macro_rules! get_float_arg {
    ($args:ident, $index:expr) => {
        {
            if $index >= $args.len() {
                return Err(String::from("Not enough args"));
            }

            match $args[$index].clone() {
                RedisType::String{value} => {
                    match value.parse() {
                        Ok(value) => value,
                        Err(_) => return Err(String::from(format!("Attempted to use {} as a float", $args[$index]))),
                    }
                },
                RedisType::Integer{value} => value as f64,
                _ => return Err(String::from(format!("Attempted to use {} as a float", $args[$index]))),
            }
        }
    }
}
```

Again, if it's the right type, we can just convert it, but if we have something that's a string and *can* be a number, try to convert it. If not, error with details. 

Not bad!

I do have one more, but that's mostly specific to `SET`, so let's leave it for that. 

## Re-parsing SET 

Okay, so how how do we handle `SET`? 

```rust
m.insert("SET", Command {
    help: String::from("\
SET key value [NX | XX] [GET] [EX seconds | PX milliseconds | EXAT unix-time-seconds | PXAT unix-time-milliseconds | KEEPTTL]

Sets key to a given value.

NX|XX - only set if the key does not / does already exist.
EX|PX|EXAT|PXAT - key expires after seconds/milliseconds or at a Unix timestamp in seconds/milliseconds
KEEPTTL - retain the previously set TTL
GET - return the previous value, returns NIL and doesn't return if the key wasn't set

Returns OK if SET succeeded, nil if SET was not performed for NX|XX or because of GET, the old value if GET was specified. 
    "),
    f: Box::new(|state, args| {
        assert_n_or_more_args!(args, 2);
        let key = get_string_arg!(args, 0);
        let value = get_string_arg!(args, 1);

        let mut nx = false;
        let mut xx = false;
        let mut keepttl = false;
        let mut get = false;

        let mut expiration = None;

        let mut i = 2;
        loop {
            if i >= args.len() {
                break;
            } else if is_string_eq!(args, i, "NX") {
                nx = true;
                i += 1;
            } else if is_string_eq!(args, i, "XX") {
                xx = true;
                i += 1;
            } else if is_string_eq!(args, i, "KEEPTTL") {
                keepttl = true;
                i += 1;
            } else if is_string_eq!(args, i, "GET") {
                get = true;
                i += 1;
            } else if let Some(ex) = get_expiration!(args, i) {
                expiration = Some(ex);
                i+= 2;
            } else {
                return Err(String::from(format!("Unexpected parameter: {:?}", args[i])));
            }
        }

        if nx && xx {
            return Err(String::from("SET: Cannot set both NX and XX"));
        }

        if keepttl && expiration.is_some() {
            return Err(String::from("SET: Cannot set more than one of EX/PX/EXAT/PXAT/KEEPTTL"));
        }

        if expiration.is_some() {
            tracing::debug!("Setting expiration for key {} to {:?}", key, expiration);
            state.ttl.push(key.clone(), expiration.unwrap());
        } else if keepttl {
            // do nothing
        } else {
            state.ttl.remove(&key);
        }

        if nx && state.keystore.contains_key(&key) {
            return Ok(RedisType::NullString);
        }

        if xx && !state.keystore.contains_key(&key) {
            return Ok(RedisType::NullString);
        }

        let result = if get {
            Ok(match state.keystore.get(&key) {
                Some(value) => RedisType::String { value: value.to_owned() },
                None => RedisType::NullString,
            })
        } else {
            Ok(RedisType::String { value: "OK".to_owned() })
        };

        state.keystore.insert(key, value);
        result
    })
});
```

There are a few changes there (`help` and `state.ttl`) that I'll have to come back to in a moment. I expect, you can guess what they do. But here already, you can see how helpful it is to have these macros. I can pull off `key` and `value` in two lines, then start processing the keywords (`NX`/`XX` etc) directly. 

But then we come to the pile of arguments that set expiration. We'll use them again, so how about we macro that as well:

```rust
macro_rules! get_expiration {
    ($args:ident, $index:expr) => {
        if is_string_eq!($args, $index, "EX") {
            // Seconds from now
            let value = get_integer_arg!($args, $index + 1);
            Some((
                SystemTime::now()
                + Duration::from_secs(value as u64)
            ))
        } else if is_string_eq!($args, $index, "PX") {
            // Milliseconds from now
            let value = get_integer_arg!($args, $index + 1);
            Some((
                SystemTime::now()
                + Duration::from_millis(value as u64)
            ))
        } else if is_string_eq!($args, $index, "EXAT") {
            // Seconds since epoch
            let value = get_integer_arg!($args, $index + 1);
            Some(UNIX_EPOCH + Duration::from_secs(value as u64))
        } else if is_string_eq!($args, $index, "PXAT") {
            // Milliseconds since epoch
            let value = get_integer_arg!($args, $index + 1);
            Some(UNIX_EPOCH + Duration::from_millis(value as u64))
        } else {
            None
        }
    }
}
```

Now this is an interesting one, since there are four ways to set expiration. Either in seconds or milliseconds and either as an absolute timestamp (since epoch) or relative to 'now'. In all cases, we can parse each and turn them into an absolute `SystemTime` of when it will expire. 

## Implementing TTL on the state

Okay, we can parse the expiration time for `SET`, now we need a place to store it. You might have noticed that we're setting the `ttl` in the `State`, so what's that?

```rust
#[derive(Debug, Default)]
pub struct State {
    keystore: HashMap<String, String>,
    ttl: PriorityQueue<String, SystemTime>,
}
```

That's it. A `PriorityQueue` in this case is implemented so that items in it (the expiration times) are sorted. That means that the next to expire will be first. It also has efficient {{<inline-latex "O(log(n))">}} removal by key, which is nice. 

## Expiration thread

So now that we have *that*, how do we actually expire stored values?

Well, one open would be to expire them on demand. When we fetch a key, check if it's expired. But that's not super elegant, so instead let's more as expected: make a thread that periodically checks the next-to-expire keys and expires any that have passed their date. 

Something like this:

```rust
#[tokio::main]
async fn main() -> std::io::Result<()> {
    tracing_subscriber::fmt::init();

    let addr = "0.0.0.0:6379";

    let listener = TcpListener::bind(addr).await?;
    tracing::info!("Listening on {addr}");

    let state = Arc::new(Mutex::new(State::default()));

    let ttl_state = state.clone();
    tokio::spawn(async move {
        loop {
            let now = SystemTime::now();
            loop {
                let evict = match ttl_state.lock().await.ttl.peek() {
                    Some((_, eviction_time)) => *eviction_time < now,
                    None => false,
                };

                if evict {
                    let mut ttl_state = ttl_state.lock().await;
                    let (key, _) = ttl_state.ttl.pop().unwrap();
                    tracing::debug!("Evicting {key} from keystore");
                    ttl_state.keystore.remove(&key);
                } else {
                    break;
                }
            }
            tokio::time::sleep(Duration::from_secs(1)).await;
        }
    });

    loop {
        let (stream, addr) = listener.accept().await?;
        let thread_state = state.clone();

        tracing::debug!("Accepted connection from {addr:?}");
        tokio::spawn(async move {
            if let Err(e) = handle(stream, addr, thread_state).await {
                tracing::warn!("An error occurred: {e:?}");
            }
        });
    }
}
```

One difference here is that we're using `Arc<Mutex<State>>`. An `Arc` is a {{<wikipedia "reference counter">}} to the item held inside, so that that as long as at least one copy still exists, it will stay in scope. In this case, we have one copy for the eviction thread and then one more per connected client. 

This actually does make our client truly multi-threaded and thread safe, since we're passing the same `state` to each. 

The `Arc` alone though means we can't actually modify the `state`, just read it in multiple threads. Not super helpful. The `Mutex` on the other hand, allows us to request a `lock` in each thread and (once given the lock) read or modify. If we had more readers than writers, we could instead have used a `RwLock` and I may try that in the future. But for now, it works great. 

All that being said, now we have the ability to `state.lock().await` to get a lock on the `Mutex` so that we can read or write to it. While we have it, any other thread will `await` the release. 

And with that, we can run a thread once per second to check for eviction. It's not nanosecond perfect for eviction, but I don't think that's a guarantee that we need. 

The one last gotcha is in the eviction loop:

```rust
loop {
    let now = SystemTime::now();
    loop {
        let evict = match ttl_state.lock().await.ttl.peek() {
            Some((_, eviction_time)) => *eviction_time < now,
            None => false,
        };

        if evict {
            let mut ttl_state = ttl_state.lock().await;
            let (key, _) = ttl_state.ttl.pop().unwrap();
            tracing::debug!("Evicting {key} from keystore");
            ttl_state.keystore.remove(&key);
        } else {
            break;
        }
    }
    tokio::time::sleep(Duration::from_secs(1)).await;
}
```

Why do I calculate `evict` first and then get another lock to actually evict it? Well, that's Rust's fault. It doesn't want to let me borrow `ttl_state` as mutable (since we're writing to it) if we've already borrowed it as read only (with the `peek`). And we do want to peek, since if we actually did a `pop`, then we'd have to always put the item back on. 

Took a bit to get that working. 

With all that together, we have eviction!

```bash
[server] $ RUST_LOG=debug cargo run --bin server
[server]    Compiling redis-rs v0.1.0 (/Users/jp/Projects/redis-rs)
[server]     Finished dev [unoptimized + debuginfo] target(s) in 3.29s
[server]      Running `target/debug/server`
[server] 2023-03-26T18:35:23.329020Z  INFO server: Listening on 0.0.0.0:6379
[client] $ redis-cli
[server] 2023-03-26T18:35:24.660161Z DEBUG server: Accepted connection from 127.0.0.1:49923
[server] 2023-03-26T18:35:24.660314Z  INFO server: [127.0.0.1:49923] Accepted connection
[server] 2023-03-26T18:35:24.660388Z DEBUG server: [127.0.0.1:49923] Received 27 bytes
[server] 2023-03-26T18:35:24.660441Z DEBUG server: [127.0.0.1:49923 Received: COMMAND [String { value: "DOCS" }]
[client] 127.0.0.1:6379> SET test value EX 5
[server] 2023-03-26T18:35:30.420285Z DEBUG server: [127.0.0.1:49923] Received 49 bytes
[server] 2023-03-26T18:35:30.420417Z DEBUG server: [127.0.0.1:49923 Received: SET [String { value: "test" }, String { value: "value" }, String { value: "EX" }, String { value: "5" }]
[server] 2023-03-26T18:35:30.420585Z DEBUG server: Setting expiration for key test to Some(SystemTime { tv_sec: 1679891735, tv_nsec: 420567000 })
[client] "OK"
[client] 127.0.0.1:6379> GET test
[server] 2023-03-26T18:35:31.539128Z DEBUG server: [127.0.0.1:49923] Received 23 bytes
[server] 2023-03-26T18:35:31.539222Z DEBUG server: [127.0.0.1:49923 Received: GET [String { value: "test" }]
[client] "value"
[server] 2023-03-26T18:35:36.353723Z DEBUG server: Evicting test from keystore
[client] 127.0.0.1:6379> GET test
[server] 2023-03-26T18:35:40.465655Z DEBUG server: [127.0.0.1:49923] Received 23 bytes
[server] 2023-03-26T18:35:40.465713Z DEBUG server: [127.0.0.1:49923 Received: GET [String { value: "test" }]
[client] (nil)
[server] 2023-03-26T18:35:41.746856Z  INFO server: [127.0.0.1:49923] Ending connection
```

Still need to figure out a better way to format that. 

But in any case, we set `test = value` with an expiration of 5 seconds. A `GET test` within those five seconds returns `value` and after: `(nil)`. Nice!

So we've got eviction. 

Cool. 

## A few more examples

That's enough to write all of the [string commands](https://redis.io/commands/?group=string). Let's do it. You can see them all in the [full source](https://github.com/jpverkamp/redis-rs/), but I'll point out a few interesting ones here:

### DECR 

```rust
m.insert("DECR", Command {
    help: String::from("\
DECR key

Decrement the number stored at key by one.

If the key does not exist, it is set to 0 before performing the operation. An error is returned if the key contains a value of the wrong type or contains a string that can not be represented as integer. This operation is limited to 64 bit signed integers. 
    "),
    f: Box::new(|state, args| {
        assert_n_args!{args, 1};
        let key = get_string_arg!(args, 0);

        if let Some(current) = state.keystore.get_mut(&key) {
            match current.parse::<i64>() {
                Ok(value) => {
                    *current = (value - 1).to_string();
                    Ok(RedisType::Integer{ value: value - 1 })
                },
                Err(_) => Err(String::from("Value is not an integer or out of range")),
            }
        } else {
            state.keystore.insert(key.clone(), "-1".to_owned());
            Ok(RedisType::Integer{ value: -1 })
        }
    })
});
```

Primarily interesting because of the typing. If the value is already a string, cast it to an integer, subtract one, and cast it back. Ugly, but that's how it must be. 

```text
127.0.0.1:6379> SET test 10
"OK"
127.0.0.1:6379> DECR test
(integer) 9
127.0.0.1:6379> DECR test
(integer) 8
127.0.0.1:6379> DECR test2
(integer) -1
```

### GETRANGE

```rust
m.insert("GETRANGE", Command {
    help: String::from("\
GETRANGE key start end

Get a substring of the string stored at a key."
    ),
    f: Box::new(|state, args| {
        assert_n_args!(args, 3);
        let key = get_string_arg!(args, 0);
        let mut start = get_integer_arg!(args, 1);
        let mut end = get_integer_arg!(args, 2);

        Ok(match state.keystore.get(&key) {
            Some(value) => {
                start = start.max(0).min(value.len() as i64 - 1);
                end = end.max(0).min(value.len() as i64 - 1);

                if start > end {
                    RedisType::String { value: String::new() }
                } else {
                    RedisType::String { value: value[start as usize..end as usize].to_owned() }
                }
            },
            None => RedisType::NullString,
        })
    })
});
```

Fetches substrings (although I think it's supposed to work on arrays to? not yet anyways). I think the `start.max(0).min(value.len() as i64 - 1)` is particularly neat. 

### MGET

```rust
m.insert("MGET", Command {
    help: String::from("\
MGET key [key ...]

Get the values of all the given keys.

For every key that does not hold a string value or does not exist, the special value nil is returned.
    "),
    f: Box::new(|state, args| {
        assert_n_or_more_args!(args, 1);

        let mut values = Vec::new();

        for i in 0..args.len() {
            let key = get_string_arg!(args, i);
            match state.keystore.get(&key) {
                Some(value) => values.push(RedisType::String { value: value.to_owned() }),
                None => values.push(RedisType::NullString),
            }
        }

        Ok(RedisType::Array { value: values })
    })
});
```

It's pretty cool to be able to use `get_string_arg!(args, i)` in a loop and it just works. And matching on the `Option` of getting a value and pushing `(nil)` if it's not. Elegant. 

## Github Copilot

Full disclaimer time. Implementing all of those functions is a lot of busy work. I wasn't particularly looking forward to it. But there's been a big (and absolutely) fascinating push around AI/ML tools recently, so I decided to actually stop putting it off and give Github Copilot a try.

Holy crap. 

That's kind of awesome. 

All I had to do was starting typing `m.insert` and it would already somehow from context figure out that I was implementing Redis commands and start filling out the next one. Including help text (right in all but one case) and a description. Then in most cases, it would generate code for the function for me. 

And the absolutely craziest part (to me)? 

It used the helper macros that I'd already written. 

So it not only understands the problem, but also understands the structure that I've already put in place. 

Now don't get me wrong, the code isn't perfect. A few of them I've rewritten in part or in whole. In a few cases, it suggested additional macros (like for `MSET` it wanted `assert_even_args!` which, while cool, is just not necessary). And in a few cases, it just did something that wouldn't work at all. 

But for the moment... that's really impressive. 

Now there are also ethical concerns around Github Copilot: did Microsoft train it on private or GPL code? Probably. Will the code it generates have either no copywrite (if I don't modify it) or step on someone else's? Possibly. I feel like these are solvable problems though. 

Am I still going to play with this more? Absolutely. 

## Full source

As always (although I don't know if I've said it), the full source is [on GitHub](https://github.com/jpverkamp/redis-rs/) with [tags available](https://github.com/jpverkamp/redis-rs/tags) for the code at the state of each blog post. 

## Next steps

* Refactor commands into multiple files
* Implement another data type (sets, hashes, sorted sets, streams, etc)
* Implement persistance to disk / backups
* Improve the client to handle quoted strings
  * Test the improved client against the official server
* Try [redis-benchmark](https://redis.io/docs/management/optimization/benchmarks/)

So many things! 