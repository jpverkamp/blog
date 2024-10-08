---
title: Large scale asynchronous DNS scans
date: 2013-09-27 14:00:11
programming/languages:
- Racket
- Scheme
programming/topics:
- Bitfields
- DNS
- Data Structures
- Networks
---
On Monday we [laid out a framework]({{< ref "2013-09-23-extending-racket-structs-to-bitfields.md" >}}) for converting structures into bytes. On Wednesday, we used that to [enhance Racket's UDP and DNS capabilities]({{< ref "2013-09-25-extending-racket-s-dns-capabilities.md" >}}). Today, we're going to take that all one step further and scan large portions of the Internet. The end goal will be to look for [DNS-based]({{< ref "2013-02-09-isma-2013-aims-5.md" >}}) on a worldwide scale.

<!--more-->

To that end, there are several steps that we're going to want to go through:


* Process any command line parameters (so I can tune the results)
* Load lists of targets, resolvers, and IP to country mappings
* Find a set of active resolvers in as many countries as we can
* Scan each target at each active resolver
* Analyze results, looking for signs of censorship


Let's start at the top. First, we're going to be using <a href="http://www.alexa.com/">Alexa Top sites</a> for our targets. This should give us at least a list of sites that would be popular enough to attract a censor's notice, although by no means an obvious one. Second, we'll be using the <a href="http://dev.maxmind.com/geoip/legacy/geolite/">MaxMind GeoLite free database</a> to look up the country for a given IP address. They're all fine data sources, but we do want to tune a few parameters. Racket's {{< doc racket "command-line" >}} function will do exactly what we want:

```scheme
; ----- ----- ----- ----- -----
; 0) Get command line parameters

(define alexa-top-n (make-parameter 100))
(define resolvers/country (make-parameter 5))
(define timeout (make-parameter 5.0))

(command-line
 #:program "scan.rkt"
 #:once-each
 [("-n" "--alexa-top-n")
  n
  "Scan the top n Alexa ranked sites (default = 100)"
  (alexa-top-n (string->number n))]
 [("-r" "--resolvers")
  r
  "The maximum number of resolvers to use per country (default = 5)"
  (resolvers/country (string->number r))]
 [("-t" "--timeout")
  t
  "Timeout for DNS requests (default = 5.0 seconds)"
  (timeout (string->number t))])
```

The structure of each part within `#:once-each` block has four parts:


* A list containing the short and long forms of the argument
* The variable that will be bound to the arguments value (as a string)
* Help text to display when the user requests `--help`
* Code to run with the aforementioned parameter


{{< doc racket "Parameters" >}} do help with this, allowing for mutation of a sort. Straight forward. Next we load the data. First, check to make sure that the definitions we need exist:

```scheme
; ----- ----- ----- ----- -----
; 1) Load data

(unless (and (file-exists? "targets.txt")
             (file-exists? "resolvers.txt")
             (file-exists? "ip-mappings.csv"))
  (for-each displayln
            '("Error: Data file(s) not found. Please ensure that the following files exist:"
              "- targets.txt - a list of hostnames (one per line) to scan"
              "- resolvers.txt - a list of open DNS resolvers (one per line) to scan with"
              "- ip-mappings.csv - a list of IP -> country mappings (numeric-ip-from, numeric-ip-to, ip-from, ip-to, country)"))
  (exit))
```

Next, let's load in the list of targets. This isn't strictly the file you can get from Alexa, but rather a list of hostnames, one per line. We could read them in directly with the {{< doc racket "file->lines" >}} function, but that does more work that strictly speaking we need (since we only want the first `alexa-top-n` of them). So instead, we'll use a `for` loop with multiple conditions--with this form, they stop as soon as the first iterator to run out does:

```scheme
; 1a) Load list of targets (dynamically?) (Alexa Top n)
(debug "Loading list of targets, keeping top ~a" (alexa-top-n))
(define targets
  (call-with-input-file "targets.txt"
    (λ (fin)
      (for/list ([i (in-range (alexa-top-n))]
                 [line (in-lines fin)])
        line))))
```

Resolvers is going to be much the same. It will be a list of IPs, one per line. This time we can use {{< doc racket "file->lines" >}}:

```scheme
; 1b) Load list of resolvers (from Drew)
(debug "Loading resolvers")
(define resolvers (file->lines "resolvers.txt"))
```

Finally, we want to be able to map IPs to countries. We'll use MaxMind's data for this. Their file (at least the one we'll use) is a list of comma-separated values of the following form:

`from-ip, to-ip, numeric-from, numeric-to, country code, country`

The third and fourth entries are the IPs from the first and second, just in a numeric form. If you have the IP 8.7.245.0, you get 8*256<sup>3</sup>+7*256<sup>2</sup>+245*256+0 = 134739200. For example:

`"8.7.245.0","8.10.6.242","134739200","134874866","US","United States"`

It's not perfect, but it's certainly something we can massage into shape. But what we really want is a lookup to turn an IP into a country. If we turn the data into a sorted vector, we can do a [[wiki:binary search]]() to perform the lookups much more quickly.

The format isn't particularly optimal, but we can massage it easily enough. What we really want though is to be able to search it. So what we'll do is build a function that contains the data as a sorted vector. That way we can use a [[wiki:binary search]]() to (much) more quickly scan through

```scheme
; 1c) Load list of IP/country mappings (dynamically?) (GeoMind Lite)
; format is csv: ip-from, ip-to, numeric-from, numeric-to, code, country
; Lookup using a binary search
(debug "Loading IP -> country database")
(define ip->country
  ; Load data into a sorted vector of lists: numeric-from, numeric-to, country
  (let ([data
         (list->vector
          (sort
           (for/list ([line (in-list (file->lines "ip-mappings.csv"))])
             (match-define (list-rest _ _ ip-from ip-to cc country)
               (string-split line ","))
             (list (string->number (string-trim ip-from "\""))
                   (string->number (string-trim ip-to "\""))
                   (string-trim
                    (string-join
                     (reverse (map (λ (x) (string-trim x "\"")) country)) " "))))
           (λ (a b)
             (< (first a) (first b)))))])
    ; Perform a binary search for the given IP
    (λ (ip)
      (cond
        [(string? ip) (ip->country (ip->number ip))]
        [else
         (let loop ([lo 0] [hi (vector-length data)])
           (define mid (quotient (+ lo hi) 2))
           (match-define (list ip-from ip-to country) (vector-ref data mid))
           (cond
             [(<= ip-from ip ip-to) country]
             [(or (= lo mid)
                  (= mid hi))       #f]
             [(< ip ip-from)        (loop lo mid)]
             [(> ip ip-to)          (loop mid hi)]
             [else                  (error 'ip->country "unknown ip ~a" ip)]))]))))
```

Now we get to the interesting part. The next part that we want to do is to narrow the full list of resolvers. No matter how quickly our code runs, it's not going to be easily able to run tens of thousands of queries on tens of millions of resolvers in a reasonable amount of time. All we really want is ~5 resolvers per country.

First, let's reorganize our list of resolvers by country. Technically, we could have done this as we loaded them, but it's quick enough, let's do it now:

```scheme
; ----- ----- ----- ----- -----
; 2) Find a small set of resolvers per country

; 2a) Split the list of resolvers by country
(debug "Reorganizing resolvers by country")
(define resolvers-by-country (make-hash))
(for ([ip (in-list resolvers)])
  (with-handlers ([exn? (λ _ (printf "skipping ~an" ip))])
    (define country (ip->country ip))
    (when country
      (define new-set (set-add (hash-ref! resolvers-by-country country (set)) ip))
      (hash-set! resolvers-by-country country new-set))))
```

The {{< doc racket "with-handlers" >}} part isn't strictly speaking necessary, but my list of resolvers has a few non-IPs in it. Rather than filtering them out beforehand, this will just ignore them as we go.

Next, we'll scan them using a reference hostname. For our purposes, we're using `www.google.com`, seeing as it's likely to be well known enough to always resolved. There are cases where Google is censored, but for the moment, that doesn't actually matter. We're not looking to see if we get a correct response back, but rather any (valid) response at all. If a resolver times out or returns any return code than `no-error`, ignore it and move on:

```scheme
; 2b) Query random IPs in each country
; 2b-i)  If it returns a valid response, add it to the list
;        Remove any other IPs within the same /n prefix (avoid same ISPs etc)
; 2b-ii) If it doesn't, try the next IP in that country
; 2c) If we have n resolvers for a country, stop looking; if not, go to 2a for them
(debug "Narrowing resolver list to ~a per country" (resolvers/country))
(let ([threads-finished 0])
  (for-each
   thread-wait
   (for/list ([(country ips) (in-hash resolvers-by-country)])
     (thread
      (thunk
       (parameterize ([current-dns-timeout (timeout)])
         (let loop ([ips (shuffle (set->list ips))]
                    [active '()])
           (cond
             ; No more IPs to scan or found enough
             [(or (null? ips)
                  (>= (length active) (resolvers/country)))
              (set! threads-finished (+ threads-finished 1))
              (debug "~a/~a: ~a is ~a (~a active) -- ~a" threads-finished (hash-count resolvers-by-country) country (if (>= (length active) (resolvers/country)) "out" "full") (length active) active)
              (hash-set! resolvers-by-country country active)]
             ; Got a response, check for no-error and record
             [(dns-request (first ips) #:a "www.google.com")
              => (λ (response)
                   (match-define (list who what where result) response)
                   (cond
                     [(and (eq? (first result) 'no-error)
                           (not (null? (rest result))))
                      (loop (rest ips) (cons (first ips) active))]
                     [else
                      (loop (rest ips) active)]))]
             ; Response timed out
             [else
              (loop (rest ips) active)]))))))))
```

We're using the same technique as several times before with the `cond` and `=>` clause. Since `dns-request` returns `#f` if it times out, it will fall through to the last case, removing that IP but not recording it as active. The first clause is our base case--if we either run out of IPs to check for a given country or find enough, we can stop.

One bit that's interesting is the first few lines. `(for-each thread-wait (for/list ...))` will build up the list of threads first (since parameters are evaluated before being sent to the function in Scheme/Racket) and then wait for each of them to finish in turn. This way, we're scanning all of the known countries at once (there are almost 200 of them in the list of resolvers I have) while each country is done sequentially. This does slow the code down a bit when we get to a particularly troublesome country, but it still runs quickly enough.

Finally, we have the actual body of the code. After all of that set up, the code is actually pretty short:

```scheme
; ----- ----- ----- ----- -----
; 3) Query targets on each resolver
;    Group by target, for Alexa Top 100 and 5 resolvers/country:
;      100 requests/resolver
;      1000 requests/pass

(define output-filename (format "output-~a.txt" (current-milliseconds)))
(debug "Running queries (output to ~a):" output-filename)

(call-with-output-file output-filename
  (λ (fout)
    (define s (make-semaphore 1))
    (parameterize ([current-dns-timeout (timeout)])
      (for ([i (in-naturals 1)]
            [target (in-list targets)])
        (debug "tScanning ~a/~a: ~a" i (alexa-top-n) target)
        (for* ([(country ips) (in-hash resolvers-by-country)]
               [ip (in-list ips)])
          (dns-request/async
           ip #:a target
           (λ (host type query response)
             (define result (list* host country query response))
             (call-with-semaphore
              s
              (thunk
               (write result fout)
               (newline fout)
               (flush-output fout))))))
        (sleep (+ 1.0 (timeout)))))))
```

Rather than parallelizing by country, this time we will be target. We'll take all of the resolvers we've found (up to a thousand) and ask all of them at once about a given target asynchronously. Any responses we get will call the provided callback, writing them to file (with a semaphore to make sure we don't mix lines in the output).

And that's really all there is to it. I'm still analyzing the results, but I've already found a few interesting cases. I'll have another post up about that early next week.

If you’d like to see the entire code for this project thus far (I've added the scanning code now), you can see it on GitHub: <a href="https://github.com/jpverkamp/dns-world-scan">jpverkamp/dns-world-scan</a>. It’s still a work in progress, but it may just be useful.
