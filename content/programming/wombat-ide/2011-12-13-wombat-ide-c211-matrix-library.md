---
title: Wombat IDE - C211 Matrix Library
date: 2011-12-13 04:55:34
programming/languages:
- Java
- Scheme
series:
- Wombat IDE
---
For the final exam, I've added a matrix API. The students are supposed to have implemented this, but we know that haven't, so this way they can either use their version or mine.

Matrix API (Edit: The most up to date Matrix API can be found <a title="C211 Matrix API" href="http://www.cs.indiana.edu/cgi-pub/c211/wombat/docs/c211-matrix.htm">here</a>):

<!--more-->


* `(make-matrix i j)` - create a new matrix with `i` rows and `j` columns
* `(matrix-rows m)` - determine the number of rows in a matrix
* `(matrix-cols m)` - determine the number of columns in a matrix
* `(matrix-ref m i j)` - get the value at row `i` and column `j` of a matrix `m`
* `(matrix-set! m i j v)` - set the value stored in the matrix at row `i` and column `j` of matrix `m` to a new value `v`
* `(matrix-generator i j proc)` - generate an `i` x `j` matrix by calling the function `proc` of the form `(i j -> value)` at each row `i` and column `j` in the matrix

It's very similar to the image API and that's by design. It should be easy enough to convert from one to the other if need be.

<a title="Wombat Download Page" href="http://www.cs.indiana.edu/cgi-pub/c211/wombat/">1.346.23</a> is the newest version (and has the matrix API included).