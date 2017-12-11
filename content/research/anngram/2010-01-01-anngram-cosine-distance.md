---
title: AnnGram - Cosine Distance
date: 2010-01-01 05:05:00
programming/languages:
- .NET
- C#
programming/topics:
- Computational Linguistics
- Natural Language Processing
- Neural Networks
- Research
---
**Overview**

The first algorithm that I've chosen to implement is a simple cosine difference between the n-gram vectors.  This was the first method used in multiple of the papers that I've read and it seems like a good benchmark.

Essentially, this method gives the similarity of two n-gram documents (either Documents or Authors) as an angle ranging from 0 (identical documents) to {{< inline-latex "\pi/2" >}} (completely different documents).  Documents written by the same author should have the lowest values.

<!--more-->

**Equation**

{{< latex >}}\theta = arccos \left ( \frac{a \cdot b}{|a||b|} \right ){{< /latex >}}

**Example values**

Comparing all of the works of Shakespeare with the Book of Genesis:

* n = 3, θ = 0.132
* n = 4, θ = 0.387
* n = 5, θ = 0.453
* n = 6, θ = 0.527
* average θ = 0.375

Comparing Shakespeare with one of his plays (As You Like It):

* n = 3, θ = 0.083
* n = 4, θ = 0.095
* n = 5, θ = 0.096
* n = 6, θ = 0.083
* average θ = 0.090

As you can see, the basic premise is valid.  Shakespeare is very similar to his own plays and much less so to the Book of Genesis.
