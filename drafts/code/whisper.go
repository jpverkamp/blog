package main

import (
	"fmt"
	"math/rand"
	"time"
)

func f(id int, left, right chan string) {
	msg := []rune(<-right)

	i := rand.Intn(len(msg) - 1)

	c := msg[i]
	msg[i] = msg[i + 1]
	msg[i + 1] = c

	left <- string(msg)
}

func main() {
	rand.Seed(time.Now().UTC().UnixNano())

	start := time.Now()

	const n = 100000
	leftmost := make(chan string)
	right := leftmost
	left := leftmost
	for i := 0; i < n; i++ {
		right = make(chan string)
		go f(i, left, right)
		left = right
	}

	go func(c chan string) {
		c <- "The quick brown fox jumps over the lazy dog."
	}(right)

	fmt.Println(<-leftmost)
	fmt.Println(time.Now().Sub(start))
}
