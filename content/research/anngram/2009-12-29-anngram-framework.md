---
title: AnnGram - Framework
date: 2009-12-29 05:05:28
programming/languages:
- .NET
- C#
programming/topics:
- Computational Linguistics
- Natural Language Processing
- Neural Networks
- Research
---
**Document Framework**

The first portion of the framework that it was necessary to code was the ability to load documents.  To reduce the load on the processor when first loading the document, only a minimal amount of computation is done.  Further computation is pushed off until necessary.

To avoid duplicating work, the n-grams are stored using {{< wikipedia "memoization" >}}.  The basic idea is that when a function (in this case, a particular length of n-gram) is first requested, the calculation is done and the result is stored in memory.  During any future calls, the cached result is directly returned, greatly increasing speed at the cost of memory.  Luckily, modern computers have more than sufficient memory for the task at hand.

<!--more-->

A number of document options were included in the processing:

* Collapse whitespace - treat any amount of whitespace as a single space
* Ignore case - treat all characters as upper case letters
* Ignore non-alphanumeric - Ignore characters other than letters and numbers
* Ignore rare words - Ignore n-grams that occur less than a certain amount of the time
* Ignore whitespace - Completely remove whitespace

By default, collapse whitespace, ignore case, ignore non-alphanumeric, and ignore rare words are enabled (with a default threshold of 0.01%).

**Author Framework**

The author framework merely extends the document framework by combining all of the n-grams in each document written by that author.  To better reuse code, both the Document and Author framework inherit most of their code from a super class containing shared code.  Only the code that specifically generates n-gram data is implemented in the individual frameworks.