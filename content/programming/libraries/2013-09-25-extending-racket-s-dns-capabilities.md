---
title: Extending Racket's DNS capabilities
date: 2013-09-25 14:00:35
programming/languages:
- Racket
- Scheme
programming/topics:
- Bitfields
- DNS
- Data Structures
- Networks
---
As I [mentioned]({{< ref "2013-09-23-extending-racket-structs-to-bitfields.md" >}}) on Monday, I wrote my [DNS-based censorship]({{< ref "2013-02-09-isma-2013-aims-5.md" >}}) around the world--and to do that, I need a fair bit of control over the DNS packets that I'm sending back and over parsing the ones that I get back.

<!--more-->

Originally, I was writing this code in Python. Python doesn't have a built in DNS library, but <a href="http://www.dnspython.org/">dnspython</a> works is rather solid and does all that I want it to. On the other hand though, I'm starting to move more and more of my code over to Racket--I've found it to be more expressive in a lot of cases (particularly when creating {{< wikipedia "domain specific languages" >}} for solving a problem[^1] and (in my experience) it performs a lot better on bigger, easily parallelizable tasks.

So what does Racket have in terms of DNS? Well, unfortunately all I've been able to find is the built in {{< doc racket "net/dns" >}} module. It works well enough for simple queries ({{< doc racket "dns-get-address" >}} is certainly straight forward and far easier to direct towards arbitrary DNS servers than I found with dnspython. But unfortunately, that's about all it has. There's no way to control how long the method takes to timeout (without something like {{< doc racket "sync/timeout" >}}), there's no way to see the full set of addresses returned (it seems to just return the first {{< wikipedia page="A record (DNS)#A" text="A record" >}} in the response), and no support for asynchronous scans. Essentially, it just won't work on the scale that I'll be working with.

So what do we need? Well, first I want to build some sort of unified framework on top of the {{< doc racket "racket/udp" >}} module[^2]. In this case, it already does everything that I want, but I'd rather keep the details as seperated as I can. What I want is these three functions:


* `(get-socket port)` - returns a UDP socket for the given port, reusing sockets if the same port is requested more than once
* `(add-socket-listener! port f)` - attach a function to a given socket/port so that any incoming traffic on that port will go to the given callback function
* `(remove-socket-listener! port f)` - remove a previously attached functions (it will only work if you pass the exact same function, `eq?` can tell)


Let's start with the latter two, since the code for those is much simpler. Essentially, we'll have a hash from port numbers to a set of listeners. We'll use a set so that we can add the same listener as many times as we want without actually having to keep copies, although I'm not sure that would actually end up being a problem. In addition, the {{< doc racket "racket/set" >}} module has versions for {{< doc racket "set" >}} (using `equal?`), {{< doc racket "seteqv" >}}, and {{< doc racket "seteq" >}}.

```scheme
; Listeners sorted by port
; (hash/c port (set/c (remote-host remote-port bytes? -> void)))
(define listeners (make-hasheq))

(define (add-socket-listener! port listener)
  (define new-set (set-add (hash-ref listeners port (seteq)) listener))
  (hash-set! listeners port new-set))

(define (remove-socket-listener! port listener)
  (define new-set (set-remove (hash-ref listeners port (seteq)) listener))
  (if (set-empty? new-set)
      (hash-remove! listeners port)
      (hash-set! listeners port new-set)))
```

