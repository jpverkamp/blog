---
title: Go is faster than Python? (an example parsing huge JSON logs)
date: 2022-02-11
programming/languages:
- Python
- Go
programming/sources:
- Small Scripts
programming/topics:
- Logs
- JSON
- Optimization
---
Recently at work I came across a problem where I had to go through a year's worth of logs and corelate two different fields across all of our requests. On the good side, we have the logs stored as JSON objects (archived from Datadog which collects them). On the down side... it's kind of a huge amount of data. Not as much as I've dealt with at previous jobs/in some academic problems, but we're still talking on the order of terabytes. 

On one hand, write up a quick Python script, fire and forget. It takes maybe ten minutes to write the code and (for this specific example) half an hour to run it on the specific cloud instance the logs lived on. So we'll start with that. But then I got thinking... Python is supposed to be super slow right? Can I do better?

(Note: This problem is mostly disk bound. So Python actually for the most part does just fine.)

<!--more-->

## Problem statement

* Logs contain one JSON object per line
* There are multiple gzipped collections of log files
* The specific requests we are looking at have an object `attributes.log.response.body.user` with `id` and `name` fields
* There are many (*many*) other services with differently formatted logs, we should ignore all lines that don't have the above structure
* We have a specific list of IDs that we're interested in, we want to print the `name` supplied for each `id` *once* as a tab-delimited file

## Version 1: Python

```python
import fileinput
import json
import logging
import os

os.makedirs('output', exist_ok=True)

with open('ids.txt', 'r') as fin:
    target_ids = {
        int(line.strip())
        for line in fin
        if line.strip()
    }

seen_ids = set()

logging.info('Parsing input data')

for line in fileinput.input(openhook=fileinput.hook_compressed):
    line = line.decode()

    try:
        obj = json.loads(line)
        log = obj['attributes']['log']
    except:
        pass

    try:
        id = int(log['response']['body']['user']['id'])
        name = log['response']['body']['user']['name'].split('T')[0]

        if id not in target_ids:
            continue

        if id in seen_ids:
            continue

        print(id, name, sep='\t')

        seen_ids.add(id)
    except:
        pass
```

Okay, at least in my opinion, that's fairly clean code. Easy to write, easy to read, and gets the job done. 

```bash
$ time python3 scan2.py filtered-logs-30days.json.gz > output-python.txt
2022-02-11 03:40:35 INFO Parsing input data

real    2m11.221s
user    1m43.117s
sys     0m2.514s
```

This is a subset of the logs that specifically only deals with 30 days and already filters out most of the requests. Still has about 1/3 of a million records to parse though. I feel like it shouldn't take 2 minutes to do even that, but it gives us a baseline (and those are some very large JSON records). 

## Version 2: Go with the built in JSON library

```go
package main

import (
	"bufio"
	"compress/gzip"
	"encoding/json"
	"fmt"
	"log"
	"os"
	"strconv"
	"strings"
)

var target_ids map[string]bool
var seen_ids map[string]bool

func rget(obj map[string]interface{}, key string) (string, bool) {
	parts := strings.Split(key, "/")

	for _, part := range parts[:len(parts)-1] {
		if value, ok := obj[part]; ok {
			if _, is_map := value.(map[string]interface{}); is_map {
				obj = value.(map[string]interface{})
			} else {
				return "", false
			}
		} else {
			return "", false
		}
	}

	if value, ok := obj[parts[len(parts)-1]]; ok {
		if value_str, ok := value.(string); ok {
			return value_str, true
		}

		if value_int, ok := value.(float64); ok {
			return strconv.Itoa(int(value_int)), true
		}
	}

	return "", false
}

func scan(scanner bufio.Scanner) int {
	var obj map[string]interface{}

	lines_scanned := 0
	for scanner.Scan() {
		line := scanner.Text()
		line_bytes := []byte(line)
		lines_scanned += 1

		if err := scanner.Err(); err != nil {
			log.Fatalf("Failed to scan: %v", err)
		}

		if err := json.Unmarshal(line_bytes, &obj); err != nil {
			continue
		}

		user_id, ok1 := rget(obj, "attributes/log/response/body/user/id")
		name, ok2 := rget(obj, "attributes/log/response/body/user/name")

		if !ok1 || !ok2 {
			continue
		}

		if _, ok := target_ids[user_id]; !ok {
			continue
		}

		if _, ok := seen_ids[user_id]; ok {
			continue
		}
		seen_ids[user_id] = true

		name = strings.Split(name, "T")[0]
		fmt.Printf("%v\t%v\n", user_id, name)
	}

	return lines_scanned
}

func main() {
	target_ids = make(map[string]bool)
	seen_ids = make(map[string]bool)

	{
		f, _ := os.Open("ids.txt")
		defer f.Close()
		s := bufio.NewScanner(f)

		for s.Scan() {
			target_ids[strings.TrimSpace(s.Text())] = true
		}
	}

	lines_scanned := 0
	for _, path := range os.Args {
		log.Printf("Scanning %v\n", path)

		file, err := os.Open(path)
		if err != nil {
			log.Printf("Unable to open %v\n", path)
			continue
		}
		defer file.Close()

		gunzip, err := gzip.NewReader(file)
		if err != nil {
			log.Printf("Unable to gunzip stream from %v\n", path)
			continue
		}
		defer gunzip.Close()

		scanner := bufio.NewScanner(gunzip)

		// https://stackoverflow.com/questions/21124327/how-to-read-a-text-file-line-by-line-in-go-when-some-lines-are-long-enough-to-ca
		buffer := make([]byte, 0, 1024*1024)
		scanner.Buffer(buffer, 1024*1024)

		lines_scanned += scan(*scanner)

		log.Printf("%v lines scanned in %v\n", lines_scanned, path)
	}

	fmt.Printf("%v total scanned\n", lines_scanned)
}
```