As an added bonus, here we can see the contract that a listener will have to have (although we're not enforcing the contracts at the moment). Any function that will work as a listener has to take three arguments: the remote host as a string (will generally be an IP address), the remote port, and the bytes that make up the packet received. The function itself will be in charge of making sure that the packet is actually directed towards our application, since UDP itself doesn't provide any of the guarantees that TCP does to that end. 

Now that we have that, how will `get-socket` work? Here's what I have, although as you might notice I have a few comments that I'll want to work on later already. But it works well enough for what I need. 

```scheme
; Get the socket associated with a port, reusing sockets if possible
; (port -> void)
(define (get-socket port)
  (unless (hash-has-key? sockets port)
    ; Create the new socket, bind it to the given port
    (define s (udp-open-socket))
    (udp-bind! s #f port #t)

    ; Create a listening thread for it
    ; TODO: Allow some way to clean these up?
    ; TODO: Print out any errors we catch rather than ignoring them
    (thread 
     (thunk
      (define b (make-bytes 1024))
      (let loop ()
        (sync 
         [handle-evt 
          (udp-receive!-evt s b)
          (λ (event)
            ; Unpacket the event
            (define-values (bytes-received source-hostname source-port)
              (apply values event))

            ; Send the results to any listeners for that port
            ; Hope they can deal with anything else random to this port :smile:
            (for ([listener (in-set (hash-ref listeners port (set)))])
              (listener source-hostname
                        source-port
                        (subbytes b 0 bytes-received)))

            ; Wait for another event
            (loop))]))))

    ; Record it
    (hash-set! sockets port s))

  ; Return the old socket if we had one, new otherwise
  (hash-ref sockets port))
```

First, we check if the port already has a socket in the `sockets` hash (it's just a straightforward `hasheq`). If not, we have to create on. The arguments to {{< doc racket "udp-bind!" >}} mean that we aren't sending to a specific host (yet--we'll do that with {{< doc racket "udp-send-to" >}}) and the last `#t` means that the port can be reused. This is mostly because I'm going to be taking up rather a lot of ports, although I might change this in future versions.

The second part is the new thread. Basically, each socket has a single listening thread that uses {{< doc racket "sync" >}} with {{< doc racket "udp-receive!-evt" >}} to listen for incoming UDP packets (and block until we get one). When we get a packet, go through every listener for that port and send it out. We'll pass along the remote host and port, although passing along the number of bytes isn't actually necessary since we go ahead and cut off the buffer anyways.

And there you have it. With that, we should be able to write fairly straight forward UDP code. Now we have to build a DNS layer.

To start out with, we want to be able to provide these two methods and one parameter:


* `(dns-request server [#:type value] ...)` - make a synchronous DNS request (or more than one) of the given type(s) to the given server (as hostname or IP), return the first response
* `(dns-request/async server [#:type value] ... callback)` - make an asynchronous DNS request (or more than one) to the given server, calling callback with any responses
* `(current-dns-timeout [new-timeout])` - get/set the current timeout value; synchronous requests will return `'timeout` after this time while asynchronous requests will only return during this period; set to `#f` to disable; default is 5.0 seconds


On oddity already is the idea that you can make more than one kind of DNS request using keyword paramters. Mainly, I want this library to be more flexible (if I want to use it to look up mail servers for example), and also because it sounded like it would be interesting to implement. And that it was. In the end, we'll be making calls like this:

```scheme
(dns-request "8.8.4.4" #:a "google.com")
```

If we wanted to find the mailserver for a domain, we should be able to just do this (although it's not implemented as of yet, implementation should be trivial): 

```scheme
(dns-request "8.8.4.4" #:mx "google.com")
```

How does it work? Well, `dns-request` is actually implemented via `dns-request/async` (it just waits for the response for you), so we'll start with that:

```scheme
; Make an async DNS request
(define dns-request/async
  (make-keyword-procedure
   (λ (keys vals server callback)
     (for ([key (in-list (map keyword->symbol keys))]
           [val (in-list vals)])
       ...))))
```

So far as I can tell, {{< doc racket "make-keyword-procedure" >}} is the easiest / only way to make a procedure that will accept arbitrary keyword parameters. It will pass the keywords and their values as two seperate lists to the procedure given. Any other (non-keyword) parameters will be passed through directly, as is the case here with the `server` and `callback`. Interestingly, the order doesn't matter. The keywords will be pulled out and the order will be saved for the rest.

The for loop will go across the given requests and send each one out in turn. In this case, there's only a single request, setting `key` to `a` and `val` to `"google.com"`. For some reason, `keyword->symbol` doesn't actually exist; however, you can create it easily enough with `keyword->string` and `string->symbol`.

After that, we want to choose a random port and ID for the DNS request. The port will be used in the UDP response listeners and the ID will be used to confirm that the request actually came from us. 

```scheme
...
       ; Choose a random port and id for this request
       (define local-port (+ 10000 (random 1000)))
       (define request-id (random 65536))
       ...
```

After that, we'll use the [bit-struct]({{< ref "2013-09-23-extending-racket-structs-to-bitfields.md" >}}) library to build the actual request.

```scheme
...
       ; Create the request (error on types we don't deal with yet)
       (define request-packet
         (case key
           [(a)
            (dns->bytes
             (build-dns
              #:id request-id
              #:rd 1
              #:qdcount 1
              #:data
              (bytes-append          ; query / question
               (encode-hostname val) ; query is the hostname
               (bytes 0 1)           ; query type  (1 = Type A, host address)
               (bytes 0 1)           ; query class (1 = IN, Internet address)
               )))]
           [else
            (error 'dns-request "unknown dns type: ~a" key)]))
       ...
```

Here's the DNS bit-struct:

```scheme
; DNS packets
(define-bit-struct dns
  ([id      16]
   [qr      1]  [opcode  4]  [aa      1]  [tc      1]  [rd      1] 
   [ra      1]  [z       3]  [rcode   4]
   [qdcount 16]
   [ancount 16]
   [nscount 16]
   [arcount 16]
   [data    _]))
```

Most of these values can be set to 0 (which is the default if they aren't specified). The only ones we need are the ID we specified earlier, `#:rd 1` which states that we want a recursive query, and `#:qdcount 1` showing that we have a single question.

The data format is a bit strange, but since it was specified with `_`, it wants `bytes` rather than an integer. In this case, the hostname encoded in a particular manner, than the query type and class (2-byte one for an IPv4 A record).

The hostname encoding is a sequence of bytes. For each part of the hostname, return one byte that signifies the number of bytes following, then those bytes. So to encode `www.google.com`, we'll need:

```scheme
\3www\6google\3com\0
```

Here's how to do that:

```scheme
; Encode a hostname in the way DNS expects
(define (encode-hostname hostname)
  (bytes-append
   (apply
    bytes-append
    (for/list ([part (in-list (string-split hostname "."))])
      (bytes-append
       (bytes (string-length part))
       (string->bytes/latin-1 part))))
   (bytes 0)))
```

After we have the packet, we'll get a UDP port using the code we defined earlier: 

```scheme
...
       ; Get a socket
       (define socket (get-socket local-port))
       ...
```

Next we want to fix the callback this library is expecting and convert it to the form that the UDP library is expecting. Essentially, we want to parse any results from the UDP listener as a DNS packet and verify that it matches the ID we sent. If that's all true, we also want to try to parse any answers returned:

```scheme
...
       ; Enhance the callback to make sure the response is actually DNS
       (define (real-callback remote-host remote-port buffer)
         (define dns-packet
           (with-handlers ([exn? (λ (err) #f)])
             (bytes->dns buffer)))

         (when (and dns-packet
                    (= (dns-id dns-packet) request-id)
                    (= (dns-qr dns-packet) 1)
                    (= (dns-z dns-packet) 0))
           (callback remote-host key val (parse-dns-response dns-packet))))

       ; Listen for that on the UDP response
       (add-socket-listener! local-port real-callback)

       ; After the given timeout, remove it again
       (when (current-dns-timeout)
         (thread 
          (thunk 
           (sleep (current-dns-timeout))
           (remove-socket-listener! local-port real-callback))))
       ...
```

If the packet doesn't match, the `callback` simply isn't called. We'll come back to the `parse-dns-response` function in a moment. After that, attached the listener to the UDP library. If we have a timeout set, create a new thread here that will automatically remove it after the given time has passed. 

And with that, all that's left is to actually send the packet. `udp-send-to` will set the destination for us, everything else has already been done in `get-socket`.

```scheme
...
       ; Send the packet
       (udp-send-to socket server 53 request-packet)))))
```

53 is the standard port for UDP DNS requests. 

That's actually all we need. Granted, we still want to write the synchronous version and deal with parsing the responses. But we're well on the way.

First, the synchronous version:

```scheme
; Make a DNS request, block until the first response is received
; If multiple requests are specified only the first to return will be returned
; Timeouts after `current-dns-timeout` seconds
(define dns-request
  (make-keyword-procedure
   (λ (keys vals server)
     ; Values to set in the callback
     (define response (void))
     (define response-semaphore (make-semaphore 0))

     ; Make the async request, pass callback setting our values
     (keyword-apply 
      dns-request/async
      keys vals
      (list server
            (λ response-data
              (set! response response-data)
              (semaphore-post response-semaphore))))

     ; Wait until we have a response
     (sync/timeout
      (current-dns-timeout)
      [handle-evt
       response-semaphore
       (λ _ response)]))))
```

Essentially, we create our own callback (the second starting `(λ response-data ...)`). Since our semaphore starts at 0, it will block the `sync/timeout` until it has a non-zero value--as incremented by `semaphore-post`. If `(current-dns-timeout)` happens to be `#f`, `sync/timeout` will do exactly what we want and never time out. In all cases, we directly return the response if we get one. Otherwise, `sync/timeout` will return `#f`.

Finally, we need to actually deal with the parsing. 

```scheme
; Parse a DNS response
(define (parse-dns-response packet)
  ; Get the hostname out of the query (which theoretically we sent)
  (define-values (query-length query-hostname)
    (decode-hostname (dns-data packet) 0))

  ; Make sure we got a response
  (define rcode (decode-rcode (dns-rcode packet)))
  (define answers (dns-ancount packet))

  (cond
    ; Valid response with at least one answer
    [(and (eq? rcode 'no-error) (> answers 0))
     (define data (dns-data packet))
     (let loop ([c 0]
                [i (+ query-length 4)]
                [answers '()])
       (cond
         ; Done, return
         [(or (>= c (dns-ancount packet))
              (>= i (bytes-length data)))
          (cons rcode (reverse answers))]
         ; Add another response
         [else
          (define-values (answer-length answer-hostname) (decode-hostname data i))
          (define answer-type     (bytes->number data (+ i answer-length 0) (+ i answer-length 2)))
          (define answer-class    (bytes->number data (+ i answer-length 2) (+ i answer-length 4)))
          (define answer-ttl      (bytes->number data (+ i answer-length 4) (+ i answer-length 8)))
          (define answer-rdlength (bytes->number data (+ i answer-length 8) (+ i answer-length 10)))
          (define answer-rdata    (subbytes      data (+ i answer-length 10) (+ i answer-length 10 answer-rdlength)))

          ; We're only interested in A records
          (cond
            ; Got an a record
            [(= answer-type 1)
             ; Decode the answer IP address
             (define answer-ip (string-join (map number->string (bytes->list answer-rdata)) "."))
             (loop (+ c 1) 
                   (+ i answer-length 10 answer-rdlength)
                   (cons (list 'A answer-class answer-ip) answers))]
            ; Got something else, just record it
            [else
             (loop (+ c 1) 
                   (+ i answer-length 10 answer-rdlength)
                   (cons (list answer-type answer-class answer-rdata)))])]))]
    ; Reponse is not data
    [else
     (list rcode)]))
```

That's certainly a sizeable chunk of code, but it should be relatively straight forward. Essentially, we'll make sure we actually have answers. If we do, loop through processing one at a time. It's not as clean as I would like, since the the answers can be of variable length, but it's still relatively straight forward. We could also re-use the `bit-struct` library to parse the type, class, TTL, and data length, but because the answer name is a variable length (it uses the same format we discussed earlier), it's not particularly straight forward[^3].

Other than that, we're just returning a list of pairs, where each pair is the record type and the decoded data. So far, we only know how to deal with class 1 A records and their IPs, but I'll add more as I go. For the most part, data will be IPv4 / IPv6 addresses, hostnames, and occasionally raw text. 

One oddity here that I hadn't previously mentioned is that you don't always have to encode the hostname as I mentioned above. Since DNS packets are generally limited to only 512 bytes, every bit saved is worth it. To that end, they have pointers that allow you to reference other hostnames previously defined. Something like this:

```scheme
; Read a DNS encoded hostname, return bytes read and the name
(define (decode-hostname buffer [start 0])
  (cond
    ; Not enough data
    [(>= start (bytes-length buffer))
     (values 0 #f)]
    ; Pointer based hostname
    [(>= (bytes-ref buffer start) 64)
     (values 2
             (format "pointer: ~x~x"
                     (bytes-ref buffer start)
                     (bytes-ref buffer (+ start 1))))]
    ; Normal hostname
    [else
     (let loop ([i start] [chunks '()])
       (cond
         [(= 0 (bytes-ref buffer i))
          (values
           (+ 1 (length chunks) (apply + (map bytes-length chunks)))
           (string-join (reverse (map bytes->string/utf-8 chunks)) "."))]
         [else
          (define length (bytes-ref buffer i))
          (define chunk (subbytes buffer (+ i 1) (+ i 1 length)))
          (loop (+ i 1 length) (cons chunk chunks))]))]))
```

And that's all we need to get everything working. Let's try it out:

```scheme
> (dns-request "8.8.4.4" #:a "google.com")
'("8.8.4.4"
  a
  "google.com"
  (no-error
   (A 1 "74.125.225.68") (A 1 "74.125.225.71") (A 1 "74.125.225.72")
   (A 1 "74.125.225.78") (A 1 "74.125.225.67") (A 1 "74.125.225.73")
   (A 1 "74.125.225.64") (A 1 "74.125.225.69") (A 1 "74.125.225.66")
   (A 1 "74.125.225.70") (A 1 "74.125.225.65")))
```

That's a fair few IP addresses. :smile: What if we try the asyncronous version:

```scheme
> (define (callback host type query response)
    (printf "~a says ~a for ~a is at ~a\n" host query type response))
> (dns-request/async "8.8.4.4" #:a "google.com" callback)
> (dns-request/async "8.8.4.4" #:a "facebook.com" callback)
8.8.4.4 says google.com for a is at (no-error (A 1 74.125.225.69) ...)
8.8.4.4 says facebook.com for a is at (no-error (A 1 173.252.110.27))
```

That way we can send more than one request at a time and deal with them as we come back. Perfect for what I'm working on. I'll have another post about that when it's done--either later this week or early next. *fingers crossed*

If you'd like to see the entire code for this project thus far, you can see it on GitHub: <a href="https://github.com/jpverkamp/dns-world-scan">jpverkamp/dns-world-scan</a>. It's still very much a work in progress, but it may just be useful.

[^1]: It's my programming languages background coming out. :smile:
[^2]: Why is it racket/udp rather than net/udp?
[^3]: I should add some sort of way to add simple parsing functionality at some point...