Okay, I'll admit. I have not written that much Go code. It's rather verbose... but I think it is nice and readable enough. Certainly a lot of manual error handling, but since I want to catch and pass over those anyways, that's fine. Marshalling the JSON into a `map[string]interface{}` is... a bit weird, but the structs are far far too weird to actually fully define (many different services). That did mean that I had to write the `rget` function that would be able to pull a value out of a deeply nested structure and the types on that got a bit odd. 

But overall, I think it's pretty clean. 

```bash
$ time ./scan filtered-logs-30days.json.gz > output-go.txt
2022/02/11 03:54:32 Scanning ./scan2
2022/02/11 03:54:32 Unable to gunzip stream from ./scan2
2022/02/11 03:54:32 Scanning filtered-logs-30days.json.gz
2022/02/11 03:55:48 365573 lines scanned in filtered-logs-30days.json.gz

real    1m45.055s
user    1m28.048s
sys     0m3.553s
```

Not bad. About twice as fast already. The scanning is a bit ugly though... can we do better? 

One thing that I did absolutely love being able to do:

```bash
$ GOOS=linux GOARCH=amd64 go build scan.go
```

I'm on an M1 Mac, but I was perfectly fine cross compiling for an x86_64 Linux AWS EC2 instance with a single simple command. `scp` the binary and it just runs. How cool is that? 

## Version 3: Go with gjson

```go
package main

import (
	"bufio"
	"compress/gzip"
	"fmt"
	"log"
	"os"
	"strconv"
	"strings"

	"github.com/tidwall/gjson"
)

var target_ids map[int64]bool
var seen_ids map[int64]bool

func scan(scanner bufio.Scanner) int {
	lines_scanned := 0
	for scanner.Scan() {
		line := scanner.Text()
		lines_scanned += 1

		if lines_scanned%100000 == 0 {
			log.Printf("%v lines scanned\n", lines_scanned)
		}

		if err := scanner.Err(); err != nil {
			log.Fatalf("Failed to scan: %v", err)
		}

		gj_user := gjson.Get(line, "attributes.log.response.body.user")
		if !gj_user.Exists() {
			continue
		}

		gj_user_id := gj_user.Get("id")
		if !gj_user_id.Exists() {
			continue
		}

		gj_name := gj_user.Get("name")
		if !gj_name.Exists() {
			continue
		}

		user_id := gj_user_id.Int()
		name := gj_name.String()

		if _, ok := target_ids[user_id]; !ok {
			continue
		}

		if _, ok := seen_ids[user_id]; ok {
			continue
		}
		seen_ids[user_id] = true

        fmt.Printf("%v\t%v\n", user_id, name)
	}

	return lines_scanned
}

func main() {
	target_ids = make(map[int64]bool)
	seen_ids = make(map[int64]bool)

	{
		f, _ := os.Open("ids.txt")
		defer f.Close()
		s := bufio.NewScanner(f)

		for s.Scan() {
			if id, err := strconv.ParseInt(s.Text(), 10, 64); err == nil {
				target_ids[id] = true
			}

		}
	}

	lines_scanned := 0
	for _, path := range os.Args[1:] {
		log.Printf("Scanning %v\n", path)

		file, err := os.Open(path)
		if err != nil {
			log.Printf("Unable to open %v\n", path)
			continue
		}
		defer file.Close()

		gunzip, err := gzip.NewReader(file)
		if err != nil {
			log.Printf("Unable to gunzip stream from %v\n", path)
			continue
		}
		defer gunzip.Close()

		scanner := bufio.NewScanner(gunzip)

		// https://stackoverflow.com/questions/21124327/how-to-read-a-text-file-line-by-line-in-go-when-some-lines-are-long-enough-to-ca
		buffer := make([]byte, 0, 1024*1024)
		scanner.Buffer(buffer, 1024*1024)

		lines_scanned += scan(*scanner)

		log.Printf("%v lines scanned in %v\n", lines_scanned, path)
	}

	fmt.Printf("%v total scanned\n", lines_scanned)
}
```

This time around I'm using a third party library [gjson](https://github.com/tidwall/gjson). They claim to be `fast` and `simple`--and, it's true! It takes the `rget` code I wrote and bundles it up for me in a way that seems a lot better. 

I did learn a good lesson about making sure you deal with `scanner.Err()` though... I have some lines that happen to go over the `scanner` Token default length... which meant it just silently stopped running (since I wasn't catching the err). Oops... (I backported it to the previous solution but found it here...)

```go
if err := scanner.Err(); err != nil {
    log.Fatalf("Failed to scan: %v", err)
}
```

Other than that, nice relatively elegant code and...

```bash
$ time ./scan2 filtered-logs-30days.json.gz > output-go3.txt
2022/02/11 04:19:15 Scanning filtered-logs-30days.json.gz
2022/02/11 04:19:34 100000 lines scanned
2022/02/11 04:19:56 200000 lines scanned
2022/02/11 04:20:17 300000 lines scanned
2022/02/11 04:20:30 365573 lines scanned in filtered-logs-30days.json.gz

real    1m15.648s
user    0m57.985s
sys     0m2.308s
```

Nice! It's slightly faster than the above!

Run it on the full example and now instead of half an hour, we're done in 18 minutes. Granted, I spent more than the difference getting the Go code working. 

[![XKCD has a comic for everything](https://imgs.xkcd.com/comics/is_it_worth_the_time.png)](https://xkcd.com/1205)

Overall, I found it an interesting experience. I hope you do as well. :D